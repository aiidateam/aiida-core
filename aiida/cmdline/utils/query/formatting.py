# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""A utility module with simple functions to format variables into strings for cli outputs."""


def format_relative_time(datetime):
    """
    Return a string formatted timedelta of the given datetime with respect to the current datetime

    :param datetime: the datetime to format
    :return: string representation of the relative time since the given datetime
    """
    from aiida.common import timezone
    from aiida.common.utils import str_timedelta

    timedelta = timezone.delta(datetime)

    return str_timedelta(timedelta, negative_to_zero=True, max_num_fields=1)


def format_state(process_state, paused=None, exit_status=None):
    """
    Return a string formatted representation of a process' state, which consists of its process state and exit status

    :param process_state: the process state
    :param exit_status: the process' exit status
    :return: string representation of the process' state
    """
    if process_state in ['excepted']:
        symbol = '\u2A2F'
    elif process_state in ['killed']:
        symbol = '\u2620'
    elif process_state in ['created', 'finished']:
        symbol = '\u23F9'
    elif process_state in ['running', 'waiting']:
        if paused is True:
            symbol = '\u23F8'
        else:
            symbol = '\u23F5'
    else:
        # Unknown process state, use invisible separator
        symbol = '\u00B7'  # middle dot

    if process_state == 'finished' and exit_status is not None:
        return f'{symbol} {format_process_state(process_state)} [{exit_status}]'

    return f'{symbol} {format_process_state(process_state)}'


def format_process_state(process_state):
    """
    Return a string formatted representation of the given process state

    :param process_state: the process state
    :return: string representation of process state
    """
    return f'{process_state.capitalize() if process_state else None}'


def format_sealed(sealed):
    """
    Return a string formatted representation of a node's sealed status

    :param sealed: the value for the sealed attribute of the node
    :return: string representation of seal status
    """
    return 'True' if sealed == 1 else 'False'
