###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ZMQ single-layer JSON encoding.

This module tests that the message protocol uses a single JSON encoding layer
for both the envelope and payload, including UUID serialization support.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock

import pytest

from aiida.brokers.zmq.protocol import (
    MessageType,
    _UUIDEncoder,
    decode_message,
    encode_message,
)
from aiida.brokers.zmq.server import ZmqBrokerServer


@pytest.mark.presto
class TestProtocolEncodingOptimization:
    """Tests for protocol.py single-layer JSON encoding."""

    def test_encode_decode_roundtrip(self):
        """Test encode/decode roundtrip with JSON."""
        original = {
            'type': MessageType.TASK.value,
            'id': 'msg-123',
            'sender': 'client-abc',
            'body': {'data': [1, 2, 3]},
        }

        encoded = encode_message(original)
        assert isinstance(encoded, bytes)

        decoded = decode_message(encoded)
        assert decoded == original

    def test_encode_message_no_encoder_parameter(self):
        """Verify encode_message signature has no encoder parameter."""
        import inspect

        sig = inspect.signature(encode_message)
        assert 'msg' in sig.parameters
        assert 'encoder' not in sig.parameters

    def test_decode_message_no_decoder_parameter(self):
        """Verify decode_message signature has no decoder parameter."""
        import inspect

        sig = inspect.signature(decode_message)
        assert 'data' in sig.parameters
        assert 'decoder' not in sig.parameters

    def test_uuid_encoder_converts_uuid_to_string(self):
        """Test that _UUIDEncoder converts uuid.UUID to string."""
        test_uuid = uuid.UUID('12345678-1234-5678-1234-567812345678')
        msg = {'pid': test_uuid}

        encoded = json.dumps(msg, cls=_UUIDEncoder)
        decoded = json.loads(encoded)

        assert decoded['pid'] == str(test_uuid)

    def test_encode_message_handles_uuid_in_body(self):
        """Test that encode_message handles uuid.UUID objects in body."""
        test_uuid = uuid.UUID('12345678-1234-5678-1234-567812345678')
        msg = {
            'type': MessageType.TASK.value,
            'id': 'msg-123',
            'sender': 'client-abc',
            'body': {'pid': test_uuid, 'action': 'continue'},
        }

        encoded = encode_message(msg)
        decoded = decode_message(encoded)

        assert decoded['body']['pid'] == str(test_uuid)
        assert decoded['body']['action'] == 'continue'

    def test_encode_message_handles_nested_uuid(self):
        """Test that encode_message handles nested uuid.UUID objects."""
        test_uuid = uuid.UUID('abcdef12-3456-7890-abcd-ef1234567890')
        msg = {
            'type': MessageType.RPC.value,
            'id': 'msg-456',
            'body': {'args': {'pid': test_uuid, 'nested': {'id': test_uuid}}},
        }

        encoded = encode_message(msg)
        decoded = decode_message(encoded)

        assert decoded['body']['args']['pid'] == str(test_uuid)
        assert decoded['body']['args']['nested']['id'] == str(test_uuid)


