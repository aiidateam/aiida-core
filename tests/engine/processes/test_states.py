"""Tests for process states and commands."""

from unittest.mock import Mock

import yaml

from aiida.engine.processes import persistence
from aiida.engine.processes.states import Continue, Excepted, ProcessState, Running


def test_excepted_state_restores_formatted_traceback():
    """Test persisted tracebacks are restored as formatted text without a live traceback."""

    def create_exception():
        try:
            raise ValueError('failure')
        except ValueError as exception:
            return exception

    exception = create_exception()
    state = Excepted(Mock(), exception, exception.__traceback__)
    saved_state = {
        'in_state': False,
        Excepted.EXC_VALUE: yaml.dump(exception),
        Excepted.TRACEBACK: state.traceback_string,
    }
    load_context = persistence.LoadSaveContext(loader=Mock(), process=Mock())

    restored = Excepted.recreate_from(saved_state, load_context)

    assert restored.traceback is None
    assert restored.traceback_string == state.traceback_string


def test_continue_forwards_keyword_arguments():
    """Test a continue command forwards positional and keyword arguments."""

    def continue_fn(*args, **kwargs):
        pass

    running = Running.__new__(Running)
    running.create_state = Mock()
    command = Continue(continue_fn, 'value', keyword='value')

    running._action_command(command)

    running.create_state.assert_called_once_with(ProcessState.RUNNING, continue_fn, 'value', keyword='value')
