from __future__ import division
import aiida.common
from aiida.common import aiidalogger
from aiida.orm.workflow import Workflow
from aiida.orm import Calculation, Code, Computer
from aiida.orm import CalculationFactory, DataFactory
        
UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
StructureData = DataFactory('structure')

logger = aiidalogger.getChild('WorkflowDemo')

## ===============================================
##    WorkflowXTiO3
## ===============================================

class WorkflowXTiO3(Workflow):
    
    def __init__(self,**kwargs):
        
        super(WorkflowXTiO3, self).__init__(**kwargs)
    
    def get_ph_parameters(self):
        
        parameters = ParameterData({
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
        
        ph_codename            = params.pop('ph_codename', 'phlocal')
        num_machines           = int(params.pop('num_machines', 1))
        num_cpus_per_machine   = int(params.pop('num_cpus_per_machine', 8))
        max_wallclock_seconds  = int(params.pop('max_wallclock_seconds', 30*60))
        
        code = Code.get(ph_codename)
        computer = code.get_remote_computer()
        
        QEPhCalc = CalculationFactory('quantumespresso.ph')
        calc = QEPhCalc(computer=computer)
        
        calc.set_max_wallclock_seconds(max_wallclock_seconds) # 30 min
        calc.set_resources(num_machines=num_machines, num_cpus_per_machine=num_cpus_per_machine)
        calc.store()
        
        calc.use_parameters(ph_parameters)
        calc.use_code(code)
        calc.set_parent_calc(pw_calc)
        
        return calc
    
    ## ===============================================
    ##    Wf steps
    ## ===============================================
    
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
        
    def final_step(self):
        
        #self.append_to_report(x_material+"Ti03 EOS started")
        from aiida.orm.data.parameter import ParameterData
        import aiida.tools.physics as ps
        
        params = self.get_parameters()
        
        # Get calculations
        start_calcs = self.get_step(self.run_ph).get_calculations()
        
        for c in start_calcs:
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
        
        parameters = ParameterData({
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
        
        kpoints = ParameterData({
                        'type': 'automatic',
                        'points': [4, 4, 4, 0, 0, 0],
                        }).store()
        
        return kpoints
    
    ## ===============================================
    ##    Calculations generators
    ## ===============================================
    
    def get_pw_calculation(self, pw_structure, pw_parameters, pw_keypoint):
        
        params = self.get_parameters()
        
        pw_codename               = params.pop('pw_codename', 'pwlocal')
        num_machines           = int(params.pop('num_machines', 1))
        num_cpus_per_machine   = int(params.pop('num_cpus_per_machine', 8))
        max_wallclock_seconds  = int(params.pop('max_wallclock_seconds', 30*60))
        pseudo_family          = params.pop('pseudo_family', 'PBEsol_rrkjus_pslibrary_0.3.0')
        
        code = Code.get(pw_codename)
        computer = code.get_remote_computer()
        
        QECalc = CalculationFactory('quantumespresso.pw')
        
        calc = QECalc(computer=computer)
        calc.set_max_wallclock_seconds(max_wallclock_seconds)
        calc.set_resources(num_machines=num_machines, num_cpus_per_machine=num_cpus_per_machine)
        calc.store()
        
        calc.use_code(code)
        
        calc.use_structure(pw_structure)
        calc.use_pseudo_from_family(pseudo_family)
        calc.use_parameters(pw_parameters)
        calc.use_kpoints(pw_keypoint)
        
        return calc
        
        
    ## ===============================================
    ##    Wf steps
    ## ===============================================
    
    
    def start(self):
        
        params = self.get_parameters()
        x_material             = params.pop('x_material', 'Ba')
        
        self.append_to_report(x_material+"Ti03 EOS started")
        self.next(self.eos)
    
    def eos(self):
        
        from aiida.orm import Code, Computer, CalculationFactory
        import numpy as np
        
        params = self.get_parameters()
        
        x_material             = params.pop('x_material', 'Ba')
        starting_alat          = float(params.pop('starting_alat', 4.0))
        alat_steps             = int(params.pop('alat_steps', 5))
        
        
        a_sweep = np.linspace(starting_alat*0.85,starting_alat*1.15,alat_steps).tolist()
        
        aiidalogger.info("Storing a_sweep as "+str(a_sweep))
        self.add_parameters({'a_sweep':a_sweep})
        
        for a in a_sweep:
            
            self.append_to_report("Preparing structure {0} with alat {1}".format(x_material+"TiO3",a))
            
            calc = self.get_pw_calculation(self.get_structure(alat=a, x_material=x_material),
                                      self.get_pw_parameters(),
                                      self.get_kpoints())
            
            self.attach_calculation(calc)
            
            
        self.next(self.optimize)
        
        
    def optimize(self):
        
        from aiida.orm.data.parameter import ParameterData
        import aiida.tools.physics as ps
        
        params = self.get_parameters()
        x_material   = params.pop('x_material', 'Ba')
        a_sweep      = params.pop('a_sweep',[])
        
        aiidalogger.info("Retrieving a_sweep as "+str(a_sweep))
        
        # Get calculations
        start_calcs = self.get_step(self.eos).get_calculations()
        
        #  Calculate results
        #-----------------------------------------
        
        e_calcs = [c.get_outputs(type=ParameterData)[0].get_dict()['energy'][-1] for c in start_calcs]
        v_calcs = [c.get_outputs(type=ParameterData)[0].get_dict()['cell']['volume'] for c in start_calcs]
        
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
        self.add_parameters({'optimal_alat':optimal_alat})
        
        #  Build last calculation
        #-----------------------------------------
        
        calc = self.get_pw_calculation(self.get_structure(alat=optimal_alat, x_material=x_material),
                                      self.get_pw_parameters(),
                                      self.get_kpoints())
        self.attach_calculation(calc)
        
        
        self.next(self.final_step)
        
    def final_step(self):
        
        params = self.get_parameters()
        x_material   = params.pop('x_material', 'Ba')
        optimal_alat   = params.pop('optimal_alat', -1.0)
        
        opt_calc = self.get_step(self.optimize).get_calculations()[0]
        opt_e = opt_calc.get_outputs(type=ParameterData)[0].get_dict()['energy'][-1]
        
        self.append_to_report(x_material+"Ti03 optimal with a="+str(optimal_alat)+", e="+str(opt_e))
            
        self.next(self.exit)



