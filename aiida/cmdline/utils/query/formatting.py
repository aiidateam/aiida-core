# -*- coding: utf-8 -*-
"""A utility module with simple functions to format variables into strings for cli outputs."""


def format_relative_time(datetime):
    """
    Return a string formatted timedelta of the given datetime with respect to the current datetime

    :param datetime: the datetime to format
    :return: string representation of the relative time since the given datetime
    """
    from aiida.common.utils import str_timedelta
    from aiida.utils import timezone

    timedelta = timezone.delta(datetime, timezone.now())

    return str_timedelta(timedelta, negative_to_zero=True, max_num_fields=1)


def format_state(process_state, exit_status=None):
    """
    Return a string formatted representation of a process' state, which consists of its process state and exit status

    :param process_state: the process state
    :param exit_status: the process' exit status
    :return: string representation of the process' state
    """
    return '{} | {}'.format(process_state.capitalize() if process_state else None, exit_status)


def format_process_state(process_state):
    """
    Return a string formatted representation of the given process state

    :param process_state: the process state
    :return: string representation of process state
    """
    return '{}'.format(process_state.capitalize() if process_state else None)


def format_sealed(sealed):
    """
    Return a string formatted representation of a node's sealed status

    :param sealed: the value for the sealed attribute of the node
    :return: string representation of seal status
    """
    return 'True' if sealed == 1 else 'False'
