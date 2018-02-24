# -*- coding: utf-8 -*-
import numbers
from aiida.orm.data.base import NumericType
from aiida.orm.data.base import to_aiida_type


class Int(NumericType):
    """
    Class to store integer numbers as AiiDA nodes
    """
    _type = int


@to_aiida_type.register(numbers.Integral)
def _(value):
    return Int(value)
