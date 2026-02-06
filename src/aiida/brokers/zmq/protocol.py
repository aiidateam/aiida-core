"""Message protocol definitions for ZMQ broker."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
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


@dataclass
class Message:
    """Base message structure."""

    type: MessageType
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    sender: str = ''


@dataclass
class TaskMessage(Message):
    """Task message sent to the broker for processing."""

    type: MessageType = field(default=MessageType.TASK, init=False)
    body: Any = None
    no_reply: bool = False


@dataclass
class TaskResponse(Message):
    """Response to a task message."""

    type: MessageType = field(default=MessageType.TASK_RESPONSE, init=False)
    task_id: str = ''
    result: Any = None
    error: str | None = None


@dataclass
class RpcMessage(Message):
    """RPC message sent to a specific recipient."""

    type: MessageType = field(default=MessageType.RPC, init=False)
    recipient: str = ''
    body: Any = None


@dataclass
class RpcResponse(Message):
    """Response to an RPC message."""

    type: MessageType = field(default=MessageType.RPC_RESPONSE, init=False)
    rpc_id: str = ''
    result: Any = None
    error: str | None = None


@dataclass
class BroadcastMessage(Message):
    """Broadcast message sent to all subscribers."""

    type: MessageType = field(default=MessageType.BROADCAST, init=False)
    body: Any = None
    subject: str | None = None
    correlation_id: str | None = None


@dataclass
class SubscribeMessage(Message):
    """Subscription request message."""

    type: MessageType = MessageType.SUBSCRIBE_TASK
    identifier: str | None = None


def encode_message(msg: dict, encoder=json.dumps) -> bytes:
    """Encode a message dictionary to bytes."""
    return encoder(msg).encode('utf-8')


def decode_message(data: bytes, decoder=json.loads) -> dict:
    """Decode bytes to a message dictionary."""
    return decoder(data.decode('utf-8'))


def make_task_message(body: Any, sender: str, no_reply: bool = False) -> dict:
    """Create a task message dictionary."""
    return {
        'type': MessageType.TASK.value,
        'id': uuid.uuid4().hex,
        'sender': sender,
        'body': body,
        'no_reply': no_reply,
    }


def make_task_response(task_id: str, sender: str, result: Any = None, error: str | None = None) -> dict:
    """Create a task response dictionary."""
    return {
        'type': MessageType.TASK_RESPONSE.value,
        'id': uuid.uuid4().hex,
        'sender': sender,
        'task_id': task_id,
        'result': result,
        'error': error,
    }


def make_task_ack(task_id: str, sender: str) -> dict:
    """Create a task acknowledgment message."""
    return {
        'type': MessageType.TASK_ACK.value,
        'id': uuid.uuid4().hex,
        'sender': sender,
        'task_id': task_id,
    }


def make_task_nack(task_id: str, sender: str) -> dict:
    """Create a task negative acknowledgment message."""
    return {
        'type': MessageType.TASK_NACK.value,
        'id': uuid.uuid4().hex,
        'sender': sender,
        'task_id': task_id,
    }


def make_rpc_message(recipient: str, body: Any, sender: str) -> dict:
    """Create an RPC message dictionary."""
    return {
        'type': MessageType.RPC.value,
        'id': uuid.uuid4().hex,
        'sender': sender,
        'recipient': recipient,
        'body': body,
    }


def make_rpc_response(rpc_id: str, sender: str, result: Any = None, error: str | None = None) -> dict:
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
) -> dict:
    """Create a broadcast message dictionary."""
    return {
        'type': MessageType.BROADCAST.value,
        'id': uuid.uuid4().hex,
        'sender': sender,
        'body': body,
        'subject': subject,
        'correlation_id': correlation_id,
    }


def make_subscribe_message(msg_type: MessageType, sender: str, identifier: str | None = None) -> dict:
    """Create a subscription message dictionary."""
    return {
        'type': msg_type.value,
        'id': uuid.uuid4().hex,
        'sender': sender,
        'identifier': identifier,
    }
