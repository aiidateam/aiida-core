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

from runner import get_runner
from . import legacy
from . import utils

__all__ = ['run', 'run_get_pid', 'run_get_node', 'submit']

RunningInfo = namedtuple("RunningInfo", ["type", "pid"])
ResultAndPid = namedtuple("ResultWithPid", ["result", "pid"])


def legacy_workflow(pk):
    return legacy.WaitOnWorkflow(pk)


def submit(process_class, **inputs):
    runner = get_runner()
    return runner.submit(process_class, **inputs)


def run(process, *args, **inputs):
    """
    Run a workfunction or process and return the result.

    :param process: The process class, instance or workfunction
    :param args: Positional arguments for a workfunction
    :param inputs: The list of keyword inputs
    :return: The result of the process
    """
    if utils.is_workfunction(process):
        return process(*args, **inputs)
    else:
        runner = get_runner()
        return runner.run(process, *args, **inputs)


def run_get_node(process, *args, **inputs):
    if utils.is_workfunction(process):
        process.run_get_node(*args, **inputs)
    else:
        runner = get_runner()
        return runner.run_get_node(process, *args, **inputs)


def run_get_pid(process, *args, **inputs):
    result, node = run_get_node(process, *args, **inputs)
    return result, node.pid
