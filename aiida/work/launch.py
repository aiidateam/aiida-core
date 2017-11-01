# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from collections import namedtuple

from enum import Enum

from aiida.work.default_loop import enqueue
from runner import create_runner
from . import legacy

__all__ = ['run', 'rrun', 'run_get_pid', 'rrun_get_pid', 'async', 'submit']


class RunningType(Enum):
    """
    A type to indicate what type of object is running: a process,
    a calculation or a workflow
    """
    PROCESS = 0
    LEGACY_CALC = 1
    LEGACY_WORKFLOW = 2


RunningInfo = namedtuple("RunningInfo", ["type", "pid"])


def legacy_workflow(pk):
    return legacy.WaitOnWorkflow(pk)


def legacy_calc(pk):
    """
    Create a :class:`.RunningInfo` object for a legacy calculation

    :param pk: The calculation pk
    :type pk: int
    :return: The running info
    :rtype: :class:`.RunningInfo`
    """
    return RunningInfo(RunningType.LEGACY_CALC, pk)


def async(process_class, *args, **inputs):
    """
    Run a workfunction or workchain asynchronously.  The inputs get passed
    on to the workchain/workchain.

    :param process_class: The workchain or workfunction to run asynchronously
    :param args:
    :param kwargs: The keyword argument pairs
    :return: A future that represents the execution of the task.
    :rtype: :class:`plum.thread_executor.Future`
    """
    return enqueue(process_class, *args, **inputs)


def submit(process_class, **inputs):
    with create_runner() as runner:
        return runner.submit(process_class, **inputs)


def run(process_or_workfunction, *args, **inputs):
    """
    Run a workfunction or process and return the result.

    :param process_or_workfunction: The process class, instance or workfunction
    :param args: Positional arguments for a workfunction
    :param inputs: The list of keyword inputs
    :return: The result of the process
    """
    with create_runner() as runner:
        return rrun(runner, process_or_workfunction, *args, **inputs)


def rrun(runner, process_or_workfunction, *args, **inputs):
    """
    Run with the supplied runner.
    
    :param runner: The runner to run with
    :param process_or_workfunction: The process class, instance or workfunction
    :param args: Positional arguments for a workfunction
    :param inputs: The list of keyword inputs
    :return: The result of the process
    """
    proc = runner.create(process_or_workfunction, *args, **inputs)
    return runner.run_until_complete(proc)


def run_get_pid(process_or_workfunction, *args, **inputs):
    with create_runner() as runner:
        return rrun_get_pid(runner, process_or_workfunction, *args, **inputs)


def rrun_get_pid(runner, process_or_workfunction, *args, **inputs):
    proc = runner.create(process_or_workfunction, *args, **inputs)
    return runner.ResultAndPid(runner.run_until_complete(proc), proc.pid)
