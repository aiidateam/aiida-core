# -*- coding: utf-8 -*-
from past.builtins import basestring
from aiida.orm.data import BaseType
from aiida.orm.data import to_aiida_type


class Str(BaseType):
    """
    Class to store strings as AiiDA nodes
    """
    _type = str


@to_aiida_type.register(basestring)
def _(value):
    return Str(value)