@pytest.mark.presto
class TestCommunicatorPayloadEncoding:
    """Tests for communicator.py single-layer JSON encoding (no pre/post-encode)."""

    def test_send_encodes_body_as_json_native(self):
        """Test that _send passes body through as a JSON-native object (no pre-encoding)."""
        from aiida.brokers.zmq.communicator import ZmqCommunicator

        comm = ZmqCommunicator(router_endpoint='ipc://test')
        comm._dealer = MagicMock()
        comm._closed = False

        msg = {
            'type': MessageType.TASK.value,
            'id': 'msg-123',
            'sender': 'client-abc',
            'body': {'data': [1, 2, 3]},
        }

        comm._send(msg)

        call_args = comm._dealer.send_multipart.call_args
        frames = call_args[0][0]
        encoded_msg = frames[1]

        decoded_msg = json.loads(encoded_msg.decode('utf-8'))

        # Body should remain a dict (JSON-native), not a pre-encoded string
        assert isinstance(decoded_msg['body'], dict)
        assert decoded_msg['body'] == {'data': [1, 2, 3]}

    def test_send_encodes_result_as_json_native(self):
        """Test that _send passes result through as a JSON-native object."""
        from aiida.brokers.zmq.communicator import ZmqCommunicator

        comm = ZmqCommunicator(router_endpoint='ipc://test')
        comm._dealer = MagicMock()
        comm._closed = False

        msg = {
            'type': MessageType.TASK_RESPONSE.value,
            'id': 'msg-456',
            'sender': 'worker-xyz',
            'task_id': 'task-123',
            'result': {'status': 'completed', 'value': 42},
        }

        comm._send(msg)

        call_args = comm._dealer.send_multipart.call_args
        frames = call_args[0][0]
        encoded_msg = frames[1]

        decoded_msg = json.loads(encoded_msg.decode('utf-8'))

        # Result should remain a dict, not a pre-encoded string
        assert isinstance(decoded_msg['result'], dict)
        assert decoded_msg['result'] == {'status': 'completed', 'value': 42}

    def test_send_ignores_none_body(self):
        """Test that _send doesn't fail with None body."""
        from aiida.brokers.zmq.communicator import ZmqCommunicator

        comm = ZmqCommunicator(router_endpoint='ipc://test')
        comm._dealer = MagicMock()
        comm._closed = False

        msg = {
            'type': MessageType.PING.value,
            'id': 'msg-789',
            'sender': 'client-abc',
            'body': None,
        }

        comm._send(msg)

        call_args = comm._dealer.send_multipart.call_args
        frames = call_args[0][0]
        encoded_msg = frames[1]

        decoded_msg = json.loads(encoded_msg.decode('utf-8'))
        assert decoded_msg['body'] is None

    def test_dispatch_passes_body_directly(self):
        """Test that _dispatch_dealer_message passes body directly (no post-decode)."""
        from aiida.brokers.zmq.communicator import ZmqCommunicator

        comm = ZmqCommunicator(router_endpoint='ipc://test')
        comm._dealer = MagicMock()
        comm._closed = False

        original_body = {'data': [1, 2, 3]}
        msg = {
            'type': MessageType.TASK.value,
            'id': 'msg-123',
            'body': original_body,
        }

        received_body = None

        def mock_subscriber(comm_obj, body):
            nonlocal received_body
            received_body = body
            return True

        comm._task_subscribers['test-task'] = mock_subscriber
        comm._dispatch_dealer_message(msg)

        assert received_body == original_body

    def test_communicator_no_encoder_decoder_params(self):
        """Verify ZmqCommunicator.__init__ has no encoder/decoder parameters."""
        import inspect

        from aiida.brokers.zmq.communicator import ZmqCommunicator

        sig = inspect.signature(ZmqCommunicator.__init__)
        param_names = [p for p in sig.parameters.keys() if p != 'self']
        assert 'encoder' not in param_names
        assert 'decoder' not in param_names


@pytest.mark.presto
class TestServerInitializationOptimization:
    """Tests for server.py encoder/decoder parameter removal."""

    def test_server_init_no_encoder_parameter(self, tmp_path):
        """Test ZmqBrokerServer.__init__ has no encoder/decoder parameters."""
        import inspect

        sig = inspect.signature(ZmqBrokerServer.__init__)
        param_names = [p for p in sig.parameters.keys() if p != 'self']
        assert 'storage_path' in param_names
        assert 'sockets_path' in param_names
        assert 'encoder' not in param_names
        assert 'decoder' not in param_names

    def test_server_init_creates_with_positional_args(self, tmp_path):
        """Test server initialization with positional args only."""
        storage_path = tmp_path / 'storage'
        sockets_path = tmp_path / 'sockets'

        server = ZmqBrokerServer(storage_path, sockets_path)
        assert server.storage_path == storage_path
        assert server.sockets_path == sockets_path


