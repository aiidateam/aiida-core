# -*- coding: utf-8 -*-
from aiida.orm.data.int import Int
from aiida.work.launch import submit
from aiida.work.workchain import WorkChain

class AddAndMultiplyWorkChain(WorkChain):
    ...

node = submit(AddAndMultiplyWorkChain, a=Int(1), b=Int(2), c=Int(3))