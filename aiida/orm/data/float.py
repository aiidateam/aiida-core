# -*- coding: utf-8 -*-
import numbers
from aiida.orm.data import to_aiida_type
from aiida.orm.data.numeric import NumericType


class Float(NumericType):
    """
    Class to store float numbers as AiiDA nodes
    """
    _type = float


@to_aiida_type.register(numbers.Real)
def _(value):
    return Float(value)
