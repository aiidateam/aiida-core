# -*- coding: utf-8 -*-
from aiida.engine import run_get_node, run_get_pid
from aiida.engine.workchain import WorkChain
from aiida.orm import Int


class AddAndMultiplyWorkChain(WorkChain):
    pass


result, node = run_get_node(AddAndMultiplyWorkChain, a=Int(1), b=Int(2), c=Int(3))
result, pid = run_get_pid(AddAndMultiplyWorkChain, a=Int(1), b=Int(2), c=Int(3))
