# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for defintion of base `Data` sub class for numeric based data types."""

from .base import BaseType, to_aiida_type

__all__ = ('NumericType',)


def _left_operator(func):
    """Function decorator to treat a method as the left operator."""

    def inner(self, other):
        """Decorator wrapper."""
        left = self.value
        if isinstance(other, NumericType):
            right = other.value
        else:
            right = other
        return to_aiida_type(func(left, right))

    return inner


def _right_operator(func):
    """Function decorator to treat a method as the right operator."""

    def inner(self, other):
        """Decorator wrapper."""
        assert not isinstance(other, NumericType)
        return to_aiida_type(func(self.value, other))

    return inner


class NumericType(BaseType):
    """Sub class of Data to store numbers, overloading common operators (``+``, ``*``, ...)."""

    @_left_operator
    def __add__(self, other):
        return self + other

    @_right_operator
    def __radd__(self, other):
        return other + self

    @_left_operator
    def __sub__(self, other):
        return self - other

    @_right_operator
    def __rsub__(self, other):
        return other - self

    @_left_operator
    def __mul__(self, other):
        return self * other

    @_right_operator
    def __rmul__(self, other):
        return other * self

    @_left_operator
    def __div__(self, other):
        return self / other

    @_right_operator
    def __rdiv__(self, other):
        return other / self

    @_left_operator
    def __truediv__(self, other):
        return self / other

    @_right_operator
    def __rtruediv__(self, other):
        return other / self

    @_left_operator
    def __floordiv__(self, other):
        return self // other

    @_right_operator
    def __rfloordiv__(self, other):
        return other // self

    @_left_operator
    def __pow__(self, power):
        return self**power

    @_left_operator
    def __lt__(self, other):
        return self < other

    @_left_operator
    def __le__(self, other):
        return self <= other

    @_left_operator
    def __gt__(self, other):
        return self > other

    @_left_operator
    def __ge__(self, other):
        return self >= other

    @_left_operator
    def __mod__(self, other):
        return self % other

    @_right_operator
    def __rmod__(self, other):
        return other % self

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)
