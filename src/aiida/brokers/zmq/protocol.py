###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Application-level message protocol for the ZMQ broker.

This protocol implements the subset of AMQP semantics that AiiDA requires
(via kiwipy's ``Communicator`` interface, originally designed for RabbitMQ)
using ZMQ as the transport layer instead of raw TCP.

Socket architecture:
    A single ROUTER/DEALER pair carries all traffic (tasks, RPC, broadcasts).
    The server binds a ROUTER socket; each client connects a DEALER socket.
    ROUTER provides identity-based routing so the server can send messages
    to specific clients. Broadcasts are sent by the server to all connected
    clients (derived from subscriber registries).

What ZMQ provides (transport layer):
    - Identity-based routing (ROUTER auto-prepends sender identity to messages)
    - Automatic reconnection and async I/O
    - ZMTP heartbeats for dead peer detection
    - IPC transport for same-machine communication

What ZMQ does NOT provide (requiring this protocol):
    - Request-reply correlation (matching responses to requests)
    - Task acknowledgment and redelivery on worker death
    - Persistent/durable queues
    - Server-side subscription awareness
    - Directed RPC routing to a named recipient
    - Message serialization

AMQP concepts mapped to message types:
    ========================  ================================
    AMQP concept              ZMQ broker message type
    ========================  ================================
    ``basic.ack``             ``TASK_ACK``
    ``basic.nack``            ``TASK_NACK``
    consumer with prefetch    ``TASK`` dispatch to workers
    fanout exchange           ``BROADCAST`` via ROUTER fan-out
    direct exchange           ``RPC`` to specific recipient
    durable queue             ``PersistentQueue`` (file-based)
    ``basic.consume``         ``SUBSCRIBE_TASK`` / ``SUBSCRIBE_RPC``
    ========================  ================================

Why not use an AMQP library directly: the goal is to eliminate the RabbitMQ
server dependency. ZMQ provides the transport primitives; this module adds
only the AMQP-like semantics that ``kiwipy.Communicator`` requires.
"""

from __future__ import annotations

import json
import uuid
from enum import Enum
from typing import Any


class MessageType(str, Enum):
    """Message types for the ZMQ broker protocol."""

    # Task messages
    TASK = 'task'
    TASK_RESPONSE = 'task_response'
    TASK_ACK = 'task_ack'
    TASK_NACK = 'task_nack'
    # RPC messages
    RPC = 'rpc'
    RPC_RESPONSE = 'rpc_response'

    # Broadcast messages
    BROADCAST = 'broadcast'

    # Subscription management
    SUBSCRIBE_TASK = 'subscribe_task'
    SUBSCRIBE_RPC = 'subscribe_rpc'
    UNSUBSCRIBE_TASK = 'unsubscribe_task'
    UNSUBSCRIBE_RPC = 'unsubscribe_rpc'

    # Health check
    PING = 'ping'


class _UUIDEncoder(json.JSONEncoder):
    """JSON encoder that converts uuid.UUID to string."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)


def encode_message(msg: dict[str, Any]) -> bytes:
    """Encode a message dictionary to bytes using JSON."""
    return json.dumps(msg, cls=_UUIDEncoder).encode('utf-8')


def decode_message(data: bytes) -> dict[str, Any]:
    """Decode bytes to a message dictionary using JSON."""
    return json.loads(data.decode('utf-8'))  # type: ignore[no-any-return]


def make_task_message(body: Any, sender: str, no_reply: bool = False) -> dict[str, Any]:
    """Create a task message dictionary."""
    return {
        'type': MessageType.TASK.value,
        'id': uuid.uuid4().hex,
        'sender': sender,
        'body': body,
        'no_reply': no_reply,
    }


def make_task_response(task_id: str, sender: str, result: Any = None, error: str | None = None) -> dict[str, Any]:
    """Create a task response dictionary."""
    return {
        'type': MessageType.TASK_RESPONSE.value,
        'id': uuid.uuid4().hex,
        'sender': sender,
        'task_id': task_id,
        'result': result,
        'error': error,
    }


def make_task_ack(task_id: str, sender: str) -> dict[str, Any]:
    """Create a task acknowledgment message."""
    return {
        'type': MessageType.TASK_ACK.value,
        'id': uuid.uuid4().hex,
        'sender': sender,
        'task_id': task_id,
    }


def make_task_nack(task_id: str, sender: str) -> dict[str, Any]:
    """Create a task negative acknowledgment message."""
    return {
        'type': MessageType.TASK_NACK.value,
        'id': uuid.uuid4().hex,
        'sender': sender,
        'task_id': task_id,
    }


def make_ping(sender: str) -> dict[str, Any]:
    """Create a ping message for worker liveness probing."""
    return {
        'type': MessageType.PING.value,
        'id': uuid.uuid4().hex,
        'sender': sender,
    }


def make_rpc_message(recipient: str, body: Any, sender: str) -> dict[str, Any]:
    """Create an RPC message dictionary."""
    return {
        'type': MessageType.RPC.value,
        'id': uuid.uuid4().hex,
        'sender': sender,
        'recipient': recipient,
        'body': body,
    }


def make_rpc_response(rpc_id: str, sender: str, result: Any = None, error: str | None = None) -> dict[str, Any]:
    """Create an RPC response dictionary."""
    return {
        'type': MessageType.RPC_RESPONSE.value,
        'id': uuid.uuid4().hex,
        'sender': sender,
        'rpc_id': rpc_id,
        'result': result,
        'error': error,
    }


def make_broadcast_message(
    body: Any, sender: str, subject: str | None = None, correlation_id: str | None = None
) -> dict[str, Any]:
    """Create a broadcast message dictionary."""
    return {
        'type': MessageType.BROADCAST.value,
        'id': uuid.uuid4().hex,
        'sender': sender,
        'body': body,
        'subject': subject,
        'correlation_id': correlation_id,
    }


def make_subscribe_message(msg_type: MessageType, sender: str, identifier: str | None = None) -> dict[str, Any]:
    """Create a subscription message dictionary."""
    return {
        'type': msg_type.value,
        'id': uuid.uuid4().hex,
        'sender': sender,
        'identifier': identifier,
    }
