# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# Regroup Django's specific function needed by the command line.

import datetime
import json

from django.db.models import Q

from aiida.common.datastructures import wf_states
from aiida.utils import timezone
from aiida.utils.logger import get_dblogger_extra



def get_group_list(user, type_string, n_days_ago=None,
                   name_filters={}):
    from aiida.orm.implementation.django.group import Group

    name_filters = {"name__" + k: v for (k, v) in name_filters.iteritems() if v}

    if n_days_ago:
        n_days_ago = timezone.now() - datetime.timedelta(days=n_days_ago)

    groups = Group.query(user=user, type_string=type_string,
                         past_days=n_days_ago,
                         **name_filters)

    return tuple([
                     (str(g.pk), g.name, len(g.nodes), g.user.email.strip(),
                      g.description)
                     for g in groups
                     ])


def get_workflow_list(pk_list=tuple(), user=None, all_states=False,
                      n_days_ago=None):
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
        filters = Q(user=user._dbuser)

        if not all_states:
            filters &= ~Q(state=wf_states.FINISHED) & ~Q(state=wf_states.ERROR)
        if n_days_ago:
            t = timezone.now() - datetime.timedelta(days=n_days_ago)
            filters &= Q(ctime__gte=t)

    wf_list = DbWorkflow.objects.filter(filters).order_by('ctime')

    return list(wf_list)


def get_log_messages(obj):
    """
    Get the log messages for the object.
    """
    from aiida.backends.djsite.db.models import DbLog
    extra = get_dblogger_extra(obj)
    # convert to list, too
    log_messages = list(DbLog.objects.filter(**extra).order_by('time').values(
        'loggername', 'levelname', 'message', 'metadata', 'time'))

    # deserialize metadata
    for log in log_messages:
        log.update({'metadata': json.loads(log['metadata'])})

    return log_messages


def get_computers_work_dir(calculations, user):
    """
    Get a list of computers and their remotes working directory.

   `calculations` should be a list of JobCalculation object.
    """

    from aiida.orm.computer import Computer
    from aiida.backends.utils import get_authinfo

    computers = [Computer.get(c.dbcomputer) for c in calculations]

    remotes = {}
    for computer in computers:
        remotes[computer.name] = {
            'transport': get_authinfo(computer=computer,
                                      aiidauser=user).get_transport(),
            'computer': computer,
        }

    return remotes
