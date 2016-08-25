

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

    def _run(self):
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

    def _run(self):
        self.out("bad_output", 5)
