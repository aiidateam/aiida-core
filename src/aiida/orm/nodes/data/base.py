###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to be used as a base for data containers that represent base python data types."""

from __future__ import annotations

import typing as t
from functools import singledispatch

from aiida.orm.nodes.data.data import Data
from aiida.orm.pydantic import OrmMetadataField

__all__ = ('BaseType', 'from_aiida_type', 'to_aiida_type')


@singledispatch
def to_aiida_type(value):
    """Turns basic Python types (str, int, float, bool) into the corresponding AiiDA types."""
    msg = f'Cannot convert value of type {type(value)} to AiiDA type.'
    raise TypeError(msg)


@singledispatch
def from_aiida_type(node):
    """Return the plain Python value a node holds, and the node itself where it holds none.

    The inverse of :func:`to_aiida_type`, and what hands a task's function what it asked for: a plugin that
    registers how its type is stored registers how it is read back here, beside it.

    >>> @to_aiida_type.register(Molecule)
    >>> def _(value): return MoleculeData(value)
    >>>
    >>> @from_aiida_type.register(MoleculeData)
    >>> def _(node): return node.get_object()

    Anything with no registration is handed back as the node it is, which is what a port annotated with a
    ``Data`` subclass asks for.
    """
    return node


class BaseType(Data):
    """`Data` sub class to be used as a base for data containers that represent base python data types."""

    class AttributesModel(Data.AttributesModel):
        value: t.Any = OrmMetadataField(
            title='Data value',
            description='The value of the data',
        )

    def __init__(self, value=None, **kwargs):
        try:
            getattr(self, '_type')
        except AttributeError:
            raise RuntimeError('Derived class must define the `_type` class member')
        super().__init__(**kwargs)
        self.value = value if value is not None else self._type()

    @property
    def value(self):
        return self.base.attributes.get('value', None)

    @value.setter
    def value(self, value):
        self.base.attributes.set('value', self._type(value))

    def __str__(self):
        return f'{super().__str__()} value: {self.value}'

    def __eq__(self, other):
        if isinstance(other, BaseType):
            return self.value == other.value
        return self.value == other

    def new(self, value=None):
        return self.__class__(value)


@from_aiida_type.register(BaseType)
def _base_type_from_aiida_type(node):
    return node.value
