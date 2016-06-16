# -*- coding: utf-8 -*-
from aiida.orm import Data

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Andrius Merkys, Giovanni Pizzi, Martin Uhrin, Nicolas Mounet"


class SimpleData(Data):
    def set_typevalue(self, typevalue):
        _type, value = typevalue
        self._type = _type
        if value:
            self.value = value
        else:
            self.value = _type()

    @property
    def value(self):
        return self.get_attr('value')

    @value.setter
    def value(self, value):
        self._set_attr('value', self._type(value))

    def __str__(self):
        return self.value.__str__()

    def __repr__(self):
        return self.value.__repr__()

    def new(self, value=None):
        return self.__class__(typevalue=(self._type, value))


class NumericType(SimpleData):
    def __add__(self, other):
        if isinstance(other, NumericType):
            return self.new(self.value + other.value)
        else:
            return self.new(self.value + other)

    def __iadd__(self, other):
        assert not self.is_stored
        if isinstance(other, NumericType):
            self.value += other.value
        else:
            self.value += other
        return self

    def __radd__(self, other):
        assert not isinstance(other, NumericType)
        return self.new(other + self.value)

    def __sub__(self, other):
        if isinstance(other, NumericType):
            return self.new(self.value - other.value)
        else:
            return self.new(self.value - other)

    def __isub__(self, other):
        assert not self.is_stored
        if isinstance(other, NumericType):
            self.value -= other.value
        else:
            self.value -= other
        return self

    def __rsub__(self, other):
        assert not isinstance(other, NumericType)
        return self.new(other - self.value)

    def __mul__(self, other):
        if isinstance(other, NumericType):
            return self.new(self.value * other.value)
        else:
            return self.new(self.value * other)

    def __imul__(self, other):
        assert not self.is_stored
        if isinstance(other, NumericType):
            self.value *= other.value
        else:
            self.value *= other
        return self

    def __rmul__(self, other):
        assert not isinstance(other, NumericType)
        return self.new(other * self.value)

    def __lt__(self, other):
        if isinstance(other, NumericType):
            return self.value < other.value
        else:
            return self.value < other

    def __le__(self, other):
        if isinstance(other, NumericType):
            return self.value <= other.value
        else:
            return self.value <= other

    def __eq__(self, other):
        if isinstance(other, NumericType):
            return self.value == other.value
        else:
            return self.value == other

    def __ne__(self, other):
        if isinstance(other, NumericType):
            return self.value != other.value
        else:
            return self.value != other

    def __gt__(self, other):
        if isinstance(other, NumericType):
            return self.value > other.value
        else:
            return self.value > other

    def __ge__(self, other):
        if isinstance(other, NumericType):
            return self.value >= other.value
        else:
            return self.value >= other


def Float(value=None):
    return NumericType(typevalue=(float, value))


def Int(value=None):
    return NumericType(typevalue=(int, value))


def Str(value=None):
    return NumericType(typevalue=(str, value))
