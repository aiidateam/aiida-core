# -*- coding: utf-8 -*-
from aiida.engine import submit
from aiida.engine.workchain import WorkChain
from aiida.orm import Int


class AddAndMultiplyWorkChain(WorkChain):
    pass

node = submit(AddAndMultiplyWorkChain, a=Int(1), b=Int(2), c=Int(3))
