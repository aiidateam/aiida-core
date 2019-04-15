# -*- coding: utf-8 -*-

from aiida.common import aiidalogger
from aiida.common.datastructures import wf_states, wf_exit_call, wf_default_call

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0.1"
__authors__ = "The AiiDA team."

logger = aiidalogger.getChild('workflowmanager')


def daemon_main_loop():
    """
    Support method to keep coherence with the Execution Manager, only launches ``execute_steps``
    """

    execute_steps()


def execute_steps():
    """
    This method loops on the RUNNING workflows and handled the execution of the steps until
    each workflow reaches an end (or gets stopped for errors).

    In the loop for each RUNNING workflow the method loops also in each of its RUNNING steps,
    testing if all the calculation and subworkflows attached to the step are FINISHED. In this
    case the step is set as FINISHED and the workflow is advanced to the step's next method present
    in the db with ``advance_workflow``, otherwise if any step's JobCalculation is found in NEW state
    the method will submit. If none of the previous conditions apply the step is flagged as
    ERROR and cannot proceed anymore, blocking the future execution of the step and, connected,
    the workflow.

    Finally, for each workflow the method tests if there are INITIALIZED steps to be launched,
    and in case reloads the workflow and execute the specific those steps. In case or error
    the step is flagged in ERROR state and the stack is reported in the workflow report.
    """

    from aiida.backends.utils import get_automatic_user
    from aiida.orm.workflow import Workflow
    from aiida.common.datastructures import wf_states
    from aiida.orm import JobCalculation

    logger.info("Querying the worflow DB")

    w_list = Workflow.query(user=get_automatic_user(), state=wf_states.RUNNING)

    for w in w_list:

        logger.info("Found active workflow: {0}".format(w.uuid))

        # Launch INITIALIZED Workflows
        #
        running_steps = w.get_steps(state=wf_states.RUNNING)
        for s in running_steps:

            logger.info("[{0}] Found active step: {1}".format(w.uuid, s.name))

            s_calcs_new = [c.uuid for c in s.get_calculations() if c._is_new()]
            s_calcs_running = [c.uuid for c in s.get_calculations() if c._is_running()]
            s_calcs_finished = [c.uuid for c in s.get_calculations() if c.has_finished_ok()]
            s_calcs_failed = [c.uuid for c in s.get_calculations() if c.has_failed()]
            s_calcs_num = len(s.get_calculations())

            s_sub_wf_running = [sw.uuid for sw in s.get_sub_workflows() if sw.is_running()]
            s_sub_wf_finished = [sw.uuid for sw in s.get_sub_workflows() if sw.has_finished_ok()]
            s_sub_wf_failed = [sw.uuid for sw in s.get_sub_workflows() if sw.has_failed()]
            s_sub_wf_num = len(s.get_sub_workflows())

            if s_calcs_num == (len(s_calcs_finished) + len(s_calcs_failed)) and s_sub_wf_num == (
                len(s_sub_wf_finished) + len(s_sub_wf_failed)):

                logger.info("[{0}] Step: {1} ready to move".format(w.uuid, s.name))

                s.set_state(wf_states.FINISHED)
                advance_workflow(w, s)

            elif len(s_calcs_new) > 0:

                for uuid in s_calcs_new:

                    obj_calc = JobCalculation.get_subclass_from_uuid(uuid=uuid)
                    try:
                        obj_calc.submit()
                        logger.info("[{0}] Step: {1} launched calculation {2}".format(w.uuid, s.name, uuid))
                    except:
                        logger.error("[{0}] Step: {1} cannot launch calculation {2}".format(w.uuid, s.name, uuid))

                        ## DO NOT STOP ANYMORE IF A CALCULATION FAILS
                        # elif s_calcs_failed:
                        #s.set_state(wf_states.ERROR)

        initialized_steps = w.get_steps(state=wf_states.INITIALIZED)
        for s in initialized_steps:

            import sys

            try:
                w_class = Workflow.get_subclass_from_uuid(w.uuid)
                getattr(w, s.name)()
                return True

            except:

                exc_type, exc_value, exc_traceback = sys.exc_info()
                w.append_to_report(
                    "ERROR ! This workflow got an error in the {0} method, we report down the stack trace".format(
                        s.name))
                w.append_to_report("full traceback: {0}".format(exc_traceback.format_exc()))

                s.set_state(wf_states.ERROR)
                w.set_state(wf_states.ERROR)

    for w in w_list:
        if w.get_steps(state=wf_states.ERROR):
            w.set_state(wf_states.ERROR)


