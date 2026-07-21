###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Enums used by WorkGraph."""

from __future__ import annotations

from enum import Enum, unique
from typing import Final, Literal, TypedDict

__all__ = (
    'TERMINAL_TASK_STATES',
    'RuntimeInfoKey',
    'TaskAction',
    'TaskActionMessage',
    'TaskState',
)


@unique
class TaskState(str, Enum):
    """Lifecycle state of a single task within a running WorkGraph."""

    PLANNED = 'PLANNED'
    READY = 'READY'
    CREATED = 'CREATED'
    RUNNING = 'RUNNING'
    FINISHED = 'FINISHED'
    FAILED = 'FAILED'
    SKIPPED = 'SKIPPED'
    MAPPED = 'MAPPED'

    def __str__(self) -> str:
        # Return the bare value ('RUNNING'), not 'TaskState.RUNNING', uniformly
        # across Python versions so reports and logs read naturally.
        return self.value

    @property
    def is_terminal(self) -> bool:
        """Whether the task has settled and will not transition further."""
        return self in TERMINAL_TASK_STATES


#: States a task does not transition out of; a task in any of these is "done" for
#: readiness and finished checks.
TERMINAL_TASK_STATES: Final[frozenset[TaskState]] = frozenset({TaskState.FINISHED, TaskState.SKIPPED, TaskState.FAILED})


@unique
class TaskAction(str, Enum):
    """Externally-triggered action requested on a task."""

    PAUSE = 'PAUSE'
    PLAY = 'PLAY'
    KILL = 'KILL'
    SKIP = 'SKIP'
    RESET = 'RESET'

    def __str__(self) -> str:
        return self.value


#: Keys addressing a task's runtime info on the process node, used as the dispatch
#: key in ``get_task_runtime_info`` / ``set_task_runtime_info``.
RuntimeInfoKey = Literal['process', 'state', 'action', 'execution_count', 'map_info']


class TaskActionMessage(TypedDict):
    """RPC payload sent to a running WorkGraph to act on its tasks.

    Built by ``create_task_action`` and consumed by ``apply_task_actions``.
    """

    intent: str
    catalog: str
    action: str
    tasks: list[str]
