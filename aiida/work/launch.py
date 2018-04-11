# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm import load_node
from . import runners
from . import rmq
from . import utils

__all__ = ['run', 'run_get_pid', 'run_get_node', 'submit']


def submit(process_class, **inputs):
    """
    Submit the process with the supplied inputs to the daemon runner immediately returning control to
    the interpreter. The return value will be the calculation node of the submitted process

    :param process: the process class to submit
    :param inputs: the inputs to be passed to the process
    :return: the calculation node of the process
    """
    assert not utils.is_workfunction(process_class), 'Cannot submit a workfunction'

    # Use a context manager to make sure connection is closed at end
    with rmq.new_blocking_control_panel() as control_panel:
        pid = control_panel.execute_process_start(process_class, init_kwargs={'inputs': inputs})
        return load_node(pid)


def run(process, *args, **inputs):
    """
    Run the process with the supplied inputs in a local runner that will block until the process is completed.
    The return value will be the results of the completed process

    :param process: the process class or workfunction to run
    :param inputs: the inputs to be passed to the process
    :return: the outputs of the process
    """
    runner = runners.get_runner()
    return runner.run(process, *args, **inputs)


def run_get_node(process, *args, **inputs):
    """
    Run the process with the supplied inputs in a local runner that will block until the process is completed.
    The return value will be the results of the completed process

    :param process: the process class or workfunction to run
    :param inputs: the inputs to be passed to the process
    :return: tuple of the outputs of the process and the calculation node
    """
    runner = runners.get_runner()
    return runner.run_get_node(process, *args, **inputs)


def run_get_pid(process, *args, **inputs):
    """
    Run the process with the supplied inputs in a local runner that will block until the process is completed.
    The return value will be the results of the completed process

    :param process: the process class or workfunction to run
    :param inputs: the inputs to be passed to the process
    :return: tuple of the outputs of the process and process pid
    """
    runner = runners.get_runner()
    return runner.run_get_pid(process, *args, **inputs)
