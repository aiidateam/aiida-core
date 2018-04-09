from aiida.work import ToContext, WorkChain, run

from child import ChildWorkChain

class ComplexParentWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super(ComplexParentWorkChain, cls).define(spec)

        spec.expose_inputs(ChildWorkChain, include=['a'])
        spec.expose_inputs(
            ChildWorkChain,
            namespace='child_1',
            exclude=['a']
        )
        spec.expose_inputs(
            ChildWorkChain,
            namespace='child_2',
            exclude=['a']
        )

        spec.expose_outputs(ChildWorkChain, include=['e'])
        spec.expose_outputs(
            ChildWorkChain,
            namespace='child_1',
            exclude=['e'],
        )
        spec.expose_outputs(
            ChildWorkChain,
            namespace='child_2',
            exclude=['e'],
        )

        spec.outline(cls.run_children, cls.finalize)

    def run_children(self):
        return ToContext(
            child_1=self.submit(
                ChildWorkChain,
                **self.exposed_inputs(
                    ChildWorkChain,
                    namespace='child_1'
                )
            ),
            child_2=self.submit(
                ChildWorkChain,
                a=self.inputs.a,
                **self.exposed_inputs(
                    ChildWorkChain,
                    namespace='child_2',
                    agglomerate=False
                )
            )
        )

    def finalize(self):
        self.out_many(
            self.exposed_outputs(
                self.ctx.child_1,
                ChildWorkChain,
                namespace='child_1'
            )
        )
        self.out_many(
            self.exposed_outputs(
                self.ctx.child_2,
                ChildWorkChain,
                namespace='child_2',
                agglomerate=False
            )
        )
