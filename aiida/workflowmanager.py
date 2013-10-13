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
        
        logger.info("Found active workflow: {0}".format(w.uuid()))
        
        running_steps    = w.get_steps(state=wf_states.RUNNING)
        for s in running_steps:
            
            logger.info("[{0}] Found active step: ".format(w.uuid(),s.name))
            
            s_calcs       = s.get_calculations()
            s_calc_states = s.get_calculations_status()
            
            s_sub_wf        = s.get_sub_workflows()
            s_sub_wf_states = s.get_sub_workflows_status()
            
            if (not s_calcs or (len(s_calc_states) == 1 and calc_states.FINISHED in s_calc_states)) and \
               (not s_sub_wf or (len(s_sub_wf_states) == 1 and wf_states.FINISHED in s_sub_wf_states)):
                
                logger.info("[{0}] Step: {1} ready to step".format(w.uuid(),s.name))
                
                s.set_status(wf_states.FINISHED)
                advance_workflow(w, s)
                    
        
        initialized_steps    = w.get_steps(state=wf_states.INITIALIZED)
        for s in initialized_steps:
            
            logger.info("[{0}] Found initialized step: ".format(w.uuid(),s.name))
            
            for s_calc in s.get_calculations(calc_states.NEW):
                    
                obj_calc = Calculation.get_subclass_from_uuid(uuid=s_calc.uuid)
                try:
                    logger.info("[{0}] Step: {1} launching calculation {2}".format(w.uuid(),s.name, s_calc.uuid))
                    obj_calc.submit()
                except:
                    logger.error("[{0}] Step: {1} cannot launch calculation {2}".format(w.uuid(),s.name, s_calc.uuid))

            s.set_status(wf_states.RUNNING)
            
def advance_workflow(w_superclass, step):
    
    from aiida.orm.workflow import Workflow
    import sys, os
    
    if (step.nextcall==wf_exit_call):
        logger.error("This is an exit call")
        if len(w_superclass.get_steps(wf_states.RUNNING))==0 and len(w_superclass.get_steps(wf_states.ERROR))==0:
            logger.error("Ok, ready to go")
            w_superclass.set_status(wf_states.FINISHED)
            return True
        else:
            logger.error("Error, we're going to bump it")
            w_superclass.set_status(wf_states.ERROR)
            return False
            
    elif (not step.nextcall==None):
        
        try:
            w = Workflow.get_subclass_from_uuid(w_superclass.uuid())
            getattr(w,step.nextcall)()
            return True
        
        except:
            
            exc_type, exc_value, exc_traceback = sys.exc_info()
            w.append_to_report("ERROR ! This workflow got and error in the {0} method, we report down the stack trace".format(step.nextcall))
            w.append_to_report("filename: {0}".format(exc_traceback.tb_frame.f_code.co_filename))
            w.append_to_report("lineno: {0}".format(exc_traceback.tb_lineno))
            w.append_to_report("name: {0}".format(exc_traceback.tb_frame.f_code.co_name))
            w.append_to_report("type: {0}".format(exc_type.__name__))
            w.append_to_report("message: {0}".format(exc_value.message))
            
            w.set_status(wf_states.ERROR)
            
            return False
    else:
        
        w.append_to_report("ERROR ! Method {0} has no nextcall".format(step.name))
        w.set_status(wf_states.ERROR)

        return False


