"""Tests for process communication helpers."""

import asyncio
from unittest.mock import Mock

import pytest

from aiida.common.processes import ProcessState
from aiida.engine.processes.communications import LocalProcessController
from tests.utils import processes as test_processes


async def reach_waiting_state(process):
    """Wait for a process to enter the waiting state."""
    while process.state != ProcessState.WAITING:
        await asyncio.sleep(0.01)


def test_local_process_controller_kills_process(runner):
    """The local controller should kill a process running on its event loop."""
    process = runner.instantiate_process(test_processes.WaitProcess)
    controller = LocalProcessController(process, runner.loop)

    async def kill_process():
        task = asyncio.create_task(process.step_until_terminated())
        await asyncio.wait_for(reach_waiting_state(process), timeout=5)

        assert await controller.kill_process(process.pid, msg_text='Stopped by local controller') is True
        await asyncio.wait_for(task, timeout=5)

    runner.loop.run_until_complete(kill_process())

    assert process.node.is_killed
    assert process.node.process_status == 'Stopped by local controller'


def test_local_process_controller_pauses_and_plays_process(runner):
    """The local controller should pause and resume its process on its event loop."""
    process = runner.instantiate_process(test_processes.WaitProcess)
    controller = LocalProcessController(process, runner.loop)

    assert runner.loop.run_until_complete(controller.pause_process(process.pid)) is True
    assert process.paused

    assert runner.loop.run_until_complete(controller.play_process(process.pid)) is True
    assert not process.paused


@pytest.mark.parametrize('method', ('kill_process', 'pause_process', 'play_process'))
def test_local_process_controller_rejects_unknown_process(method):
    """The local controller should only control its process."""
    loop = asyncio.new_event_loop()
    process = Mock(pid=1)
    controller = LocalProcessController(process, loop)

    try:
        with pytest.raises(ValueError, match='is not controlled by this controller'):
            loop.run_until_complete(getattr(controller, method)(process.pid + 1))
    finally:
        loop.close()


@pytest.mark.parametrize('method', ('kill_process', 'pause_process', 'play_process'))
def test_local_process_controller_requires_own_event_loop(method):
    """The local controller should reject calls from another event loop."""
    loop = asyncio.new_event_loop()
    process = Mock(pid=1)
    controller = LocalProcessController(process, loop)

    try:
        with pytest.raises(RuntimeError, match='must be called from its event loop'):
            asyncio.run(getattr(controller, method)(process.pid))
    finally:
        loop.close()


@pytest.mark.parametrize('method', ('kill', 'pause'))
def test_local_process_controller_awaits_process_control(method, runner):
    """The local controller should await an asynchronous process response."""
    process = Mock(pid=1)

    async def result(*_):
        return False

    getattr(process, method).side_effect = result
    controller = LocalProcessController(process, runner.loop)

    assert runner.loop.run_until_complete(getattr(controller, f'{method}_process')(process.pid)) is False


def test_local_process_controller_returns_synchronous_play_result(runner):
    """The local controller should return a synchronous play response."""
    process = Mock(pid=1)
    process.play.return_value = False
    controller = LocalProcessController(process, runner.loop)

    assert runner.loop.run_until_complete(controller.play_process(process.pid)) is False
