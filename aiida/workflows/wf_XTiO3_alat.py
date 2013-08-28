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

class WorkflowXTiO3_alat(Workflow):
    
    def __init__(self,**kwargs):
        
        super(WorkflowXTiO3_alat, self).__init__(**kwargs)

    ## ===============================================
    ##    Structure generators
    ## ===============================================
    
    def linspace(self, start, stop, n):
        if n == 1:
            yield stop
            return
        h = (stop - start) / (n - 1)
        for i in range(n):
            yield start + h * i
        
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
    ##    Wf steps
    ## ===============================================
    
    
    def start(self):
        
        from aiida.orm import Code, Computer, CalculationFactory
        
        params = self.get_parameters()
        
        x_material             = params.pop('x_material', 'Ba')
        starting_alat          = float(params.pop('starting_alat', 4.0))
        
        codename               = params.pop('codename', 'pwlocal')
        num_machines           = int(params.pop('num_machines', 1))
        num_cpus_per_machine   = int(params.pop('num_cpus_per_machine', 8))
        max_wallclock_seconds  = int(params.pop('max_wallclock_seconds', 30*60))
        pseudo_family          = params.pop('pseudo_family', 'PBEsol_rrkjus_pslibrary_0.3.0')
        
        code = Code.get(codename)
        computer = code.get_remote_computer()
        
        QECalc = CalculationFactory('quantumespresso.pw')
        
        for a in self.linspace(starting_alat*0.85,starting_alat*1.15,5):
            
            calc = QECalc(computer=computer)
            calc.set_max_wallclock_seconds(max_wallclock_seconds)
            calc.set_resources(num_machines=num_machines, num_cpus_per_machine=num_cpus_per_machine)
            calc.store()
            
            aiidalogger.info("Loading structure with alat {0} with alat {1}".format(x_material+"TiO3",a))
            
            calc.use_structure(self.get_structure(alat=a, x_material=x_material))
            calc.use_code(code)
            calc.use_parameters(self.get_pw_parameters())
            calc.use_kpoints(self.get_kpoints())
            
            calc.use_pseudo_from_family(pseudo_family)
            
            aiidalogger.info("Launched structure {0} with alat {1}".format(x_material+"TiO3",a))
            
            
        self.next(self.optimize)
        
        # Run calculations
    
    def optimize(self):
        
        from aiida.orm.data.parameter import ParameterData
        
        start_calcs = self.get_step(self.start).get_calculations()
        
        e_calcs = [c.get_outputs(type=ParameterData)[0].get_dict()['energy'][-1] for c in start_calcs]
        v_calcs = [c.get_outputs(type=ParameterData)[0].get_dict()['cell']['volume'] for c in start_calcs]
        
        v_calcs, e_calcs = zip(*sorted(zip(v_calcs, e_calcs)))
        
        aiidalogger.info("Running Murnaghan_fit for optimal structure")
        
        import aiida.tools.physics as ps
        murnpars, ier = ps.Murnaghan_fit(e_calcs, v_calcs)
        optimal_alat  = murnpars[3]** (1 / 3.0)
        
        
        #-----------------------------------------
        params = self.get_parameters()
        
        x_material             = params.pop('x_material', 'Ba')
        codename               = params.pop('codename', 'pwlocal')
        num_machines           = int(params.pop('num_machines', 1))
        num_cpus_per_machine   = int(params.pop('num_cpus_per_machine', 8))
        max_wallclock_seconds  = int(params.pop('max_wallclock_seconds', 30*60))
        pseudo_family          = params.pop('pseudo_family', 'PBEsol_rrkjus_pslibrary_0.3.0')
        
        code = Code.get(codename)
        computer = code.get_remote_computer()
        
        QECalc = CalculationFactory('quantumespresso.pw')
        
        calc = QECalc(computer=computer)
        calc.set_max_wallclock_seconds(max_wallclock_seconds)
        calc.set_resources(num_machines=num_machines, num_cpus_per_machine=num_cpus_per_machine)
        calc.store()
        
        aiidalogger.info("Loading optimal structure with alat {0} with alat {1}".format(x_material+"TiO3",optimal_alat))
        
        calc.use_structure(self.get_structure(alat=optimal_alat, x_material=x_material))
        calc.use_code(code)
        calc.use_parameters(self.get_pw_parameters())
        calc.use_kpoints(self.get_kpoints())
        
        calc.use_pseudo_from_family(pseudo_family)
        
        aiidalogger.info("Launched optimal structure {0} with alat {1}".format(x_material+"TiO3",optimal_alat))
        aiidalogger.info("Energies {0}".format(e_calcs))
        
        self.next(self.final_step)
        
    def final_step(self):
        
        self.next(self.exit)



