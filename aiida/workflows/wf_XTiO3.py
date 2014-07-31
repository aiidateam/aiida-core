# -*- coding: utf-8 -*-
from __future__ import division
import aiida.common
from aiida.common import aiidalogger
from aiida.orm.workflow import Workflow
from aiida.orm import Calculation, Code, Computer
from aiida.orm import CalculationFactory, DataFactory
        
__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')
StructureData = DataFactory('structure')

logger = aiidalogger.getChild('WorkflowXTiO3')

## ===============================================
##    WorkflowXTiO3
## ===============================================

class WorkflowXTiO3(Workflow):
    
    def __init__(self,**kwargs):
        
        super(WorkflowXTiO3, self).__init__(**kwargs)
    
    def get_ph_parameters(self):
        
        parameters = ParameterData(dict={
            'INPUTPH': {
                'tr2_ph' : 1.0e-8,
                'epsil' : True,
                'ldisp' : True,
                'nq1' : 1,
                'nq2' : 1,
                'nq3' : 1,
                }}).store()
                
        return parameters
    
    ## ===============================================
    ##    Calculations generators
    ## ===============================================
    
    def get_ph_calculation(self, pw_calc, ph_parameters):
        
        params = self.get_parameters()
        
        ph_codename            = params['ph_codename']
        num_machines           = params['num_machines']
        num_mpiprocs_per_machine   = params['num_mpiprocs_per_machine']
        max_wallclock_seconds  = params['max_wallclock_seconds']
        
        code = Code.get(ph_codename)
        computer = code.get_remote_computer()
        
        QEPhCalc = CalculationFactory('quantumespresso.ph')
        calc = QEPhCalc(computer=computer)
        
        calc.set_max_wallclock_seconds(max_wallclock_seconds) # 30 min
        calc.set_resources({"num_machines": num_machines, "num_mpiprocs_per_machine": num_mpiprocs_per_machine})
        calc.store()
        
        calc.use_parameters(ph_parameters)
        calc.use_code(code)
        calc.set_parent_calc(pw_calc)
        
        return calc
    
    ## ===============================================
    ##    Wf steps
    ## ===============================================
    
    @Workflow.step
    def start(self):
        
        params = self.get_parameters()
        elements_alat = [('Ba',4.0),('Sr', 3.89), ('Pb', 3.9)]
        #elements_alat = [('Ba',4.0)]
        
        for x in elements_alat:
            
            params.update({'x_material':x[0]})
            params.update({'starting_alat':x[1]})
            
            aiidalogger.info("Launching workflow WorkflowXTiO3_EOS for {0} with alat {1}".format(x[0],x[1]))
            
            w = WorkflowXTiO3_EOS(params=params)
            w.start()
            self.attach_workflow(w)
        
        self.next(self.run_ph)
        
    @Workflow.step
    def run_ph(self):
        
        # Get calculations
        sub_wfs = self.get_step(self.start).get_sub_workflows()
        
        for sub_wf in sub_wfs:
            
            # Retrieve the pw optimized calculation
            pw_calc = sub_wf.get_step("optimize").get_calculations()[0]
            
            aiidalogger.info("Launching PH for PW {0}".format(pw_calc.get_job_id()))
            ph_calc = self.get_ph_calculation(pw_calc, self.get_ph_parameters())
            self.attach_calculation(ph_calc)
            
        self.next(self.final_step)
    
    @Workflow.step
    def final_step(self):
        
        #self.append_to_report(x_material+"Ti03 EOS started")
        from aiida.orm.data.parameter import ParameterData
        import aiida.tools.physics as ps
        
        params = self.get_parameters()
        
        # Get calculations
        run_ph_calcs = self.get_step_calculations(self.run_ph) #.get_calculations()
        
        for c in run_ph_calcs:
            dm = c.get_outputs(type=ParameterData)[0].get_dict()['dynamical_matrix_1']
            self.append_to_report("Point q: {0} Frequencies: {1}".format(dm['q_point'],dm['frequencies']))
        
        self.next(self.exit)
    

## ===============================================
##    WorkflowXTiO3_EOS
## ===============================================
        
