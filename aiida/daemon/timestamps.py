# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from pytz import UTC

from aiida.backends import settings
from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA


if settings.BACKEND == BACKEND_DJANGO:
    from aiida.backends.djsite.globalsettings import set_global_setting, get_global_setting
elif settings.BACKEND == BACKEND_SQLA:
    from aiida.backends.sqlalchemy.globalsettings import set_global_setting, get_global_setting
else:
    raise Exception("Unkown backend {}".format(settings.BACKEND))


celery_tasks = {
        'submitter': 'submitter',
        'updater': 'updater',
        'retriever': 'retriever',
        'workflow': 'workflow_stepper',
}


def get_most_recent_daemon_timestamp():
    """
    Try to detect any last timestamp left by the daemon, for instance
    to get a hint on whether the daemon is running or not.

    :return:  a datetime.datetime object with the most recent time.
      Return None if no information is found in the DB.
    """
    import datetime
    # I go low-level here
    if settings.BACKEND == BACKEND_DJANGO:
        from aiida.backends.djsite.db.models import DbSetting
        daemon_timestamps = DbSetting.objects.filter(key__startswith='daemon|task_')
        timestamps = []
        for timestamp_setting in daemon_timestamps:
            timestamp = timestamp_setting.getvalue()
            if isinstance(timestamp, datetime.datetime):
                timestamps.append(timestamp)

        if timestamps:
            # The most recent timestamp

            return max(timestamps)
        else:
            return None

    elif settings.BACKEND == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.models.settings import DbSetting
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()

        from sqlalchemy import func
        from pytz import utc
        from sqlalchemy.dialects.postgresql import TIMESTAMP

        maxtimestamp, = session.query(
            func.max(DbSetting.val[()].cast(TIMESTAMP))).filter(
            DbSetting.key.like("daemon|task%")).first()

        if maxtimestamp is None:
            return None
        else:
            return utc.localize(maxtimestamp)


def set_daemon_timestamp(task_name, when):
    """
    Set in the DB the current time associated with the given task;
    this is used to store a timestamp to know when the daemon run for the last
    time.

    :param task_name: the task for which we want to set the timestamp
      It has to be one of the keys of the
      ``aiida.backends.djsite.settings.settings.djcelery_tasks`` dictionary.
    :param when: can either be 'start' (to call when the task started) or
      'stop' (to call when the task ended)
    """
    from aiida.utils import timezone

    if when == 'start':
        verb = 'started'
    elif when == 'stop':
        verb = 'finished'
    else:
        raise ValueError("the 'when' parameter can only be 'start' or 'stop'")

    try:
        actual_task_name = celery_tasks[task_name]
    except KeyError:
        raise ValueError("Unknown value for 'task_name', not found in the "
                         "celery_tasks dictionary")

    set_global_setting(
            'daemon|task_{}|{}'.format(when, actual_task_name),
            timezone.datetime.now(tz=UTC),
            description=(
                    "The last time the daemon {} to run the "
                    "task '{}' ({})"
                    "".format(
                            verb,
                            task_name,
                            actual_task_name
                    )
            )
    )


def get_last_daemon_timestamp(task_name, when='stop'):
    """
    Return the last time stored in the DB that the daemon executed the given
    task.

    :param task_name: the task for which we want the information.
      It has to be one of the keys of the
      ``celery_tasks`` dictionary.
    :param when: can either be 'start' (to know when the task started) or
      'stop' (to know when the task ended)

    :return: a datetime.datetime object. Return None if no information is
      found in the DB.
    """
    try:
        actual_task_name = celery_tasks[task_name]
    except KeyError:
        raise ValueError("Unknown value for '{}', not found in the "
                         "celery_tasks dictionary".format(task_name))

    try:
        return get_global_setting('daemon|task_{}|{}'.format(when,
                                                             actual_task_name))
    except KeyError:  # No such global setting found
        return None

