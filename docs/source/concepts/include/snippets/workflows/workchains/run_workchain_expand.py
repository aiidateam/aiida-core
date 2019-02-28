# -*- coding: utf-8 -*-
from aiida.engine import run
from aiida.engine.workchain import WorkChain
from aiida.orm import Int


class AddAndMultiplyWorkChain(WorkChain):
    pass


inputs = {
    'a': Int(1),
    'b': Int(2),
    'c': Int(3)
}
result = run(AddAndMultiplyWorkChain, **inputs)
