from __future__ import annotations

from collections.abc import Callable

from typing_extensions import assert_never

from aiida.workgraph.enums import TaskAction, TaskActionMessage, TaskState


class TaskActionManager:
    """
    Handles externally-triggered task actions (RESET, PAUSE, PLAY, SKIP, KILL)
    to change task states or runtime behavior.
    """

    def __init__(self, state_manager, logger, process):
        """
        :param state_manager: A reference to TaskStateManager for updating states.
        :param logger: A logger instance.
        """
        self.state_manager = state_manager
        self.logger = logger
        self.process = process

    def apply_task_actions(self, msg: TaskActionMessage) -> None:
        """
        Apply task actions to the workgraph based on user or external messages.

        :raises ValueError: if the message carries an unknown task action.
        """
        action = TaskAction(msg['action'].upper())
        tasks = msg['tasks']
        self.process.report(f'Action: {action}. Tasks: {tasks}')

        # Each action maps to a callable that takes a single task name.
        handler: Callable[[str], None]
        match action:
            case TaskAction.RESET:
                handler = self.state_manager.reset_task
            case TaskAction.PAUSE:
                handler = self.pause_task
            case TaskAction.PLAY:
                handler = self.play_task
            case TaskAction.SKIP:
                handler = self.skip_task
            case TaskAction.KILL:
                handler = self.kill_task
            case _:
                assert_never(action)
        for name in tasks:
            handler(name)

    def pause_task(self, name: str) -> None:
        """Mark the task to be paused."""
        self.state_manager.set_task_runtime_info(name, 'action', TaskAction.PAUSE)
        self.process.report(f'Task {name} action: PAUSE.')

    def play_task(self, name: str) -> None:
        """Remove the PAUSE action on a task."""
        self.state_manager.set_task_runtime_info(name, 'action', '')
        self.process.report(f'Task {name} action: PLAY.')

    def skip_task(self, name: str) -> None:
        """Force a task to be SKIPPED."""
        self.state_manager.set_task_runtime_info(name, 'state', TaskState.SKIPPED)
        self.process.report(f'Task {name} action: SKIP.')

    def kill_task(self, name: str) -> None:
        """KILL a running task.
        This is not needed for task with AiiDA process, because one can kill the AiiDA process directly.
        """
