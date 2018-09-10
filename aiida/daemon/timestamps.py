# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
from aiida.backends.utils import set_global_setting, get_global_setting
from aiida.utils import timezone


def set_timestamp_workflow_stepper(when):
    """
    Store the current timestamp in the DbSettings for the workflow_stepper task

    :param when: can either be 'start' or 'stop', to set when the task started or stopped
    """
    task = 'workflow_stepper'

    if when == 'start':
        verb = 'started'
    elif when == 'stop':
        verb = 'finished'
    else:
        raise ValueError("the 'when' parameter can only be 'start' or 'stop'")

    set_global_setting(
        'daemon|task_{}|{}'.format(when, task), timezone.datetime.now(),
        description=(
            "The last time the daemon {} to run the task '{}'".format(verb, task)
        )
    )


def get_timestamp_workflow_stepper(when='stop'):
    """
    Return the timestamp stored in the DbSettings table for the workflow_stepper task

    :param when: can either be 'start' or 'stop', to get when the task started or stopped
    :return: a datetime.datetime object. Return None if no information is found in the DB.
    """
    task = 'workflow_stepper'

    try:
        return get_global_setting('daemon|task_{}|{}'.format(when, task))
    except KeyError:
        return None
