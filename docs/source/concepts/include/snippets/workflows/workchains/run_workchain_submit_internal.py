# -*- coding: utf-8 -*-
from aiida.orm.data.int import Int
from aiida.work.workchain import WorkChain

class AddAndMultiplyWorkChain(WorkChain):
    ...

    def submit_sub_workchain(self):
        node = self.submit(AddAndMultiplyWorkChain, a=Int(1), b=Int(2), c=Int(3))
