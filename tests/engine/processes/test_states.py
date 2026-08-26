"""Tests for process states and commands."""

from unittest.mock import Mock

from aiida.engine.processes.states import Continue, ProcessState, Running


def test_continue_forwards_keyword_arguments():
    """Test a continue command forwards positional and keyword arguments."""

    def continue_fn(*args, **kwargs):
        pass

    running = Running.__new__(Running)
    running.create_state = Mock()
    command = Continue(continue_fn, 'value', keyword='value')

    running._action_command(command)

    running.create_state.assert_called_once_with(ProcessState.RUNNING, continue_fn, 'value', keyword='value')
