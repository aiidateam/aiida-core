"""Data plugin that allows to easily wrap an :class:`enum.Enum` member.

Nomenclature is taken from Python documentation: https://docs.python.org/3/library/enum.html
Given the following example implementation:

.. code:: python

    from enum import Enum
    class Color(Enum):
        RED = 1
        GREEN = 2

The class ``Color`` is an enumeration (or enum). The attributes ``Color.RED`` and ``Color.GREEN`` are enumeration
members (or enum members) and are functionally constants. The enum members have names and values: the name of
``Color.RED`` is ``RED`` and the value of ``Color.RED`` is ``1``.
"""

from __future__ import annotations

import typing as t
from enum import Enum

from typing_extensions import Self

from aiida.common.lang import type_check
from aiida.common.loaders import get_object_loader
from aiida.orm.decorators import attribute
from aiida.orm.nodes.data.base import to_aiida_type
from aiida.orm.nodes.data.data import Data

__all__ = ('EnumData',)

_EnumT = t.TypeVar('_EnumT', bound=Enum)


class EnumData(Data, t.Generic[_EnumT]):
    """Data plugin that allows to easily wrap an :class:`enum.Enum` member.

    The enum member is stored in the database by storing the value, name and the identifier (string that represents the
    class of the enumeration) in the ``KEY_NAME``, ``KEY_VALUE`` and ``KEY_IDENTIFIER`` attribute, respectively. The
    original enum member can be reconstructured from the (loaded) node through the ``get_member`` method. The enum
    itself can be retrieved from the ``get_enum`` method. Like a normal enum member, the ``EnumData`` plugin provides
    the ``name`` and ``value`` properties which return the name and value of the enum member, respectively.
    """

    KEY_NAME = 'name'
    KEY_VALUE = 'value'
    KEY_IDENTIFIER = 'identifier'

    @classmethod
    def from_member(cls, member: Enum, **kwargs: t.Any) -> Self:
        """Construct a new instance for the enum member that is to be wrapped."""
        type_check(member, Enum)

        instance = cls(**kwargs)
        instance.base.attributes.set_many(
            {
                instance.KEY_NAME: member.name,
                instance.KEY_VALUE: member.value,
                instance.KEY_IDENTIFIER: get_object_loader().identify_object(member.__class__),
            }
        )
        return instance

    def __eq__(self, other: t.Any) -> bool:
        """Return whether the other object is equivalent to ourselves."""
        if isinstance(other, Enum):
            try:
                return self.get_member() == other
            except (ImportError, ValueError):
                return False

        if isinstance(other, EnumData):
            return self.base.attributes.all == other.base.attributes.all

        return False

    @attribute(readonly=True)
    def name(self) -> str:
        """The name of the enum member."""
        return self.base.attributes.get(self.KEY_NAME)

    @attribute(readonly=True)
    def value(self) -> object:
        """The value of the enum member."""
        return self.base.attributes.get(self.KEY_VALUE)

    @attribute(readonly=True)
    def identifier(self) -> str:
        """The identifier of the enum member."""
        return self.base.attributes.get(self.KEY_IDENTIFIER)

    @property
    def member(self) -> Enum:
        """Return the enum member wrapped by this node."""
        return self.get_member()

    def get_enum(self) -> type[_EnumT]:
        """Return the enum class reconstructed from the serialized identifier stored in the database.

        :raises `ImportError`: if the enum class represented by the stored identifier cannot be imported.
        """
        identifier = self.identifier

        try:
            return get_object_loader().load_object(identifier)
        except ValueError as exc:
            msg = f'Could not reconstruct enum class because `{identifier}` could not be loaded.'
            raise ImportError(msg) from exc

    def get_member(self) -> _EnumT:
        """Return the enum member reconstructed from the serialized data stored in the database.

        For the enum member to be successfully reconstructed, the class of course has to still be importable and its
        implementation should not have changed since the node was stored. That is to say, the value of the member when
        it was stored, should still be a valid value for the enum class now.

        :raises `ImportError`: if the enum class represented by the stored identifier cannot be imported.
        :raises `ValueError`: if the stored enum member value is no longer valid for the imported enum class.
        """
        value = self.value
        enum: type[_EnumT] = self.get_enum()

        try:
            return enum(value)
        except ValueError as exc:
            msg = (
                f'The stored value `{value}` is no longer a valid value for the enum `{enum}`. The definition must '
                'have changed since storing the node.'
            )
            raise ValueError(msg) from exc

    def _validate(self) -> None:
        """Validate the stored enum metadata."""
        from aiida.common.exceptions import ValidationError

        super()._validate()

        try:
            name = self.name
        except AttributeError as exc:
            raise ValidationError("attribute 'name' not set.") from exc

        try:
            value = self.value
        except AttributeError as exc:
            raise ValidationError("attribute 'value' not set.") from exc

        try:
            self.identifier
        except AttributeError as exc:
            raise ValidationError("attribute 'identifier' not set.") from exc

        try:
            enum = self.get_enum()
        except ImportError as exc:
            raise ValidationError(str(exc)) from exc

        try:
            member = enum(value)
        except ValueError as exc:
            msg = f"The stored value '{value}' is not a valid value for the enum '{enum}'."
            raise ValidationError(msg) from exc

        if member.name != name:
            msg = f"Attribute 'name' says '{name}' but '{member.name}' was reconstructed from the stored value."
            raise ValidationError(msg)


@to_aiida_type.register(Enum)
def _(value: Enum):
    return EnumData.from_member(member=value)
