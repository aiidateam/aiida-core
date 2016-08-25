# -*- coding: utf-8 -*-
from abc import ABCMeta
from aiida.orm import Data

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


class SimpleData(Data):
    __metaclass__ = ABCMeta

    def create_init_args(self, **kwargs):
        assert getattr(self, '_type', None) is not None
        if 'dbnode' not in kwargs:
            if 'typevalue' in kwargs:
                assert kwargs['typevalue'][0] is self._type
                if kwargs['typevalue'][1] is not None:
                    kwargs['typevalue'] = \
                        (self._type, self._type(kwargs['typevalue'][1]))
            else:
                kwargs['typevalue'] = (self._type, None)

        return kwargs

    def __init__(self, **kwargs):
        assert 'dbnode' in kwargs or 'typevalue' in kwargs
        super(SimpleData, self).__init__(**self.create_init_args(**kwargs))

    def init(self, type_):
        assert getattr(self, '_type', None) is None, "Can only be called once"
        self._type = type_

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

    def __eq__(self, other):
        if isinstance(other, SimpleData):
            return self.value == other.value
        else:
            return self.value == other

    def __ne__(self, other):
        if isinstance(other, SimpleData):
            return self.value != other.value
        else:
            return self.value != other

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

    def __pow__(self, power, modulo=None):
        if isinstance(power, NumericType):
            return self.new(self.value ** power.value)
        else:
            return self.new(self.value ** power)

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

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)


class Float(NumericType):
    def __init__(self, **kwargs):
        self.init(float)
        super(Float, self).__init__(**kwargs)


def make_float(value=None):
    return Float(typevalue=(float, value))


class Int(NumericType):
    def __init__(self, **kwargs):
        self.init(int)
        super(Int, self).__init__(**kwargs)


def make_int(value=None):
    return Int(typevalue=(int, value))


class Str(SimpleData):
    def __init__(self, **kwargs):
        self.init(str)
        super(Str, self).__init__(**kwargs)


def make_str(value=None):
    return Str(typevalue=(str, value))


class Bool(SimpleData):
    def __init__(self, **kwargs):
        self.init(bool)
        super(Bool, self).__init__(**kwargs)

    def __int__(self):
        return 0 if not self.value else 1

TRUE = Bool(typevalue=(bool, True))
FALSE = Bool(typevalue=(bool, False))
