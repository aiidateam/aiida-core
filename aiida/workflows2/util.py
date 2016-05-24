# -*- coding: utf-8 -*-

from aiida.orm import Data
from aiida.orm.data.simple import SimpleData
from threading import local
import importlib

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


class ProcessStack(object):
    # Use thread-local storage for the stack
    _thread_local = local()

    @staticmethod
    def scoped(process):
        return ProcessStack(process)

    @classmethod
    def stack(self):
        try:
            return self._thread_local.wf_stack
        except AttributeError:
            self._thread_local.wf_stack = []
            return self._thread_local.wf_stack

    @classmethod
    def push(cls, process):
        cls.stack().append(process)

    @classmethod
    def pop(cls):
        cls.stack().pop()

    def __init__(self, process):
        self._process = process

    def __enter__(self):
        self.push(self._process)
        if len(self.stack()) > 1:
            self._process._parent = self.stack()[-2]
        else:
            self._process._parent = None
        return self.stack

    def __exit__(self, type, value, traceback):
        self.pop()
        self._process._parent = None


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


def load_class(classstring):
    """
    Load a class from a string
    """
    class_data = classstring.split(".")
    module_path = ".".join(class_data[:-1])
    class_name = class_data[-1]

    module = importlib.import_module(module_path)
    # Finally, we retrieve the Class
    return getattr(module, class_name)


def is_workfunction(func):
    try:
        return func._is_workfunction
    except AttributeError:
        return False
