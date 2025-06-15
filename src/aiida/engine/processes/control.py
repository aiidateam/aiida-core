"""Functions to control and interact with running processes."""

from __future__ import annotations

import collections
import concurrent
import functools
import typing as t

import kiwipy
from kiwipy import communications
from plumpy.futures import unwrap_kiwi_future

from aiida.brokers import Broker
from aiida.common.exceptions import AiidaException
from aiida.common.log import AIIDA_LOGGER
from aiida.engine.daemon.client import DaemonException, get_daemon_client
from aiida.manage.manager import get_manager
from aiida.orm import ProcessNode, QueryBuilder
from aiida.tools.query.calculation import CalculationQueryBuilder

LOGGER = AIIDA_LOGGER.getChild('process_control')


class ProcessTimeoutException(AiidaException):
    """Raised when action to communicate with a process times out."""


def get_active_processes(paused: bool = False, project: str | list[str] = '*') -> list[ProcessNode] | list[t.Any]:
    """Return all active processes, i.e., those with a process state of created, waiting or running.

    :param paused: Boolean, if True, filter for processes that are paused.
    :param project: Single or list of properties to project. By default projects the entire node.
    :return: A list of process nodes of active processes.
    """
    filters = CalculationQueryBuilder().get_filters(process_state=('created', 'waiting', 'running'), paused=paused)
    builder = QueryBuilder().append(ProcessNode, filters=filters, project=project)
    return builder.all(flat=True)


def iterate_process_tasks(broker: Broker) -> collections.abc.Iterator[kiwipy.rmq.RmqIncomingTask]:
    """Return the list of process pks that have a process task in the RabbitMQ process queue.

    :returns: A list of process pks that have a corresponding process task with RabbitMQ.
    """
    for task in broker.iterate_tasks():
        yield task


def get_process_tasks(broker: Broker) -> list[int]:
    """Return the list of process pks that have a process task in the RabbitMQ process queue.

    :returns: A list of process pks that have a corresponding process task with RabbitMQ.
    """
    pks = []

    for task in iterate_process_tasks(broker):
        try:
            pks.append(task.body.get('args', {})['pid'])
        except KeyError:
            pass

    return pks


def revive_processes(processes: list[ProcessNode], *, wait: bool = False) -> None:
    """Revive processes that seem stuck and are no longer reachable.

    Warning: Use only as a last resort after you've gone through the checklist below.

        1. Does ``verdi status`` indicate that both daemon and RabbitMQ are running properly?
           If not, restart the daemon with ``verdi daemon restart`` and restart RabbitMQ.
        2. Try to play the process through ``play_processes``.
           If a ``ProcessTimeoutException`` is raised use this method to attempt to revive it.

    Details: When RabbitMQ loses the process task before the process has completed, the process is never picked up by
    the daemon and will remain "stuck". This method recreates the task, which can lead to multiple instances of the task
    being executed and should thus be used with caution.

    .. note:: Requires the daemon to be running.

    :param processes: List of processes to revive.
    :param wait: Set to ``True`` to wait for a response, for ``False`` the action is fire-and-forget.
    """
    if not get_daemon_client().is_daemon_running:
        raise DaemonException('The daemon is not running.')

    process_controller = get_manager().get_process_controller()

    for process in processes:
        future = process_controller.continue_process(process.pk, nowait=not wait, no_reply=False)

        if future:
            response = future.result()  # type: ignore[union-attr]
        else:
            response = None

        if response and response.done():
            LOGGER.info(f'Message to continue Process<{process.pk}> received successfully.')
        elif response:
            LOGGER.warning(f'Failed to deliver message to Process<{process.pk}>: {response}|{response.exception()}')
        else:
            LOGGER.warning(f'No response when trying to continue Process<{process.pk}>, try resetting the daemon.')


def play_processes(
    processes: list[ProcessNode] | None = None, *, all_entries: bool = False, timeout: float = 5.0
) -> None:
    """Play (unpause) paused processes.

    .. note:: Requires the daemon to be running, or processes will be unresponsive.

    :param processes: List of processes to play.
    :param all_entries: Play all paused processes.
    :param timeout: Raise a ``ProcessTimeoutException`` if the process does not respond within this amount of seconds.
    :raises ``ProcessTimeoutException``: If the processes do not respond within the timeout.
    """
    if not get_daemon_client().is_daemon_running:
        LOGGER.warning('The daemon is not running, so processes submitted to the daemon are not reachable.')

    if processes and all_entries:
        raise ValueError('cannot specify processes when `all_entries = True`.')

    if not processes and all_entries:
        processes = get_active_processes(paused=True)

    if not processes:
        LOGGER.report('no active processes selected.')
        return

    controller = get_manager().get_process_controller()
    _perform_actions(processes, controller.play_process, 'play', 'playing', timeout)


def pause_processes(
    processes: list[ProcessNode] | None = None,
    *,
    msg_text: str = 'Paused through `aiida.engine.processes.control.pause_processes`',
    all_entries: bool = False,
    timeout: float = 5.0,
) -> None:
    """Pause running processes.

    .. note:: Requires the daemon to be running, or processes will be unresponsive.

    :param processes: List of processes to play.
    :param all_entries: Pause all playing processes.
    :param timeout: Raise a ``ProcessTimeoutException`` if the process does not respond within this amount of seconds.
    :raises ``ProcessTimeoutException``: If the processes do not respond within the timeout.
    """
    if not get_daemon_client().is_daemon_running:
        LOGGER.warning('The daemon is not running, so processes submitted to the daemon are not reachable.')

    if processes and all_entries:
        raise ValueError('cannot specify processes when `all_entries = True`.')

    if not processes and all_entries:
        processes = get_active_processes()

    if not processes:
        LOGGER.report('no active processes selected.')
        return

    controller = get_manager().get_process_controller()
    action = functools.partial(controller.pause_process, msg_text=msg_text)
    _perform_actions(processes, action, 'pause', 'pausing', timeout)


