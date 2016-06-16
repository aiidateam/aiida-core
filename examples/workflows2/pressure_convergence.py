from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from aiida.orm import load_node
from aiida.orm.utils import DataFactory
from aiida.workflows2.db_types import Float, Str
from aiida.orm.code import Code
from aiida.orm.data.structure import StructureData
from aiida.workflows2.run import run
from aiida.workflows2.fragmented_wf import FragmentedWorkfunction, \
    ResultToContext, while_
from examples.workflows2.common import generate_scf_input_params
from examples.workflows2.diamond_fcc import rescale
from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation


# Set up the factories
ParameterData = DataFactory("parameter")
KpointsData = DataFactory("array.kpoints")


PwProcess = PwCalculation.process()


class PressureConvergence(FragmentedWorkfunction):
    @classmethod
    def _define(cls, spec):
        spec.input("structure", valid_type=StructureData)
        spec.input("target_pressure", valid_type=Float, default=Float(0))
        spec.input("step", valid_type=Float, default=Float(0.01))
        spec.input("tolerance", valid_type=Float, default=Float(0.1))
        spec.input("code", valid_type=Str)
        spec.input("pseudo_family", valid_type=Str)
        spec.outline(
            cls.init,
            cls.extract_results,
            while_(cls.not_converged)(
                cls.minimise,
                cls.extract_results
            ),
            cls.finish
        )

    def init(self, ctx):
        # Get some inputs
        ctx.inputs = generate_scf_input_params(
            ctx.structure, self.inputs.code, self.inputs.pseudo_family)
        # Set the structure
        ctx.structure = self.inputs.structure
        # Run PW
        future = self.submit(PwProcess, ctx.inputs)
        # Wait to complete before next step
        return ResultToContext(results=future)

    def extract_results(self, ctx):
        ctx.structure = None  # TODO: get result
        ctx.pressure = None  # TODO get result

    def not_converged(self, ctx):
        return abs(ctx._pressure.value - self.inputs.target_pressure) > \
               self.inputs.tolerance.value

    def minimise(self, ctx):
        target_pressure = self.inputs.target_pressure.value
        # Find the fractional difference from the target pressure
        frac_delta = (target_pressure - ctx.pressure) / ctx.pressure
        # Scale the structure
        ctx.inputs.structure = rescale(ctx.structure, frac_delta + 1.0)
        # Run PW
        future = self.submit(PwProcess, ctx.inputs)
        # Wait to complete before next step
        return ResultToContext(results=future)

    def finish(self, ctx):
        self.out("structure", ctx.structure)

