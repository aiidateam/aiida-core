from aiida.engine import WorkChain
from aiida.orm import Int


class AddAndMultiplyWorkChain(WorkChain):
    def submit_sub_workchain(self):
        self.submit(AddAndMultiplyWorkChain, a=Int(value=1), b=Int(value=2), c=Int(value=3))
