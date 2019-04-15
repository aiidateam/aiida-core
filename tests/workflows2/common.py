# -*- coding: utf-8 -*-

from aiida.workflows2.process import Process


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"

class DummyProcess(Process):
    """
    A Process that does nothing when it runs.
    """
    @classmethod
    def _define(cls, spec):
        spec.dynamic_input()
        spec.dynamic_output()

    def _run(self):
        pass


class BadOutput(Process):
    """
    A Process that emits an output that isn't part of the spec raising an
    exception.
    """
    @classmethod
    def _define(cls, spec):
        spec.dynamic_output()

    def _run(self):
        self.out("bad_output", 5)


class ProcessScope(object):
    def __init__(self, process, pid=None, inputs=None):
        self._process = process
        self._pid = pid
        self._inputs = inputs

    def __enter__(self):
        self._process.on_create(self._pid, self._inputs)
        self._process.on_start()
        return self._process

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._process.on_stop()
        self._process.on_destroy()
