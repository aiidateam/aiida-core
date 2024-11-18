from aiida.engine import WorkChain
from aiida.plugins.factories import CalculationFactory

SomeOtherWorkChain = CalculationFactory('some.module')


class SomeWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.outline(
            cls.submit_workchains,
            cls.inspect_workchains,
        )

    def submit_workchains(self):
        for i in range(3):
            future = self.submit(SomeOtherWorkChain)
            key = f'workchains.sub{i}'
            self.to_context(**{key: future})

    def inspect_workchains(self):
        for key, workchain in self.ctx.workchains.items():
            assert workchain.is_finished_ok
