
import aiida.common
from aiida.common import aiidalogger
from aiida.orm.workflow import Workflow
from aiida.orm import Calculation, Code, Computer

logger = aiidalogger.getChild('WorkflowDemo')

class WorkflowDemoSubWorkflow(Workflow):
    
    def __init__(self,**kwargs):
        
        super(WorkflowDemoSubWorkflow, self).__init__(**kwargs)
        
    
    def start(self):
        
        from aiida.workflows.wf_demo import WorkflowDemo
        
        from aiida.orm import CalculationFactory
        CustomCalc = CalculationFactory('simpleplugins.templatereplacer')
        
        computer = Computer.get("localhost")
        
        calc = CustomCalc(computer=computer,withmpi=True)
        calc.set_resources(num_machines=1, num_cpus_per_machine=1)
        calc.store()
        self.attach_calculation(calc)
        
        params = {}
        params['nmachine']=2
    
        w = WorkflowDemo()
        w.set_params(params)
        w.start()
        self.attach_workflow(w)
        
        params['nmachine']=4
        w = WorkflowDemo()
        w.set_params(params)
        w.start()
        self.attach_workflow(w)
        
        self.next(self.second)
    
    def second(self):
        
        aiidalogger.info("ARRIVED !!")
        
        self.next(self.exit)
