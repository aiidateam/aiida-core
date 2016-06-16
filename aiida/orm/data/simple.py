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


class NumericType(SimpleData):
    def __add__(self, other):
        return self.value.__add__(other)

    def __sub__(self, other):
        return self.value.__sub__(other)

    def __mul__(self, other):
        return self.value.__mul__(other)

    def __iadd__(self, other):
        return self.value.__iadd__(other)

    def __isub__(self, other):
        return self.value.__isub__(other)

    def __imul__(self, other):
        return self.value.__imul__(other)

    def __lt__(self, other):
        return self.value.__lt__(other)

    def __le__(self, other):
        return self.value.__le__(other)

    def __eq__(self, other):
        return self.value.__eq__(other)

    def __ne__(self, other):
        return self.value.__ne__(other)

    def __gt__(self, other):
        return self.value.__gt__(other)

    def __ge__(self, other):
        return self.value.__ge__(other)


class Float(NumericType):
    def __init__(self, value):
        super(Float, self).__init__(typevalue=(float, value))


class Str(SimpleData):
    def __init__(self, value):
        super(Str, self).__init__(typevalue=(str, value))
