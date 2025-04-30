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
    processes: list[ProcessNode] | None = None, *, all_entries: bool = False, timeout: float = 5.0, wait: bool = False
) -> None:
    """Play (unpause) paused processes.

    .. note:: Requires the daemon to be running, or processes will be unresponsive.

    :param processes: List of processes to play.
    :param all_entries: Play all paused processes.
    :param timeout: Raise a ``ProcessTimeoutException`` if the process does not respond within this amount of seconds.
    :param wait: Set to ``True`` to wait for process response, for ``False`` the action is fire-and-forget.
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
    _perform_actions(processes, controller.play_process, 'play', 'playing', timeout, wait)


def pause_processes(
    processes: list[ProcessNode] | None = None,
    *,
    msg_text: str = 'Paused through `aiida.engine.processes.control.pause_processes`',
    all_entries: bool = False,
    timeout: float = 5.0,
    wait: bool = False,
) -> None:
    """Pause running processes.

    .. note:: Requires the daemon to be running, or processes will be unresponsive.

    :param processes: List of processes to play.
    :param all_entries: Pause all playing processes.
    :param timeout: Raise a ``ProcessTimeoutException`` if the process does not respond within this amount of seconds.
    :param wait: Set to ``True`` to wait for process response, for ``False`` the action is fire-and-forget.
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
    _perform_actions(processes, action, 'pause', 'pausing', timeout, wait)


def kill_processes(
    processes: list[ProcessNode] | None = None,
    *,
    msg_text: str = 'Killed through `aiida.engine.processes.control.kill_processes`',
    force_kill: bool = False,
    all_entries: bool = False,
    timeout: float = 5.0,
    wait: bool = False,
) -> None:
    """Kill running processes.

    .. note:: Requires the daemon to be running, or processes will be unresponsive.

    :param processes: List of processes to play.
    :param all_entries: Kill all active processes.
    :param timeout: Raise a ``ProcessTimeoutException`` if the process does not respond within this amount of seconds.
    :param wait: Set to ``True`` to wait for process response, for ``False`` the action is fire-and-forget.
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
    action = functools.partial(controller.kill_process, msg_text=msg_text, force_kill=force_kill)
    _perform_actions(processes, action, 'kill', 'killing', timeout, wait)


def _perform_actions(
    processes: list[ProcessNode],
    action: t.Callable,
    infinitive: str,
    present: str,
    timeout: t.Optional[float] = None,
    wait: bool = False,
    **kwargs: t.Any,
) -> None:
    """Perform an action on a list of processes.

    :param processes: The list of processes to perform the action on.
    :param action: The action to perform.
    :param infinitive: The infinitive of the verb that represents the action.
    :param present: The present tense of the verb that represents the action.
    :param past: The past tense of the verb that represents the action.
    :param timeout: Raise a ``ProcessTimeoutException`` if the process does not respond within this amount of seconds.
    :param wait: Set to ``True`` to wait for process response, for ``False`` the action is fire-and-forget.
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
        except communications.UnroutableError:
            LOGGER.error(f'Process<{process.pk}> is unreachable.')
        else:
            futures[future] = process

    _resolve_futures(futures, infinitive, present, wait, timeout)


def _resolve_futures(
    futures: dict[concurrent.futures.Future, ProcessNode],
    infinitive: str,
    present: str,
    wait: bool = False,
    timeout: t.Optional[float] = None,
) -> None:
    """Process a mapping of futures representing an action on an active process.

    This function will echo the correct information strings based on the outcomes of the futures and the given verb
    conjugations. You can optionally wait for any pending actions to be completed before the functions returns and use a
    timeout to put a maximum wait time on the actions.

    :param futures: The map of action futures and the corresponding processes.
    :param infinitive: The infinitive form of the action verb.
    :param present: The present tense form of the action verb.
    :param wait: Set to ``True`` to wait for process response, for ``False`` the action is fire-and-forget.
    :param timeout: Raise a ``ProcessTimeoutException`` if the process does not respond within this amount of seconds.
    """
    scheduled = {}

    def handle_result(result):
        if result is True:
            LOGGER.report(f'request to {infinitive} Process<{process.pk}> sent')
        elif result is False:
            LOGGER.error(f'problem {present} Process<{process.pk}>')
        elif isinstance(result, kiwipy.Future):
            LOGGER.report(f'scheduled {infinitive} Process<{process.pk}>')
            scheduled[result] = process
        else:
            LOGGER.error(f'got unexpected response when {present} Process<{process.pk}>: {result}')

    try:
        for future, process in futures.items():
            # unwrap is need here since LoopCommunicator will also wrap a future
            unwrapped = unwrap_kiwi_future(future)
            try:
                result = unwrapped.result(timeout=timeout)
            except communications.TimeoutError:
                cancelled = unwrapped.cancel()
                if cancelled:
                    LOGGER.error(f'call to {infinitive} Process<{process.pk}> timed out and was cancelled.')
                else:
                    LOGGER.error(f'call to {infinitive} Process<{process.pk}> timed out but could not be cancelled.')
            except Exception as exception:
                LOGGER.error(f'failed to {infinitive} Process<{process.pk}>: {exception}')
            else:
                if isinstance(result, kiwipy.Future):
                    LOGGER.report(f'scheduled {infinitive} Process<{process.pk}>')
                    scheduled[result] = process
                else:
                    handle_result(result)

        if not wait or not scheduled:
            return

        LOGGER.report(f"waiting for process(es) {','.join([str(proc.pk) for proc in scheduled.values()])}")

        for future in concurrent.futures.as_completed(scheduled.keys(), timeout=timeout):
            process = scheduled[future]

            try:
                result = future.result()
            except Exception as exception:
                LOGGER.error(f'failed to {infinitive} Process<{process.pk}>: {exception}')
            else:
                handle_result(result)

    except concurrent.futures.TimeoutError:
        raise ProcessTimeoutException(
            f'timed out trying to {infinitive} processes {futures.values()}\n'
            'This could be because the daemon workers are too busy to respond, please try again later.\n'
            'If the problem persists, make sure the daemon and RabbitMQ are running properly by restarting them.\n'
            'If the processes remain unresponsive, as a last resort, try reviving them with ``revive_processes``.'
        )
