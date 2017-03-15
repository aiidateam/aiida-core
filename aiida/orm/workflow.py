# -*- coding: utf-8 -*-
from aiida.common.exceptions import NotExistent
from aiida.orm.implementation import Workflow, get_workflow_info
from aiida.orm.implementation.general.workflow import WorkflowKillError, WorkflowUnkillable



def kill_from_pk(pk, verbose=False):
    """
    Kills a workflow without loading the class, useful when there was a problem
    and the workflow definition module was changed/deleted (and the workflow
    cannot be reloaded).

    :param pk: the principal key (id) of the workflow to kill
    :param verbose: True to print the pk of each subworkflow killed
    """
    try:
        Workflow.get_subclass_from_pk(pk).kill(verbose=verbose)
    except IndexError:
        raise NotExistent("No workflow with pk= {} found.".format(pk))

