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
from runner import get_runner, _object_factory
from . import legacy
from . import process

__all__ = ['run', 'run_get_pid', 'submit']

RunningInfo = namedtuple("RunningInfo", ["type", "pid"])
ResultAndPid = namedtuple("ResultWithPid", ["result", "pid"])


def legacy_workflow(pk):
    return legacy.WaitOnWorkflow(pk)


def submit(process_class, **inputs):
    runner = get_runner()
    return runner.submit(process_class, **inputs)


def run(process_or_workfunction, *args, **inputs):
    """
    Run a workfunction or process and return the result.

    :param process_or_workfunction: The process class, instance or workfunction
    :param args: Positional arguments for a workfunction
    :param inputs: The list of keyword inputs
    :return: The result of the process
    """
    runner = get_runner()
    return runner.run(process_or_workfunction, *args, **inputs)


def run_get_pid(process_or_workfunction, *args, **inputs):
    runner = get_runner()
    return runner.run_get_pid(process_or_workfunction, *args, **inputs)