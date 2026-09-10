"""Collecting declarations onto a class. Mirrors ``aiida.orm.entities``.

There are two declaration channels. Core entities declare their fixed schema in ``_column_fields``;
data subclasses declare their open attributes in ``_attribute_fields``. The latter is a protected
subclass API: plugin authors may define it, but ordinary users have no reason to access it.

Both channels are collected across the MRO into the internal ``_field_declarations`` mapping. A
declaration is deliberately not installed under its own name, leaving that name free for a property
where the stored value and Python value differ.
"""

from __future__ import annotations

import inspect
import typing as t
from collections.abc import Mapping, Sequence

from poc.orm._core.fields import BaseField
from poc.orm._core.qb_fields import QbField, QbFields


class Entity:
    """Base class that collects the declarations of itself and its bases."""

    #: Fixed-schema declarations introduced by a core entity class.
    _column_fields: t.ClassVar[Sequence[BaseField]] = ()

    #: Complete internal declaration mapping, collected across the MRO.
    _field_declarations: t.ClassVar[Mapping[str, BaseField]] = {}

    #: The row this entity is backed by. Every entity has one, and it is what a ``ColumnField``
    #: reads through; the subclass decides its type.
    backend_entity: t.Any

    #: The query view of the collected declarations, one ``QbField`` per declaration.
    fields: t.ClassVar[QbFields] = QbFields()

    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._collect_fields()

    @classmethod
    def _collect_fields(cls) -> None:
        """Collect the declarations, base classes first so a subclass narrows what it inherits."""
        declarations: dict[str, BaseField] = {}

        for klass in reversed(cls.__mro__):
            for channel, is_attribute in (('_column_fields', False), ('_attribute_fields', True)):
                for declaration in vars(klass).get(channel, ()):
                    if not isinstance(declaration, BaseField) or declaration.is_attribute is not is_attribute:
                        kind = 'AttributeField' if is_attribute else 'ColumnField'
                        msg = f'`{klass.__name__}.{channel}` accepts only {kind} declarations'
                        raise TypeError(msg)
                    declarations[declaration.name] = declaration

        cls._field_declarations = declarations
        cls.fields = QbFields(cls._build_query_fields(declarations))

    @classmethod
    def from_model(cls, model: t.Any) -> t.Self:
        """Return an entity built from a validated model of any layer.

        **Which arguments ``__init__`` takes is a fact about this class, not about the layer that
        produced the model**, so it is answered here once rather than in every consuming layer.
        A layer that *encodes* a value differently has already normalised it, in its layer field's
        ``deserialize``, so what arrives here is a domain value whoever asked.

        All this does is hand those values to the constructor. It deliberately does no more: there
        is no general recipe for building an entity -- a constructor may take a ``Computer`` and
        store a primary key, or a directory that becomes repository content, or arguments that are
        no field at all. Whatever a class needs beyond "pass the values through" is that class's
        to write, by overriding this or by taking the arguments in ``__init__``.
        """
        accepted = inspect.signature(cls.__init__).parameters
        takes_kwargs = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in accepted.values())
        published = type(model).model_fields
        return cls(**{name: getattr(model, name) for name in published if takes_kwargs or name in accepted})

    @classmethod
    def _build_query_fields(cls, declarations: Mapping[str, BaseField]) -> dict[str, QbField]:
        """Build the query view of the declarations.

        A hook, so ``Node`` can wire up its attributes namespace.
        """
        return {name: QbField.from_spec(declaration) for name, declaration in declarations.items()}
