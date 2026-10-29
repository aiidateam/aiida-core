###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Declare port namespaces using PortModel fields.

Pydantic models declare namespaces too; they validate through ports like PortModels but serialize through
``model_dump`` instead of ``as_dict``.
"""

from __future__ import annotations

import dataclasses
import functools
import operator
import types
import typing as t

from pydantic import BaseModel
from pydantic_core import PydanticUndefined
from typing_extensions import Self, dataclass_transform

from aiida.engine.processes.generic.ports import UNSPECIFIED

__all__ = (
    'PortField',
    'PortModel',
)


@dataclasses.dataclass(frozen=True, kw_only=True)
class PortField:
    """Metadata for a port, written as ``Annotated[T, PortField(help='...')]``.

    :param help: the help displayed for the generated port or namespace.
    """

    help: str | None = None


@dataclass_transform(frozen_default=True, kw_only_default=True, field_specifiers=(dataclasses.field,))
class PortModel:
    """Declare a namespace using annotated fields and optional defaults.

    Subclasses are frozen, keyword-only dataclasses. AiiDA ports validate the
    values; the model itself does not coerce them. Task functions receive
    attribute-accessible namespace mappings, not reconstructed model instances.
    Model instances are optional input/output conveniences. Opaque inputs use ORM nodes.
    """

    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        super().__init_subclass__(**kwargs)
        dataclasses.dataclass(cls, frozen=True, kw_only=True)

    def as_dict(self) -> dict[str, t.Any]:
        """Return the declared fields as a namespace mapping."""
        return {field.name: _namespace_value(getattr(self, field.name)) for field in fields_of(type(self)) or ()}

    @classmethod
    def from_dict(cls, values: t.Mapping[str, t.Any]) -> Self:
        """Reconstruct a model, including nested namespaces, from a mapping.

        :param values: supplied field values.
        :return: the reconstructed model.
        """
        fields = {field.name: field for field in fields_of(cls) or ()}
        return cls(**{name: _rebuild_model_value(fields.get(name), value) for name, value in values.items()})


@dataclasses.dataclass(frozen=True)
class Field:
    """One `PortModel` field."""

    name: str
    annotation: t.Any
    default: t.Any = UNSPECIFIED
    help: str | None = None

    @property
    def required(self) -> bool:
        """Return whether a value has to be given for this field."""
        return self.default is UNSPECIFIED


_ModelAdapter = t.Callable[[t.Any], type[PortModel] | None]
"""Try converting an annotation to a ``PortModel`` subclass; return ``None`` when not applicable."""

_ADAPTERS: list[_ModelAdapter] = []


def _as_port_model(annotation: t.Any) -> t.Any:
    """Rewrite supported model annotations to their ``PortModel`` equivalents, once, at declaration.

    Recurses into union branches and rebuilds the union, so every port mismatch still points at
    one flat declaration per level. The enclosing union still declares a leaf port, so optional
    namespaces remain a follow-up.
    """
    if t.get_origin(annotation) in (t.Union, types.UnionType):
        originals = t.get_args(annotation)
        branches = tuple(_as_port_model(branch) for branch in originals)
        if any(branch is not original for branch, original in zip(branches, originals)):
            return functools.reduce(operator.or_, branches)
        return annotation
    for adapter in _ADAPTERS:
        converted = adapter(annotation)
        if converted is not None:
            return converted
    return annotation


class _NamedTupleClass(t.Protocol):
    """The ``NamedTuple`` surface the adapter reads: fields and their defaults."""

    __name__: str
    _fields: tuple[str, ...]
    _field_defaults: dict[str, t.Any]


def _is_namedtuple_class(annotation: t.Any) -> t.TypeGuard[_NamedTupleClass]:
    """Return whether an annotation is a ``NamedTuple`` subclass."""
    return isinstance(annotation, type) and issubclass(annotation, tuple) and hasattr(annotation, '_fields')


def _pydantic_adapter(annotation: t.Any) -> type[PortModel] | None:
    """Convert a pydantic model, or return ``None`` when not applicable."""
    if not (_is_a_plain_class(annotation) and issubclass(annotation, BaseModel)):
        return None
    return _port_model_from_pydantic(annotation)


def _reject_optional_structured(annotation: t.Any, *, name: str) -> None:
    """Reject optional structured values: optional namespaces are not supported yet."""
    if t.get_origin(_without_marks(annotation)) in (t.Union, types.UnionType):
        branches = [branch for branch in t.get_args(_without_marks(annotation)) if branch is not type(None)]
        if any(is_structured(_as_port_model(branch)) for branch in branches):
            msg = (
                f'`{name}` is an optional structured value; '
                'optional namespaces are not supported yet: declare a required namespace instead.'
            )
            raise TypeError(msg)


def _synthesize_model(name: str, annotations: dict[str, t.Any], defaults: dict[str, t.Any]) -> type[PortModel]:
    """Build a ``PortModel`` subclass from per-field annotations and defaults."""
    namespace: dict[str, t.Any] = {'__annotations__': dict(annotations)}
    namespace.update(defaults)
    return t.cast(type[PortModel], type(f'{name}Model', (PortModel,), namespace))


def _namedtuple_adapter(annotation: t.Any) -> type[PortModel] | None:
    """Convert a ``NamedTuple`` subclass, or return ``None`` when not applicable."""
    if not _is_namedtuple_class(annotation):
        return None
    hints = t.get_type_hints(annotation, include_extras=True)
    annotations: dict[str, t.Any] = {}
    defaults: dict[str, t.Any] = {}
    for name in annotation._fields:
        hint = hints.get(name, t.Any)
        bare = _without_marks(hint)
        adapted = _as_port_model(bare)
        if adapted is bare:
            _reject_non_json_leaf(name, bare, kind='NamedTuple')
        annotations[name] = adapted
        help_text = _port_help(hint)
        if help_text is not None:
            annotations[name] = t.Annotated[adapted, PortField(help=help_text)]
        default = annotation._field_defaults.get(name, UNSPECIFIED)
        if default is not UNSPECIFIED:
            if adapted is not bare and is_structured(adapted):
                default = _adapted_default(default, bare, adapted, call_factory=False)
            defaults[name] = default
    return _synthesize_model(annotation.__name__, annotations, defaults)


_ADAPTERS.extend([_pydantic_adapter, _namedtuple_adapter])


def field_from_annotation(
    name: str,
    annotation: t.Any,
    default: t.Any = UNSPECIFIED,
    help: str | None = None,
) -> Field:
    """Build a :class:`Field` from one annotated declaration.

    This is the extraction half of ``annotation -> port``: strip ``Annotated`` marks for the
    declared type and read ``PortField`` help, falling back to the given help (typically a
    docstring entry). Non-``PortModel`` structured annotations are adapted once, here, so
    downstream code only ever sees ``PortModel``. Conversion of the returned field to ports
    belongs to the spec.

    :param name: the field (port) name.
    :param annotation: the declared annotation, possibly ``Annotated`` with ``PortField``.
    :param default: the declared default, or ``UNSPECIFIED`` when required.
    :param help: fallback help text when the annotation carries none.
    """
    return Field(
        name=name,
        annotation=_as_port_model(_without_marks(annotation)),
        default=default,
        help=_port_help(annotation) or help,
    )


def _is_a_plain_class(annotation: t.Any) -> bool:
    """Return whether an annotation is a class without generic arguments."""
    return isinstance(annotation, type) and t.get_origin(annotation) is None


def is_structured(annotation: t.Any) -> bool:
    """Return whether an annotation directly declares a port namespace.

    Only ``PortModel`` subclasses qualify. Pydantic models and named tuples adapt through
    `fields_of`; `Optional` forms keep their union shape and declare a leaf.
    """
    return _is_a_plain_class(annotation) and issubclass(annotation, PortModel)


def fields_of(annotation: t.Any) -> tuple[Field, ...] | None:
    """Read a structured declaration, or return None for other annotations.

    Non-``PortModel`` structured annotations (e.g. pydantic models) are adapted
    once, here, so every caller sees ``PortModel`` fields regardless of entry point.

    :param annotation: the parameter or return annotation.
    """
    annotation = _as_port_model(_without_marks(annotation))
    if annotation is PortModel or not is_structured(annotation):
        return None
    return _port_model_fields(annotation)


def _port_model_fields(annotation: t.Any) -> tuple[Field, ...]:
    """Read the fields of a `PortModel` subclass."""
    hints = t.get_type_hints(annotation, include_extras=True)
    fields = []
    for declared in dataclasses.fields(annotation):
        if not declared.init:
            continue
        hint = hints.get(declared.name)
        bare = _without_marks(hint)
        adapted = _as_port_model(bare)
        if adapted is not bare and is_structured(adapted):
            if declared.default is not dataclasses.MISSING:
                default = _adapted_default(declared.default, bare, adapted, call_factory=False)
            elif declared.default_factory is not dataclasses.MISSING:
                default = _adapted_default(declared.default_factory, bare, adapted, call_factory=True)
            else:
                default = UNSPECIFIED
        elif declared.default is not dataclasses.MISSING:
            default = declared.default
        elif declared.default_factory is not dataclasses.MISSING:
            # Keep the factory itself: ports evaluate callable defaults per launch instead of freezing one value.
            default = declared.default_factory
        else:
            default = UNSPECIFIED
        fields.append(Field(name=declared.name, annotation=adapted, default=default, help=_port_help(hint)))
    return tuple(fields)


def _adapted_default(default: t.Any, bare: t.Any, adapted: t.Any, *, call_factory: bool) -> t.Any:
    """Convert a nested model default to a per-launch ``from_dict`` factory.

    Ports evaluate callable defaults per launch instead of freezing one
    value, so an instance default becomes a factory, and a factory
    default is called first (pydantic may hand us the class itself when
    the factory takes no arguments) and wrapped to convert its result.
    """
    if call_factory:
        default = default()
    if isinstance(default, bare):
        return lambda: adapted.from_dict(_namespace_value(default))
    if callable(default) and not isinstance(default, type):
        return lambda: adapted.from_dict(_namespace_value(default()))
    return default


def _port_model_from_pydantic(annotation: t.Any) -> type[PortModel]:
    """Build the equivalent ``PortModel`` subclass for a pydantic model, once, at declaration.

    Only JSON-native leaves (``str``/``int``/``float``/``bool`` and their ``Optional`` forms) are
    supported. Validators must live in the ``@task`` body. Nested models are adapted recursively,
    so every port mismatch still points at one flat declaration per level.
    """

    _reject_pydantic_validators(annotation)
    hints = t.get_type_hints(annotation, include_extras=True)
    annotations: dict[str, t.Any] = {}
    defaults: dict[str, t.Any] = {}
    for name, info in annotation.model_fields.items():
        hint = hints.get(name, info.annotation)
        bare = _without_marks(hint)
        adapted = _as_port_model(bare)
        if adapted is bare:
            _reject_pydantic_aliases(name, info)
            _reject_non_json_leaf(name, bare, kind='pydantic')
        if info.default is not PydanticUndefined:
            default: t.Any = info.default
        elif info.default_factory is not None:
            # Keep the factory itself: ports evaluate callable defaults per launch instead of freezing one value.
            default = info.default_factory
        else:
            default = UNSPECIFIED
        if adapted is not bare and is_structured(adapted) and default is not UNSPECIFIED:
            default = _adapted_default(default, bare, adapted, call_factory=info.default_factory is not None)
        annotations[name] = adapted
        help_text = _pydantic_help(hint, info)
        if help_text is not None:
            annotations[name] = t.Annotated[adapted, PortField(help=help_text)]
        if default is not UNSPECIFIED:
            defaults[name] = default
    return _synthesize_model(annotation.__name__, annotations, defaults)


def _reject_pydantic_validators(annotation: t.Any) -> None:
    """Reject pydantic validators, which must live in the ``@task`` body instead."""
    decorators = annotation.__pydantic_decorators__
    offenders = [*decorators.field_validators, *decorators.model_validators, *decorators.root_validators]
    if offenders:
        names = ', '.join(sorted(offenders))
        msg = f'`{annotation.__name__}` declares validators ({names}); move validation into the `@task` body instead.'
        raise TypeError(msg)


def _reject_pydantic_aliases(name: str, info: t.Any) -> None:
    """Reject pydantic aliases and exotic population modes: ports are addressed by field name."""
    if info.alias is not None or info.validation_alias is not None or info.serialization_alias is not None:
        msg = f'pydantic field `{name}` uses an alias; ports are addressed by field name, so remove it.'
        raise TypeError(msg)
    if info.frozen or info.exclude:
        msg = f'pydantic field `{name}` is frozen or excluded; declare plain mutable fields instead.'
        raise TypeError(msg)


_JSON_LEAF_TYPES: tuple[type, ...] = (str, int, float, bool)


def _reject_non_json_leaf(name: str, annotation: t.Any, *, kind: str) -> None:
    """Reject model leaves without a JSON-native storage representation."""
    origin = t.get_origin(annotation)
    pending = t.get_args(annotation) if origin in (t.Union, types.UnionType) else (annotation,)
    for raw_option in pending:
        option = _without_marks(raw_option)
        if option is type(None) or option in _JSON_LEAF_TYPES:
            continue
        label = str(option)
        msg = (
            f'{kind} field `{name}` with type `{label}` cannot be stored in provenance; '
            'use a JSON-native leaf (`str`, `int`, `float`, `bool`) instead.'
        )
        raise TypeError(msg)


def _pydantic_help(annotation: t.Any, info: t.Any) -> str | None:
    """Return the help text of a pydantic field, preferring ``PortField`` over ``description``."""
    for mark in info.metadata:
        if isinstance(mark, PortField):
            return mark.help
    return _port_help(annotation) or info.description


def _namespace_value(value: t.Any) -> t.Any:
    """Return a model instance as its namespace mapping, passing other values through."""
    if isinstance(value, PortModel):
        return value.as_dict()
    if isinstance(value, BaseModel):
        return value.model_dump(mode='python')
    if isinstance(value, tuple) and hasattr(value, '_asdict'):
        return value._asdict()
    return value


def _rebuild_model_value(field: Field | None, value: t.Any) -> t.Any:
    """Rebuild a nested model value, passing other values through."""
    if field is None or not isinstance(value, t.Mapping) or not is_structured(field.annotation):
        return value
    return field.annotation.from_dict(value)


def _marks(annotation: t.Any) -> t.Iterator[t.Any]:
    """Yield the metadata marks of a possibly annotated annotation."""
    while t.get_origin(annotation) is t.Annotated:
        args = t.get_args(annotation)
        yield from args[1:]
        annotation = args[0]


def _port_help(annotation: t.Any) -> str | None:
    """Return the help text of a `PortField` mark."""
    for mark in _marks(annotation):
        if isinstance(mark, PortField):
            return mark.help
    return None


def _without_marks(annotation: t.Any) -> t.Any:
    """Return an annotation without its metadata."""
    while t.get_origin(annotation) is t.Annotated:
        annotation = t.get_args(annotation)[0]
    return annotation
