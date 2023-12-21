from child import ChildWorkChain

from aiida.engine import ToContext, WorkChain


class ComplexParentWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.expose_inputs(ChildWorkChain, include=['a'])
        spec.expose_inputs(ChildWorkChain, namespace='child_1', exclude=['a'])
        spec.expose_inputs(ChildWorkChain, namespace='child_2', exclude=['a'])
        spec.outline(cls.run_children, cls.finalize)
        spec.expose_outputs(ChildWorkChain, include=['e'])
        spec.expose_outputs(ChildWorkChain, namespace='child_1', exclude=['e'])
        spec.expose_outputs(ChildWorkChain, namespace='child_2', exclude=['e'])

    def run_children(self):
        child_1_inputs = self.exposed_inputs(ChildWorkChain, namespace='child_1')
        child_2_inputs = self.exposed_inputs(ChildWorkChain, namespace='child_2', agglomerate=False)
        child_1 = self.submit(ChildWorkChain, **child_1_inputs)
        child_2 = self.submit(ChildWorkChain, a=self.inputs.a, **child_2_inputs)
        return ToContext(child_1=child_1, child_2=child_2)

    def finalize(self):
        self.out_many(self.exposed_outputs(self.ctx.child_1, ChildWorkChain, namespace='child_1'))
        self.out_many(self.exposed_outputs(self.ctx.child_2, ChildWorkChain, namespace='child_2', agglomerate=False))
