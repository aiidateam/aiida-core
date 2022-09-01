# -*- coding: utf-8 -*-
"""Tests for the :mod:`aiida.engine.processes.control` module."""
import pytest

from aiida.engine.daemon.client import DaemonException
from aiida.engine.processes import control
from tests.utils.processes import WaitProcess


@pytest.mark.usefixtures('started_daemon_client')
@pytest.mark.parametrize('action', (control.pause_processes, control.play_processes, control.kill_processes))
def test_processes_all_exclusivity(submit_and_await, action):
    """Test that control methods raise if both ``processes`` is specified and ``all_entries=True``."""
    node = submit_and_await(WaitProcess)
    assert not node.paused

    with pytest.raises(ValueError, match='cannot specify processes when `all_entries = True`.'):
        action([node], all_entries=True)


@pytest.mark.usefixtures('stopped_daemon_client')
@pytest.mark.parametrize('action', (control.pause_processes, control.play_processes, control.kill_processes))
def test_daemon_not_running(action):
    """Test that control methods raise if the daemon is not running."""
    with pytest.raises(DaemonException, match='The daemon is not running.'):
        action(all_entries=True)


@pytest.mark.usefixtures('started_daemon_client')
def test_pause_processes(submit_and_await):
    """Test :func:`aiida.engine.processes.control.pause_processes`."""
    node = submit_and_await(WaitProcess)
    assert not node.paused

    control.pause_processes([node], wait=True)
    assert node.paused


@pytest.mark.usefixtures('started_daemon_client')
def test_pause_processes_all_entries(submit_and_await):
    """Test :func:`aiida.engine.processes.control.pause_processes` with ``all_entries=True``."""
    node = submit_and_await(WaitProcess)
    assert not node.paused

    control.pause_processes(all_entries=True, wait=True)
    assert node.paused


@pytest.mark.usefixtures('started_daemon_client')
def test_play_processes(submit_and_await):
    """Test :func:`aiida.engine.processes.control.play_processes`."""
    node = submit_and_await(WaitProcess)
    assert not node.paused

    control.pause_processes([node], wait=True)
    assert node.paused

    control.play_processes([node], wait=True)
    assert not node.paused


@pytest.mark.usefixtures('started_daemon_client')
def test_play_processes_all_entries(submit_and_await):
    """Test :func:`aiida.engine.processes.control.play_processes` with ``all_entries=True``."""
    node = submit_and_await(WaitProcess)
    assert not node.paused

    control.pause_processes([node], wait=True)
    assert node.paused

    control.play_processes(all_entries=True, wait=True)
    assert not node.paused


@pytest.mark.usefixtures('started_daemon_client')
def test_kill_processes(submit_and_await):
    """Test :func:`aiida.engine.processes.control.kill_processes`."""
    node = submit_and_await(WaitProcess)

    control.kill_processes([node], wait=True)
    assert node.is_terminated
    assert node.is_killed


@pytest.mark.usefixtures('started_daemon_client')
def test_kill_processes_all_entries(submit_and_await):
    """Test :func:`aiida.engine.processes.control.kill_processes` with ``all_entries=True``."""
    node = submit_and_await(WaitProcess)

    control.kill_processes(all_entries=True, wait=True)
    assert node.is_terminated
    assert node.is_killed
