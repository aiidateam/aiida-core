
from aiida.workflows2.process import Process


class DummyProcess(Process):
    """
    A Process that does nothing when it runs.
    """
    @classmethod
    def _define(cls, spec):
        super(DummyProcess, cls)._define(spec)
        spec.dynamic_input()
        spec.dynamic_output()

    def _main(self):
        pass


class BadOutput(Process):
    """
    A Process that emits an output that isn't part of the spec raising an
    exception.
    """
    @classmethod
    def _define(cls, spec):
        super(BadOutput, cls)._define(spec)
        spec.dynamic_output()

    def _main(self):
        self.out("bad_output", 5)


class ProcessScope(object):
    def __init__(self, process, pid=None, inputs=None):
        self._process = process
        self._pid = pid
        self._inputs = inputs

    def __enter__(self):
        self._process.perform_create(self._pid, self._inputs, None)
        self._process.perform_run(None, None)
        return self._process

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._process.perform_finish(None)
        self._process.perform_stop()
        self._process.perform_destroy()
