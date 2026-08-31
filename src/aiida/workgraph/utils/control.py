from __future__ import annotations

import logging

from aiida import orm
from aiida.engine.processes import control
from aiida.manage import get_manager
from aiida.workgraph.enums import RuntimeInfoKey, TaskAction, TaskActionMessage, TaskState

LOGGER = logging.getLogger(__name__)


def create_task_action(
    pk: int,
    tasks: list,
    action: TaskAction = TaskAction.PAUSE,
):
    """Send task action to Process."""

    controller = get_manager().get_process_controller()
    # Send the canonical action value as a plain string; the engine re-validates it
    # into a TaskAction on receipt.
    message: TaskActionMessage = {'intent': 'custom', 'catalog': 'task', 'action': str(action), 'tasks': tasks}
    controller._communicator.rpc_send(pk, message)


def get_task_runtime_info(node, name: str, key: RuntimeInfoKey) -> str:
    """Get task state info from attributes."""
    from aiida.workgraph.orm.utils import deserialize_safe

    match key:
        case 'process':
            return deserialize_safe(node.task_processes.get(name, ''))
        case 'state':
            return node.task_states.get(name, '')
        case 'action':
            return node.task_actions.get(name, '')
        case _:
            raise ValueError(f'Invalid key: {key}')


def pause_tasks(pk: int, tasks: list[str], timeout: int = 5):
    """Pause task."""
    node = orm.load_node(pk)
    if node.is_finished:
        message = 'WorkGraph is finished. Cannot pause tasks.'
        LOGGER.warning(message)
        return False, message
    elif node.process_state.value.upper() in [
        'CREATED',
        'RUNNING',
        'WAITING',
        'PAUSED',
    ]:
        for name in tasks:
            if get_task_runtime_info(node, name, 'state') == TaskState.PLANNED:
                create_task_action(pk, tasks, action=TaskAction.PAUSE)
            elif get_task_runtime_info(node, name, 'state') == TaskState.RUNNING:
                try:
                    control.pause_processes(
                        [get_task_runtime_info(node, name, 'process')],
                        all_entries=None,
                        timeout=timeout,
                    )
                except Exception as e:
                    LOGGER.exception('Pause task %s failed: %s', name, e)
    return True, ''


def play_tasks(pk: int, tasks: list, timeout: int = 5):
    node = orm.load_node(pk)
    if node.is_finished:
        message = 'WorkGraph is finished. Cannot kill tasks.'
        LOGGER.warning(message)
        return False, message
    elif node.process_state.value.upper() in [
        'CREATED',
        'RUNNING',
        'WAITING',
        'PAUSED',
    ]:
        for name in tasks:
            state = get_task_runtime_info(node, name, 'state')
            if state == TaskState.PLANNED:
                create_task_action(pk, tasks, action=TaskAction.PLAY)
                break
            process = get_task_runtime_info(node, name, 'process')
            if process.is_finished:
                raise ValueError(f'Task {name} is already finished.')
            elif process.process_state.value.upper() in ['CREATED', 'WAITING']:
                try:
                    control.play_processes(
                        [process],
                        all_entries=None,
                        timeout=timeout,
                    )
                except Exception as e:
                    LOGGER.exception('Play task %s failed: %s', name, e)
    return True, ''


def kill_tasks(pk: int, tasks: list, timeout: int = 5):
    node = orm.load_node(pk)
    if node.is_finished:
        message = 'WorkGraph is finished. Cannot kill tasks.'
        LOGGER.warning(message)
        return False, message
    elif node.process_state.value.upper() in [
        'CREATED',
        'RUNNING',
        'WAITING',
        'PAUSED',
    ]:
        for name in tasks:
            state = get_task_runtime_info(node, name, 'state')
            process = get_task_runtime_info(node, name, 'process')
            if state == TaskState.PLANNED:
                create_task_action(pk, tasks, action=TaskAction.SKIP)
            # A live task to kill is either CREATED or RUNNING; WAITING/PAUSED are
            # AiiDA process states a *task* state never takes, so they were dead
            # entries in this list.
            elif state in {TaskState.CREATED, TaskState.RUNNING}:
                if process is None:
                    LOGGER.warning('Task %s is not an AiiDA process.', name)
                    create_task_action(pk, tasks, action=TaskAction.KILL)
                else:
                    try:
                        control.kill_processes(
                            [process],
                            all_entries=None,
                            timeout=timeout,
                        )
                    except Exception as e:
                        LOGGER.exception('Kill task %s failed: %s', name, e)
    return True, ''


def reset_tasks(pk: int, tasks: list) -> None:
    """Reset tasks
    Args:
        tasks (list): a list of task names.
    """
    node = orm.load_node(pk)
    if node.is_finished:
        message = 'WorkGraph is finished. Cannot kill tasks.'
        LOGGER.warning(message)
        return False, message
    elif node.process_state.value.upper() in [
        'CREATED',
        'RUNNING',
        'WAITING',
        'PAUSED',
    ]:
        for name in tasks:
            create_task_action(pk, tasks, action=TaskAction.RESET)

    return True, ''
