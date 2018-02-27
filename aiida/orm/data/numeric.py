# -*- coding: utf-8 -*-
from aiida.orm.data import to_aiida_type, BaseType


def _left_operator(func):
    def inner(self, other):
        l = self.value
        if isinstance(other, NumericType):
            r = other.value
        else:
            r = other
        return to_aiida_type(func(l, r))
    return inner


def _right_operator(func):
    def inner(self, other):
        assert not isinstance(other, NumericType)
        return to_aiida_type(func(self.value, other))
    return inner


class NumericType(BaseType):
    """
    Specific subclass of :py:class:`BaseType` to store numbers,
    overloading common operators (``+``, ``*``, ...)
    """
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
    def __pow__(self, power):
        return self ** power

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

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)