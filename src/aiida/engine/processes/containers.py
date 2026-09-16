###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Reading the fields of a structured container, so that one can say what a namespace of ports holds.

A ``TypedDict``, a dataclass, a ``NamedTuple`` and a pydantic model all say the same thing in different words:
these names, of these types, some of them with a default. A namespace of ports says it too, so a container used
as an annotation names one and the ports under it are its fields.

This is the only place that knows which kinds of container there are, and it knows nothing about ports in return:
it reads a container into :class:`Field`, and whoever wants ports makes them from those. Adding a kind is one
entry in :data:`READERS`.
"""

from __future__ import annotations

import dataclasses
import typing as t

__all__ = ('Field', 'Whole', 'as_dict', 'build', 'fields_of', 'is_a_container', 'marked_whole', 'without_marks')

UNSPECIFIED = object()
"""What a field has instead of a default when it has none, since ``None`` is a default like any other."""


class Whole:
    """Marks a field, or a parameter, as one value rather than as the namespace its fields would name.

    A container is usually a wiring surface: one port per field, so a graph fills one of them with what another
    task produced. Where it is opaque data instead, a configuration nobody wires into, this says so and the whole
    of it is one node:

    >>> class Given(BaseModel):
    >>>     structure: str
    >>>     config: Annotated[SomeConfig, Whole]

    It is written as metadata of the type rather than as a keyword, so that it reaches a field of a container as
    readily as a parameter, and survives in a container written for a function somebody else wrote.
    """


@dataclasses.dataclass(frozen=True)
class Field:
    """One field of a structured container, in the words a port is declared with."""

    name: str
    annotation: t.Any
    default: t.Any = UNSPECIFIED
    whole: bool = False
    """Whether the field is one value rather than the namespace its own fields would name."""

    @property
    def required(self) -> bool:
        """Return whether a value has to be given for this field."""
        return self.default is UNSPECIFIED


def is_a_container(annotation: t.Any) -> bool:
    """Return whether the annotation is a structured container, whose fields name the ports of a namespace."""
    return fields_of(annotation) is not None


def fields_of(annotation: t.Any) -> tuple[Field, ...] | None:
    """Return the fields of a structured container, or ``None`` where the annotation is not one.

    :param annotation: what a parameter or a return value is annotated with.
    """
    if not isinstance(annotation, type):
        return None

    for recognises, read in READERS:
        if recognises(annotation):
            return read(annotation)

    return None


def as_dict(value: t.Any) -> dict[str, t.Any] | None:
    """Return what an instance of a structured container holds, by field, or ``None`` where it is not one.

    This is what flattens a container into the namespace its fields are taken under, so that each of them is
    stored, validated and wired as the port it is.

    :param value: an instance of a structured container, or anything else.
    """
    if isinstance(value, type):
        return None

    fields = fields_of(type(value))

    if fields is None:
        return None

    kept = {field.name: getattr(value, field.name) for field in fields if field.whole}

    if _is_a_model(type(value)):
        # A model renders its own fields, which is how a value AiiDA has no way to store is stored: whatever the
        # model says it renders to is. Building it back coerces the rendering to the field's own type again. It
        # renders a nested model as well, which is the nested namespace that one names.
        return {**value.model_dump(), **kept}

    return {
        field.name: getattr(value, field.name) if field.whole else _held(getattr(value, field.name)) for field in fields
    }


def _held(value: t.Any) -> t.Any:
    """Return a value as the namespace holds it, which for a container of its own is a namespace again."""
    nested = as_dict(value)

    return value if nested is None else nested


def build(container: type, values: t.Mapping[str, t.Any]) -> t.Any:
    """Return an instance of the container holding these values.

    This is the way back: a namespace holds what a container said it would, so the function that named the
    container is handed one rather than the mapping the ports were filled in as.

    :param container: the structured container to build.
    :param values: what each of its fields holds, as :func:`as_dict` rendered them.
    """
    fields = {field.name: field for field in fields_of(container) or ()}
    held = {
        name: build(fields[name].annotation, value)
        if name in fields
        and not fields[name].whole
        and isinstance(value, t.Mapping)
        and is_a_container(fields[name].annotation)
        else value
        for name, value in values.items()
    }

    if t.is_typeddict(container):
        return dict(held)

    return container(**held)


def marked_whole(annotation: t.Any) -> bool:
    """Return whether the annotation is marked as one value rather than as a namespace."""
    return Whole in t.get_args(annotation)[1:] if t.get_origin(annotation) is t.Annotated else False


def without_marks(annotation: t.Any) -> t.Any:
    """Return the type an annotation names, without the marks written beside it."""
    return t.get_args(annotation)[0] if t.get_origin(annotation) is t.Annotated else annotation


def _is_a_model(annotation: type) -> bool:
    """Return whether the annotation is a pydantic model."""
    from pydantic import BaseModel

    return issubclass(annotation, BaseModel)


def _of_model(annotation: t.Any) -> tuple[Field, ...]:
    """Return the fields of a pydantic model, which says outright which of them are required."""
    return tuple(
        Field(
            name=name,
            annotation=info.annotation,
            default=UNSPECIFIED if info.is_required() else info.get_default(call_default_factory=True),
            whole=Whole in info.metadata,
        )
        for name, info in annotation.model_fields.items()
    )


def _of_typed_dict(annotation: t.Any) -> tuple[Field, ...]:
    """Return the fields of a ``TypedDict``, which are optional where it says they are.

    It records no default, only whether a key has to be there, so an optional field defaults to ``None`` rather
    than to a value the container does not have.
    """
    optional = set(getattr(annotation, '__optional_keys__', ()))

    return tuple(
        Field(
            name=name,
            annotation=without_marks(hint),
            default=None if name in optional else UNSPECIFIED,
            whole=marked_whole(hint),
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
            )
        )

    return tuple(fields)


READERS: tuple[tuple[t.Callable[[type], bool], t.Callable[[t.Any], tuple[Field, ...]]], ...] = (
    (t.is_typeddict, _of_typed_dict),
    (_is_a_model, _of_model),
    (_is_a_named_tuple, _of_named_tuple),
    (dataclasses.is_dataclass, _of_dataclass),
)
"""Every kind of container that can name a namespace, and how to read its fields.

Ordered, since a kind may recognise another: a ``NamedTuple`` is a tuple, and a pydantic model is not a
dataclass but is close enough to one that the dataclass reader would have to be asked last anyway.
"""
