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

from . import rmq
from . import runners
from . import utils

__all__ = ['run', 'run_get_pid', 'run_get_node', 'submit']

RunningInfo = namedtuple("RunningInfo", ["type", "pid"])

_rmq_control_panel = None


def get_rmq_control_panel():
    global _rmq_control_panel
    if _rmq_control_panel is None:
        _rmq_control_panel = rmq.BlockingProcessControlPanel('aiida')
    return _rmq_control_panel


def submit(process_class, **inputs):
    assert not utils.is_workfunction(process_class), "Cannot submit a workfunction"

    submit_runner = runners.new_runner(rmq_submit=True, enable_persistence=True)
    future = submit_runner.submit(process_class, **inputs)
    return submit_runner.run_until_complete(future)

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
        runner = runners.get_runner()
        return runner.run(process, *args, **inputs)


def run_get_node(process, *args, **inputs):
    if utils.is_workfunction(process):
        return process.run_get_node(*args, **inputs)
    else:
        runner = runners.get_runner()
        return runner.run_get_node(process, *args, **inputs)


def run_get_pid(process, *args, **inputs):
    result, calc = run_get_node(process, *args, **inputs)
    return runners.ResultAndPid(result, calc.pk)
