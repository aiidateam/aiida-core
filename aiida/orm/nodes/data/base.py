# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to be used as a base for data containers that represent base python data types."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import abc
import six

try:
    from functools import singledispatch  # Python 3.4+
except ImportError:
    from singledispatch import singledispatch

from .data import Data

__all__ = ('BaseType', 'to_aiida_type')


@singledispatch
def to_aiida_type(value):
    """
    Turns basic Python types (str, int, float, bool) into the corresponding AiiDA types.
    """
    raise TypeError("Cannot convert value of type {} to AiiDA type.".format(type(value)))


@six.add_metaclass(abc.ABCMeta)
class BaseType(Data):
    """`Data` sub class to be used as a base for data containers that represent base python data types."""

    def __init__(self, *args, **kwargs):
        try:
            getattr(self, '_type')
        except AttributeError:
            raise RuntimeError('Derived class must define the `_type` class member')

        super(BaseType, self).__init__(**kwargs)

        try:
            value = args[0]
        except IndexError:
            value = self._type()  # pylint: disable=no-member

        self.value = value

    @property
    def value(self):
        return self.get_attribute('value', None)

    @value.setter
    def value(self, value):
        self.set_attribute('value', self._type(value))  # pylint: disable=no-member

    def __str__(self):
        return super(BaseType, self).__str__() + ' value: {}'.format(self.value)

    def __eq__(self, other):
        if isinstance(other, BaseType):
            return self.value == other.value
        return self.value == other

    def __ne__(self, other):
        if isinstance(other, BaseType):
            return self.value != other.value
        return self.value != other

    def new(self, value=None):
        return self.__class__(value)
