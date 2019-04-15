# -*- coding: utf-8 -*-

from aiida.utils.logger import get_dblogger_extra

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"


def get_group_list(user, type_string, n_days_ago=None,
                   name_filters={}):
    pass


def get_workflow_list(pk_list=tuple(), user=None, all_states=False, 
                      n_days_ago=None):
    """
    Get a list of workflow.
    """
    pass
    from aiida.orm.workflow import Workflow
    from aiida.backends.sqlalchemy.models.workflow import DbWorkflow
    from aiida.common.datastructures import wf_states
                                             
    if pk_list:
        q = DbWorkflow.query.filter(DbWorkflow.id.in_(pk_list))
    else:
        q = DbWorkflow.query.filter() # (user=user)

        if not all_states:
            q = q.filter(DbWorkflow.state.in_([wf_states.CREATED, 
                                               wf_states.RUNNING, 
                                               wf_states.SLEEP, 
                                               wf_states.INITIALIZED]))
        if n_days_ago:
            t = timezone.now() - datetime.timedelta(days=n_days_ago)
            q = q.filter(DbWorkflow.ctime>=t)

    wf_list = list(q.distinct().order_by('ctime'))
    return wf_list
    
def get_log_messages(obj):
    """
    Get the log messages for the object.
    """
    from aiida.backends.sqlalchemy.models.log import DbLog
    from aiida.backends.sqlalchemy import session

    extra = get_dblogger_extra(obj)
    log_messages = []
    for log_message in (
            session.query(DbLog).filter_by(**extra).order_by('time').all()):
        val_dict = log_message.__dict__
        updated_val_dict = {
            "loggername": val_dict["loggername"],
            "levelname": val_dict["levelname"],
            "message": val_dict["message"],
            "metadata": val_dict["_metadata"],
            "time": val_dict["time"]}
        log_messages.append(updated_val_dict)

    return log_messages


def get_computers_work_dir(calculations, user):
    """
    Get a list of computers and their remotes working directory.

   `calculations` should be a list of JobCalculation object.
    """
    pass
