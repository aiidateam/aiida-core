"""
Workflow to calculate the band structure from a given structure in the DB.
"""
from aiida.common import aiidalogger
from aiida.orm.workflow import Workflow
from aiida.orm import Calculation, Code, Computer, Data
from aiida.common.exceptions import WorkflowInputValidationError
from aiida.orm import CalculationFactory, DataFactory

logger = aiidalogger.getChild('WorkflowDemo')

class WorkflowQEBands(Workflow):
    def __init__(self,**kwargs):        
        super(WorkflowQEBands, self).__init__(**kwargs)
   
    def start(self):       
                
        self.next(self.first_step)
        
    def first_step(self):
        PWCalc = CalculationFactory('quantumespresso.pw')

        calc = PWCalc(computer=self.get_parameters()['computername'],
                      withmpi=True)
        calc.set_resources(**self.get_parameters()['resources'])
        calc.store()

        s = Data.get_subclass_from_uuid(self.get_parameters()['structure_uuid'])
        calc.use_structure(s)
        
        calc.use_pseudo_from_family(self.get_parameters()['pseudo_family'])
        
        k = Data.get_subclass_from_uuid(self.get_parameters()['kpoints_uuid'])
        calc.use_kpoints(k)
                        
        self.add_calculation(calc)

        self.next(self.second_step)
    
    def second_step(self):
        self.next(self.exit)
