# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import contextlib
from threading import local
import tornado.ioloop

from aiida.common.links import LinkType
from aiida.orm.calculation import Calculation
from aiida.orm.data.frozendict import FrozenDict

__all__ = ['ProcessStack']

PROCESS_STATE_CHANGE_KEY = 'process|state_change|{}'
PROCESS_STATE_CHANGE_DESCRIPTION = 'The last time a process of type {}, changed state'


class ProcessStack(object):
    """
    Keep track of the per-thread call stack of processes.
    """

    _thread_local = local()

    @classmethod
    def get_active_process_id(cls):
        """
        Get the pid of the process at the top of the stack

        :return: The pid
        """
        return cls.top().pid

    @classmethod
    def get_active_process_calc_node(cls):
        """
        Get the calculation node of the process at the top of the stack

        :return: The calculation node
        :rtype: :class:`aiida.orm.implementation.general.calculation.job.AbstractJobCalculation`
        """
        return cls.top().calc

    @classmethod
    def top(cls):
        return cls.stack()[-1]

    @classmethod
    def stack(cls):
        try:
            return cls._thread_local.wf_stack
        except AttributeError:
            cls._thread_local.wf_stack = []
            return cls._thread_local.wf_stack

    @classmethod
    def pids(cls):
        try:
            return cls._thread_local.pids_stack
        except AttributeError:
            cls._thread_local.pids_stack = []
            return cls._thread_local.pids_stack

    @classmethod
    def push(cls, process):
        try:
            process._parent = cls.top()
        except IndexError:
            process._parent = None
        cls.stack().append(process)
        cls.pids().append(process.pid)

    @classmethod
    def pop(cls, process=None, pid=None):
        """
        Pop a process from the stack.  To make sure the stack is not corrupted
        the process instance or pid of the calling process should be supplied
        so we can verify that is really is top of the stack.

        :param process: The process instance
        :param pid: The process id.
        """
        assert process is not None or pid is not None
        if process is not None:
            assert process is cls.top(), \
                "Can't pop a process that is not top of the stack"
        elif pid is not None:
            assert pid == cls.pids()[-1], \
                "Can't pop a process that is not top of the stack"
        else:
            raise ValueError("Must supply process or pid")

        process = cls.stack().pop()
        process._parent = None

        cls.pids().pop()

    def __init__(self):
        raise NotImplementedError("Can't instantiate the ProcessStack")


def is_workfunction(func):
    try:
        return func._is_workfunction
    except AttributeError:
        return False


def get_or_create_output_group(calculation):
    """
    For a given Calculation, get or create a new frozendict Data node that
    has as its values all output Data nodes of the Calculation.

    :param calculation: Calculation
    """
    if not isinstance(calculation, Calculation):
        raise TypeError("Can only create output groups for type Calculation")

    d = calculation.get_outputs_dict(link_type=LinkType.CREATE)
    d.update(calculation.get_outputs_dict(link_type=LinkType.RETURN))

    return FrozenDict(dict=d)


@contextlib.contextmanager
def loop_scope(loop):
    """
    Make an event loop current for the scope of the context

    :param loop: The event loop to make current for the duration of the scope
    :type loop: :class:`tornado.ioloop.IOLoop`
    """

    current = tornado.ioloop.IOLoop.current()
    try:
        loop.make_current()
        yield
    finally:
        current.make_current()


def set_process_state_change_timestamp(process):
    """
    Set the global setting that reflects the last time a process changed state, for the process type
    of the given process, to the current timestamp. The process type will be determined based on
    the class of the calculation node it has as its database container.

    :param process: the Process instance that changed its state
    """
    from aiida.backends.utils import set_global_setting
    from aiida.common.exceptions import UniquenessError
    from aiida.orm.calculation.function import FunctionCalculation
    from aiida.orm.calculation.inline import InlineCalculation
    from aiida.orm.calculation.job import JobCalculation
    from aiida.orm.calculation.work import WorkCalculation
    from aiida.utils import timezone

    if isinstance(process.calc, (JobCalculation, InlineCalculation)):
        process_type = 'calculation'
    elif isinstance(process.calc, (FunctionCalculation, WorkCalculation)):
        process_type = 'work'
    else:
        raise ValueError('unsupported calculation node type {}'.format(type(process.calc)))

    key = PROCESS_STATE_CHANGE_KEY.format(process_type)
    description = PROCESS_STATE_CHANGE_DESCRIPTION.format(process_type)
    value = timezone.now()

    try:
        set_global_setting(key, value, description)
    except UniquenessError as exception:
        process.logger.debug('could not update the {} setting because of a UniquenessError: {}'.format(key, exception))
        pass


def get_process_state_change_timestamp(process_type='calculation'):
    """
    Get the global setting that reflects the last time a process of the given process type changed
    its state. The returned value will be the corresponding timestamp or None if the setting does
    not exist.

    :param process_type: the process type for which to get the latest state change timestamp.
        Valid process types are either 'calculation' or 'work'.
    :return: a timestamp or None
    """
    from aiida.backends.utils import get_global_setting

    if process_type not in ['calculation', 'work']:
        raise ValueError('invalid value for process_type')

    key = PROCESS_STATE_CHANGE_KEY.format(process_type)

    try:
        return get_global_setting(key)
    except KeyError:
        return None
