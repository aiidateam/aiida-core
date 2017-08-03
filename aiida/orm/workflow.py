# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
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

