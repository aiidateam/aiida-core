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

from aiida.common import exceptions
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

    def __init__(
        self,
        member: Enum | None = None,
        *,
        name: str | None = None,
        value: object | None = None,
        identifier: str | None = None,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(**kwargs)
        if member is not None:
            self.set_member(member)
        elif name is not None and value is not None and identifier is not None:
            self._set_member_parts(name, value, identifier)

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

    @attribute
    def name(self) -> str:
        """The name of the enum member."""
        return self.base.attributes.get(self.KEY_NAME)

    @name.setter
    def name(self, value: str) -> None:
        type_check(value, str)
        self.base.attributes.set(self.KEY_NAME, value)

    @attribute
    def value(self) -> object:
        """The value of the enum member."""
        return self.base.attributes.get(self.KEY_VALUE)

    @value.setter
    def value(self, value: object) -> None:
        type_check(value, object)
        self.base.attributes.set(self.KEY_VALUE, value)

    @attribute
    def identifier(self) -> str:
        """The identifier of the enum class (<module>:<class>)."""
        return self.base.attributes.get(self.KEY_IDENTIFIER)

    @identifier.setter
    def identifier(self, value: str) -> None:
        type_check(value, str)
        self.base.attributes.set(self.KEY_IDENTIFIER, value)

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

    def set_member(self, member: Enum) -> None:
        """Set the enum member for this node."""
        type_check(member, Enum)
        self._set_member_parts(
            name=member.name,
            value=member.value,
            identifier=get_object_loader().identify_object(member.__class__),
        )

    def _set_member_parts(self, name: str, value: object, identifier: str) -> None:
        """Set the enum member for this node using its individual parts."""
        type_check(name, str)
        type_check(value, object)
        type_check(identifier, str)
        self.base.attributes.set_many(
            {
                self.KEY_NAME: name,
                self.KEY_VALUE: value,
                self.KEY_IDENTIFIER: identifier,
            }
        )

    def _validate(self) -> None:
        super()._validate()

        try:
            name = self.name
        except AttributeError as exc:
            raise exceptions.ValidationError("'name' not set.") from exc

        try:
            value = self.value
        except AttributeError as exc:
            raise exceptions.ValidationError("'value' not set.") from exc

        try:
            self.identifier
        except AttributeError as exc:
            raise exceptions.ValidationError("'identifier' not set.") from exc

        try:
            enum = self.get_enum()
        except ImportError as exc:
            raise exceptions.ValidationError(str(exc)) from exc

        try:
            member = enum(value)
        except ValueError as exc:
            msg = f"The stored value '{value}' is not a valid value for the enum '{enum}'."
            raise exceptions.ValidationError(msg) from exc

        if member.name != name:
            msg = f"Attribute 'name' says '{name}' but '{member.name}' was reconstructed from the stored value."
            raise exceptions.ValidationError(msg)


@to_aiida_type.register(Enum)
def _(value: Enum):
    return EnumData(member=value)
