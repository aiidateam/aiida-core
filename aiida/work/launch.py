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
from runner import create_runner, _object_factory
from . import legacy
from . import process

__all__ = ['run', 'run_get_pid', 'async', 'submit']

RunningInfo = namedtuple("RunningInfo", ["type", "pid"])
ResultAndPid = namedtuple("ResultWithPid", ["result", "pid"])


def legacy_workflow(pk):
    return legacy.WaitOnWorkflow(pk)


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
    proc = _ensure_process(process_or_workfunction, *args, **inputs)
    return proc.execute()


def run_get_pid(process_or_workfunction, *args, **inputs):
    proc = _ensure_process(process_or_workfunction, *args, **inputs)
    return ResultAndPid(proc.execute(), proc.pid)


def _ensure_process(proc, *args, **kwargs):
    if isinstance(proc, process.Process):
        return proc

    return _object_factory(proc, *args, inputs=kwargs)
