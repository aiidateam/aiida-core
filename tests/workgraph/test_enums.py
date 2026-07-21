###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the task-state and task-action enums.

These cover the behaviour the engine relies on: the human-facing string form
drops the ``TaskState.``/``TaskAction.`` prefix, only canonical values are
accepted, and the terminal-state set matches both enum members and bare strings.
"""

import pytest

from aiida.workgraph.enums import TERMINAL_TASK_STATES, TaskAction, TaskState


@pytest.mark.parametrize('enum_cls', [TaskState, TaskAction])
def test_str_and_format_drop_class_prefix(enum_cls):
    """``__str__``/f-strings must yield the bare value on every supported Python
    version, so report messages stay e.g. ``Action: RESET`` (test_workgraph)."""
    member = next(iter(enum_cls))
    assert str(member) == member.value
    assert f'{member}' == member.value


@pytest.mark.parametrize('enum_cls', [TaskState, TaskAction])
@pytest.mark.parametrize(
    'bad',
    [
        pytest.param('running', id='lowercased-state'),
        pytest.param('reset', id='lowercased-action'),
        pytest.param('nope', id='gibberish'),
        pytest.param('', id='empty'),
    ],
)
def test_construction_from_noncanonical_value_raises(enum_cls, bad):
    """Only the canonical uppercase values are valid; a typo or wrong case fails
    loud instead of silently never matching."""
    with pytest.raises(ValueError):
        enum_cls(bad)


@pytest.mark.parametrize(
    'state, terminal',
    [
        (TaskState.FINISHED, True),
        (TaskState.SKIPPED, True),
        (TaskState.FAILED, True),
        (TaskState.PLANNED, False),
        (TaskState.RUNNING, False),
        (TaskState.CREATED, False),
        (TaskState.READY, False),
        (TaskState.MAPPED, False),
    ],
)
def test_is_terminal(state, terminal):
    assert state.is_terminal is terminal


def test_terminal_set_matches_bare_strings_and_not_unset_default():
    """The engine checks ``stored_state in TERMINAL_TASK_STATES`` where the
    stored value is a bare string and the unset default is ``''``."""
    assert TERMINAL_TASK_STATES == frozenset({TaskState.FINISHED, TaskState.SKIPPED, TaskState.FAILED})
    for state in TERMINAL_TASK_STATES:
        assert state.value in TERMINAL_TASK_STATES  # hash-equality with bare strings
    assert '' not in TERMINAL_TASK_STATES
    assert TaskState.PLANNED not in TERMINAL_TASK_STATES
