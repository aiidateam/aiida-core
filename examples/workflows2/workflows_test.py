
from aiida.backends.utils import load_dbenv, is_dbenv_loaded
if not is_dbenv_loaded():
    load_dbenv()

from aiida.workflows2.wf import aiidise, wf
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

    # aiida_add = aiidise(add)
    # aiida_multiply = aiidise(multiply)
    #
    two = to_db_type(2)
    three = to_db_type(3)
    four = to_db_type(4)

    print(add_multiply_wf(two, three, four))
    print(MulAdd.create()(a=two, b=three, c=four))

    # mul_add = MulAddWithFun.create()
    # mul_add.bind('e', 2)
    # mul_add.bind('f', 3)
    # mul_add.bind('g', 4)
    # mul_add.run()

    #print(aiida_multiply(aiida_add(two, three), two))



    # import aiida.new_workflows.workflows as workflows
    #
    # add_proc = workflows.FunctionProcess(add)
    # mul_proc = workflows.FunctionProcess(multiply)
    #
    # wf = workflows.Workflow("test")
    #
    # wf.add_input("add1").push(2)
    # wf.add_input("add2").push(3)
    # wf.add_input("mul1").push(2)
    #
    # wf.add_process(add_proc)
    # wf.add_process(mul_proc)
    #
    # wf.add_output("value")
    #
    # wf.link(":add1", "add:a")
    # wf.link(":add2", "add:b")
    # wf.link("add:value", "multiply:a")
    # wf.link(":mul1", "multiply:b")
    # wf.link("multiply:value", ":value")
    #
    # outputs = wf.run()
    #
    # print(outputs)
    #wf.link("multiply:")

    #wf.link(":add1", "")


