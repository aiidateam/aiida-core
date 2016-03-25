from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from aiida.workflows2.wf import wf
from aiida.workflows2.util import to_db_type
from plum.process import Process
from plum.workflow import Workflow


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


@wf
def add_wf(a, b):
    return {'value': to_db_type(a.value + b.value)}


@wf
def muliply_wf(a, b):
    return {'value': to_db_type(a.value * b.value)}


@wf
def add_multiply_wf(a, b, c):
    return muliply_wf(add_wf(a, b)['value'], c)


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
    two = to_db_type(2)
    three = to_db_type(3)
    four = to_db_type(4)

    print "WORKFUNCTION:"

    simpledata = add_multiply_wf(two, three, four)['value']
    print "output pk:", simpledata.pk
    print "output value:", simpledata.value

    print "PROCESS:"
    wf = MulAdd.create()
    wf(a=two, b=three, c=four)
    simpledata = wf.get_last_outputs()['value']
    print "output pk:", simpledata.pk
    print "output value:", simpledata.value
