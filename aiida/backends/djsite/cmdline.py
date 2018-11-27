# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Regroup Django's specific function needed by the command line."""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import datetime

from django.db.models import Q  # pylint: disable=import-error, no-name-in-module

from aiida.common.datastructures import wf_states
from aiida.utils import timezone


def get_workflow_list(pk_list=tuple(), user=None, all_states=False, n_days_ago=None):
    """
    Get a list of workflow.

    :param user: A ORM User class if you want to filter by user
    :param pk_list: Limit the results to this list of PKs
    :param all_states: if False, limit results to "active" (e.g., running) wfs
    :param n_days_ago: an integer number of days. If specifies, limit results to
      workflows started up to this number of days ago
    """
    from aiida.backends.djsite.db.models import DbWorkflow

    if pk_list:
        filters = Q(pk__in=pk_list)
    else:
        filters = Q(user__id=user.id)

        if not all_states:
            filters &= ~Q(state=wf_states.FINISHED) & ~Q(state=wf_states.ERROR)
        if n_days_ago:
            time = timezone.now() - datetime.timedelta(days=n_days_ago)
            filters &= Q(ctime__gte=time)

    wf_list = DbWorkflow.objects.filter(filters).order_by('ctime')  # pylint: disable=no-member

    return list(wf_list)
