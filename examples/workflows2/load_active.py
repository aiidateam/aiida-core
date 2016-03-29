from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from aiida.workflows2.persistance.active_factory import load_all_process_records
from aiida.workflows2.process import Process
from aiida.workflows2.workflow import Workflow
from aiida.workflows2.util import to_db_type
from aiida.workflows2.execution_engine import TrackingExecutionEngine


class Add(Process):
    @staticmethod
    def _init(spec):
        spec.add_input('a', default=0)
        spec.add_input('b', default=0)
        spec.add_output('value')

    def _run(self, a, b):
        self._out('value', to_db_type(a.value + b.value))


class Mul(Process):
    @staticmethod
    def _init(spec):
        spec.add_input('a', default=1)
        spec.add_input('b', default=1)
        spec.add_output('value')

    def _run(self, a, b):
        self._out('value', to_db_type(a.value * b.value))


class MulAdd(Workflow):
    @staticmethod
    def _init(spec):
        spec.add_process(Mul)
        spec.add_process(Add)

        spec.expose_inputs('Add')
        spec.expose_outputs('Mul')
        spec.add_input('c')

        spec.link(':c', 'Mul:a')
        spec.link('Add:value', 'Mul:b')

if __name__ == '__main__':
    # ee = TrackingExecutionEngine()
    #
    # two = to_db_type(2)
    # three = to_db_type(3)
    # four = to_db_type(4)
    #
    # mul_add = MulAdd.create()
    # mul_add.bind('a', two)
    # mul_add.bind('b', three)
    # mul_add.bind('c', four)
    # ee.run(mul_add)

    active = load_all_process_records()
    print(active)
