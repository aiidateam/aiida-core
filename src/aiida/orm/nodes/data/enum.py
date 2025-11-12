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

import typing as t
from enum import Enum

from plumpy.loaders import get_object_loader

from aiida.common.lang import type_check
from aiida.common.pydantic import MetadataField

from .base import to_aiida_type
from .data import Data

__all__ = ('EnumData',)

EnumType = t.TypeVar('EnumType', bound=Enum)


@to_aiida_type.register(Enum)
def _(value):
    return EnumData(member=value)


class EnumData(Data):
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

    class Model(Data.Model):
        member: Enum = MetadataField(
            description='The member name.',
            orm_to_model=lambda node, _: t.cast(EnumData, node).get_member(),
        )

    def __init__(self, member: Enum, *args, **kwargs):
        """Construct the node for the to enum member that is to be wrapped."""
        type_check(member, Enum)
        super().__init__(*args, **kwargs)

        data = {
            self.KEY_NAME: member.name,
            self.KEY_VALUE: member.value,
            self.KEY_IDENTIFIER: get_object_loader().identify_object(member.__class__),
        }

        self.base.attributes.set_many(data)

    @property
    def name(self) -> str:
        """Return the name of the enum member."""
        return self.base.attributes.get(self.KEY_NAME)

    @property
    def value(self) -> t.Any:
        """Return the value of the enum member."""
        return self.base.attributes.get(self.KEY_VALUE)

    def get_enum(self) -> t.Type[EnumType]:
        """Return the enum class reconstructed from the serialized identifier stored in the database.

        :raises `ImportError`: if the enum class represented by the stored identifier cannot be imported.
        """
        identifier = self.base.attributes.get(self.KEY_IDENTIFIER)
        try:
            return get_object_loader().load_object(identifier)
        except ValueError as exc:
            raise ImportError(f'Could not reconstruct enum class because `{identifier}` could not be loaded.') from exc

    def get_member(self) -> EnumType:  # type: ignore[misc, type-var]
        """Return the enum member reconstructed from the serialized data stored in the database.

        For the enum member to be successfully reconstructed, the class of course has to still be importable and its
        implementation should not have changed since the node was stored. That is to say, the value of the member when
        it was stored, should still be a valid value for the enum class now.

        :raises `ImportError`: if the enum class represented by the stored identifier cannot be imported.
        :raises `ValueError`: if the stored enum member value is no longer valid for the imported enum class.
        """
        value = self.base.attributes.get(self.KEY_VALUE)
        enum: t.Type[EnumType] = self.get_enum()

        try:
            return enum(value)
        except ValueError as exc:
            raise ValueError(
                f'The stored value `{value}` is no longer a valid value for the enum `{enum}`. The definition must '
                'have changed since storing the node.'
            ) from exc

    def __eq__(self, other: t.Any) -> bool:
        """Return whether the other object is equivalent to ourselves."""
        if isinstance(other, Enum):
            try:
                return self.get_member() == other
            except (ImportError, ValueError):
                return False
        elif isinstance(other, EnumData):
            return self.base.attributes.all == other.base.attributes.all

        return False
