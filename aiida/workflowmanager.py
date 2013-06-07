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
    import ntpath
    
    logger.info("Querying the worflow DB")
    
    w_list = DbWorkflow.objects.filter(user=get_automatic_user(),status=wf_states.RUNNING)
    
    for w in w_list:
        
        logger.info("[{0}] Found active workflow: {1}.{2} ".format(w.uuid,w.module,w.module_class))
        
        steps = w.steps.filter(status=wf_states.RUNNING)
        
        if len(steps) == 0:
            
            # Finish the worflow in case there are no running steps
            w.set_status(wf_states.FINISHED)
            
        else :
        
            for s in steps:
                
                if (not s.get_calculations() or s.get_calculations_status()==wf_states.FINISHED):
                    
                    logger.info("[{0}] Step: {1} ready to step".format(w.uuid,s.name))
                    s.set_status(wf_states.FINISHED)
                    advance_workflow(w, s)
                    
                else:
                    logger.info("[{0}] Step: {1} still running".format(w.uuid,s.name))


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
    
