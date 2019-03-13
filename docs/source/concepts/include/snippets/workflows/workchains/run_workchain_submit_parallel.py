# -*- coding: utf-8 -*-
from aiida.engine.workchain import WorkChain


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
            key = 'workchain_{}'.format(i)
            self.to_context(**{key: future})

    def inspect_workchains(self):
        for i in range(3):
            key = 'workchain_{}'.format(i)
            assert self.ctx[key].is_finished_ok
