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
    ResultToContext
from examples.workflows2.common import generate_scf_input_params
from examples.workflows2.diamond_fcc import rescale
from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation


# Set up the factories
ParameterData = DataFactory("parameter")
KpointsData = DataFactory("array.kpoints")


PwProcess = PwCalculation.process()


class EquationOfStates(FragmentedWorkfunction):
    @classmethod
    def _define(cls, spec):
        spec.input("structure", valid_type=StructureData)
        spec.input("start", valid_type=Float, default=Float(0.96))
        spec.input("delta", valid_type=Float, default=Float(0.02))
        spec.input("end", valid_type=Float, default=Float(1.04))
        spec.input("code", valid_type=Str)
        spec.input("pseudo_family", valid_type=Str)
        spec.outline(
            cls.run_pw,
            cls.plot_eos
        )

    def run_pw(self, ctx):
        calcs = {}

        scale = self.inputs.start.value
        while scale <= self.inputs.end:
            scaled = rescale(self.inputs.structure, Float(scale))

            inputs = generate_scf_input_params(
                scaled, self.inputs.code, self.inputs.pseudo_family)

            # Launch the code
            future = self.submit(PwProcess, inputs)
            #print scale.value, future.pid
            # Store the future
            calcs["s_{}".format(scale)] = future
            scale += self.inputs.delta.value

        # Ask the workflow to continue when the results are ready and store them
        # in the context
        return ResultToContext(**calcs)

    def plot_eos(self, ctx):
        for label in ctx:
            if "s_" in label:
                print "{} {}".format(
                    label, ctx[label]['output_parameters'].dict.energy)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Equation of states example.')
    parser.add_argument('--structure', type=int, dest='structure_pk',
                        help='The structure pk to use.')
    parser.add_argument('--range', type=str, dest='range',
                        help='The scale range of the equation of states '
                             'calculation written as [start]:[end]:[delta]',
                             default='0.96:0.1.04:0.02')
    parser.add_argument('--pseudo', type=str, dest='pseudo',
                        help='The pseudopotential family')
    parser.add_argument('--code', type=str, dest='code',
                        help='The codename to use')

    args = parser.parse_args()
    start, end, delta = args.range.split(':')

    # Get the structure from the calculation
    run(EquationOfStates, structure=load_node(args.structure_pk),
        start=Float(start), end=Float(end), delta=Float(delta),
        code=Str(args.code), pseudo_family=Str(args.pseudo))