def kill_processes(
    processes: list[ProcessNode] | None = None,
    *,
    msg_text: str = 'Killed through `aiida.engine.processes.control.kill_processes`',
    force: bool = False,
    all_entries: bool = False,
    timeout: float = 5.0,
) -> None:
    """Kill running processes.

    .. note:: Requires the daemon to be running, or processes will be unresponsive.

    :param processes: List of processes to play.
    :param all_entries: Kill all active processes.
    :param timeout: Raise a ``ProcessTimeoutException`` if the process does not respond within this amount of seconds.
    :raises ``ProcessTimeoutException``: If the processes do not respond within the timeout.
    """
    if not get_daemon_client().is_daemon_running:
        LOGGER.warning('The daemon is not running, so processes submitted to the daemon are not reachable.')

    if processes and all_entries:
        raise ValueError('cannot specify processes when `all_entries = True`.')

    if not processes and all_entries:
        processes = get_active_processes()

    if not processes:
        LOGGER.report('no active processes selected.')
        return

    controller = get_manager().get_process_controller()
    action = functools.partial(controller.kill_process, msg_text=msg_text, force_kill=force)
    _perform_actions(processes, action, 'kill', 'killing', timeout)


def _perform_actions(
    processes: list[ProcessNode],
    action: t.Callable,
    infinitive: str,
    present: str,
    timeout: t.Optional[float] = None,
    **kwargs: t.Any,
) -> None:
    """Perform an action on a list of processes.

    :param processes: The list of processes to perform the action on.
    :param action: The action to perform.
    :param infinitive: The infinitive of the verb that represents the action.
    :param present: The present tense of the verb that represents the action.
    :param past: The past tense of the verb that represents the action.
    :param timeout: Raise a ``ProcessTimeoutException`` if the process does not respond within this amount of seconds.
    :param kwargs: Keyword arguments that will be passed to the method ``action``.
    :raises ``ProcessTimeoutException``: If the processes do not respond within the timeout.
    """
    futures = {}

    for process in processes:
        if process.is_terminated:
            LOGGER.error(f'Process<{process.pk}> is already terminated.')
            continue

        try:
            future = action(process.pk, **kwargs)
            LOGGER.report(f'Request to {infinitive} Process<{process.pk}> sent.')
        except communications.UnroutableError:
            LOGGER.error(f'Process<{process.pk}> is unreachable.')
        else:
            futures[future] = process

    _resolve_futures(futures, infinitive, present, timeout)


def _resolve_futures(
    futures: dict[concurrent.futures.Future, ProcessNode],
    infinitive: str,
    present: str,
    timeout: t.Optional[float] = None,
) -> None:
    """Process a mapping of futures representing an action on an active process.

    This function will echo the correct information strings based on the outcomes of the futures and the given verb
    conjugations. The function waits for any pending actions to be completed. By specifying a timeout the function
    aborts after the specified time and cancels pending actions.

    :param futures: The map of action futures and the corresponding processes.
    :param infinitive: The infinitive form of the action verb.
    :param present: The present tense form of the action verb.
    :param timeout: If None or float('inf') it waits until the actions are completed otherwise it waits for response the
        amount in seconds.
    """
    if not timeout or not futures:
        if futures:
            LOGGER.report(
                f"Request to {infinitive} process(es) {','.join([str(proc.pk) for proc in futures.values()])}"
                ' sent. Skipping waiting for response.'
            )
        return

    LOGGER.report(f"Waiting for process(es) {','.join([str(proc.pk) for proc in futures.values()])}.")

    # Ensure that when futures are only are completed if they return an actual value (not a future)
    unwrapped_futures = {unwrap_kiwi_future(future): process for future, process in futures.items()}
    try:
        # future does not interpret float('inf') correctly by changing it to None we get the intended behavior
        for future in concurrent.futures.as_completed(
            unwrapped_futures.keys(), timeout=None if timeout == float('inf') else timeout
        ):
            process = unwrapped_futures[future]
            try:
                result = future.result()
            except Exception as exception:
                LOGGER.error(f'Failed to {infinitive} Process<{process.pk}>: {exception}')
            else:
                if result is True:
                    LOGGER.report(f'Request to {infinitive} Process<{process.pk}> processed.')
                elif result is False:
                    LOGGER.error(f'Problem {present} Process<{process.pk}>')
                else:
                    LOGGER.error(f'Got unexpected response when {present} Process<{process.pk}>: {result}')
    except concurrent.futures.TimeoutError:
        # We cancel the tasks that are not done
        undone_futures = {future: process for future, process in unwrapped_futures.items() if not future.done()}
        if not undone_futures:
            LOGGER.error(f'Call to {infinitive} timed out but already done.')
        for future, process in undone_futures.items():
            if not future.done():
                cancelled = future.cancel()
                if cancelled:
                    LOGGER.error(f'Call to {infinitive} Process<{process.pk}> timed out and was cancelled.')
                else:
                    LOGGER.error(f'Call to {infinitive} Process<{process.pk}> timed out but could not be cancelled.')