class WorkflowXTiO3_EOS(Workflow):
    
    def __init__(self,**kwargs):
        
        super(WorkflowXTiO3_EOS, self).__init__(**kwargs)

    ## ===============================================
    ##    Structure generators
    ## ===============================================
    
    def get_structure(self, alat = 4, x_material = 'Ba'):
        
        cell = [[alat, 0., 0.,],
                [0., alat, 0.,],
                [0., 0., alat,],
               ]
        
        # BaTiO3 cubic structure
        s = StructureData(cell=cell)
        s.append_atom(position=(0.,0.,0.),symbols=x_material)
        s.append_atom(position=(alat/2.,alat/2.,alat/2.),symbols=['Ti'])
        s.append_atom(position=(alat/2.,alat/2.,0.),symbols=['O'])
        s.append_atom(position=(alat/2.,0.,alat/2.),symbols=['O'])
        s.append_atom(position=(0.,alat/2.,alat/2.),symbols=['O'])
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
        kpoints.set_kpoints_mesh([4,4,4])
        kpoints.store()
        
        return kpoints
    
    ## ===============================================
    ##    Calculations generators
    ## ===============================================
    
    def get_pw_calculation(self, pw_structure, pw_parameters, pw_kpoint):
        
        params = self.get_parameters()
        
        pw_codename            = params['pw_codename']
        num_machines           = params['num_machines']
        num_mpiprocs_per_machine   = params['num_mpiprocs_per_machine']
        max_wallclock_seconds  = params['max_wallclock_seconds']
        pseudo_family          = params['pseudo_family']
        
        code = Code.get(pw_codename)
        computer = code.get_remote_computer()
        
        QECalc = CalculationFactory('quantumespresso.pw')
        
        calc = QECalc(computer=computer)
        calc.set_max_wallclock_seconds(max_wallclock_seconds)
        calc.set_resources({"num_machines": num_machines, "num_mpiprocs_per_machine": num_mpiprocs_per_machine})
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
        x_material             = params['x_material']
        
        self.append_to_report(x_material+"Ti03 EOS started")
        self.next(self.eos)
    
    @Workflow.step
    def eos(self):
        
        from aiida.orm import Code, Computer, CalculationFactory
        import numpy as np
        
        params = self.get_parameters()
        
        x_material             = params['x_material']
        starting_alat          = params['starting_alat']
        alat_steps             = params['alat_steps']
        
        
        a_sweep = np.linspace(starting_alat*0.85,starting_alat*1.15,alat_steps).tolist()
        
        aiidalogger.info("Storing a_sweep as "+str(a_sweep))
        self.add_attribute('a_sweep',a_sweep)
        
        for a in a_sweep:
            
            self.append_to_report("Preparing structure {0} with alat {1}".format(x_material+"TiO3",a))
            
            calc = self.get_pw_calculation(self.get_structure(alat=a, x_material=x_material),
                                      self.get_pw_parameters(),
                                      self.get_kpoints())
            
            self.attach_calculation(calc)
            
            
        self.next(self.optimize)
        
    @Workflow.step  
    def optimize(self):
        
        from aiida.orm.data.parameter import ParameterData
        import aiida.tools.physics as ps
        
        x_material   = self.get_parameter("x_material")
        a_sweep      = self.get_attribute("a_sweep")
        
        aiidalogger.info("Retrieving a_sweep as {0}".format(a_sweep))
        
        # Get calculations
        start_calcs = self.get_step_calculations(self.eos) #.get_calculations()
        
        #  Calculate results
        #-----------------------------------------
        
        e_calcs = [c.res.energy[-1] for c in start_calcs]
        v_calcs = [c.res.cell['volume'] for c in start_calcs]
        
        e_calcs = zip(*sorted(zip(a_sweep, e_calcs)))[1]
        v_calcs = zip(*sorted(zip(a_sweep, v_calcs)))[1]
        
        #  Add to report
        #-----------------------------------------
        for i in range (len(a_sweep)):
            self.append_to_report(x_material+"Ti03 simulated with a="+str(a_sweep[i])+", e="+str(e_calcs[i]))
        
        #  Find optimal alat
        #-----------------------------------------
        
        murnpars, ier = ps.Murnaghan_fit(e_calcs, v_calcs)
        
        # New optimal alat
        optimal_alat  = murnpars[3]** (1 / 3.0)
        self.add_attribute('optimal_alat',optimal_alat)
        
        #  Build last calculation
        #-----------------------------------------
        
        calc = self.get_pw_calculation(self.get_structure(alat=optimal_alat, x_material=x_material),
                                      self.get_pw_parameters(),
                                      self.get_kpoints())
        self.attach_calculation(calc)
        
        
        self.next(self.final_step)
     
    @Workflow.step   
    def final_step(self):
        
        x_material   = self.get_parameter("x_material")
        optimal_alat = self.get_attribute("optimal_alat")
        
        opt_calc = self.get_step_calculations(self.optimize) #.get_calculations()[0]
        opt_e = opt_calc.get_outputs(type=ParameterData)[0].get_dict()['energy'][-1]
        
        self.append_to_report(x_material+"Ti03 optimal with a="+str(optimal_alat)+", e="+str(opt_e))
        
        self.add_result("scf.converged", opt_calc)
            
        self.next(self.exit)



