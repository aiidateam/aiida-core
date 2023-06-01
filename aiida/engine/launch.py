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
from typing import Any, Dict, Tuple, Type, Union

from aiida.common import InvalidOperation
from aiida.manage import manager
from aiida.orm import ProcessNode

from .processes.builder import ProcessBuilder
from .processes.functions import FunctionProcess
from .processes.process import Process
from .utils import instantiate_process, is_process_scoped  # pylint: disable=no-name-in-module

__all__ = ('run', 'run_get_pk', 'run_get_node', 'submit')

TYPE_RUN_PROCESS = Union[Process, Type[Process], ProcessBuilder]  # pylint: disable=invalid-name
# run can also be process function, but it is not clear what type this should be
TYPE_SUBMIT_PROCESS = Union[Process, Type[Process], ProcessBuilder]  # pylint: disable=invalid-name


def run(process: TYPE_RUN_PROCESS, *args: Any, **inputs: Any) -> Dict[str, Any]:
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


def run_get_node(process: TYPE_RUN_PROCESS, *args: Any, **inputs: Any) -> Tuple[Dict[str, Any], ProcessNode]:
    """Run the process with the supplied inputs in a local runner that will block until the process is completed.

    :param process: the process class, instance, builder or function to run
    :param inputs: the inputs to be passed to the process

    :return: tuple of the outputs of the process and the process node

    """
    if isinstance(process, Process):
        runner = process.runner
    else:
        runner = manager.get_manager().get_runner()

    return runner.run_get_node(process, *args, **inputs)


def run_get_pk(process: TYPE_RUN_PROCESS, *args: Any, **inputs: Any) -> Tuple[Dict[str, Any], int]:
    """Run the process with the supplied inputs in a local runner that will block until the process is completed.

    :param process: the process class, instance, builder or function to run
    :param inputs: the inputs to be passed to the process

    :return: tuple of the outputs of the process and process node pk

    """
    if isinstance(process, Process):
        runner = process.runner
    else:
        runner = manager.get_manager().get_runner()

    return runner.run_get_pk(process, *args, **inputs)


def submit(process: TYPE_SUBMIT_PROCESS, **inputs: Any) -> ProcessNode:
    """Submit the process with the supplied inputs to the daemon immediately returning control to the interpreter.

    .. warning: this should not be used within another process. Instead, there one should use the `submit` method of
        the wrapping process itself, i.e. use `self.submit`.

    .. warning: submission of processes requires `store_provenance=True`

    :param process: the process class, instance or builder to submit
    :param inputs: the inputs to be passed to the process

    :return: the calculation node of the process

    """
    # Submitting from within another process requires `self.submit` unless it is a work function, in which case the
    # current process in the scope should be an instance of `FunctionProcess`
    if is_process_scoped() and not isinstance(Process.current(), FunctionProcess):
        raise InvalidOperation('Cannot use top-level `submit` from within another process, use `self.submit` instead')

    runner = manager.get_manager().get_runner()
    assert runner.persister is not None, 'runner does not have a persister'
    assert runner.controller is not None, 'runner does not have a persister'

    process_inited = instantiate_process(runner, process, **inputs)

    # If a dry run is requested, simply forward to `run`, because it is not compatible with `submit`. We choose for this
    # instead of raising, because in this way the user does not have to change the launcher when testing. The same goes
    # for if `remote_folder` is present in the inputs, which means we are importing an already completed calculation.
    if process_inited.metadata.get('dry_run', False) or 'remote_folder' in inputs:
        _, node = run_get_node(process_inited)
        return node

    if not process_inited.metadata.store_provenance:
        raise InvalidOperation('cannot submit a process with `store_provenance=False`')

    runner.persister.save_checkpoint(process_inited)
    process_inited.close()

    # Do not wait for the future's result, because in the case of a single worker this would cock-block itself
    runner.controller.continue_process(process_inited.pid, nowait=False, no_reply=True)

    return process_inited.node


# Allow one to also use run.get_node and run.get_pk as a shortcut, without having to import the functions themselves
run.get_node = run_get_node  # type: ignore[attr-defined]
run.get_pk = run_get_pk  # type: ignore[attr-defined]
