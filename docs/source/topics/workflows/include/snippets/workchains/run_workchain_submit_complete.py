from aiida.engine import ToContext, WorkChain
from aiida.plugins.factories import CalculationFactory

SomeOtherWorkChain = CalculationFactory('some.module')


class SomeWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.outline(
            cls.submit_workchain,
            cls.inspect_workchain,
        )

    def submit_workchain(self):
        future = self.submit(SomeOtherWorkChain)
        return ToContext(workchain=future)

    def inspect_workchain(self):
        assert self.ctx.workchain.is_finished_ok
