# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Top level functions that can be used to launch a Process."""
from __future__ import absolute_import
from . import processes
from . import runners

__all__ = ['run', 'run_get_pid', 'run_get_node', 'submit']


def submit(process, **inputs):
    """
    Submit the process with the supplied inputs to the daemon runner immediately returning control to
    the interpreter. The return value will be the calculation node of the submitted process

    :param process: the process class to submit
    :param inputs: the inputs to be passed to the process
    :return: the calculation node of the process
    """
    runner = runners.new_runner(rmq_submit=True)
    return runner.submit(process, **inputs)


def run(process, *args, **inputs):
    """
    Run the process with the supplied inputs in a local runner that will block until the process is completed.
    The return value will be the results of the completed process

    :param process: the process class or workfunction to run
    :param inputs: the inputs to be passed to the process
    :return: the outputs of the process
    """
    if isinstance(process, processes.Process):
        runner = process.runner
    else:
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
    if isinstance(process, processes.Process):
        runner = process.runner
    else:
        runner = runners.get_runner()
    return runner.run_get_node(process, *args, **inputs)


# Allow user to also use run.get_node as a convenience (one less import)
run.get_node = run_get_node


def run_get_pid(process, *args, **inputs):
    """
    Run the process with the supplied inputs in a local runner that will block until the process is completed.
    The return value will be the results of the completed process

    :param process: the process class or workfunction to run
    :param inputs: the inputs to be passed to the process
    :return: tuple of the outputs of the process and process pid
    """
    if isinstance(process, processes.Process):
        runner = process.runner
    else:
        runner = runners.get_runner()
    return runner.run_get_pid(process, *args, **inputs)
