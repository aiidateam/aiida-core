###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``aiida.brokers.zmq.queue.PersistentQueue``."""

from __future__ import annotations

from aiida.brokers.zmq.queue import PersistentQueue


class TestPersistentQueue:
    """Tests for the PersistentQueue."""

    def test_init(self, tmp_path):
        """Test queue initialization."""
        queue = PersistentQueue(tmp_path)
        assert queue._storage_path == tmp_path

    def test_push_pop(self, tmp_path):
        """Test pushing and popping tasks."""
        queue = PersistentQueue(tmp_path)

        task_id = 'task-001'
        queue.push(task_id, {'type': 'test', 'data': 'hello'})

        popped_id, task_data = queue.pop()
        assert popped_id == task_id
        assert task_data['type'] == 'test'
        assert task_data['data'] == 'hello'

    def test_pop_empty(self, tmp_path):
        """Test popping from empty queue."""
        queue = PersistentQueue(tmp_path)
        result = queue.pop()
        assert result is None

    def test_ack_task(self, tmp_path):
        """Test acknowledging a task."""
        queue = PersistentQueue(tmp_path)

        task_id = 'task-002'
        queue.push(task_id, {'type': 'test'})
        queue.pop()
        result = queue.ack(task_id)

        assert result is True
        assert queue.pop() is None

    def test_nack_task(self, tmp_path):
        """Test negative acknowledgment (requeue)."""
        queue = PersistentQueue(tmp_path)

        task_id = 'task-003'
        queue.push(task_id, {'type': 'test'})
        queue.pop()
        result = queue.nack(task_id, requeue=True)

        assert result is True
        popped_id, _ = queue.pop()
        assert popped_id == task_id

    def test_get_all_pending(self, tmp_path):
        """Test getting all pending tasks."""
        queue = PersistentQueue(tmp_path)

        task_id1 = 'task-004'
        task_id2 = 'task-005'
        queue.push(task_id1, {'type': 'test1'})
        queue.push(task_id2, {'type': 'test2'})

        pending = queue.get_all_pending()
        assert len(pending) == 2

        task_ids = [t[0] for t in pending]
        assert task_id1 in task_ids
        assert task_id2 in task_ids

    def test_crash_recovery_moves_processing_to_pending(self, tmp_path):
        """Test _load recovers processing tasks back to pending."""
        queue = PersistentQueue(tmp_path)
        queue.push('t1', {'data': 'hello'})
        queue.pop()  # moves to processing

        # Create a fresh queue from the same path — simulates crash recovery
        queue2 = PersistentQueue(tmp_path)
        assert queue2.size() == 1
        result = queue2.pop()
        assert result is not None
        assert result[0] == 't1'

    def test_load_logs_count(self, tmp_path):
        """Test that _load reports the loaded count."""
        queue = PersistentQueue(tmp_path)
        queue.push('t1', {'a': 1})
        queue.push('t2', {'b': 2})

        queue2 = PersistentQueue(tmp_path)
        assert queue2.size() == 2

    def test_pop_file_not_found(self, tmp_path):
        """Test pop when pending file is deleted externally."""
        queue = PersistentQueue(tmp_path)
        queue.push('t1', {'data': 'test'})

        for f in (tmp_path / 'pending').glob('*.json'):
            f.unlink()

        result = queue.pop()
        assert result is None

    def test_pop_corrupted_json(self, tmp_path):
        """Test pop with corrupted JSON file."""
        queue = PersistentQueue(tmp_path)
        queue.push('t1', {'data': 'test'})

        for f in (tmp_path / 'pending').glob('*.json'):
            f.write_text('NOT VALID JSON{{{')

        result = queue.pop()
        assert result is None
        assert list((tmp_path / 'pending').glob('*.json')) == []

    def test_peek_returns_task(self, tmp_path):
        """Test peek returns task data without removing it."""
        queue = PersistentQueue(tmp_path)
        queue.push('t1', {'key': 'val'})

        result = queue.peek()
        assert result is not None
        task_id, data = result
        assert task_id == 't1'
        assert data['key'] == 'val'
        assert queue.size() == 1

    def test_peek_empty_queue(self, tmp_path):
        """Test peek on empty queue."""
        queue = PersistentQueue(tmp_path)
        assert queue.peek() is None

    def test_peek_file_missing(self, tmp_path):
        """Test peek when file is deleted externally."""
        queue = PersistentQueue(tmp_path)
        queue.push('t1', {'data': 'x'})
        for f in (tmp_path / 'pending').glob('*.json'):
            f.unlink()
        assert queue.peek() is None

    def test_nack_unknown_task(self, tmp_path):
        """Test nacking an unknown task returns False."""
        queue = PersistentQueue(tmp_path)
        assert queue.nack('nonexistent') is False

    def test_nack_file_not_found(self, tmp_path):
        """Test nack requeue when processing file is gone."""
        queue = PersistentQueue(tmp_path)
        queue.push('t1', {'data': 'x'})
        queue.pop()

        for f in (tmp_path / 'processing').glob('*.json'):
            f.unlink()

        assert queue.nack('t1', requeue=True) is False

    def test_nack_discard(self, tmp_path):
        """Test nack with requeue=False discards the task."""
        queue = PersistentQueue(tmp_path)
        queue.push('t1', {'data': 'x'})
        queue.pop()

        assert queue.nack('t1', requeue=False) is True
        assert queue.size() == 0
        assert queue.processing_count() == 0

    def test_is_empty(self, tmp_path):
        """Test is_empty."""
        queue = PersistentQueue(tmp_path)
        assert queue.is_empty()
        queue.push('t1', {'data': 'x'})
        assert not queue.is_empty()

    def test_clear(self, tmp_path):
        """Test clear removes all pending tasks."""
        queue = PersistentQueue(tmp_path)
        queue.push('t1', {'a': 1})
        queue.push('t2', {'b': 2})
        queue.push('t3', {'c': 3})

        count = queue.clear()
        assert count == 3
        assert queue.size() == 0
        assert list((tmp_path / 'pending').glob('*.json')) == []

    def test_remove_pending(self, tmp_path):
        """Test remove_pending by task ID."""
        queue = PersistentQueue(tmp_path)
        queue.push('t1', {'a': 1})
        queue.push('t2', {'b': 2})

        assert queue.remove_pending('t1') is True
        assert queue.size() == 1
        assert queue.remove_pending('nonexistent') is False

    def test_get_all_pending_skips_errors(self, tmp_path):
        """Test get_all_pending continues on corrupted files."""
        queue = PersistentQueue(tmp_path)
        queue.push('t1', {'a': 1})
        queue.push('t2', {'b': 2})

        first_file = next((tmp_path / 'pending').glob('*.json'))
        first_file.write_text('{INVALID')

        pending = queue.get_all_pending()
        assert len(pending) == 1

    def test_get_all_processing(self, tmp_path):
        """Test get_all_processing returns tasks being processed."""
        queue = PersistentQueue(tmp_path)
        queue.push('t1', {'a': 1})
        queue.push('t2', {'b': 2})
        queue.pop()
        queue.pop()

        processing = queue.get_all_processing()
        assert len(processing) == 2
        task_ids = {t[0] for t in processing}
        assert 't1' in task_ids
        assert 't2' in task_ids

    def test_get_all_processing_skips_errors(self, tmp_path):
        """Test get_all_processing continues on corrupted files."""
        queue = PersistentQueue(tmp_path)
        queue.push('t1', {'a': 1})
        queue.pop()

        for f in (tmp_path / 'processing').glob('*.json'):
            f.write_text('{BAD')

        processing = queue.get_all_processing()
        assert len(processing) == 0
