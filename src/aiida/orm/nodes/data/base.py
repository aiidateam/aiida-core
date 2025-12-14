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

from aiida.common.pydantic import MetadataField

from .data import Data

__all__ = ('BaseType', 'to_aiida_type')


@singledispatch
def to_aiida_type(value):
    """Turns basic Python types (str, int, float, bool) into the corresponding AiiDA types."""
    raise TypeError(f'Cannot convert value of type {type(value)} to AiiDA type.')


class BaseType(Data):
    """`Data` sub class to be used as a base for data containers that represent base python data types."""

    class AttributesModel(Data.AttributesModel):
        value: t.Any = MetadataField(
            ...,
            title='Data value',
            description='The value of the data',
        )

    def __init__(self, value=None, **kwargs):
        try:
            getattr(self, '_type')
        except AttributeError:
            raise RuntimeError('Derived class must define the `_type` class member')

        value = value or kwargs.get('attributes', {}).pop('value', None)

        super().__init__(**kwargs)

        self.value = value or self._type()

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
