# -*- coding: utf-8 -*-
from aiida.engine import submit
from aiida.engine.workchain import WorkChain
from aiida.orm import Int


class AddAndMultiplyWorkChain(WorkChain):
    pass


builder = AddAndMultiplyWorkChain.get_builder()
builder.a = Int(1)
builder.b = Int(2)
builder.c = Int(3)

node = submit(builder)
