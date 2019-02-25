# -*- coding: utf-8 -*-
from aiida.orm.nodes.data.int import Int
from aiida.engine import submit
from aiida.engine.workchain import WorkChain

class AddAndMultiplyWorkChain(WorkChain):
    ...

node = submit(AddAndMultiplyWorkChain, a=Int(1), b=Int(2), c=Int(3))