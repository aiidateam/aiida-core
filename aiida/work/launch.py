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

import aiida.orm
from . import runners
from . import rmq
from . import utils

__all__ = ['run', 'run_get_pid', 'run_get_node', 'submit']

RunningInfo = namedtuple("RunningInfo", ["type", "pid"])

_persister = None


def submit(process_class, **inputs):
    assert not utils.is_workfunction(process_class), "Cannot submit a workfunction"

    pid = rmq.new_blocking_control_panel().execute_process_start(
        process_class, init_kwargs={'inputs': inputs})
    return aiida.orm.load_node(pid)


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
