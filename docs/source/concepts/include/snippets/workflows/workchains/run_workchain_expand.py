# -*- coding: utf-8 -*-
from aiida.orm.data.int import Int
from aiida.work.launch import run
from aiida.work.workchain import WorkChain

class AddAndMultiplyWorkChain(WorkChain):
    ...

inputs = {
    'a': Int(1),
    'b': Int(2),
    'c': Int(3)
}
result = run(AddAndMultiplyWorkChain, **inputs)