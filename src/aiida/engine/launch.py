###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Top level functions that can be used to launch a Process."""

from __future__ import annotations

import time
import typing as t

from aiida.common import InvalidOperation
from aiida.common.lang import type_check
from aiida.common.log import AIIDA_LOGGER
from aiida.common.workgraph import is_workgraph_instance
from aiida.manage import manager
from aiida.orm import ProcessNode

from .processes.builder import ProcessBuilder
from .processes.functions import FunctionProcess
from .processes.process import Process
from .runners import ResultAndPk
from .utils import instantiate_process, is_process_scoped, prepare_inputs

__all__ = ('await_processes', 'run', 'run_get_node', 'run_get_pk', 'submit')

TYPE_RUN_PROCESS = t.Union[Process, t.Type[Process], ProcessBuilder]
# run can also be process function, but it is not clear what type this should be
TYPE_SUBMIT_PROCESS = t.Union[Process, t.Type[Process], ProcessBuilder]
LOGGER = AIIDA_LOGGER.getChild('engine.launch')


def _prepare_workgraph_inputs(
    inputs: dict[str, t.Any] | None,
    kwargs: dict[str, t.Any],
) -> dict[str, t.Any] | None:
    """Prepare inputs for a WorkGraph by merging inputs dict and kwargs.

    :param inputs: the input dictionary
    :param kwargs: additional keyword arguments to be merged with inputs
    :return: merged inputs dictionary, or None if both are empty
    """
    if not inputs and not kwargs:
        return None
    wg_inputs: dict[str, t.Any] = {}
    if inputs:
        wg_inputs.update(inputs)
    if kwargs:
        wg_inputs.update(kwargs)
    return wg_inputs if wg_inputs else None


def run(process: TYPE_RUN_PROCESS, inputs: dict[str, t.Any] | None = None, **kwargs: t.Any) -> dict[str, t.Any]:
    """Run the process with the supplied inputs in a local runner that will block until the process is completed.

    :param process: the process class or process function to run
    :param inputs: the inputs to be passed to the process
    :return: the outputs of the process
    """
    # Handle WorkGraph instances (cast to Any since mypy can't narrow the union type)
    if is_workgraph_instance(process):
        wg_inputs = _prepare_workgraph_inputs(inputs, kwargs)
        wg = t.cast(t.Any, process)
        return wg.run(inputs=wg_inputs)

    if isinstance(process, Process):
        runner = process.runner
    else:
        runner = manager.get_manager().get_runner()

    return runner.run(process, inputs, **kwargs)


def run_get_node(
    process: TYPE_RUN_PROCESS, inputs: dict[str, t.Any] | None = None, **kwargs: t.Any
) -> tuple[dict[str, t.Any], ProcessNode]:
    """Run the process with the supplied inputs in a local runner that will block until the process is completed.

    :param process: the process class, instance, builder or function to run
    :param inputs: the inputs to be passed to the process
    :return: tuple of the outputs of the process and the process node
    """
    if isinstance(process, Process):
        runner = process.runner
    # Handle WorkGraph instances (cast to Any since mypy can't narrow the union type)
    elif is_workgraph_instance(process):
        wg_inputs = _prepare_workgraph_inputs(inputs, kwargs)
        wg = t.cast(t.Any, process)
        result = wg.run(inputs=wg_inputs)
        return result, wg.process

    else:
        runner = manager.get_manager().get_runner()

    return runner.run_get_node(process, inputs, **kwargs)


def run_get_pk(process: TYPE_RUN_PROCESS, inputs: dict[str, t.Any] | None = None, **kwargs: t.Any) -> ResultAndPk:
    """Run the process with the supplied inputs in a local runner that will block until the process is completed.

    :param process: the process class, instance, builder or function to run
    :param inputs: the inputs to be passed to the process
    :return: tuple of the outputs of the process and process node pk
    """
    # Handle WorkGraph instances (cast to Any since mypy can't narrow the union type)
    if is_workgraph_instance(process):
        wg_inputs = _prepare_workgraph_inputs(inputs, kwargs)
        wg = t.cast(t.Any, process)
        result = wg.run(inputs=wg_inputs)
        return ResultAndPk(result, wg.process.pk)

    if isinstance(process, Process):
        runner = process.runner
    else:
        runner = manager.get_manager().get_runner()

    return runner.run_get_pk(process, inputs, **kwargs)


