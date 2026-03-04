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
from aiida.manage import manager
from aiida.orm import ProcessNode

if t.TYPE_CHECKING:
    from aiida.brokers.broker import QueueType

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


def _determine_queue_type(process_class: t.Type[Process]) -> 'QueueType':
    """Determine which queue type a process should be routed to.

    :param process_class: The process class being submitted.
    :return: Queue type (ROOT_WORKCHAIN or CALCJOB).
    """
    from aiida.brokers.broker import QueueType
    from aiida.engine.processes.calcjobs import CalcJob
    from aiida.engine.processes.workchains import WorkChain

    # CalcJobs always go to calcjob queue
    if issubclass(process_class, CalcJob):
        return QueueType.CALCJOB

    # WorkChains at top level go to root-workchain queue
    if issubclass(process_class, WorkChain):
        return QueueType.ROOT_WORKCHAIN

    # Default to calcjob queue for other process types (e.g., work functions)
    return QueueType.CALCJOB


def _get_queue_info_for_submit(
    process_inited: Process, user_queue: str | None = None
) -> 'tuple[str, QueueType] | None':
    """Get the queue info (user_queue, queue_type) for submitting a top-level process.

    :param process_inited: The initialized process instance.
    :param user_queue: Optional user queue name. If None, uses the default queue.
    :return: Tuple of (user_queue, queue_type), or None if no broker is configured.
    """
    broker = manager.get_manager().get_broker()
    if broker is None:
        return None

    from aiida.brokers.rabbitmq.defaults import DEFAULT_USER_QUEUE

    if user_queue is None:
        user_queue = DEFAULT_USER_QUEUE
    queue_type = _determine_queue_type(type(process_inited))
    return (user_queue, queue_type)


def run(process: TYPE_RUN_PROCESS, inputs: dict[str, t.Any] | None = None, **kwargs: t.Any) -> dict[str, t.Any]:
    """Run the process with the supplied inputs in a local runner that will block until the process is completed.

    :param process: the process class or process function to run
    :param inputs: the inputs to be passed to the process
    :return: the outputs of the process
    """
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
    else:
        runner = manager.get_manager().get_runner()

    return runner.run_get_node(process, inputs, **kwargs)


def run_get_pk(process: TYPE_RUN_PROCESS, inputs: dict[str, t.Any] | None = None, **kwargs: t.Any) -> ResultAndPk:
    """Run the process with the supplied inputs in a local runner that will block until the process is completed.

    :param process: the process class, instance, builder or function to run
    :param inputs: the inputs to be passed to the process
    :return: tuple of the outputs of the process and process node pk
    """
    if isinstance(process, Process):
        runner = process.runner
    else:
        runner = manager.get_manager().get_runner()

    return runner.run_get_pk(process, inputs, **kwargs)


def _get_process_class(process: TYPE_SUBMIT_PROCESS) -> t.Type[Process]:
    """Get the process class from a process argument.

    :param process: Process class, instance, or builder.
    :return: The process class.
    """
    if isinstance(process, ProcessBuilder):
        return process.process_class
    if isinstance(process, Process):
        return type(process)
    return process


def _has_input_port(process: TYPE_SUBMIT_PROCESS, port_name: str) -> bool:
    """Check if a process has a specific input port.

    :param process: Process class, instance, or builder.
    :param port_name: Name of the input port to check.
    :return: True if the process has the input port.
    """
    process_class = _get_process_class(process)
    return port_name in process_class.spec().inputs


def submit(
    process: TYPE_SUBMIT_PROCESS,
    inputs: dict[str, t.Any] | None = None,
    *,
    user_queue: str | None = None,
    wait: bool = False,
    wait_interval: int = 5,
    **kwargs: t.Any,
) -> ProcessNode:
    """Submit the process with the supplied inputs to the daemon immediately returning control to the interpreter.

    .. warning: this should not be used within another process. Instead, there one should use the ``submit`` method of
        the wrapping process itself, i.e. use ``self.submit``.

    .. warning: submission of processes requires ``store_provenance=True``.

    :param process: the process class, instance or builder to submit
    :param inputs: the input dictionary to be passed to the process
    :param user_queue: the user queue name to submit to (default: 'default'). Must be created with
        `verdi broker queue create`. If the process has an input port named `user_queue`, use `_user_queue` instead.
    :param wait: when set to ``True``, the submission will be blocking and wait for the process to complete at which
        point the function returns the calculation node.
    :param wait_interval: the number of seconds to wait between checking the state of the process when ``wait=True``.
    :param kwargs: inputs to be passed to the process. This is an alternative to the positional ``inputs`` argument.
    :return: the calculation node of the process
    """
    from aiida.common.docs import URL_NO_BROKER

    # Handle user_queue parameter conflict with process input ports
    # If the process has an input port named 'user_queue', users must use '_user_queue' instead
    if _has_input_port(process, 'user_queue'):
        if user_queue is not None:
            raise InvalidOperation(
                "This process has an input port named 'user_queue'. To specify the submission queue, "
                "use '_user_queue' instead: submit(process, _user_queue='queue_name', ...)"
            )
        # Check for _user_queue fallback in kwargs
        if '_user_queue' in kwargs:
            user_queue = kwargs.pop('_user_queue')

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

    # Determine queue routing for multi-queue mode
    # Since we verified runner.controller exists above, broker must also exist,
    # so _get_queue_info_for_submit will return a valid tuple (not None)
    queue_info = _get_queue_info_for_submit(process_inited, user_queue=user_queue)
    assert queue_info is not None, 'Queue info must be set when broker is configured'
    user_queue, queue_type = queue_info
    process_inited.set_queue_name(user_queue)  # Store for nested submissions

    # Get the full RabbitMQ queue name including the profile prefix
    broker = manager.get_manager().get_broker()
    full_queue_name = broker.get_full_queue_name(user_queue, queue_type)

    runner.persister.save_checkpoint(process_inited)
    process_inited.close()

    # Do not wait for the future's result, because in the case of a single worker this would cock-block itself
    runner.controller.continue_process(process_inited.pid, nowait=False, no_reply=True, queue_name=full_queue_name)
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
