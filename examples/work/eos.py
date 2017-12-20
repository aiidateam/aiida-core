#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-

from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from aiida.orm import CalculationFactory, DataFactory, Code
from aiida.orm.data.base import BaseType, Float, Str
from aiida.orm.data.structure import StructureData
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.array.kpoints import KpointsData
from aiida.work.utils import ProcessStack
from aiida.work.workfunctions import workfunction
from aiida.work.workchain import WorkChain, ToContext, while_, Outputs
from aiida import work
from examples.work import common

PwCalculation = CalculationFactory('quantumespresso.pw')


@workfunction
def create_diamond_fcc(element, alat):
    """
    Workfunction to create a diamond crystal structure with a given element.

    :param element: The element to create the structure with.
    :return: The structure.
    """
    from numpy import array
    the_cell = array([[0., 0.5, 0.5],
                      [0.5, 0., 0.5],
                      [0.5, 0.5, 0.]]) * alat
    StructureData = DataFactory("structure")
    structure = StructureData(cell=the_cell)
    structure.append_atom(position=(0., 0., 0.), symbols=str(element))
    structure.append_atom(position=(0.25 * alat, 0.25 * alat, 0.25 * alat), symbols=str(element))
    return structure


@workfunction
def rescale(structure, scale):
    """
    Workfunction to rescale a structure

    :param structure: An AiiDA structure to rescale
    :param scale: The scale factor
    :return: The rescaled structure
    """
    the_ase = structure.get_ase()
    new_ase = the_ase.copy()
    new_ase.set_cell(the_ase.get_cell() * float(scale), scale_atoms=True)
    new_structure = DataFactory('structure')(ase=new_ase)
    return new_structure


class EquationOfState(WorkChain):
    @classmethod
    def define(cls, spec):
        super(EquationOfState, cls).define(spec)
        spec.input("structure", valid_type=StructureData)
        spec.input("codename", valid_type=BaseType)
        spec.input("pseudo_family", valid_type=BaseType)
        spec.outline(
            cls.init,
            while_(cls.not_finished)(
                cls.run_pw,
                cls.print_result
            )
        )

    def init(self):
        self.ctx.scales = (0.96, 0.98, 1., 1.02, 1.04)
        self.ctx.i = 0

    def not_finished(self):
        return self.ctx.i < len(self.ctx.scales)

    def run_pw(self):
        scale = self.ctx.scales[self.ctx.i]
        scaled = rescale(self.inputs.structure, Float(scale))

        inputs = common.generate_scf_input_params(
            scaled, self.inputs.codename, self.inputs.pseudo_family)

        # Launch the code
        process = PwCalculation.process()
        future = self.submit(process, **inputs)

        return ToContext(result=Outputs(future))

    def print_result(self):
        print self.ctx.scales[self.ctx.i], self.ctx.result['output_parameters'].dict.energy
        self.ctx.i += 1


structure = create_diamond_fcc(Str('C'), Float(3.57))
codename = 'pwx@localhost'
pseudo_family_name = 'sssp_eff'

work.run(EquationOfState,
         structure=structure,
         codename=Str(codename),
         pseudo_family=Str(pseudo_family_name)
         )