@pytest.mark.presto
class TestQueueCompressionOptimization:
    """Tests for queue.py indent removal."""

    def test_queue_push_no_indent(self, tmp_path):
        """Test that queue.push writes JSON without indent."""
        from aiida.brokers.zmq.queue import PersistentQueue

        queue = PersistentQueue(tmp_path / 'queue')

        task_id = 'task-123'
        task_data = {
            'id': task_id,
            'sender': 'client-abc',
            'body': {'large': 'data' * 100},
        }

        queue.push(task_id, task_data)

        files = list((tmp_path / 'queue' / 'pending').glob('*.json'))
        assert len(files) == 1

        content = files[0].read_text()

        # Minified JSON should not have newlines
        lines = content.split('\n')
        assert len(lines) == 1, f'Expected single line, got {len(lines)} lines'

        # But should still be valid JSON
        parsed = json.loads(content)
        assert parsed == task_data

    def test_queue_pop_handles_minified_json(self, tmp_path):
        """Test that queue.pop can read minified JSON."""
        from aiida.brokers.zmq.queue import PersistentQueue

        queue = PersistentQueue(tmp_path / 'queue')

        task_id = 'task-456'
        task_data = {
            'id': task_id,
            'sender': 'worker-xyz',
            'body': {'result': 42},
            'no_reply': False,
        }

        queue.push(task_id, task_data)
        popped_id, popped_data = queue.pop()

        assert popped_id == task_id
        assert popped_data == task_data

    def test_minified_json_smaller_than_indented(self):
        """Test that minified JSON is smaller than indented JSON."""
        large_data = {'data': list(range(1000))}

        minified = json.dumps(large_data)
        indented = json.dumps(large_data, indent=2)

        size_reduction = (len(indented) - len(minified)) / len(indented)
        assert size_reduction > 0.15, f'Expected >15% size reduction, got {size_reduction * 100:.1f}%'


@pytest.mark.presto
class TestTaskBodyPreEncoding:
    """Tests for task body handling in ZmqIncomingTask."""

    def test_zmq_incoming_task_reads_body_directly(self):
        """Test that ZmqIncomingTask reads body directly as a JSON-native object."""
        from aiida.brokers.zmq.broker import ZmqIncomingTask
        from aiida.brokers.zmq.queue import PersistentQueue

        original_body = {'function': 'test_function', 'args': [1, 2, 3]}

        task_data = {
            'id': 'task-123',
            'sender': 'client-abc',
            'body': original_body,
            'no_reply': False,
        }

        queue = MagicMock(spec=PersistentQueue)
        task = ZmqIncomingTask(task_id='task-123', task_data=task_data, queue=queue)

        assert task.body == original_body

    def test_zmq_incoming_task_handles_none_body(self):
        """Test that ZmqIncomingTask handles None body."""
        from aiida.brokers.zmq.broker import ZmqIncomingTask
        from aiida.brokers.zmq.queue import PersistentQueue

        task_data = {
            'id': 'task-456',
            'sender': 'client-xyz',
            'no_reply': False,
        }

        queue = MagicMock(spec=PersistentQueue)
        task = ZmqIncomingTask(task_id='task-456', task_data=task_data, queue=queue)

        assert task.body is None


@pytest.mark.presto
class TestEndToEndEnvelopeSeparation:
    """Integration tests for single-layer JSON encoding flow."""

    def test_message_flow_single_layer_json(self):
        """Test full message flow with single-layer JSON encoding."""
        large_payload = {
            'function': 'compute',
            'inputs': [{'data': list(range(100))} for _ in range(10)],
        }

        msg = {
            'type': MessageType.TASK.value,
            'id': 'task-123',
            'sender': 'client-abc',
            'body': large_payload,
            'no_reply': False,
        }

        encoded = encode_message(msg)
        assert isinstance(encoded, bytes)

        decoded_msg = decode_message(encoded)
        assert decoded_msg['type'] == MessageType.TASK.value
        assert decoded_msg['body'] == large_payload

    def test_message_flow_with_uuid(self):
        """Test full message flow with UUID in payload."""
        test_uuid = uuid.uuid4()

        msg = {
            'type': MessageType.TASK.value,
            'id': 'task-456',
            'sender': 'client-abc',
            'body': {'pid': test_uuid, 'action': 'continue'},
            'no_reply': False,
        }

        encoded = encode_message(msg)
        decoded_msg = decode_message(encoded)

        # UUID should be serialized as string
        assert decoded_msg['body']['pid'] == str(test_uuid)
        assert decoded_msg['body']['action'] == 'continue'
