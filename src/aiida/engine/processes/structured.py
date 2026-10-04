###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Reading the fields of a structured type, so that one can say what a namespace of ports holds.

A ``TypedDict``, a dataclass, a ``NamedTuple`` and a ``PortModel`` all say the same thing in different words:
these names, of these types, some of them with a default. A namespace of ports says it too, so a structured type used
as an annotation names one and the ports under it are its fields.

This is the only place that knows which kinds of structured type there are, and it knows nothing about ports in return:
it reads a structured type into :class:`Field`, and whoever wants ports makes them from those. Adding a kind is one
entry in :data:`READERS`.
"""

from __future__ import annotations

import dataclasses
import typing as t

from typing_extensions import NotRequired, Required

__all__ = (
    'Field',
    'PortField',
    'PortModel',
    'Whole',
    'as_dict',
    'build',
    'fields_of',
    'is_structured',
    'marked_whole',
    'without_marks',
)

UNSPECIFIED = object()
"""What a field has instead of a default when it has none, since ``None`` is a default like any other."""


class Whole:
    """Marks a field, or a parameter, as one value rather than as the namespace its fields would name.

    A structured type is usually a wiring surface: one port per field, so a graph fills one of them with what another
    task produced. Where it is opaque data instead, a configuration nobody wires into, this says so and the whole
    of it is one node:

    >>> class Given(PortModel):
    >>>     structure: str
    >>>     config: Annotated[SomeConfig, Whole]

    It is written as metadata of the type rather than as a keyword, so that it reaches a field of a structured type as
    readily as a parameter, and survives in a structured type written for a function somebody else wrote.
    """


@dataclasses.dataclass(frozen=True, kw_only=True)
class PortField:
    """Metadata for an input port, written as ``Annotated[T, PortField(help='...')]``.

    Requiredness remains part of the type or default, rather than being duplicated in this metadata.

    :param help: the help displayed for the generated input port or namespace.
    """

    help: str | None = None


class PortModel:
    """Declare a namespace using annotated fields and optional defaults.

    Subclasses are frozen, keyword-only dataclasses. Values are not coerced or
    validated here: ordinary AiiDA ports perform validation at the boundary.
    """

    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        super().__init_subclass__(**kwargs)
        dataclasses.dataclass(cls, frozen=True, kw_only=True)

    def as_dict(self) -> dict[str, t.Any]:
        """Return the declared fields as a namespace mapping."""
        return t.cast(dict[str, t.Any], as_dict(self))

    @classmethod
    def from_dict(cls, values: t.Mapping[str, t.Any]) -> t.Any:
        """Reconstruct a model, including nested namespaces, from a mapping."""
        return build(cls, values)


@dataclasses.dataclass(frozen=True)
class Field:
    """One field of a structured type, in the words a port is declared with."""

    name: str
    annotation: t.Any
    default: t.Any = UNSPECIFIED
    whole: bool = False
    """Whether the field is one value rather than the namespace its own fields would name."""

    help: str | None = None
    """Help for the input port or namespace this field declares."""

    @property
    def required(self) -> bool:
        """Return whether a value has to be given for this field."""
        return self.default is UNSPECIFIED


def is_structured(annotation: t.Any) -> bool:
    """Return whether the annotation is a structured type, whose fields name the ports of a namespace."""
    return fields_of(annotation) is not None


def is_a_plain_class(annotation: t.Any) -> bool:
    """Return whether the annotation is a class, and not a class with type arguments such as ``Many[int]``.

    Python 3.10 answers `isinstance(list[int], type)` with `True` where 3.11 and up answer `False`, and
    `issubclass` refuses a subscripted class on every version, so asking whether it is a type is not enough.
    """
    return isinstance(annotation, type) and t.get_origin(annotation) is None


def fields_of(annotation: t.Any) -> tuple[Field, ...] | None:
    """Return the fields of a structured type, or ``None`` where the annotation is not one.

    :param annotation: what a parameter or a return value is annotated with.
    """
    if not is_a_plain_class(annotation):
        return None

    for recognises, read in READERS:
        if recognises(annotation):
            return read(annotation)

    return None


def as_dict(value: t.Any) -> dict[str, t.Any] | None:
    """Return what an instance of a structured type holds, by field, or ``None`` where it is not one.

    This is what flattens a structured type into the namespace its fields are taken under, so that each of them is
    stored, validated and wired as the port it is.

    :param value: an instance of a structured type, or anything else.
    """
    if isinstance(value, type):
        return None

    fields = fields_of(type(value))

    if fields is None:
        return None

    return {
        field.name: getattr(value, field.name) if field.whole else _held(getattr(value, field.name)) for field in fields
    }


def _held(value: t.Any) -> t.Any:
    """Return a value as the namespace holds it, which for a structured type of its own is a namespace again."""
    nested = as_dict(value)

    return value if nested is None else nested


def build(container: type, values: t.Mapping[str, t.Any]) -> t.Any:
    """Return an instance of the structured type holding these values.

    This is the way back: a namespace holds what a structured type said it would, so the function that named the
    structured type is handed one rather than the mapping the ports were filled in as.

    :param structured type: the structured type to build.
    :param values: what each of its fields holds, as :func:`as_dict` rendered them.
    """
    fields = {field.name: field for field in fields_of(container) or ()}
    held = {
        name: build(fields[name].annotation, value)
        if name in fields
        and not fields[name].whole
        and isinstance(value, t.Mapping)
        and is_structured(fields[name].annotation)
        else value
        for name, value in values.items()
    }

    if t.is_typeddict(container):
        return dict(held)

    return container(**held)


def _metadata(annotation: t.Any) -> tuple[object, ...]:
    """Read metadata through key-requiredness wrappers, regardless of their nesting order."""
    metadata: list[object] = []
    while (origin := t.get_origin(annotation)) in (t.Annotated, Required, NotRequired):
        args = t.get_args(annotation)
        if origin is t.Annotated:
            metadata.extend(args[1:])
        annotation = args[0]
    return tuple(metadata)


def marked_whole(annotation: t.Any) -> bool:
    """Return whether the annotation is marked as one value rather than as a namespace."""
    return Whole in _metadata(annotation)


def _help(metadata: t.Iterable[object]) -> str | None:
    """Read only explicit port help, leaving unrelated annotation metadata untouched."""
    return next((mark.help for mark in metadata if isinstance(mark, PortField)), None)


def _port_help(annotation: t.Any) -> str | None:
    """Return explicitly annotated input help, or ``None`` when none is declared.

    :param annotation: the type annotation of a field or parameter.
    :return: the help carried by its ``PortField`` metadata.
    """
    return _help(_metadata(annotation))


def without_marks(annotation: t.Any) -> t.Any:
    """Return the type an annotation names, without metadata or key-requiredness wrappers."""
    while t.get_origin(annotation) in (t.Annotated, Required, NotRequired):
        annotation = t.get_args(annotation)[0]
    return annotation


def _required_key(annotation: t.Any, *, fallback: bool) -> bool:
    """Prefer resolved markers over key sets that can be stale with postponed annotations.

    Unmarked inherited fields still need the key sets: the child's totality says nothing about the parent's.
    """
    while (origin := t.get_origin(annotation)) in (t.Annotated, Required, NotRequired):
        if origin is Required:
            return True
        if origin is NotRequired:
            return False
        annotation = t.get_args(annotation)[0]
    return fallback


def _of_typed_dict(annotation: t.Any) -> tuple[Field, ...]:
    """Return the fields of a ``TypedDict``, which are optional where it says they are.

    It records no default, only whether a key has to be there, so an optional field defaults to ``None`` rather
    than to a value the structured type does not have.
    """
    optional = set(getattr(annotation, '__optional_keys__', ()))

    return tuple(
        Field(
            name=name,
            annotation=without_marks(hint),
            default=UNSPECIFIED if _required_key(hint, fallback=name not in optional) else None,
            whole=marked_whole(hint),
            help=_port_help(hint),
        )
        for name, hint in t.get_type_hints(annotation, include_extras=True).items()
    )


def _is_a_named_tuple(annotation: type) -> bool:
    """Return whether the annotation is a ``NamedTuple``, which is a tuple that knows its field names."""
    return issubclass(annotation, tuple) and hasattr(annotation, '_fields')


def _of_named_tuple(annotation: t.Any) -> tuple[Field, ...]:
    """Return the fields of a ``NamedTuple``, whose defaults are the ones it was written with."""
    defaults = getattr(annotation, '_field_defaults', {})
    hints = t.get_type_hints(annotation, include_extras=True)

    return tuple(
        Field(
            name=name,
            annotation=without_marks(hints.get(name)),
            default=defaults.get(name, UNSPECIFIED),
            whole=marked_whole(hints.get(name)),
            help=_port_help(hints.get(name)),
        )
        for name in annotation._fields
    )


def _of_dataclass(annotation: t.Any) -> tuple[Field, ...]:
    """Return the fields of a dataclass, taking a default factory as the value it makes."""
    fields = []
    hints = t.get_type_hints(annotation, include_extras=True)

    for field in dataclasses.fields(annotation):
        if field.default is not dataclasses.MISSING:
            default = field.default
        elif field.default_factory is not dataclasses.MISSING:
            default = field.default_factory()
        else:
            default = UNSPECIFIED

        hint = hints.get(field.name)
        fields.append(
            Field(
                name=field.name,
                annotation=without_marks(hint),
                default=default,
                whole=marked_whole(hint),
                help=_port_help(hint),
            )
        )

    return tuple(fields)


READERS: tuple[tuple[t.Callable[[type], bool], t.Callable[[t.Any], tuple[Field, ...]]], ...] = (
    (t.is_typeddict, _of_typed_dict),
    (_is_a_named_tuple, _of_named_tuple),
    (dataclasses.is_dataclass, _of_dataclass),
)
"""Every kind of structured type that can name a namespace, and how to read its fields.

``PortModel`` subclasses are read by the dataclass reader.
"""
