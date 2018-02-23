from aiida.work import ToContext, WorkChain, run

from child import ChildWorkChain

class SimpleParentWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super(SimpleParentWorkChain, cls).define(spec)

        spec.expose_inputs(ChildWorkChain)
        spec.expose_outputs(ChildWorkChain)

        spec.outline(cls.run_child, cls.finalize)

    def run_child(self):
        return ToContext(child=self.submit(
            ChildWorkChain,
            **self.exposed_inputs(ChildWorkChain)
        ))

    def finalize(self):
        self.out_many(
            self.exposed_outputs(
                self.ctx.child,
                ChildWorkChain
            )
        )
