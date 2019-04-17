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
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.manage import manager
from .processes.process import Process
from .utils import is_process_function, instantiate_process

__all__ = ('run', 'run_get_pk', 'run_get_node', 'submit')


def run(process, *args, **inputs):
    """Run the process with the supplied inputs in a local runner that will block until the process is completed.

    :param process: the process class or process function to run
    :param inputs: the inputs to be passed to the process
    :return: the outputs of the process
    """
    if isinstance(process, Process):
        runner = process.runner
    else:
        runner = manager.get_manager().get_runner()

    return runner.run(process, *args, **inputs)


def run_get_node(process, *args, **inputs):
    """Run the process with the supplied inputs in a local runner that will block until the process is completed.

    :param process: the process class or process function to run
    :param inputs: the inputs to be passed to the process
    :return: tuple of the outputs of the process and the process node
    """
    if isinstance(process, Process):
        runner = process.runner
    else:
        runner = manager.get_manager().get_runner()

    return runner.run_get_node(process, *args, **inputs)


def run_get_pk(process, *args, **inputs):
    """Run the process with the supplied inputs in a local runner that will block until the process is completed.

    :param process: the process class or process function to run
    :param inputs: the inputs to be passed to the process
    :return: tuple of the outputs of the process and process node pk
    """
    if isinstance(process, Process):
        runner = process.runner
    else:
        runner = manager.get_manager().get_runner()

    return runner.run_get_pk(process, *args, **inputs)


def submit(process, **inputs):
    """Submit the process with the supplied inputs to the daemon immediately returning control to the interpreter.

    :param process: the process class to submit
    :param inputs: the inputs to be passed to the process
    :return: the calculation node of the process
    """
    assert not is_process_function(process), 'Cannot submit a process function'

    runner = manager.get_manager().get_runner()
    controller = manager.get_manager().get_process_controller()

    process = instantiate_process(runner, process, **inputs)
    runner.persister.save_checkpoint(process)
    process.close()

    # Do not wait for the future's result, because in the case of a single worker this would cock-block itself
    controller.continue_process(process.pid, nowait=False, no_reply=True)

    return process.node


# Allow one to also use run.get_node and run.get_pk as a shortcut, without having to import the functions themselves
run.get_node = run_get_node
run.get_pk = run_get_pk
