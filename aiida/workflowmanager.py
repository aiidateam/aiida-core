from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.auth.models import User

from aiida.common.datastructures import calc_states
from aiida.scheduler.datastructures import job_states
from aiida.common import aiidalogger
from aiida.common.datastructures import wf_states, wf_exit_call

logger = aiidalogger.getChild('workflowmanager')

def daemon_main_loop():
    
    """
    Support method to keep coherence with the Execution Manager
    """
    
    execute_steps()
    
def execute_steps():
    
    """
    This method loops on the RUNNING workflows and checks for RUNNING steps.
    
    - If all the calculation of the step are finished the step is advanced to the next method
    - If the step does not have a next method is flagged as finished anyway
    - If the method does not have anymore RUNNING steps is flagged as finished 
    
    """
    
    from aiida.djsite.utils import get_automatic_user
    from aiida.djsite.db.models import DbWorkflow
    from aiida.orm.workflow import Workflow
    from aiida.common.datastructures import calc_states, wf_states, wf_exit_call
    from aiida.orm import Calculation
    
    logger.info("Querying the worflow DB")
    
    w_list = Workflow.query(user=get_automatic_user(),status=wf_states.RUNNING)
    
    for w in w_list:
        
        logger.info("[{0}] Found active workflow: ".format(w.uuid))
        steps = w.get_steps(state=wf_states.RUNNING)
        
        if len(steps) == 0:
            
            # Finish the worflow in case there are no running steps
            w.set_status(wf_states.FINISHED)
            
        else :
        
            for s in steps:
                
                s_calcs       = s.get_calculations()
                s_calc_states = s.get_calculations_status()
                
                s_sub_wf        = s.get_sub_workflows()
                s_sub_wf_states = s.get_sub_workflows_status()
                
                if (not s_calcs or (len(s_calc_states) == 1 and calc_states.FINISHED in s_calc_states)) and \
                   (not s_sub_wf or (len(s_sub_wf_states) == 1 and wf_states.FINISHED in s_sub_wf_states)):
                    
                    logger.info("[{0}] Step: {1} ready to step".format(w.uuid,s.name))
                    s.set_status(wf_states.FINISHED)
                    advance_workflow(w, s)
                    
                elif calc_states.NEW in calc_states:
                    
                    for s_calc in s.get_calculations(calc_states.NEW):
                        obj_calc = Calculation.get_subclass_from_uuid(uuid=s_calc.uuid)
                        obj_calc.submit()
                        logger.info("[{0}] Step: {1} launching calculation {2}".format(w.uuid,s.name, s_calc.uuid))


def advance_workflow(w, step):
    
    import aiida.orm.workflow as wf
    from aiida.common.exceptions import ValidationError
    
    if (step.nextcall==wf_exit_call):
        
        logger.info("[{0}] Closing the workflow".format(w.uuid))
        w.set_status(wf_states.FINISHED)
    
    elif (not step.nextcall==None):
        
        logger.info("[{0}] Running call: {1} after {2}".format(w.uuid,step.nextcall,step.name))
        
        try:
            w_obj = wf.retrieve_by_uuid(w.uuid)
            getattr(w_obj,step.nextcall)()
        except ValidationError:
            logger.error("[{0}] Closing the workflow due to reload ERROR ".format(w.uuid))
            w.set_status(wf_states.FINISHED)
    
