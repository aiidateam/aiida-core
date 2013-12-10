import aiida.common
from aiida.common import aiidalogger
from aiida.orm.workflow import Workflow
from aiida.orm import Calculation, Code, Computer

logger = aiidalogger.getChild('wfgiovanni')

class WorkflowCustomEOS(Workflow):
    
    def __init__(self,**kwargs):
        
        super(WorkflowCustomEOS, self).__init__(**kwargs)
    
    def generate_calc(self, parameters, structure, kpoints):
        """
        Generate a suitable QE PW calculation using the parameters given in
        input to the WF for code, resources and pseudos.

        In input: structure, parameters and kpoints (must be nodes)
        """
        
        from aiida.orm import CalculationFactory
        
        params = self.get_parameters()
        
        pw_codename            = params['pw_codename']
        num_machines           = params['num_machines']
        num_cpus_per_machine   = params['num_cpus_per_machine']
        max_wallclock_seconds  = params['max_wallclock_seconds']
        pseudo_family          = params['pseudo_family']
        
        code = Code.get(pw_codename)
        computer = code.get_remote_computer()
        
        QECalc = CalculationFactory('quantumespresso.pw')
        
        calc = QECalc(computer=computer)
        calc.set_max_wallclock_seconds(max_wallclock_seconds)
        calc.set_resources(num_machines=num_machines, num_cpus_per_machine=num_cpus_per_machine)
        calc.store()
        
        calc.use_code(code)
        
        calc.use_structure(structure)
        calc.use_pseudo_from_family(pseudo_family)
        calc.use_parameters(parameters)
        calc.use_kpoints(kpoints)
        
        return calc
        
    @Workflow.step
    def start(self):
        
        from aiida.orm import CalculationFactory, DataFactory 
        import ase
        import copy
        
        UpfData = DataFactory('upf')
        ParameterData = DataFactory('parameter')
        StructureData = DataFactory('structure')

        # BNBNHHHH, z-axis = 20
        template_rel_coords = [
            [0.166666667,   0.000000000,   0.010828843],
            [0.333333333,   0.500000000,  -0.014942177],
            [0.666666667,   0.500000000,   0.010828843],
            [0.833333333,   0.000000000,  -0.014942177],
            [0.166666667,   0.000000000,   0.070745836],
            [0.333333333,   0.500000000,  -0.066632502],
            [0.666666667,   0.500000000,   0.070745836],
            [0.833333333,   0.000000000,  -0.066632502]] 

        # Testing parameters
        p = self.get_parameters()

        # Testing report
        self.append_to_report("Starting workflow with params: {0}".format(p))

        kpoints = ParameterData({
                'type': 'automatic',
                'points': [6, 12, 1, 1, 1, 0],
                }).store()

        parameters = ParameterData({
            'CONTROL': {
                'calculation': 'vc-relax',
                'restart_mode': 'from_scratch',
                'wf_collect': True,
                'forc_conv_thr': 1.e-5,
                },
            'SYSTEM': {
                'ecutwfc': 60.,
                'ecutrho': 350.,
                },
            'ELECTRONS': {
                'conv_thr': 1.e-10,
                },
             'CELL': {
                 'cell_dofree': p['cell_dofree']}}).store()

        if p['functionalized']:
            asecell = ase.Atoms('BNBNHHHH', cell=(4.49, 2.59, 20.))
            rel_coords = copy.deepcopy(template_rel_coords)
        else:
            asecell = ase.Atoms('BNBN', cell=(4.35, 2.51, 20.))
            rel_coords = copy.deepcopy(template_rel_coords[:4])
            for rel_coord in rel_coords:
                rel_coord[2] = 0.


        for value in p['value_range']:
            # BaTiO3 cubic structure
            asecell.cell[p['change_coord'],p['change_coord']] = value
            asecell.set_scaled_positions(rel_coords)
            structure = StructureData(ase=asecell).store()
            # Testing calculations
            self.attach_calculation(self.generate_calc(parameters, structure,
                                                       kpoints))
        
        
#        n = Node()
#        attrs = {"a": [1,2,3], "n": n}
#        self.add_attributes(attrs)

        # Test process
        self.next(self.second_step)
    
    @Workflow.step
    def second_step(self):
        
        # Test retrieval
        calcs = self.get_step_calculations(self.start)
        for calc in calcs:
            self.append_to_report("Retrieved calculation {0}".format(calc.pk))
                
        self.next(self.exit)
        
        
        
