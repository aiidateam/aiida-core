# -*- coding: utf-8 -*-

import importlib
from threading import local

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"


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
