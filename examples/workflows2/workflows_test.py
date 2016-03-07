
from aiida import load_dbenv

from aiida.workflows2.wf import aiidise
from aiida.workflows2.util import to_db_type


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


if __name__ == '__main__':
    load_dbenv()

    aiida_add = aiidise(add)
    aiida_multiply = aiidise(multiply)

    two = to_db_type(2)
    three = to_db_type(3)

    print(aiida_multiply(aiida_add(two, three), two))

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


