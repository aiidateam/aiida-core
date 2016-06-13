
from aiida.workflows2.process import Process


class DummyProcess(Process):
    @classmethod
    def _define(cls, spec):
        spec.dynamic_input()
        spec.dynamic_output()

    def _run(self):
        pass
