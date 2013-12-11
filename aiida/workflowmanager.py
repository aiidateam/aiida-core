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
        
        logger.info("Found active workflow: {0}".format(w.uuid))
        
        # Launch INITIALIZED Workflows
        #
        running_steps    = w.get_steps(state=wf_states.RUNNING)
        for s in running_steps:
            
            logger.info("[{0}] Found active step: {1}".format(w.uuid,s.name))
            
            s_calcs_new       = [c.uuid for c in s.get_calculations() if c.is_new()]
            s_calcs_running   = [c.uuid for c in s.get_calculations() if c.is_running()]
            s_calcs_finished  = [c.uuid for c in s.get_calculations() if c.has_finished_ok()]
            s_calcs_failed    = [c.uuid for c in s.get_calculations() if c.has_failed()]
            s_calcs_num       = len(s.get_calculations())
            
            s_sub_wf_running  = [sw.uuid for sw in s.get_sub_workflows() if sw.is_running()]
            s_sub_wf_finished = [sw.uuid for sw in s.get_sub_workflows() if sw.has_finished_ok()]
            s_sub_wf_failed   = [sw.uuid for sw in s.get_sub_workflows() if sw.has_failed()]
            s_sub_wf_num      = len(s.get_sub_workflows())
            
            if s_calcs_num==len(s_calcs_finished) and s_sub_wf_num==len(s_sub_wf_finished):
                
                logger.info("[{0}] Step: {1} ready to move".format(w.uuid,s.name))
                
                s.set_status(wf_states.FINISHED)
                advance_workflow(w, s)
            
            elif len(s_calcs_new)>0:
                    
                for uuid in s_calcs_new:
                    
                    obj_calc = Calculation.get_subclass_from_uuid(uuid=uuid)
                    try:
                        obj_calc.submit()
                        logger.info("[{0}] Step: {1} launched calculation {2}".format(w.uuid,s.name, uuid))
                    except:
                        logger.error("[{0}] Step: {1} cannot launch calculation {2}".format(w.uuid,s.name, uuid))
            
            elif len(s_calcs_failed)>0:
                
                s.set_status(wf_states.ERROR)
        
        
        initialized_steps    = w.get_steps(state=wf_states.INITIALIZED)
        for s in initialized_steps:
            
            import sys
            
            try:
                w_class = Workflow.get_subclass_from_uuid(w.uuid)
                getattr(w, s.name)()
                return True
            
            except:
                
                exc_type, exc_value, exc_traceback = sys.exc_info()
                w.append_to_report("ERROR ! This workflow got and error in the {0} method, we report down the stack trace".format(s.name))
                w.append_to_report("full traceback: {0}".format(exc_traceback.format_exc()))
                
                s.set_status(wf_states.ERROR)
                w.set_status(wf_states.ERROR)
                
#         # Launch INITIALIZED Workflows with all calculations and subworkflows
#         #
#         initialized_steps    = w.get_steps(state=wf_states.INITIALIZED)
#         for s in initialized_steps:
#             
#             logger.info("[{0}] Found initialized step: {1}".format(w.uuid(),s.name))
#             
#             got_any_error = False
#             for s_calc in s.get_calculations(calc_states.NEW):
#                     
#                 obj_calc = Calculation.get_subclass_from_uuid(uuid=s_calc.uuid)
#                 try:
#                     logger.info("[{0}] Step: {1} launching calculation {2}".format(w.uuid(),s.name, s_calc.uuid))
#                     obj_calc.submit()
#                 except:
#                     logger.error("[{0}] Step: {1} cannot launch calculation {2}".format(w.uuid(),s.name, s_calc.uuid))
#                     got_any_error = True
#             
#             if not got_any_error:
#                 s.set_status(wf_states.RUNNING)
#             else:
#                 s.set_status(wf_states.ERROR)        
        
        
#         if len(w.get_steps(state=wf_states.RUNNING))==0 and \
#            len(w.get_steps(state=wf_states.INITIALIZED))==0 and \
#            len(w.get_steps(state=wf_states.ERROR))==0 and \
#            w.get_status()==wf_states.RUNNING:
#               w.set_status(wf_states.FINISHED)
              
        
def advance_workflow(w_superclass, step):
    
    from aiida.orm.workflow import Workflow
    import sys, os
    
    if step.nextcall==wf_exit_call:
        logger.info("[{0}] Step: {1} has an exit call".format(w_superclass.uuid,step.name))
        if len(w_superclass.get_steps(wf_states.RUNNING))==0 and len(w_superclass.get_steps(wf_states.ERROR))==0:
            logger.info("[{0}] Step: {1} is really finished, going out".format(w_superclass.uuid,step.name))
            w_superclass.set_status(wf_states.FINISHED)
            return True
        else:
            logger.error("[{0}] Step: {1} is NOT finished, stopping workflow with error".format(w_superclass.uuid,step.name))
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
            w = Workflow.get_subclass_from_uuid(w_superclass.uuid)
            getattr(w,step.nextcall)()
            return True
        
        except:
            
            exc_type, exc_value, exc_traceback = sys.exc_info()
            w.append_to_report("ERROR ! This workflow got and error in the {0} method, we report down the stack trace".format(step.nextcall))
            w.append_to_report("full traceback: {0}".format(exc_traceback.format_exc()))
            
            w.get_step(step.nextcall).set_status(wf_states.ERROR)
            w.set_status(wf_states.ERROR)
            
            return False
    else:
        
        logger.error("Step: {0} ERROR, no nextcall".format(step.name))
        w.append_to_report("Step: {0} ERROR, no nextcall".format(step.name))
        w.set_status(wf_states.ERROR)

        return False


