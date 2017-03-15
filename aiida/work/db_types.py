# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.orm import Data
from aiida.orm.data.base import BaseType, Int, Bool, Float, Str




_TYPE_MAPPING = {
    int: Int,
    float: Float,
    bool: Bool,
    str: Str
}


def to_db_type(value):
    if isinstance(value, Data):
        return value
    elif isinstance(value, bool):
        return Bool(value)
    elif isinstance(value, (int, long)):
        return Int(value)
    elif isinstance(value, float):
        return Float(value)
    elif isinstance(value, basestring):
        return Str(value)
    else:
        raise ValueError("Cannot convert value to database type")


def to_native_type(data):
    if not isinstance(data, Data):
        return data
    elif isinstance(data, BaseType):
        return data.value
    else:
        raise ValueError("Cannot convert from database to native type")


def get_db_type(native_type):
    if issubclass(native_type, Data):
        return native_type
    if native_type in _TYPE_MAPPING:
        return _TYPE_MAPPING[native_type]
    return None
