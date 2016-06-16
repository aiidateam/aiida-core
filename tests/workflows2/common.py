
from aiida.workflows2.process import Process


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
        return self._process

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._process.on_stop()
        self._process.on_destroy()
