# -*- coding: utf-8 -*-
from aiida.orm.data.int import Int
from aiida.work.launch import run_get_node, run_get_pid
from aiida.work.workchain import WorkChain

class AddAndMultiplyWorkChain(WorkChain):
    ...

result, node = run_get_node(AddAndMultiplyWorkChain, a=Int(1), b=Int(2), c=Int(3))
result, pid = run_get_pid(AddAndMultiplyWorkChain, a=Int(1), b=Int(2), c=Int(3))