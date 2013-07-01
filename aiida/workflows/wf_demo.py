
import aiida.common
from aiida.common import aiidalogger
from aiida.orm.workflow import Workflow
from aiida.orm import Calculation, Code, Computer

logger = aiidalogger.getChild('WorkflowDemo')

class WorkflowDemo(Workflow):
    
    def __init__(self,**kwargs):
        
        super(WorkflowDemo, self).__init__(**kwargs)
    
    
    def start(self):
        
        from aiida.orm import Code, Computer, CalculationFactory
        CustomCalc = CalculationFactory('simpleplugins.templatereplacer')
        
        computer = Computer.get("localhost")
        
        calc = CustomCalc(computer=computer,withmpi=True)
        calc.set_resources(num_machines=1, num_cpus_per_machine=1)
        calc.store()
        
        calc2 = CustomCalc(computer=computer,withmpi=True)
        calc2.set_resources(num_machines=1, num_cpus_per_machine=1)
        calc2.store()
        
        #self.add_calculation(calc)
        #self.add_calculation(calc2)
        
        self.next(self.second_step)
        
        # Run calculations
    
    def second_step(self):
        
        calcs_init = self.get_calculations(self.start)
        
        aiidalogger.info("Second runned and retived calculation:")
        for c in calcs_init:
            aiidalogger.info("  Calculation {0}".format(c.uuid))
        
        from aiida.orm import CalculationFactory
        CustomCalc = CalculationFactory('simpleplugins.templatereplacer')
        
        computer = Computer.get("localhost")
        
        calc = CustomCalc(computer=computer,withmpi=True)
        calc.set_resources(num_machines=1, num_cpus_per_machine=1)
        calc.store()
        
        #self.add_calculation(calc)
        
        self.next(self.third_step)
    
        
    def third_step(self):
        
        calcs_init = self.get_calculations(self.second_step)
        
        aiidalogger.info("Third runned and retived calculation:")
        for c in calcs_init:
            aiidalogger.info("  Calculation {0}".format(c.uuid))
            
        
        self.next(self.exit)


class WorkflowDemoBranch(Workflow):
    
    def start(self):
    
        self.branch_a_one()
        self.branch_b_one()
        
    def branch_a_one(self):
        
        aiidalogger.info("branch_a_one launched")
        
        from aiida.orm import CalculationFactory
        CustomCalc = CalculationFactory('simpleplugins.templatereplacer')
        
        computer = Computer.get("localhost")
        
        calc = CustomCalc(computer=computer,withmpi=True)
        calc.set_resources(num_machines=1, num_cpus_per_machine=1)
        calc.store()
        
        #self.add_calculation(calc)
        
        self.next(self.branch_a_two)
    
    def branch_a_two(self):
        
        aiidalogger.info("branch_a_two launched")
        
        from aiida.orm import CalculationFactory
        CustomCalc = CalculationFactory('simpleplugins.templatereplacer')
        
        computer = Computer.get("localhost")
        
        calc = CustomCalc(computer=computer,withmpi=True)
        calc.set_resources(num_machines=1, num_cpus_per_machine=1)
        calc.store()
        
        #self.add_calculation(calc)
        
        self.next(self.recollect)
        
    def branch_b_one(self):
        
        aiidalogger.info("branch_b_one launched")
        
        from aiida.orm import CalculationFactory
        CustomCalc = CalculationFactory('simpleplugins.templatereplacer')
        
        computer = Computer.get("localhost")
        
        calc = CustomCalc(computer=computer,withmpi=True)
        calc.set_resources(num_machines=1, num_cpus_per_machine=1)
        calc.store()
        
        #self.add_calculation(calc)
        
        self.next(self.recollect)
    
    def recollect(self):
        
        aiidalogger.info("recollect launched")
        
        if (self.get_step(self.branch_b_one).is_finished() and 
            self.get_step(self.branch_a_two).is_finished()):
        
            aiidalogger.info("All the steps have been done")
            self.next(self.exit)
            

class WorkflowDemoLoop(Workflow):

    def start(self):
        
        from aiida.orm import Calculation, Code, Computer
        
        from aiida.orm import CalculationFactory
        CustomCalc = CalculationFactory('simpleplugins.templatereplacer')
        
        computer = Computer.get("localhost")
        
        calc = CustomCalc(computer=computer,withmpi=True)
        calc.set_resources(num_machines=1, num_cpus_per_machine=1)
        calc.store()
        
        #self.add_calculation(calc)
        
        self.next(self.convergence)        
    
    def convergence(self):
        
        calcs_init = self.get_calculations(self.start)
        
        calcs_convergence = self.get_calculations(self.convergence)
        
        if calcs_convergence == None or len(calcs_convergence) < 5:
            from aiida.orm import CalculationFactory
            CustomCalc = CalculationFactory('simpleplugins.templatereplacer')
            
            computer = Computer.get("localhost")
            
            calc = CustomCalc(computer=computer,withmpi=True)
            calc.set_resources(num_machines=1, num_cpus_per_machine=1)
            calc.store()
            
            #self.add_calculation(calc)
            self.next(self.convergence)
        
        else:
            
            aiidalogger.info("Enough calculations runned, going to the next step")
            self.next(self.third_step)
    
        
    def third_step(self):
        
        calcs_init = self.get_calculations(self.convergence)
        
        aiidalogger.info("Third runned and retived calculation:")
        for c in calcs_init:
            aiidalogger.info("  Calculation {0}".format(c.uuid))
            
        
        self.next(self.exit)
