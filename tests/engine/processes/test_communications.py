"""Tests for process communication helpers."""

import asyncio
from unittest.mock import Mock

import pytest

from aiida.brokers import communicator as broker_communicator
from aiida.brokers import futures as broker_futures
from aiida.common.processes import ProcessState
from aiida.engine.processes.communications import (
    LocalProcessController,
    RemoteProcessController,
    RemoteProcessThreadController,
)
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


def nested_future(result):
    """Return a future resolving to a future with ``result``."""
    result_future = broker_futures.Future()
    result_future.set_result(result)
    send_future = broker_futures.Future()
    send_future.set_result(result_future)
    return send_future


def test_remote_process_controller_rpc_methods():
    """The remote controller should send RPC messages and await their results."""
    communicator = Mock(spec=broker_communicator.Communicator)
    communicator.rpc_send.side_effect = [
        nested_future('status'),
        nested_future('paused'),
        nested_future('playing'),
        nested_future('killed'),
    ]
    controller = RemoteProcessController(communicator)

    async def control_process():
        assert await controller.get_status(1) == 'status'
        assert await controller.pause_process(2, 'pause') == 'paused'
        assert await controller.play_process(3) == 'playing'
        assert await controller.kill_process(4, 'kill', force_kill=True) == 'killed'

    asyncio.run(control_process())

    assert communicator.rpc_send.call_args_list == [
        ((1, {'intent': 'status', 'message': None}),),
        ((2, {'intent': 'pause', 'message': 'pause'}),),
        ((3, {'intent': 'play', 'message': None}),),
        ((4, {'intent': 'kill', 'message': 'kill', 'force_kill': True}),),
    ]


def test_remote_process_controller_continues_process():
    """The remote controller should send a continue task and await its result."""
    communicator = Mock(spec=broker_communicator.Communicator)
    communicator.task_send.return_value = nested_future('result')
    controller = RemoteProcessController(communicator)

    assert asyncio.run(controller.continue_process(1, tag='checkpoint', nowait=True)) == 'result'
    assert communicator.task_send.call_args.args == (
        {'task': 'continue', 'args': {'pid': 1, 'nowait': True, 'tag': 'checkpoint'}},
    )


def test_remote_process_controller_continues_process_without_reply():
    """The remote controller should support fire-and-forget continuation."""
    communicator = Mock(spec=broker_communicator.Communicator)
    communicator.task_send.return_value = None
    controller = RemoteProcessController(communicator)

    assert asyncio.run(controller.continue_process(1, no_reply=True)) is None
    assert communicator.task_send.call_args.kwargs == {'no_reply': True}


def test_remote_process_controller_launches_process():
    """The remote controller should send a launch task and await its result."""
    communicator = Mock(spec=broker_communicator.Communicator)
    communicator.task_send.return_value = nested_future('result')
    loader = Mock()
    loader.identify_object.return_value = 'tests:DummyProcess'
    controller = RemoteProcessController(communicator)

    assert (
        asyncio.run(controller.launch_process(object, (1,), {'key': 'value'}, persist=True, loader=loader)) == 'result'
    )
    assert communicator.task_send.call_args.args == (
        {
            'task': 'launch',
            'args': {
                'process_class': 'tests:DummyProcess',
                'persist': True,
                'nowait': False,
                'init_args': (1,),
                'init_kwargs': {'key': 'value'},
            },
        },
    )


def test_remote_process_controller_launches_process_without_reply():
    """The remote controller should support fire-and-forget launching."""
    communicator = Mock(spec=broker_communicator.Communicator)
    communicator.task_send.return_value = None
    loader = Mock()
    loader.identify_object.return_value = 'tests:DummyProcess'
    controller = RemoteProcessController(communicator)

    assert asyncio.run(controller.launch_process(object, loader=loader, no_reply=True)) is None
    assert communicator.task_send.call_args.kwargs == {'no_reply': True}


def test_remote_process_controller_executes_process():
    """The remote controller should create and then continue a process."""
    communicator = Mock(spec=broker_communicator.Communicator)
    communicator.task_send.side_effect = [nested_future(1), nested_future('result')]
    loader = Mock()
    loader.identify_object.return_value = 'tests:DummyProcess'
    controller = RemoteProcessController(communicator)

    assert (
        asyncio.run(controller.execute_process(object, (1,), {'key': 'value'}, loader=loader, nowait=True)) == 'result'
    )
    assert communicator.task_send.call_args_list == [
        (
            (
                {
                    'task': 'create',
                    'args': {
                        'process_class': 'tests:DummyProcess',
                        'persist': True,
                        'init_args': (1,),
                        'init_kwargs': {'key': 'value'},
                    },
                },
            ),
            {},
        ),
        (({'task': 'continue', 'args': {'pid': 1, 'nowait': True, 'tag': None}},), {'no_reply': False}),
    ]


def test_remote_process_controller_executes_process_without_reply():
    """The remote controller should support fire-and-forget execution."""
    communicator = Mock(spec=broker_communicator.Communicator)
    communicator.task_send.side_effect = [nested_future(1), None]
    loader = Mock()
    loader.identify_object.return_value = 'tests:DummyProcess'
    controller = RemoteProcessController(communicator)

    assert asyncio.run(controller.execute_process(object, loader=loader, no_reply=True)) is None
    assert communicator.task_send.call_args.kwargs == {'no_reply': True}


def test_execute_process_no_reply():
    """Test executing a process without a reply resolves the returned future."""
    create_future = broker_futures.Future()
    create_future.set_result(1)

    communicator = Mock(spec=broker_communicator.Communicator)
    communicator.task_send.side_effect = [create_future, None]

    loader = Mock()
    loader.identify_object.return_value = 'tests:DummyProcess'

    controller = RemoteProcessThreadController(communicator)
    execute_future = controller.execute_process(object, loader=loader, no_reply=True)

    assert execute_future.result() is None
    assert communicator.task_send.call_count == 2
    assert communicator.task_send.call_args_list[1].kwargs == {'no_reply': True}
