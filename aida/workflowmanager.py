from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.auth.models import User

from aida.common.datastructures import calc_states
from aida.scheduler.datastructures import job_states
from aida.common import aidalogger
from aida.common.datastructures import wf_states, wf_exit_call

logger = aidalogger.getChild('workflowmanager')

def daemon_main_loop():
    
    execute_steps()
    
def execute_steps():
    
    from aida.djsite.utils import get_automatic_user
    from aida.djsite.db.models import DbWorkflow
    import ntpath
    
    logger.info("Querying the worflow DB")
    
    w_list = DbWorkflow.objects.filter(user=get_automatic_user(),status=wf_states.RUNNING)
    
    for w in w_list:
        
        logger.info("[{0}] Found active workflow: {1}.{2} ".format(w.uuid,w.module,w.module_class))
        
        steps = w.steps.filter(status=wf_states.RUNNING)
        
        for s in steps:
            
            if (s.get_calculations_status()==wf_states.FINISHED or not s.get_calculations()):
                
                logger.info("[{0}] Step: {1} ready to step".format(w.uuid,s.name))
                s.set_status(wf_states.FINISHED)
                advance_workflow(w, s)
                
            else:
                logger.info("[{0}] Step: {1} still running".format(w.uuid,s.name))


def advance_workflow(w, step):
    
    import aida.orm.workflow as wf
    
    if (step.nextcall==wf_exit_call):
        
        logger.info("[{0}] Closing the workflow".format(w.uuid))
        w.set_status(wf_states.FINISHED)
        
    else:
        
        logger.info("[{0}] Running call: {1} after {2}".format(w.uuid,step.nextcall,step.name))
        w_obj = wf.retrieve_by_uuid(w.uuid)
        getattr(w_obj,step.nextcall)()
    
