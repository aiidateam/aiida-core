from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from aiida.workflows2.wf import wf
from aiida.workflows2.db_types import to_db_type, SimpleData
from aiida.workflows2.process import Process
from aiida.workflows2.workflow import Workflow


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


@wf
def sum(a, b):
    return {'sum': to_db_type(a.value + b.value)}


@wf
def prod(a, b):
    return {'prod': to_db_type(a.value * b.value)}


@wf
def add_multiply_wf(a, b, c):
    return {'result': prod(sum(a, b)['sum'], c)['prod']}


class Add(Process):
    @staticmethod
    def _define(spec):
        spec.input('a', default=0)
        spec.input('b', default=0)
        spec.output('value')

    def _run(self, a, b):
        self._out('value', to_db_type(a.value + b.value))


class Mul(Process):
    @staticmethod
    def _define(spec):
        spec.input('a', default=1)
        spec.input('b', default=1)
        spec.output('value')

    def _run(self, a, b):
        self._out('value', to_db_type(a.value * b.value))


class MulAdd(Workflow):
    @staticmethod
    def _define(spec):
        spec.process(Mul)
        spec.process(Add)

        spec.exposed_inputs('Add')
        spec.exposed_outputs('Mul')
        spec.input('c')

        spec.link(':c', 'Mul:a')
        spec.link('Add:value', 'Mul:b')


if __name__ == '__main__':
    two = Int(2)
    three = Int(3)
    four = Int(4)

    print "WORKFUNCTION:"

    simpledata = add_multiply_wf(two, three, four)['value']
    print "output pk:", simpledata.pk
    print "output value:", simpledata.value

    print "PROCESS:"
    workflow = MulAdd.create()
    workflow(a=two, b=three, c=four)
    simpledata = workflow.get_last_outputs()['value']
    print "output pk:", simpledata.pk
    print "output value:", simpledata.value
