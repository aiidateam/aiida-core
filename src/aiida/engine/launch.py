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

from .processes.builder import ProcessBuilder
from .processes.functions import FunctionProcess
from .processes.process import Process
from .runners import ResultAndPk
from .utils import instantiate_process, is_process_scoped, prepare_inputs

__all__ = ('ProcessTimeoutError', 'await_processes', 'run', 'run_get_node', 'run_get_pk', 'submit')

TYPE_RUN_PROCESS = t.Union[Process, t.Type[Process], ProcessBuilder]
# run can also be process function, but it is not clear what type this should be
TYPE_SUBMIT_PROCESS = t.Union[Process, t.Type[Process], ProcessBuilder]
LOGGER = AIIDA_LOGGER.getChild('engine.launch')


class ProcessTimeoutError(TimeoutError):
    """Raised when a blocking wait (``submit(wait=True, timeout=...)``) exceeds its ``timeout``.

    Subclasses the built-in :class:`TimeoutError`, so existing ``except TimeoutError`` handlers keep working. The wait
    timing out does not cancel the process; it keeps being processed by the daemon. The process node is attached as
    :attr:`node` so a caller that catches this can keep monitoring the process without parsing the message.
    """

    def __init__(self, message: str, node: ProcessNode) -> None:
        super().__init__(message)
        self.node = node


def run(process: TYPE_RUN_PROCESS, inputs: dict[str, t.Any] | None = None, **kwargs: t.Any) -> dict[str, t.Any]:
    """Run the process with the supplied inputs in a local runner that will block until the process is completed.

    :param process: the process class or process function to run
    :param inputs: the inputs to be passed to the process
    :return: the outputs of the process
    """
    if isinstance(process, Process):
        runner = process.runner
    else:
        # Note: it is safe to create new local runner here without but the explanation can be found in issue #7353
        runner = manager.get_manager().create_runner(communicator=None)

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
        # Note: it is safe to create new local runner here without but the explanation can be found in issue #7353
        runner = manager.get_manager().create_runner(communicator=None)

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
        # Note: it is safe to create new local runner here without but the explanation can be found in issue #7353
        runner = manager.get_manager().create_runner(communicator=None)

    return runner.run_get_pk(process, inputs, **kwargs)


def submit(
    process: TYPE_SUBMIT_PROCESS,
    inputs: dict[str, t.Any] | None = None,
    *,
    wait: bool = False,
    wait_interval: float = 5,
    timeout: float | None = None,
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
    :param timeout: optional maximum number of seconds to wait for the process to terminate, only used when
        ``wait=True``. Must be a positive number. If the process does not terminate within this time, a
        ``TimeoutError`` is raised. The timeout only stops waiting; the process itself is not cancelled and keeps
        being processed by the daemon. If ``None`` (default), waits indefinitely.
    :param kwargs: inputs to be passed to the process. This is an alternative to the positional ``inputs`` argument.
    :return: the calculation node of the process
    :raises ValueError: if ``timeout`` is not a positive number.
    :raises ProcessTimeoutError: subclass of ``TimeoutError``, if ``wait=True`` and the process does not terminate
        within ``timeout`` seconds. The timeout only stops waiting; the process is not cancelled, keeps being processed
        by the daemon, and is available as the exception's ``node`` attribute.
    """
    from aiida.common.docs import URL_NO_BROKER

    if timeout is not None and timeout <= 0:
        msg = f'`timeout` must be a positive number of seconds, but got {timeout}.'
        raise ValueError(msg)

    inputs = prepare_inputs(inputs, **kwargs)

    # Submitting from within another process requires ``self.submit``` unless it is a work function, in which case the
    # current process in the scope should be an instance of ``FunctionProcess``.
    if is_process_scoped() and not isinstance(Process.current(), FunctionProcess):
        raise InvalidOperation('Cannot use top-level `submit` from within another process, use `self.submit` instead')

    # If a dry run is requested, simply forward to `run`, because it is not compatible with `submit`. We choose for this
    # instead of raising, because in this way the user does not have to change the launcher when testing. The same goes
    # for if `remote_folder` is present in the inputs, which means we are importing an already completed calculation.
    # Builder inputs need to be merged so that detection works for ``submit(builder)`` too.
    if isinstance(process, ProcessBuilder):
        merged_inputs = {**inputs, **process._inputs(prune=True)}
    else:
        merged_inputs = inputs
    if (merged_inputs.get('metadata') or {}).get('dry_run', False) or 'remote_folder' in merged_inputs:
        _, node = run_get_node(process, inputs)
        return node

    current_manager = manager.get_manager()
    profile = current_manager.get_profile()

    if profile is not None and profile.process_control_backend == 'core.zmq':
        daemon_client = current_manager.get_daemon_client()
        # Note: ``is_daemon_running`` only checks for a PID file, so a stale PID from a crashed daemon will let this
        # check pass.
        if not daemon_client.is_daemon_running:
            msg = (
                'Cannot submit because the daemon is not running. The ZMQ broker is bundled into the daemon for this '
                'profile, so submission requires `verdi daemon start`. To run the process locally without the daemon '
                'instead, use `aiida.engine.run` (or `run_get_node`).'
            )
            raise InvalidOperation(msg)

    runner = current_manager.get_runner()

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

    if not process_inited.metadata.store_provenance:
        raise InvalidOperation('cannot submit a process with `store_provenance=False`')

    runner.persister.save_checkpoint(process_inited)
    process_inited.close()

    # Do not wait for the future's result, because in the case of a single worker this would cock-block itself
    runner.controller.continue_process(process_inited.pid, nowait=False, no_reply=True)
    node = process_inited.node

    if not wait:
        return node

    return _wait_for_process_termination(node, wait_interval=wait_interval, timeout=timeout)


def _wait_for_process_termination(node: ProcessNode, wait_interval: float, timeout: float | None = None) -> ProcessNode:
    """Block until ``node`` reaches a terminal state, polling its state every ``wait_interval`` seconds.

    :param node: the process node to wait for.
    :param wait_interval: the number of seconds to wait between checks of the process state.
    :param timeout: optional maximum number of seconds to wait. If the process does not terminate within this time, a
        ``TimeoutError`` is raised; the process is not cancelled and keeps being processed by the daemon. If ``None``,
        waits indefinitely. Assumed to be ``None`` or a positive number (validated by the caller).
    :return: the ``node``, once it has reached a terminal state.
    :raises ProcessTimeoutError: if ``timeout`` is set and the process does not terminate within it.
    """
    start_time = time.monotonic()

    while not node.is_terminated:
        elapsed = time.monotonic() - start_time

        if timeout is not None and elapsed >= timeout:
            msg = (
                f'Process<{node.pk}> did not terminate within the {timeout}s timeout '
                f'(current state: `{node.process_state}`). The timeout only stopped waiting; the process was not '
                f'cancelled and keeps being processed by the daemon. Use `verdi process status {node.pk}` to '
                f'monitor it or `verdi process kill {node.pk}` to stop it.'
            )
            raise ProcessTimeoutError(msg, node)

        # Never sleep past the deadline, so the timeout fires on time rather than overshooting by up to
        # ``wait_interval`` (relevant when ``timeout`` is smaller than, or not a multiple of, ``wait_interval``).
        wait = wait_interval if timeout is None else min(wait_interval, timeout - elapsed)
        LOGGER.report(
            f'Process<{node.pk}> has not yet terminated, current state is `{node.process_state}`. '
            f'Waiting for {wait:g} seconds.'
        )
        time.sleep(wait)

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
