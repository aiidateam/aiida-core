# -*- coding: utf-8 -*-

from aiida.orm import Data
from aiida.orm.data.simple import NumericType, SimpleData, Float, Str


__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"


_TYPE_MAPPING = {
    int: SimpleData,
    float: SimpleData,
    bool: SimpleData,
    str: SimpleData
}


def Int(value):
    return NumericType(typevalue=(int, value))


def Bool(value):
    return SimpleData(typevalue=(bool, value))


def to_db_type(value):
    if isinstance(value, Data):
        return value
    elif isinstance(value, bool):
        return SimpleData(typevalue=(bool, value))
    elif isinstance(value, (int, long)):
        return SimpleData(typevalue=(int, value))
    elif isinstance(value, float):
        return Float(value)
    elif isinstance(value, basestring):
        return SimpleData(typevalue=(type(value), value))
    else:
        raise ValueError("Cannot convert value to database type")


def to_native_type(data):
    if not isinstance(data, Data):
        return data
    elif isinstance(data, SimpleData):
        return data.value
    else:
        raise ValueError("Cannot convert from database to native type")


def get_db_type(native_type):
    if issubclass(native_type, Data):
        return native_type
    if native_type in _TYPE_MAPPING:
        return _TYPE_MAPPING[native_type]
    return None
