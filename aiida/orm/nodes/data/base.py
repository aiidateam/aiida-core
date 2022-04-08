# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to be used as a base for data containers that represent base python data types."""
from functools import singledispatch

from .data import Data

__all__ = ('BaseType', 'to_aiida_type')


@singledispatch
def to_aiida_type(value):
    """Turns basic Python types (str, int, float, bool) into the corresponding AiiDA types."""
    raise TypeError(f'Cannot convert value of type {type(value)} to AiiDA type.')


class BaseType(Data):
    """`Data` sub class to be used as a base for data containers that represent base python data types."""

    def __init__(self, value=None, **kwargs):
        try:
            getattr(self, '_type')
        except AttributeError:
            raise RuntimeError('Derived class must define the `_type` class member')

        super().__init__(**kwargs)

        self.value = value or self._type()  # pylint: disable=no-member

    @property
    def value(self):
        return self.base.attributes.get('value', None)

    @value.setter
    def value(self, value):
        self.base.attributes.set('value', self._type(value))  # pylint: disable=no-member

    def __str__(self):
        return f'{super().__str__()} value: {self.value}'

    def __eq__(self, other):
        if isinstance(other, BaseType):
            return self.value == other.value
        return self.value == other

    def new(self, value=None):
        return self.__class__(value)
