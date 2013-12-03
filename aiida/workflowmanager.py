from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.auth.models import User

from aiida.common.datastructures import calc_states
from aiida.scheduler.datastructures import job_states
from aiida.common import aiidalogger
from aiida.common.datastructures import wf_states, wf_exit_call, wf_default_call

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
        
        # Launch INITIALIZED Workflows
        #
        running_steps    = w.get_steps(state=wf_states.RUNNING)
        for s in running_steps:
            
            logger.info("[{0}] Found active step: {1}".format(w.uuid(),s.name))
            
            s_calcs       = s.get_calculations()
            s_calc_states = s.get_calculations_status()
            
            s_sub_wf        = s.get_sub_workflows()
            s_sub_wf_states = s.get_sub_workflows_status()
            
            if (not s_calcs or (len(s_calc_states) == 1 and calc_states.FINISHED in s_calc_states)) and \
               (not s_sub_wf or (len(s_sub_wf_states) == 1 and wf_states.FINISHED in s_sub_wf_states)):
                
                logger.info("[{0}] Step: {1} ready to move".format(w.uuid(),s.name))
                
                s.set_status(wf_states.FINISHED)
                advance_workflow(w, s)

                    
        # Launch INITIALIZED Workflows with all calculations and subworkflows
        #
        initialized_steps    = w.get_steps(state=wf_states.INITIALIZED)
        for s in initialized_steps:
            
            logger.info("[{0}] Found initialized step: {1}".format(w.uuid(),s.name))
            
            got_any_error = False
            for s_calc in s.get_calculations(calc_states.NEW):
                    
                obj_calc = Calculation.get_subclass_from_uuid(uuid=s_calc.uuid)
                try:
                    logger.info("[{0}] Step: {1} launching calculation {2}".format(w.uuid(),s.name, s_calc.uuid))
                    obj_calc.submit()
                except:
                    logger.error("[{0}] Step: {1} cannot launch calculation {2}".format(w.uuid(),s.name, s_calc.uuid))
                    got_any_error = True
            
            if not got_any_error:
                s.set_status(wf_states.RUNNING)
            else:
                s.set_status(wf_states.ERROR)        
        
        
#         if len(w.get_steps(state=wf_states.RUNNING))==0 and \
#            len(w.get_steps(state=wf_states.INITIALIZED))==0 and \
#            len(w.get_steps(state=wf_states.ERROR))==0 and \
#            w.get_status()==wf_states.RUNNING:
#               w.set_status(wf_states.FINISHED)
              
        
def advance_workflow(w_superclass, step):
    
    from aiida.orm.workflow import Workflow
    import sys, os
    
    if step.nextcall==wf_exit_call:
        logger.info("[{0}] Step: {1} has an exit call".format(w_superclass.uuid(),step.name))
        if len(w_superclass.get_steps(wf_states.RUNNING))==0 and len(w_superclass.get_steps(wf_states.ERROR))==0:
            logger.info("[{0}] Step: {1} is really finished, going out".format(w_superclass.uuid(),step.name))
            w_superclass.set_status(wf_states.FINISHED)
            return True
        else:
            logger.error("[{0}] Step: {1} is NOT finished, stopping workflow with error".format(w_superclass.uuid(),step.name))
            w_superclass.append_to_report("""Step: {1} is NOT finished, some calculations or workflows 
            are still running and there is a next call, stopping workflow with error""".format(step.name))
            w_superclass.set_status(wf_states.ERROR)
            
            return False
    elif step.nextcall==wf_default_call:
            logger.info("Step: {0} is not finished and has no next call, waiting for other methods to kick.".format(step.name))
            w_superclass.append_to_report("Step: {0} is not finished and has no next call, waiting for other methods to kick.".format(step.name))
            return True
        
    elif not step.nextcall==None:
        
        logger.info("In  advance_workflow the step {0} goes to nextcall {1}".format(step.name, step.nextcall))
        
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
        
        logger.error("Step: {0} ERROR, no nextcall".format(step.name))
        w.append_to_report("Step: {0} ERROR, no nextcall".format(step.name))
        w.set_status(wf_states.ERROR)

        return False


