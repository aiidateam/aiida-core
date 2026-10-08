###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Declare port namespaces using PortModel fields."""

from __future__ import annotations

import dataclasses
import typing as t

from typing_extensions import Self, dataclass_transform

__all__ = ('Field', 'PortField', 'PortModel', 'as_dict', 'fields_of', 'is_structured', 'without_marks')

UNSPECIFIED = object()

M = t.TypeVar('M', bound='PortModel')


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
    """One model field in the words a port is declared with."""

    name: str
    annotation: t.Any
    default: t.Any = UNSPECIFIED
    help: str | None = None

    @property
    def required(self) -> bool:
        """Return whether a value has to be given for this field."""
        return self.default is UNSPECIFIED


def is_a_plain_class(annotation: t.Any) -> bool:
    """Return whether an annotation is a class without generic arguments."""
    return isinstance(annotation, type) and t.get_origin(annotation) is None


def is_structured(annotation: t.Any) -> bool:
    """Return whether an annotation declares a PortModel namespace."""
    return is_a_plain_class(annotation) and issubclass(annotation, PortModel)


def fields_of(annotation: t.Any) -> tuple[Field, ...] | None:
    """Read a PortModel declaration, or return None for other annotations.

    :param annotation: the parameter or return annotation.
    """
    if not is_structured(annotation):
        return None
    hints = t.get_type_hints(annotation, include_extras=True)
    fields = []
    for field in dataclasses.fields(annotation):
        if not field.init:
            continue
        if field.default is not dataclasses.MISSING:
            default = field.default
        elif field.default_factory is not dataclasses.MISSING:
            # Keep the factory itself: ports evaluate callable defaults per launch instead of freezing one value.
            default = field.default_factory
        else:
            default = UNSPECIFIED
        hint = hints.get(field.name)
        fields.append(Field(name=field.name, annotation=without_marks(hint), default=default, help=_port_help(hint)))
    return tuple(fields)


def as_dict(value: t.Any) -> dict[str, t.Any] | None:
    """Return a model's namespace values, or None for other values.

    :param value: a model instance or any other value.
    """
    return value.as_dict() if isinstance(value, PortModel) else None


def _namespace_value(value: t.Any) -> t.Any:
    return value.as_dict() if isinstance(value, PortModel) else value


def _rebuild_model_value(field: Field | None, value: t.Any) -> t.Any:
    """Rebuild a nested model value, passing other values through."""
    if field is None or not isinstance(value, t.Mapping) or not is_structured(field.annotation):
        return value
    return build(field.annotation, value)


def build(container: type[M], values: t.Mapping[str, t.Any]) -> M:
    """Reconstruct a model from namespace values.

    :param container: the model class.
    :param values: supplied field values.
    """
    return container.from_dict(values)


def _port_help(annotation: t.Any) -> str | None:
    while t.get_origin(annotation) is t.Annotated:
        args = t.get_args(annotation)
        for mark in args[1:]:
            if isinstance(mark, PortField):
                return mark.help
        annotation = args[0]
    return None


def without_marks(annotation: t.Any) -> t.Any:
    """Return an annotation without its metadata."""
    while t.get_origin(annotation) is t.Annotated:
        annotation = t.get_args(annotation)[0]
    return annotation
