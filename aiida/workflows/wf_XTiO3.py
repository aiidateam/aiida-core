# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
import aiida.common
from aiida.common import aiidalogger
from aiida.orm.workflow import Workflow
from aiida.orm import Code, Computer
from aiida.orm import CalculationFactory, DataFactory


UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')
StructureData = DataFactory('structure')

logger = aiidalogger.getChild('WorkflowXTiO3')

## ===============================================
##    WorkflowXTiO3_EOS
## ===============================================

class WorkflowXTiO3_EOS(Workflow):
    def __init__(self, **kwargs):

        super(WorkflowXTiO3_EOS, self).__init__(**kwargs)

    ## ===============================================
    ##    Structure generators
    ## ===============================================

    def get_structure(self, alat=4, x_material='Ba'):

        cell = [[alat, 0., 0., ],
                [0., alat, 0., ],
                [0., 0., alat, ],
        ]

        # BaTiO3 cubic structure
        s = StructureData(cell=cell)
        s.append_atom(position=(0., 0., 0.), symbols=x_material)
        s.append_atom(position=(alat / 2., alat / 2., alat / 2.), symbols=['Ti'])
        s.append_atom(position=(alat / 2., alat / 2., 0.), symbols=['O'])
        s.append_atom(position=(alat / 2., 0., alat / 2.), symbols=['O'])
        s.append_atom(position=(0., alat / 2., alat / 2.), symbols=['O'])
        s.store()

        return s

    def get_pw_parameters(self):

        parameters = ParameterData(dict={
            'CONTROL': {
                'calculation': 'scf',
                'restart_mode': 'from_scratch',
                'wf_collect': True,
            },
            'SYSTEM': {
                'ecutwfc': 30.,
                'ecutrho': 240.,
            },
            'ELECTRONS': {
                'conv_thr': 1.e-6,
            }}).store()

        return parameters

    def get_kpoints(self):

        kpoints = KpointsData()
        kpoints.set_kpoints_mesh([4, 4, 4])
        kpoints.store()

        return kpoints

    ## ===============================================
    ##    Calculations generators
    ## ===============================================

    def get_pw_calculation(self, pw_structure, pw_parameters, pw_kpoint):

        params = self.get_parameters()

        pw_codename = params['pw_codename']
        num_machines = params['num_machines']
        max_wallclock_seconds = params['max_wallclock_seconds']
        pseudo_family = params['pseudo_family']

        code = Code.get_from_string(pw_codename)
        computer = code.get_remote_computer()

        QECalc = CalculationFactory('quantumespresso.pw')

        calc = QECalc(computer=computer)
        calc.set_max_wallclock_seconds(max_wallclock_seconds)
        calc.set_resources({"num_machines": num_machines})
        calc.store()

        calc.use_code(code)

        calc.use_structure(pw_structure)
        calc.use_pseudos_from_family(pseudo_family)
        calc.use_parameters(pw_parameters)
        calc.use_kpoints(pw_kpoint)

        return calc

    ## ===============================================
    ##    Wf steps
    ## ===============================================

    @Workflow.step
    def start(self):

        params = self.get_parameters()
        x_material = params['x_material']

        self.append_to_report(x_material + "Ti03 EOS started")
        self.next(self.eos)

    @Workflow.step
    def eos(self):

        from aiida.orm import Code, Computer, CalculationFactory
        import numpy as np

        params = self.get_parameters()

        x_material = params['x_material']
        starting_alat = params['starting_alat']
        alat_steps = params['alat_steps']

        a_sweep = np.linspace(starting_alat * 0.85, starting_alat * 1.15, alat_steps).tolist()

        aiidalogger.info("Storing a_sweep as " + str(a_sweep))
        self.add_attribute('a_sweep', a_sweep)

        for a in a_sweep:
            self.append_to_report("Preparing structure {0} with alat {1}".format(x_material + "TiO3", a))

            calc = self.get_pw_calculation(self.get_structure(alat=a, x_material=x_material),
                                           self.get_pw_parameters(),
                                           self.get_kpoints())

            self.attach_calculation(calc)

        self.next(self.optimize)

    @Workflow.step
    def optimize(self):

        from aiida.orm.data.parameter import ParameterData

        x_material = self.get_parameter("x_material")
        a_sweep = self.get_attribute("a_sweep")

        aiidalogger.info("Retrieving a_sweep as {0}".format(a_sweep))

        # Get calculations
        start_calcs = self.get_step_calculations(self.eos)  # .get_calculations()

        # Calculate results
        #-----------------------------------------

        e_calcs = [c.res.energy for c in start_calcs]
        v_calcs = [c.res.volume for c in start_calcs]

        e_calcs = zip(*sorted(zip(a_sweep, e_calcs)))[1]
        v_calcs = zip(*sorted(zip(a_sweep, v_calcs)))[1]

        #  Add to report
        #-----------------------------------------
        for i in range(len(a_sweep)):
            self.append_to_report(x_material + "Ti03 simulated with a=" + str(a_sweep[i]) + ", e=" + str(e_calcs[i]))

        #  Find optimal alat
        #-----------------------------------------

        murnpars, ier = Murnaghan_fit(e_calcs, v_calcs)

        # New optimal alat
        optimal_alat = murnpars[3] ** (1 / 3.0)
        self.add_attribute('optimal_alat', optimal_alat)

        #  Build last calculation
        #-----------------------------------------

        calc = self.get_pw_calculation(self.get_structure(alat=optimal_alat, x_material=x_material),
                                       self.get_pw_parameters(),
                                       self.get_kpoints())
        self.attach_calculation(calc)

        self.next(self.final_step)

    @Workflow.step
    def final_step(self):

        from aiida.orm.data.parameter import ParameterData

        x_material = self.get_parameter("x_material")
        optimal_alat = self.get_attribute("optimal_alat")

        opt_calc = self.get_step_calculations(self.optimize)[0]  # .get_calculations()[0]
        opt_e = opt_calc.get_outputs(type=ParameterData)[0].get_dict()['energy']

        self.append_to_report(x_material + "Ti03 optimal with a=" + str(optimal_alat) + ", e=" + str(opt_e))

        self.add_result("scf_converged", opt_calc)

        self.next(self.exit)


def Murnaghan_fit(e, v):
    import pylab
    import numpy as np
    import scipy.optimize as optimize

    e = np.array(e)
    v = np.array(v)

    # Fit with parabola for first guess
    a, b, c = pylab.polyfit(v, e, 2)

    # Initial parameters
    v0 = -b / (2 * a)
    e0 = a * v0 ** 2 + b * v0 + c
    b0 = 2 * a * v0
    bP = 4

    def Murnaghan(vol, parameters):
        E0 = parameters[0]
        B0 = parameters[1]
        BP = parameters[2]
        V0 = parameters[3]

        EM = E0 + B0 * vol / BP * ( ((V0 / vol) ** BP) / (BP - 1) + 1 ) - V0 * B0 / (BP - 1.0)

        return EM

    # Minimization function
    def residuals(pars, y, x):
        # we will minimize this function
        err = y - Murnaghan(x, pars)
        return err

    p0 = [e0, b0, bP, v0]

    return optimize.leastsq(residuals, p0, args=(e, v))
