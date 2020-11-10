# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Top level functions that can be used to launch a Process."""

from aiida.common import InvalidOperation
from aiida.manage import manager
from .processes.functions import FunctionProcess
from .processes.process import Process
from .utils import is_process_scoped, instantiate_process

__all__ = ('run', 'run_get_pk', 'run_get_node', 'submit')


def run(process, *args, **inputs):
    """Run the process with the supplied inputs in a local runner that will block until the process is completed.

    :param process: the process class or process function to run
    :type process: :class:`aiida.engine.Process`

    :param inputs: the inputs to be passed to the process
    :type inputs: dict

    :return: the outputs of the process
    :rtype: dict
    """
    if isinstance(process, Process):
        runner = process.runner
    else:
        runner = manager.get_manager().get_runner()

    return runner.run(process, *args, **inputs)


def run_get_node(process, *args, **inputs):
    """Run the process with the supplied inputs in a local runner that will block until the process is completed.

    :param process: the process class or process function to run
    :type process: :class:`aiida.engine.Process`

    :param inputs: the inputs to be passed to the process
    :type inputs: dict

    :return: tuple of the outputs of the process and the process node
    :rtype: (dict, :class:`aiida.orm.ProcessNode`)

    """
    if isinstance(process, Process):
        runner = process.runner
    else:
        runner = manager.get_manager().get_runner()

    return runner.run_get_node(process, *args, **inputs)


def run_get_pk(process, *args, **inputs):
    """Run the process with the supplied inputs in a local runner that will block until the process is completed.

    :param process: the process class or process function to run
    :type process: :class:`aiida.engine.Process`

    :param inputs: the inputs to be passed to the process
    :type inputs: dict

    :return: tuple of the outputs of the process and process node pk
    :rtype: (dict, int)
    """
    if isinstance(process, Process):
        runner = process.runner
    else:
        runner = manager.get_manager().get_runner()

    return runner.run_get_pk(process, *args, **inputs)


def submit(process, **inputs):
    """Submit the process with the supplied inputs to the daemon immediately returning control to the interpreter.

    .. warning: this should not be used within another process. Instead, there one should use the `submit` method of
        the wrapping process itself, i.e. use `self.submit`.

    .. warning: submission of processes requires `store_provenance=True`

    :param process: the process class to submit
    :type process: :class:`aiida.engine.Process`

    :param inputs: the inputs to be passed to the process
    :type inputs: dict

    :return: the calculation node of the process
    :rtype: :class:`aiida.orm.ProcessNode`
    """
    # Submitting from within another process requires `self.submit` unless it is a work function, in which case the
    # current process in the scope should be an instance of `FunctionProcess`
    if is_process_scoped() and not isinstance(Process.current(), FunctionProcess):
        raise InvalidOperation('Cannot use top-level `submit` from within another process, use `self.submit` instead')

    runner = manager.get_manager().get_runner()
    controller = manager.get_manager().get_process_controller()

    process = instantiate_process(runner, process, **inputs)

    # If a dry run is requested, simply forward to `run`, because it is not compatible with `submit`. We choose for this
    # instead of raising, because in this way the user does not have to change the launcher when testing.
    if process.metadata.get('dry_run', False):
        _, node = run_get_node(process)
        return node

    if not process.metadata.store_provenance:
        raise InvalidOperation('cannot submit a process with `store_provenance=False`')

    runner.persister.save_checkpoint(process)
    process.close()

    # Do not wait for the future's result, because in the case of a single worker this would cock-block itself
    controller.continue_process(process.pid, nowait=False, no_reply=True)

    return process.node


# Allow one to also use run.get_node and run.get_pk as a shortcut, without having to import the functions themselves
run.get_node = run_get_node
run.get_pk = run_get_pk
