# -*- coding: utf-8 -*-
from aiida.orm.data.int import Int
from aiida.work.launch import submit
from aiida.work.workchain import WorkChain

class AddAndMultiplyWorkChain(WorkChain):
    ...

builder = AddAndMultiplyWorkChain.get_builder()
builder.a = Int(1)
builder.b = Int(2)
builder.c = Int(3)

node = submit(builder)