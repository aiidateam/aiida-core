# -*- coding: utf-8 -*-

"""
This file provides very simple workflows for testing purposes.
Do not delete, otherwise 'verdi developertest' will stop to work.
"""
from aiida_custom.orm import Data
from aiida_custom.orm.data.simple import SimpleData
from collections import Mapping

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
        return type
    if native_type in _TYPE_MAPPING:
        return _TYPE_MAPPING[native_type]
    return None


def to_db_type(value):
    if isinstance(value, Data):
        return value
    elif isinstance(value, int):
        return SimpleData(int, value)
    elif isinstance(value, float):
        return SimpleData(float, value)
    elif isinstance(value, bool):
        return SimpleData(bool, value)
    elif isinstance(value, str):
        return SimpleData(str, value)
    else:
        raise ValueError("Cannot convert value to database type")


def to_native_type(data):
    if not isinstance(data, Data):
        return data
    elif isinstance(data, SimpleData):
        return data.value
    else:
        raise ValueError("Cannot convert from database to native type")


class EventHelper(object):
    def __init__(self, listener_type):
        assert(listener_type is not None)
        self._listener_type = listener_type
        self._listeners = []

    def add_listener(self, listener):
        assert(isinstance(listener, self._listeners))
        self._listeners.append(listener)

    def remove_listener(self, listener):
        self._listeners.append(listener)

    @property
    def listeners(self):
        return self._listeners


class Sink(object):
    def __init__(self, type):
        self._type = type
        self._current_value = None

    def __str__(self):
        return "({}){}".format(self._type, self._current_value)

    def push(self, value):
        if value is None:
            raise ValueError("Cannot fill a sink with None")
        if self._type is not None and not isinstance(value, self._type):
            raise TypeError(
                "Sink expects values of type {}".format(self._type))

        self._current_value = value

    def pop(self):
        if not self.is_filled():
            raise RuntimeError("Sink has no value")

        val = self._current_value
        self._current_value = None
        return val

    def is_filled(self):
        return self._current_value is not None


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
