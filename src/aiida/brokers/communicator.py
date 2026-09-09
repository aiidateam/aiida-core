###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
#                                                                         #
# Portions of this file are derived from kiwipy.                          #
# Copyright (c), 2022, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE          #
# (Theory and Simulation of Materials (THEOS) and National Centre for    #
# Computational Design and Discovery of Novel Materials (NCCR MARVEL)), #
# Switzerland and ROBERT BOSCH LLC, USA. All rights reserved.            #
#                                                                         #
# The kiwipy license is reproduced in open_source_licenses.txt.          #
###########################################################################
"""Communicator interface for message-based communication."""

from __future__ import annotations

import abc
from collections.abc import Callable
from types import TracebackType
from typing import Any

from aiida.brokers import futures

__all__ = ('Communicator',)

# RPC subscriber params: communicator, msg
RpcSubscriber = Callable[['Communicator', Any], Any]
# Task subscriber params: communicator, task
TaskSubscriber = Callable[['Communicator', Any], Any]
# Broadcast subscribers params: communicator, body, sender, subject, correlation id
BroadcastSubscriber = Callable[['Communicator', Any, Any, Any, Any], Any]


class Communicator:
    """The interface for a communicator used to both send and receive various types of message."""

    def __enter__(self) -> Communicator:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    @abc.abstractmethod
    def is_closed(self) -> bool:
        """Return ``True`` if the communicator was closed."""

    @abc.abstractmethod
    def close(self) -> None:
        """Close a communicator, free up all resources and do not allow any further operations."""

    @abc.abstractmethod
    def add_rpc_subscriber(self, subscriber: RpcSubscriber, identifier: Any | None = None) -> Any:
        """Add an RPC subscriber to the communicator with an optional identifier."""

    @abc.abstractmethod
    def remove_rpc_subscriber(self, identifier: Any) -> None:
        """Remove an RPC subscriber given the identifier.

        :param identifier: The RPC subscriber identifier.
        """

    @abc.abstractmethod
    def add_task_subscriber(self, subscriber: TaskSubscriber, identifier: Any | None = None) -> Any:
        """Add a task subscriber to the communicator's default queue. Returns the identifier.

        :param subscriber: The task callback function.
        :param identifier: The subscriber identifier.
        """

    @abc.abstractmethod
    def remove_task_subscriber(self, identifier: Any) -> None:
        """Remove a task subscriber from the communicator's default queue.

        :param identifier: The subscriber to remove.
        """

    @abc.abstractmethod
    def add_broadcast_subscriber(self, subscriber: BroadcastSubscriber, identifier: Any | None = None) -> Any:
        """Add a broadcast subscriber that will receive all broadcast messages.

        :param subscriber: The subscriber function to be called.
        :param identifier: An optional identifier for the subscriber.
        :return: An identifier for the subscriber that can be subsequently used to remove it.
        """

    @abc.abstractmethod
    def remove_broadcast_subscriber(self, identifier: Any) -> None:
        """Remove a broadcast subscriber.

        :param identifier: The identifier of the subscriber to remove.
        """

    @abc.abstractmethod
    def task_send(self, task: Any, no_reply: bool = False) -> futures.Future[Any] | None:
        """Send a task message, queued and picked up by a worker at some point in the future.

        :param task: The task message.
        :param no_reply: Do not send a reply containing the result of the task.
        :return: A future corresponding to the outcome of the task, or ``None`` if ``no_reply`` is ``True``.
        """

    @abc.abstractmethod
    def rpc_send(self, recipient_id: Any, msg: Any) -> futures.Future[Any]:
        """Initiate a remote procedure call on a recipient.

        :param recipient_id: The recipient identifier.
        :param msg: The body of the message.
        :return: A future corresponding to the outcome of the call.
        """

    @abc.abstractmethod
    def broadcast_send(self, body: Any, sender: Any = None, subject: Any = None, correlation_id: Any = None) -> bool:
        """Broadcast a message to all subscribers."""
