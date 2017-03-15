# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.backends.utils import load_dbenv, is_dbenv_loaded


if not is_dbenv_loaded():
    load_dbenv()

from aiida.orm import load_node
from aiida.orm.utils import DataFactory
from aiida.work.db_types import NumericType, BaseType
from aiida.orm.code import Code
from aiida.orm.data.structure import StructureData
from aiida.work.run import run
from aiida.work.workchain import (WorkChain,
                                  ToContext, while_)
from aiida.work.workfunction import workfunction
from common import generate_scf_input_params
from diamond_fcc import rescale, create_diamond_fcc
from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation

GPa_to_eV_over_ang3 = 1. / 160.21766208

# Set up the factories
ParameterData = DataFactory("parameter")
KpointsData = DataFactory("array.kpoints")
PwProcess = PwCalculation.process()


def get_first_deriv(stress):
    """
    Return the energy first derivative from the stress
    """
    from numpy import trace
    # Get the pressure (GPa)
    p = trace(stress) / 3.
    # Pressure is -dE/dV; moreover p in kbar, we need to convert
    # it to eV/angstrom^3 to be consisten
    dE = -p * GPa_to_eV_over_ang3
    return dE


def get_volume_energy_and_derivative(output_parameters):
    """
    Given the output parameters of the pw calculation,
    return the volume (ang^3), the energy (eV), and the energy
    derivative (eV/ang^3)
    """
    V = output_parameters.dict.volume
    E = output_parameters.dict.energy
    dE = get_first_deriv(output_parameters.dict.stress)

    return (V, E, dE)


def get_second_derivative(outp1, outp2):
    """
    Given the output parameters of the two pw calculations,
    return the second derivative obtained from finite differences
    from the pressure of the two calculations (eV/ang^6)
    """
    dE1 = get_first_deriv(outp1.dict.stress)
    dE2 = get_first_deriv(outp2.dict.stress)
    V1 = outp1.dict.volume
    V2 = outp2.dict.volume
    return (dE2 - dE1) / (V2 - V1)


def get_abc(V, E, dE, ddE):
    """
    Given the volume, energy, energy first derivative and energy
    second derivative, return the a,b,c coefficients of
    a parabola E = a*V^2 + b*V + c
    """
    a = ddE / 2.
    b = dE - ddE * V
    c = E - V * dE + V ** 2 * ddE / 2.

    return a, b, c


def get_structure(original_structure, new_volume):
    """
    Given a structure and a new volume, rescale the structure to the new volume
    """
    initial_volume = original_structure.get_cell_volume()
    scale_factor = (new_volume / initial_volume) ** (1. / 3.)
    scaled_structure = rescale(original_structure, Float(scale_factor))
    return scaled_structure


class PressureConvergence(WorkChain):
    """
    Converge to minimum using Newton's algorithm on the first derivative of the energy (minus the pressure).
    """

    @classmethod
    def define(cls, spec):
        """
        Workfunction definition
        """
        spec.input("structure", valid_type=StructureData)
        spec.input("volume_tolerance",
                   valid_type=NumericType)  # , default=Float(0.1))
        spec.input("code", valid_type=BaseType)
        spec.input("pseudo_family", valid_type=BaseType)
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

    def init(self):
        """
        Launch the first calculation for the input structure,
        and a second calculation for a shifted volume (increased by 4 angstrom^3)
        Store the outputs of the two calcs in r0 and r1
        """
        inputs0 = generate_scf_input_params(
            self.inputs.structure, self.inputs.code, self.inputs.pseudo_family)

        initial_volume = self.inputs.structure.get_cell_volume()
        new_volume = initial_volume + 4.  # In ang^3

        scaled_structure = get_structure(self.inputs.structure, new_volume)
        inputs1 = generate_scf_input_params(
            scaled_structure, self.inputs.code, self.inputs.pseudo_family)

        self.ctx.last_structure = scaled_structure

        # Run PW
        future0 = self.submit(PwProcess, inputs0)
        future1 = self.submit(PwProcess, inputs1)

        # Wait to complete before next step
        return ToContext(r0=future0.pid, r1=future1.pid)

    def put_step0_in_ctx(self):
        """
        Store the outputs of the very first step in a specific dictionary
        """
        V, E, dE = get_volume_energy_and_derivative(
            self.ctx.r0['output_parameters'])

        self.ctx.step0 = {'V': V, 'E': E, 'dE': dE}

        # Prepare the list containing the steps
        # step 1 will be stored here by move_next_step
        self.ctx.steps = []

    def move_next_step(self):
        """
        Main routine that reads the two previous calculations r0 and r1,
        uses the Newton's algorithm on the pressure (i.e., fits the results
        with a parabola and sets the next point to calculate to the parabola
        minimum).
        r0 gets replaced with r1, r1 will get replaced by the results of the
        new calculation.
        """
        ddE = get_second_derivative(self.ctx.r0['output_parameters'],
                                    self.ctx.r1['output_parameters'])
        V, E, dE = get_volume_energy_and_derivative(
            self.ctx.r1['output_parameters'])
        a, b, c = get_abc(V, E, dE, ddE)

        new_step_data = {'V': V, 'E': E, 'dE': dE, 'ddE': ddE,
                         'a': a, 'b': b, 'c': c}
        self.ctx.steps.append(new_step_data)

        # Minimum of a parabola
        new_volume = -b / 2. / a

        # remove older step
        self.ctx.r0 = self.ctx.r1
        scaled_structure = get_structure(self.inputs.structure, new_volume)
        self.ctx.last_structure = scaled_structure

        inputs = generate_scf_input_params(
            scaled_structure, self.inputs.code, self.inputs.pseudo_family)

        # Run PW
        future = self.submit(PwProcess, inputs)
        # Replace r1
        return ToContext(r1=future.pid)

    def not_converged(self):
        """
        Return True if the worflow is not converged yet (i.e., the volume changed significantly)
        """
        deltaV = abs(self.ctx.r1['output_parameters'].dict.volume -
                     self.ctx.r0['output_parameters'].dict.volume)
        return deltaV > self.inputs.volume_tolerance

    def report(self):
        """
        Output final quantities
        """
        from aiida.orm import DataFactory
        self.out("steps", DataFactory('parameter')(dict={
            'steps': self.ctx.steps,
            'step0': self.ctx.step0}))
        self.out("structure", self.ctx.last_structure)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Energy calculation example.')
    parser.add_argument('--pseudo', type=str, dest='pseudo', required=True,
                        help='The pseudopotential family')
    parser.add_argument('--code', type=str, dest='code', required=True,
                        help='The codename to use')

    structure = create_diamond_fcc(element=make_str('Si'), alat=Float(5.2))

    print "Initial structure:", structure

    args = parser.parse_args()
    wf_results = run(PressureConvergence, structure=structure,
                     code=make_str(args.code), pseudo_family=make_str(args.pseudo),
                     volume_tolerance=Float(0.1))
    print "Workflow results:"
    print wf_results
