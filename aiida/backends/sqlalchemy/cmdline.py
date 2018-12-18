# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SQLA specific command line commands"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import datetime
from aiida.common import timezone


def get_workflow_list(pk_list=tuple(), user=None, all_states=False, n_days_ago=None):
    """
    Get a list of workflow

    :param user: A ORM User class if you want to filter by user
    :param pk_list: Limit the results to this list of PKs
    :param all_states: if False, limit results to "active" (e.g., running) wfs
    :param n_days_ago: an integer number of days. If specifies, limit results to
        workflows started up to this number of days ago
    """
    from aiida.backends.sqlalchemy.models.workflow import DbWorkflow
    from aiida.common.datastructures import wf_states
    from aiida.manage import get_manager

    backend = get_manager().get_backend()

    if pk_list:
        query = DbWorkflow.query.filter(DbWorkflow.id.in_(pk_list))
    else:
        query = DbWorkflow.query.filter(DbWorkflow.user_id == user.id)

        if not all_states:
            query = query.filter(
                DbWorkflow.state.in_([wf_states.CREATED, wf_states.RUNNING, wf_states.SLEEP, wf_states.INITIALIZED]))
        if n_days_ago:
            time = timezone.now() - datetime.timedelta(days=n_days_ago)
            query = query.filter(DbWorkflow.ctime >= time)

    return [backend.get_backend_entity(wf) for wf in query.distinct().order_by('ctime')]
