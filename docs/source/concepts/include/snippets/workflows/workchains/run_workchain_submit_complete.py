# -*- coding: utf-8 -*-
from aiida.orm.data.int import Int
from aiida.work.workchain import WorkChain, ToContext

class SomeWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super(SomeWorkChain, cls).define(spec)
        spec.outline(
            cls.submit_workchain,
            cls.inspect_workchain,
        )

    def submit_workchain(self):
        future = self.submit(SomeWorkChain)
        return ToContext(workchain=future)

    def inspect_workchain(self):
        assert self.ctx.workchain.is_finished_ok
