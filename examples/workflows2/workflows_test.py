
from aiida.backends.utils import load_dbenv, is_dbenv_loaded
if not is_dbenv_loaded():
    load_dbenv()

#from aiida.workflows2.wf import aiidise
#from aiida.workflows2.util import to_db_type
from plum.process import Process, FunctionProcess
from plum.workflow import Workflow


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


class Add(Process):
    @staticmethod
    def _init(spec):
        spec.add_input('a', default=0)
        spec.add_input('b', default=0)
        spec.add_output('value')

    def _run(self, a, b):
        return {'value': a + b}


class Mul(Process):
    @staticmethod
    def _init(spec):
        spec.add_input('a', default=1)
        spec.add_input('b', default=1)
        spec.add_output('value')

    def _run(self, a, b):
        return {'value': a * b}


AddFun = FunctionProcess.build(add)

class MulAdd(Workflow):
    @staticmethod
    def _init(spec):
        spec.add_input('e', default=0)
        spec.add_input('f', default=0)
        spec.add_input('g', default=0)
        spec.add_output('value')

        spec.add_process(Mul)
        spec.add_process(Add)
        spec.link(':e', 'Add:a')
        spec.link(':f', 'Add:b')
        spec.link(':g', 'Mul:a')
        spec.link('Add:value', 'Mul:b')
        spec.link('Mul:value', ':value')


# class MulAddWithFun(Workflow):
#     @staticmethod
#     def _init(spec):
#         spec.add_input('e', default='0')
#         spec.add_input('f', default='0')
#         spec.add_input('g', default='0')
#         spec.add_output('value')
#
#         spec.add_process(Mul)
#         spec.add_process(AddFun)
#         spec.link(':e', 'add:a')
#         spec.link(':f', 'add:b')
#         spec.link(':g', 'Mul:a')
#         spec.link('add:value', 'Mul:b')
#         spec.link('Mul:value', ':value')


if __name__ == '__main__':
    #load_dbenv()

    # aiida_add = aiidise(add)
    # aiida_multiply = aiidise(multiply)
    #
    # two = to_db_type(2)
    # three = to_db_type(3)

    mul_add = MulAdd.create()
    #mul_add.bind('e', 2)
    mul_add.bind('f', 3)
    mul_add.bind('g', 4)
    mul_add.run()

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


