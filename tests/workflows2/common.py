
from aiida.workflows2.process import Process


class DummyProcess(Process):
    @staticmethod
    def _define(spec):
        spec.dynamic_input()
        spec.dynamic_output()

    def _run(self):
        pass
