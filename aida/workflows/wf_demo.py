
import aida.common
from aida.common import aidalogger
from aida.orm.workflow import Workflow
from aida.orm import Calculation, Code, Computer

logger = aidalogger.getChild('WorkflowDemo')

class WorkflowDemo(Workflow):
    
    def __init__(self,**kwargs):
        
        super(WorkflowDemo, self).__init__(**kwargs)
        
    
    def start(self):
        
        from aida.orm import Calculation, Code, Computer
        
        computer = Computer.get("localhost")
        
        calc     =  Calculation(computer=computer,num_machines=self.params['nmachine'],num_cpus_per_machine=1).store()
        calc2     = Calculation(computer=computer,num_machines=self.params['nmachine']*2,num_cpus_per_machine=1).store()
        
        self.add_calculation(calc)
        self.add_calculation(calc2)
        
        self.next(self.second_step)
        
        # Run calculations
    
    def second_step(self):
        
        calcs_init = self.get_calculations(self.start)
        
        aidalogger.info("Second runned and retived calculation:")
        for c in calcs_init:
            aidalogger.info("  Calculation {0}".format(c.uuid))
        
        from aida.orm import Calculation, Code, Computer
            
        computer = Computer.get("localhost")
        calc     =  Calculation(computer=computer,num_machines=self.params['nmachine']*4,num_cpus_per_machine=1).store()
        calc2     = Calculation(computer=computer,num_machines=self.params['nmachine']*8,num_cpus_per_machine=1).store()
        
        self.add_calculation(calc)
        self.add_calculation(calc2)
        
        self.next(self.third_step)
    
        
    def third_step(self):
        
        calcs_init = self.get_calculations(self.second_step)
        
        aidalogger.info("Third runned and retived calculation:")
        for c in calcs_init:
            aidalogger.info("  Calculation {0}".format(c.uuid))
            
        
        self.next(self.exit)


class WorkflowDemoBranch(Workflow):
    
    def __init__(self,**kwargs):
        super(WorkflowDemoBranch, self).__init__(**kwargs)
    
    def start(self):
    
        self.branch_a_one()
        self.branch_b_one()
        
    def branch_a_one(self):
        
        aidalogger.info("branch_a_one launched")
        
        computer = Computer.get("localhost")
        calc     = Calculation(computer=computer,num_machines=self.params['nmachine']*4,num_cpus_per_machine=1).store()
        self.add_calculation(calc)
        
        self.next(self.branch_a_two)
    
    def branch_a_two(self):
        
        aidalogger.info("branch_a_two launched")
        
        computer = Computer.get("localhost")
        calc     = Calculation(computer=computer,num_machines=self.params['nmachine']*4,num_cpus_per_machine=1).store()
        self.add_calculation(calc)
        
        self.next(self.recollect)
        
    def branch_b_one(self):
        
        aidalogger.info("branch_b_one launched")
        
        computer = Computer.get("localhost")
        calc     = Calculation(computer=computer,num_machines=self.params['nmachine']*4,num_cpus_per_machine=1).store()
        self.add_calculation(calc)
        
        self.next(self.recollect)
    
    def recollect(self):
        
        aidalogger.info("recollect launched")
        
        if (self.get_step(self.branch_b_one).is_finished() and 
            self.get_step(self.branch_a_two).is_finished()):
        
            aidalogger.info("All the steps have been done")
            self.next(self.exit)
            
    