# # Launch INITIALIZED Workflows with all calculations and subworkflows
#         #
#         initialized_steps    = w.get_steps(state=wf_states.INITIALIZED)
#         for s in initialized_steps:
#
#             logger.info("[{0}] Found initialized step: {1}".format(w.uuid(),s.name))
#
#             got_any_error = False
#             for s_calc in s.get_calculations(calc_states.NEW):
#
#                 obj_calc = JobCalculation.get_subclass_from_uuid(uuid=s_calc.uuid)
#                 try:
#                     logger.info("[{0}] Step: {1} launching calculation {2}".format(w.uuid(),s.name, s_calc.uuid))
#                     obj_calc.submit()
#                 except:
#                     logger.error("[{0}] Step: {1} cannot launch calculation {2}".format(w.uuid(),s.name, s_calc.uuid))
#                     got_any_error = True
#
#             if not got_any_error:
#                 s.set_state(wf_states.RUNNING)
#             else:
#                 s.set_state(wf_states.ERROR)


#         if len(w.get_steps(state=wf_states.RUNNING))==0 and \
#            len(w.get_steps(state=wf_states.INITIALIZED))==0 and \
#            len(w.get_steps(state=wf_states.ERROR))==0 and \
#            w.get_state()==wf_states.RUNNING:
#               w.set_state(wf_states.FINISHED)


def advance_workflow(w_superclass, step):
    """
    The method tries to advance a step running its next method and handling possible errors.

    If the method to advance is the Workflow ``exit`` method and there are no more steps RUNNING or
    in ERROR state then the workflow is set to FINISHED, otherwise an error is added to the report
    and the Workflow is flagged as ERORR.

    If the method is the ``wf_default_call`` this means the step had no next, and possibly is part of
    a branching. In this case the Workflow is not advanced but the method returns True to let the other
    steps kick in.

    Finally the methos tries to load the Workflow and execute the selected step, reporting the errors
    and the stack trace in the report in case of problems. Is no errors are reported the method returns
    True, in all the other cases the Workflow is set to ERROR state and the method returns False.

    :param w_superclass: Workflow object to advance
    :param step: DbWorkflowStep to execute
    :return: True if the step has been executed, False otherwise
    """

    from aiida.orm.workflow import Workflow

    if step.nextcall == wf_exit_call:
        logger.info("[{0}] Step: {1} has an exit call".format(w_superclass.uuid, step.name))
        if len(w_superclass.get_steps(wf_states.RUNNING)) == 0 and len(w_superclass.get_steps(wf_states.ERROR)) == 0:
            logger.info("[{0}] Step: {1} is really finished, going out".format(w_superclass.uuid, step.name))
            w_superclass.set_state(wf_states.FINISHED)
            return True
        else:
            logger.error(
                "[{0}] Step: {1} is NOT finished, stopping workflow with error".format(w_superclass.uuid, step.name))
            w_superclass.append_to_report("""Step: {1} is NOT finished, some calculations or workflows
            are still running and there is a next call, stopping workflow with error""".format(step.name))
            w_superclass.set_state(wf_states.ERROR)

            return False
    elif step.nextcall == wf_default_call:
        logger.info(
            "Step: {0} is not finished and has no next call, waiting for other methods to kick.".format(step.name))
        w_superclass.append_to_report(
            "Step: {0} is not finished and has no next call, waiting for other methods to kick.".format(step.name))
        return True

    elif not step.nextcall == None:

        logger.info("In advance_workflow the step {0} goes to nextcall {1}".format(step.name, step.nextcall))

        try:
            w = Workflow.get_subclass_from_uuid(w_superclass.uuid)
            getattr(w, step.nextcall)()
            return True

        except Exception:
            import traceback

            w.append_to_report(
                "ERROR ! This workflow got an error in the {0} method, we report down the stack trace".format(
                    step.nextcall))
            w.append_to_report("full traceback: {0}".format(traceback.format_exc()))

            w.get_step(step.nextcall).set_state(wf_states.ERROR)
            w.set_state(wf_states.ERROR)

            return False
    else:

        logger.error("Step: {0} ERROR, no nextcall".format(step.name))
        w.append_to_report("Step: {0} ERROR, no nextcall".format(step.name))
        w.set_state(wf_states.ERROR)

        return False


