# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.common import aiidalogger
from aiida.common.datastructures import wf_states, wf_exit_call, wf_default_call


logger = aiidalogger.getChild('workflowmanager')


def execute_steps():
    """
    This method loops on the RUNNING workflows and handled the execution of the
    steps until each workflow reaches an end (or gets stopped for errors).

    In the loop for each RUNNING workflow the method loops also in each of its 
    RUNNING steps, testing if all the calculation and subworkflows attached to 
    the step are FINISHED. In this case the step is set as FINISHED and the 
    workflow is advanced to the step's next method present in the db with 
    ``advance_workflow``, otherwise if any step's JobCalculation is found in 
    NEW state the method will submit. If none of the previous conditions apply 
    the step is flagged as ERROR and cannot proceed anymore, blocking the future
    execution of the step and, connected, the workflow.

    Finally, for each workflow the method tests if there are INITIALIZED steps 
    to be launched, and in case reloads the workflow and execute the specific 
    those steps. In case or error the step is flagged in ERROR state and the 
    stack is reported in the workflow report.
    """

    from aiida.orm import JobCalculation
    from aiida.orm.implementation import get_all_running_steps
 
    logger.info("Querying the worflow DB")
    
    running_steps = get_all_running_steps()

    for s in running_steps:
        if s.parent.state == wf_states.FINISHED:
            s.set_state(wf_states.FINISHED)
            continue

        w = s.parent.get_aiida_class()

        logger.info("[{0}] Found active step: {1}".format(w.pk, s.name))

        s_calcs_new = [c.pk for c in s.get_calculations() if c._is_new()]
        s_calcs_finished = [c.pk for c in s.get_calculations()
                            if c.has_finished_ok()]
        s_calcs_failed = [c.pk for c in s.get_calculations() if c.has_failed()]
        s_calcs_num = len(s.get_calculations())

        s_sub_wf_finished = [sw.pk for sw in s.get_sub_workflows()
                             if sw.has_finished_ok()]
        s_sub_wf_failed = [sw.pk for sw in s.get_sub_workflows()
                           if sw.has_failed()]
        s_sub_wf_num = len(s.get_sub_workflows())

        if (s_calcs_num == (len(s_calcs_finished) + len(s_calcs_failed)) and
            s_sub_wf_num == (len(s_sub_wf_finished) + len(s_sub_wf_failed))):

            logger.info("[{0}] Step: {1} ready to move".format(w.pk, s.name))

            s.set_state(wf_states.FINISHED)
            
            advance_workflow(w, s)

        elif len(s_calcs_new) > 0:

            for pk in s_calcs_new:

                obj_calc = JobCalculation.get_subclass_from_pk(pk=pk)
                try:
                    obj_calc.submit()
                    logger.info("[{0}] Step: {1} launched calculation {2}".format(w.pk, s.name, pk))
                except:
                    logger.error("[{0}] Step: {1} cannot launch calculation {2}".format(w.pk, s.name, pk))


def advance_workflow(w, step):
    """
    The method tries to advance a step running its next method and handling 
    possible errors.

    If the method to advance is the Workflow ``exit`` method and there are no 
    more steps RUNNING or in ERROR state then the workflow is set to FINISHED, 
    otherwise an error is added to the report and the Workflow is flagged as 
    ERROR.

    If the method is the ``wf_default_call`` this means the step had no next, 
    and possibly is part of a branching. In this case the Workflow is not 
    advanced but the method returns True to let the other steps kick in.

    Finally the methos tries to load the Workflow and execute the selected step,
    reporting the errors and the stack trace in the report in case of problems. 
    Is no errors are reported the method returns True, in all the other cases 
    the Workflow is set to ERROR state and the method returns False.

    :param w: Workflow object to advance
    :param step: DbWorkflowStep to execute
    :return: True if the step has been executed, False otherwise
    """
    if step.nextcall == wf_exit_call:
        logger.info("[{0}] Step: {1} has an exit call".format(w.pk, step.name))
        if len(w.get_steps(wf_states.RUNNING)) == 0 and len(w.get_steps(wf_states.ERROR)) == 0:
            logger.info("[{0}] Step: {1} is really finished, going out".format(w.pk, step.name))
            w.set_state(wf_states.FINISHED)
            return True
        else:
            logger.error("[{0}] Step: {1} is NOT finished, stopping workflow "
                         "with error".format(w.pk, step.name))
            w.append_to_report("""Step: {0} is NOT finished, some calculations or workflows
            are still running and there is a next call, stopping workflow with error""".format(step.name))
            w.set_state(wf_states.ERROR)

            return False
    elif step.nextcall == wf_default_call:
        logger.info("[{0}] Step: {1} is not finished and has no next call, waiting "
                    "for other methods to kick.".format(w.pk, step.name))
        w.append_to_report("Step: {0} is not finished and has no "
                                      "next call, waiting for other methods "
                                      "to kick.".format(step.name))
        return True

    elif not step.nextcall is None:

        logger.info("[{0}] In advance_workflow the step {1} goes to nextcall {2}"
                    "".format(w.pk, step.name, step.nextcall))

        try:
            #w = Workflow.get_subclass_from_pk(w_superclass.pk)
            getattr(w, step.nextcall)()
            return True

        except Exception:
            import traceback

            w.append_to_report("ERROR ! This workflow got an error in the {0} "
                               "method, we report down the stack trace".format(
                                   step.nextcall))
            w.append_to_report("full traceback: {0}".format(traceback.format_exc()))

            w.get_step(step.nextcall).set_state(wf_states.ERROR)
            w.set_state(wf_states.ERROR)

            return False
    else:

        logger.error("[{0}] Step: {1} ERROR, no nextcall".format(w.pk,
                                                                 step.name))
        w.append_to_report("Step: {0} ERROR, no nextcall".format(step.name))
        w.set_state(wf_states.ERROR)

        return False


