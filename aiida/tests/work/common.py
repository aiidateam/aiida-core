# -*- coding: utf-8 -*-

from aiida.work.process import Process

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1"


class DummyProcess(Process):
    """
    A Process that does nothing when it runs.
    """

    @classmethod
    def define(cls, spec):
        super(DummyProcess, cls).define(spec)
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
    def define(cls, spec):
        super(BadOutput, cls).define(spec)
        spec.dynamic_output()

    def _run(self):
        self.out("bad_output", 5)
