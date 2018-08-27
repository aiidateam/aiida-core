# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import absolute_import
from aiida.work.workchain import WorkChain, while_, ToContext, Outputs
from aiida.orm.data.float import Float
from aiida.orm.data.str import Str
from aiida.orm.utils import DataFactory
from aiida.work.workfunctions import workfunction as wf
from aiida.work.launch import run, submit
from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation


Proc = PwCalculation.process()


def generate_scf_input_params(**kwargs):
    pass


@wf
def rescale(structure, scale):
    the_ase = structure.get_ase()
    new_ase = the_ase.copy()
    new_ase.set_cell(the_ase.get_cell() * float(scale), scale_atoms=True)
    new_structure = DataFactory('structure')(ase=new_ase)
    return new_structure


@wf
def eos(structure, codename, pseudo_family):
    Proc = PwCalculation.process()
    results = {}
    for s in (0.98, 0.99, 1.0, 1.02, 1.04):
        rescaled = rescale(structure, Float(s))
        inputs = generate_scf_input_params(rescaled, codename, pseudo_family)
        outputs = run(Proc, **inputs)
        res = outputs['output_parameters'].dict
        results[str(s)] = res

    return results


class EquationOfState(WorkChain):
    @classmethod
    def define(cls, spec):
        super(EquationOfState, cls)._define(spec)
        spec.input("structure", valid_type=StructureData)
        spec.input("code", valid_type=Str)
        spec.input("pseudo_family", valid_type=Str)
        spec.outline(
            cls.launch_calculations,
            cls.finalise
        )

    def launch_calculations(self):
        launched = {}
        for s in (0.96, 0.98, 1., 1.02, 1.04):
            scaled = rescale(self.inputs.structure, Float(s))
            inputs = generate_scf_input_params(scaled, self.inputs.code, self.inputs.pseudo_family)
            pid = submit(Proc, **inputs)
            launched["s_" + str(s)] = pid


        return ToContext(r=Calc(1234), s=Outputs(1234))

        return ToContext(**launched)

    def finalise(self):
        for x in [key for key in self.ctx if key.startswith("s_")]:
            res = self.ctx[x]['output_parameters'].dict
            self.out(x[2:], res)


class EquationOfState2(WorkChain):
    @classmethod
    def define(cls, spec):
        super(EquationOfState2, cls)._define(spec)
        spec.input("structure", valid_type=StructureData)
        spec.input("code", valid_type=Str)
        spec.input("pseudo_family", valid_type=Str)
        spec.outline(
            cls.launch_calculations,
            cls.finalise
        )

    def launch_calculations(self):
        self.ctx.launched = {}
        for s in (0.96, 0.98, 1., 1.02, 1.04):
            scaled = rescale(self.inputs.structure, Float(s))
            inputs = generate_scf_input_params(scaled, self.inputs.code, self.inputs.pseudo_family)
            pid = submit(Proc, **inputs)
            self.ctx.launched[str(s)] = pid
            self.insert_barrier(Calc(pid))

    def finalise(self):
        for s, pid in self.ctx.launched.items():
            self.out(s, load_node(pid)['output_parameters'].dict)