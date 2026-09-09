"""Tests for process communication helpers."""

from unittest.mock import Mock

from aiida.brokers import communicator as broker_communicator
from aiida.brokers import futures as broker_futures
from aiida.engine.processes.communications import RemoteProcessThreadController


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
