# -*- coding: utf-8 -*-

"""
This file provides very simple workflows for testing purposes.
Do not delete, otherwise 'verdi developertest' will stop to work.
"""
from aiida.orm import Data
from aiida.orm.data.simple import SimpleData

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


def get_db_type(native_type):
    if issubclass(native_type, Data):
        return native_type
    if native_type in _TYPE_MAPPING:
        return _TYPE_MAPPING[native_type]
    return None


def to_db_type(value):
    if isinstance(value, Data):
        return value
    elif isinstance(value, bool):
        return SimpleData(typevalue=(bool, value))
    elif isinstance(value, (int, long)):
        return SimpleData(typevalue=(int, value))
    elif isinstance(value, float):
        return SimpleData(typevalue=(float, value))
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


def save_calc(calc, func, inputs=None):
    # Add data input nodes as links
    if inputs:
        for k, v in inputs.iteritems():
            calc._add_link_from(v, label=k)

    _add_source_info(calc, func)


def _add_source_info(calc, func):
    import inspect

    # Note: if you pass a lambda function, the name will be <lambda>; moreover
    # if you define a function f, and then do "h=f", h.__name__ will
    # still return 'f'!
    function_name = func.__name__

    # Try to get the source code
    source_code, first_line = inspect.getsourcelines(func)
    try:
        with open(inspect.getsourcefile(func)) as f:
            source = f.read()
    except IOError:
        source = None

    calc._set_attr("source_code", "".join(source_code))
    calc._set_attr("first_line_source_code", first_line)
    calc._set_attr("source_file", source)
    calc._set_attr("function_name", function_name)
