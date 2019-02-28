# -*- coding: utf-8 -*-
from aiida.engine.workchain import WorkChain, append_


class SomeWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super(SomeWorkChain, cls).define(spec)
        spec.outline(
            cls.submit_workchains,
            cls.inspect_workchains,
        )

    def submit_workchains(self):
        for i in range(3):
            future = self.submit(SomeWorkChain)
            self.to_context(workchains=append_(future))

    def inspect_workchains(self):
        for workchain in self.ctx.workchains:
            assert workchain.is_finished_ok
