from aiida.workflows2.fragmented_wf import FragmentedWorkfunction, \
    ResultToContext
from aiida.orm.data.parameter import ParameterData


class SimpleWF(FragmentedWorkfunction):
    @classmethod
    def _define(cls, spec):
        spec.input("params", valid_type=ParameterData)
        spec.outline(
            cls.square,
            cls.get_results
        )
        spec.dynamic_output()

    def square(self, ctx):
        print "squaring"
        number = self.inputs.params.dict.number
        ctx.result = number ** 2

    def get_results(self, ctx):
        print "The result is", ctx.result
