# -*- coding: utf-8 -*-
from aiida.orm.nodes.data.int import Int
from aiida.engine import submit
from aiida.engine.workchain import WorkChain

class AddAndMultiplyWorkChain(WorkChain):
    ...

builder = AddAndMultiplyWorkChain.get_builder()
builder.a = Int(1)
builder.b = Int(2)
builder.c = Int(3)

node = submit(builder)