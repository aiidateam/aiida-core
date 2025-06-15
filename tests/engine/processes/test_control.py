"""Tests for the :mod:`aiida.engine.processes.control` module."""

import pytest
from plumpy.process_comms import RemoteProcessThreadController

from aiida.engine import ProcessState
from aiida.engine.launch import submit
from aiida.engine.processes import control
from aiida.orm import Int
from tests.utils.processes import WaitProcess


@pytest.mark.usefixtures('aiida_profile_clean', 'started_daemon_client')
@pytest.mark.parametrize('action', (control.pause_processes, control.play_processes, control.kill_processes))
def test_processes_all_exclusivity(submit_and_await, action):
    """Test that control methods raise if both ``processes`` is specified and ``all_entries=True``."""
    node = submit_and_await(WaitProcess, ProcessState.WAITING)
    assert not node.paused

    with pytest.raises(ValueError, match='cannot specify processes when `all_entries = True`.'):
        action([node], all_entries=True)


@pytest.mark.usefixtures('aiida_profile_clean', 'stopped_daemon_client')
@pytest.mark.parametrize('action', (control.pause_processes, control.play_processes, control.kill_processes))
def test_daemon_not_running(action, caplog):
    """Test that control methods warns if the daemon is not running."""
    action(all_entries=True)
    assert 'The daemon is not running' in caplog.records[0].message


@pytest.mark.usefixtures('aiida_profile_clean', 'started_daemon_client')
def test_pause_processes(submit_and_await):
    """Test :func:`aiida.engine.processes.control.pause_processes`."""
    node = submit_and_await(WaitProcess, ProcessState.WAITING)
    assert not node.paused

    control.pause_processes([node], timeout=float('inf'))
    assert node.paused
    assert node.process_status == 'Paused through `aiida.engine.processes.control.pause_processes`'


@pytest.mark.usefixtures('aiida_profile_clean', 'started_daemon_client')
def test_pause_processes_all_entries(submit_and_await):
    """Test :func:`aiida.engine.processes.control.pause_processes` with ``all_entries=True``."""
    node = submit_and_await(WaitProcess, ProcessState.WAITING)
    assert not node.paused

    control.pause_processes(all_entries=True, timeout=float('inf'))
    assert node.paused


@pytest.mark.usefixtures('aiida_profile_clean', 'started_daemon_client')
def test_play_processes(submit_and_await):
    """Test :func:`aiida.engine.processes.control.play_processes`."""
    node = submit_and_await(WaitProcess, ProcessState.WAITING)
    assert not node.paused

    control.pause_processes([node], timeout=float('inf'))
    assert node.paused

    control.play_processes([node], timeout=float('inf'))
    assert not node.paused


@pytest.mark.usefixtures('aiida_profile_clean', 'started_daemon_client')
def test_play_processes_all_entries(submit_and_await):
    """Test :func:`aiida.engine.processes.control.play_processes` with ``all_entries=True``."""
    node = submit_and_await(WaitProcess, ProcessState.WAITING)
    assert not node.paused

    control.pause_processes([node], timeout=float('inf'))
    assert node.paused

    control.play_processes(all_entries=True, timeout=float('inf'))
    assert not node.paused


@pytest.mark.usefixtures('aiida_profile_clean', 'started_daemon_client')
def test_kill_processes(submit_and_await):
    """Test :func:`aiida.engine.processes.control.kill_processes`."""
    node = submit_and_await(WaitProcess, ProcessState.WAITING)

    control.kill_processes([node], timeout=float('inf'))
    assert node.is_terminated
    assert node.is_killed
    assert node.process_status == 'Killed through `aiida.engine.processes.control.kill_processes`'


@pytest.mark.usefixtures('aiida_profile_clean', 'started_daemon_client')
def test_kill_processes_all_entries(submit_and_await):
    """Test :func:`aiida.engine.processes.control.kill_processes` with ``all_entries=True``."""
    node = submit_and_await(WaitProcess, ProcessState.WAITING)

    control.kill_processes(all_entries=True, timeout=float('inf'))
    assert node.is_terminated
    assert node.is_killed


@pytest.mark.usefixtures('aiida_profile_clean', 'started_daemon_client')
def test_revive(monkeypatch, aiida_code_installed, submit_and_await):
    """Test :func:`aiida.engine.processes.control.revive_processes`."""
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    builder = code.get_builder()
    builder.x = Int(1)
    builder.y = Int(1)
    builder.metadata.options.resources = {'num_machines': 1}

    # Temporarily patch the ``RemoteProcessThreadController.continue_process`` method to do nothing and just return a
    # completed future. This ensures that the submission creates a process node in the database but no task is sent to
    # RabbitMQ and so the daemon will not start running it.
    with monkeypatch.context() as context:
        context.setattr(RemoteProcessThreadController, 'continue_process', lambda *args, **kwargs: None)
        node = submit(builder)

    # The node should now be created in the database but "stuck"
    assert node.process_state == ProcessState.CREATED

    # Time to revive it by recreating the task and send it to RabbitMQ
    control.revive_processes([node])

    # Wait for the process to be picked up by the daemon and completed. If there is a problem with the code, this call
    # should timeout and raise an exception
    submit_and_await(node)
    assert node.is_finished_ok
