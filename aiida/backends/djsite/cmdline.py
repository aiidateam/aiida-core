# -*- coding: utf-8 -*-
# Regroup Django's specific function needed by the command line.

import datetime
import json


from django.db.models import Q

from aiida.common.datastructures import wf_states
from aiida.orm.implementation.django.group import Group
from aiida.backends.djsite.db.models import DbWorkflow, DbLog
from aiida.utils import timezone
from aiida.utils.logger import get_dblogger_extra

def get_group_list(user, type_string, n_days_ago=None,
                   name_filters={}):

    name_filters = { "name__" + k: v for (k, v) in name_filters.iteritems() if v}

    if n_days_ago:
        n_days_ago = timezone.now() - datetime.timedelta(days=n_days_ago)

    groups = Group.query(user=user, type_string=type_string, past_days=n_days_ago,
                        **name_filters)

    return tuple([
        (str(g.pk), g.name, len(g.nodes), g.user.email.strip(), g.description)
        for g in groups
    ])

def get_workflow_list(pk_list=[], user=None, all_states=False, n_days_ago=None):

    if pk_list:
        filters = Q(pk__in=pk_list)
    else:
        filters = Q(user=user)

        if not all_states:
            filters &= Q(state=wf_states.FINISHED) & Q(state=wf_states.ERROR)
        if n_days_ago:
            t = timezone.now() - datetime.timedelta(days=n_days_ago)
            filters &= Q(ctime__gte=t)

    workflows = (DbWorkflow.objects.filter(filters)
                 .order_by('ctime')
                 .select_related("parent_workflow_step__parent").all())

    return workflows


def get_log_messages(obj):
    extra = get_dblogger_extra(obj)
    # convert to list, too
    log_messages = list(DbLog.objects.filter(**extra).order_by('time').values(
        'loggername', 'levelname', 'message', 'metadata', 'time'))

    # deserialize metadata
    for log in log_messages:
        log.update({'metadata': json.loads(log['metadata'])})

    return log_messages
