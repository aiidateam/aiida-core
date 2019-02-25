# -*- coding: utf-8 -*-
from aiida.orm.nodes.data.int import Int
from aiida.engine import run
from aiida.engine.workchain import WorkChain

class AddAndMultiplyWorkChain(WorkChain):
    ...

inputs = {
    'a': Int(1),
    'b': Int(2),
    'c': Int(3)
}
result = run(AddAndMultiplyWorkChain, **inputs)