def submit(
    process: TYPE_SUBMIT_PROCESS,
    inputs: dict[str, t.Any] | None = None,
    *,
    wait: bool = False,
    wait_interval: int = 5,
    timeout: int = 600,
    **kwargs: t.Any,
) -> ProcessNode:
    """Submit the process with the supplied inputs to the daemon immediately returning control to the interpreter.

    .. warning: this should not be used within another process. Instead, there one should use the ``submit`` method of
        the wrapping process itself, i.e. use ``self.submit``.

    .. warning: submission of processes requires ``store_provenance=True``.

    :param process: the process class, instance or builder to submit
    :param inputs: the input dictionary to be passed to the process
    :param wait: when set to ``True``, the submission will be blocking and wait for the process to complete at which
        point the function returns the calculation node.
    :param wait_interval: the number of seconds to wait between checking the state of the process when ``wait=True``.
    :param timeout: when ``wait=True``, the maximum number of seconds to wait for the process to complete. Only applies
        to WorkGraph processes. Defaults to 600 seconds.
    :param kwargs: inputs to be passed to the process. This is an alternative to the positional ``inputs`` argument.
    :return: the calculation node of the process
    """
    from aiida.common.docs import URL_NO_BROKER

    # Handle WorkGraph instances (cast to Any since mypy can't narrow the union type)
    if is_workgraph_instance(process):
        wg_inputs = _prepare_workgraph_inputs(inputs, kwargs)
        # Warn if execution option names are found in inputs (might be user error)
        if wg_inputs:
            suspicious_keys = [k for k in ('wait', 'timeout', 'interval') if k in wg_inputs]
            if suspicious_keys:
                LOGGER.warning(
                    f'Found {suspicious_keys} in inputs dict. If these are meant as execution options, '
                    f'pass them as function arguments: submit(wg, wait=..., timeout=..., wait_interval=...)'
                )
        wg = t.cast(t.Any, process)
        return wg.submit(
            inputs=wg_inputs,
            wait=wait,
            timeout=timeout,
            interval=wait_interval,
        )

    inputs = prepare_inputs(inputs, **kwargs)

    # Submitting from within another process requires ``self.submit``` unless it is a work function, in which case the
    # current process in the scope should be an instance of ``FunctionProcess``.
    if is_process_scoped() and not isinstance(Process.current(), FunctionProcess):
        raise InvalidOperation('Cannot use top-level `submit` from within another process, use `self.submit` instead')

    runner = manager.get_manager().get_runner()

    if runner.controller is None:
        raise InvalidOperation(
            'Cannot submit because the runner does not have a process controller, probably because the profile does '
            'not define a broker like RabbitMQ. If a RabbitMQ server is available, the profile can be configured to '
            'use it with `verdi profile configure-rabbitmq`. Otherwise, use :meth:`aiida.engine.launch.run` instead to '
            'run the process in the local Python interpreter instead of submitting it to the daemon. '
            f'See {URL_NO_BROKER} for more details.'
        )

    assert runner.persister is not None, 'runner does not have a persister'

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
    node = process_inited.node

    if not wait:
        return node

    while not node.is_terminated:
        LOGGER.report(
            f'Process<{node.pk}> has not yet terminated, current state is `{node.process_state}`. '
            f'Waiting for {wait_interval} seconds.'
        )
        time.sleep(wait_interval)

    return node


def await_processes(nodes: t.Sequence[ProcessNode], wait_interval: int = 1) -> None:
    """Run a loop until all processes are terminated.

    :param nodes: Sequence of nodes that represent the processes to await.
    :param wait_interval: The interval between each iteration of checking the status of all processes.
    """
    type_check(nodes, (list, tuple))

    if any(not isinstance(node, ProcessNode) for node in nodes):
        raise TypeError(f'`nodes` should be a list of `ProcessNode`s but got: {nodes}')

    start_time = time.time()
    terminated = False

    while not terminated:
        running = [not node.is_terminated for node in nodes]
        terminated = not any(running)
        seconds_passed = time.time() - start_time
        LOGGER.report(f'{running.count(False)} out of {len(nodes)} processes terminated. [{round(seconds_passed)} s]')
        time.sleep(wait_interval)


# Allow one to also use run.get_node and run.get_pk as a shortcut, without having to import the functions themselves
run.get_node = run_get_node  # type: ignore[attr-defined]
run.get_pk = run_get_pk  # type: ignore[attr-defined]
