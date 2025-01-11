import concurrent.futures
from asyncio import AbstractEventLoop
from typing import Generic, TypeVar, final

import kiwipy
from plumpy.exceptions import CoordinatorConnectionError
from plumpy.rmq.communications import convert_to_comm

__all__ = ['RmqCoordinator']

U = TypeVar('U', bound=kiwipy.Communicator)


@final
class RmqLoopCoordinator(Generic[U]):
    def __init__(self, comm: U, loop: AbstractEventLoop):
        self._comm = comm
        self._loop = loop

    @property
    def communicator(self) -> U:
        """The inner communicator."""
        return self._comm

    def add_rpc_subscriber(self, subscriber, identifier=None):
        subscriber = convert_to_comm(subscriber, self._loop)
        return self._comm.add_rpc_subscriber(subscriber, identifier)

    def add_broadcast_subscriber(
        self,
        subscriber,
        subject_filters=None,
        sender_filters=None,
        identifier=None,
    ):
        # XXX: this change behavior of create_task when decide whether the broadcast is_filtered.
        # Need to understand the BroadcastFilter and make the improvement.
        # To manifest the issue of run_task not await, run twice 'test_launch.py::test_submit_wait'.

        # subscriber = kiwipy.BroadcastFilter(subscriber)
        #
        # subject_filters = subject_filters or []
        # sender_filters = sender_filters or []
        #
        # for filter in subject_filters:
        #     subscriber.add_subject_filter(filter)
        # for filter in sender_filters:
        #     subscriber.add_sender_filter(filter)

        subscriber = convert_to_comm(subscriber, self._loop)
        return self._comm.add_broadcast_subscriber(subscriber, identifier)

    def add_task_subscriber(self, subscriber, identifier=None):
        subscriber = convert_to_comm(subscriber, self._loop)
        return self._comm.add_task_subscriber(subscriber, identifier)

    def remove_rpc_subscriber(self, identifier):
        return self._comm.remove_rpc_subscriber(identifier)

    def remove_broadcast_subscriber(self, identifier):
        return self._comm.remove_broadcast_subscriber(identifier)

    def remove_task_subscriber(self, identifier):
        return self._comm.remove_task_subscriber(identifier)

    def rpc_send(self, recipient_id, msg):
        return self._comm.rpc_send(recipient_id, msg)

    def broadcast_send(
        self,
        body,
        sender=None,
        subject=None,
        correlation_id=None,
    ):
        from aio_pika.exceptions import AMQPConnectionError, ChannelInvalidStateError

        try:
            rsp = self._comm.broadcast_send(body, sender, subject, correlation_id)
        except (ChannelInvalidStateError, AMQPConnectionError, concurrent.futures.TimeoutError) as exc:
            raise CoordinatorConnectionError from exc
        else:
            return rsp

    def task_send(self, task, no_reply=False):
        return self._comm.task_send(task, no_reply)

    def close(self):
        self._comm.close()

    def is_closed(self) -> bool:
        """Return `True` if the communicator was closed"""
        return self._comm.is_closed()
