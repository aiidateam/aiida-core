from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from aiida.orm import load_node
from aiida.orm.utils import DataFactory
from aiida.workflows2.db_types import Float, Str, NumericType, SimpleData
from aiida.orm.code import Code
from aiida.orm.data.structure import StructureData
from aiida.workflows2.run import run
from aiida.workflows2.fragmented_wf import FragmentedWorkfunction, \
    ResultToContext, while_
from common import generate_scf_input_params
from diamond_fcc import rescale, create_diamond_fcc
from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation

kbar_to_eV_over_ang3 = 1. / 1602.1766208

# Set up the factories
ParameterData = DataFactory("parameter")
KpointsData = DataFactory("array.kpoints")

PwProcess = PwCalculation.process()


def get_first_deriv(stress):
    from numpy import trace
    p = trace(stress) / 3.
    # Pressure is -dE/dV; moreover p in kbar, we need to convert
    # it to eV/angstrom^3 to be consisten
    dE = -p * kbar_to_eV_over_ang3

    return dE


def get_volume_energy_and_derivative(output_parameters):
    V = output_parameters.dict.volume
    E = output_parameters.dict.energy
    dE = get_first_deriv(output_parameters.dict.stress)

    return (V, E, dE)


def get_second_derivative(outp1, outp2):
    dE1 = get_first_deriv(outp1.dict.stress)
    dE2 = get_first_deriv(outp2.dict.stress)
    V1 = outp1.dict.volume
    V2 = outp2.dict.volume

    return (dE2 - dE1) / (V2 - V1)


def get_abc(V, E, dE, ddE):
    a = ddE / 2.
    b = dE - ddE * V
    c = E - V * dE + V ** 2 * ddE / 2.

    return a, b, c


def get_structure(original_structure, new_volume):
    initial_volume = original_structure.get_cell_volume()
    scale_factor = (new_volume / initial_volume) ** (1. / 3.)
    scaled_structure = rescale(original_structure, Float(scale_factor))
    return scaled_structure


class PressureConvergence(FragmentedWorkfunction):
    """
    Converge to minimum using Newton's algorithm on the first derivative of the
    energy (minus the pressure).
    """

    @classmethod
    def _define(cls, spec):
        spec.input("structure", valid_type=StructureData)
        spec.input("volume_tolerance",
                   valid_type=NumericType)  # , default=Float(0.1))
        spec.input("code", valid_type=SimpleData)
        spec.input("pseudo_family", valid_type=SimpleData)
        spec.outline(
            cls.init,
            cls.put_step0_in_ctx,
            cls.move_next_step,
            while_(cls.not_converged)(
                cls.move_next_step,
            ),
            cls.report
        )
        spec.dynamic_output()

    def init(self, ctx):
        # Get some inputs
        # Set the structure
        inputs0 = generate_scf_input_params(
            self.inputs.structure, self.inputs.code, self.inputs.pseudo_family)

        initial_volume = self.inputs.structure.get_cell_volume()
        new_volume = initial_volume + 4.  # In ang^3

        scaled_structure = get_structure(self.inputs.structure, new_volume)
        inputs1 = generate_scf_input_params(
            scaled_structure, self.inputs.code, self.inputs.pseudo_family)

        ctx.last_structure = scaled_structure

        # Run PW
        future0 = self.submit(PwProcess, inputs0)
        future1 = self.submit(PwProcess, inputs1)

        # Wait to complete before next step
        return ResultToContext(r0=future0, r1=future1)

    def put_step0_in_ctx(self, ctx):
        V, E, dE = get_volume_energy_and_derivative(ctx.r0['output_parameters'])

        ctx.step0 = {'V': V, 'E': E, 'dE': dE}

        # Prepare the list containing the steps
        # step 1 will be stored here by move_next_step
        ctx.steps = []

    def move_next_step(self, ctx):
        print "before m", ctx._get_dict()
        ddE = get_second_derivative(ctx.r0['output_parameters'],
                                    ctx.r1['output_parameters'])
        V, E, dE = get_volume_energy_and_derivative(ctx.r1['output_parameters'])
        a, b, c = get_abc(V, E, dE, ddE)

        new_step_data = {'V': V, 'E': E, 'dE': dE, 'ddE': ddE,
                         'a': a, 'b': b, 'c': c}
        ctx.steps.append(new_step_data)

        # Minimum of a parabola
        new_volume = -b / 2. / a
        print new_volume

        # remove older step
        ctx.r0 = ctx.r1
        scaled_structure = get_structure(self.inputs.structure, new_volume)
        ctx.last_structure = scaled_structure

        inputs = generate_scf_input_params(
            scaled_structure, self.inputs.code, self.inputs.pseudo_family)

        # Run PW
        future = self.submit(PwProcess, inputs)
        print "after m", ctx._get_dict()
        # Replace r1
        return ResultToContext(r1=future)

    def not_converged(self, ctx):
        print "conv", ctx._get_dict()
        return abs(ctx.r1['output_parameters'].dict.volume - ctx.r0[
            'output_parameters'].dict.volume) > self.inputs.volume_tolerance

    def report(self, ctx):
        self.out("steps", ctx.steps)
        self.out("structure", ctx.last_structure)

        print "Num steps:", len(ctx.steps)
        print ctx.steps


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Energy calculation example.')
    parser.add_argument('--pseudo', type=str, dest='pseudo', required=True,
                        help='The pseudopotential family')
    parser.add_argument('--code', type=str, dest='code', required=True,
                        help='The codename to use')

    structure = create_diamond_fcc(element=Str('Si'), alat=Float(5.2))

    print structure

    args = parser.parse_args()
    print run(PressureConvergence, structure=structure, code=Str(args.code),
              pseudo_family=Str(args.pseudo), volume_tolerance=Float(0.1))
