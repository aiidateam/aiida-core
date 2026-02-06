"""Persistent queue implementation for ZMQ broker."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)


class PersistentQueue:
    """Folder-based persistent task queue.

    Tasks are stored as individual JSON files on disk for durability.
    The filename encodes the timestamp and task ID for ordering.

    Storage structure:
        {storage_path}/
        ├── pending/        # Tasks waiting to be processed
        │   └── {timestamp}_{task_id}.json
        └── processing/     # Tasks currently being processed (unacked)
            └── {timestamp}_{task_id}.json
    """

    def __init__(self, storage_path: Path | str):
        """Initialize the persistent queue.

        :param storage_path: Path to the queue storage directory
        """
        self._storage_path = Path(storage_path)
        self._pending_path = self._storage_path / 'pending'
        self._processing_path = self._storage_path / 'processing'

        # In-memory tracking
        self._pending: list[str] = []  # List of task filenames in order
        self._processing: dict[str, str] = {}  # task_id -> filename

        # Ensure directories exist
        self._pending_path.mkdir(parents=True, exist_ok=True)
        self._processing_path.mkdir(parents=True, exist_ok=True)

        # Load existing tasks from disk
        self._load()

    def _load(self) -> None:
        """Load pending and processing tasks from disk on startup.

        Processing tasks are moved back to pending (crash recovery).
        """
        # Move any processing tasks back to pending (crash recovery)
        for task_file in self._processing_path.glob('*.json'):
            dest = self._pending_path / task_file.name
            task_file.rename(dest)
            _LOGGER.info('Recovered task from processing: %s', task_file.stem)

        # Load pending tasks in timestamp order
        pending_files = sorted(self._pending_path.glob('*.json'))
        for task_file in pending_files:
            self._pending.append(task_file.name)

        _LOGGER.info('Loaded %d pending tasks from disk', len(self._pending))

    def _make_filename(self, task_id: str) -> str:
        """Create a filename with timestamp prefix for ordering."""
        timestamp = int(time.time() * 1000000)  # Microseconds for uniqueness
        return f'{timestamp}_{task_id}.json'

    def _extract_task_id(self, filename: str) -> str:
        """Extract task ID from filename."""
        # Format: {timestamp}_{task_id}.json
        return filename.rsplit('.', 1)[0].split('_', 1)[1]

    def push(self, task_id: str, task: dict[str, Any]) -> None:
        """Add a task to the queue.

        The task is immediately persisted to disk.

        :param task_id: Unique identifier for the task
        :param task: Task data dictionary
        """
        filename = self._make_filename(task_id)
        task_file = self._pending_path / filename

        # Write atomically by writing to temp file then renaming
        temp_file = task_file.with_suffix('.tmp')
        temp_file.write_text(json.dumps(task, indent=2))
        temp_file.rename(task_file)

        self._pending.append(filename)
        _LOGGER.debug('Queued task %s', task_id)

    def pop(self) -> tuple[str, dict[str, Any]] | None:
        """Get the next task from the queue.

        The task is moved to the processing state until acked or nacked.

        :return: Tuple of (task_id, task_data) or None if queue is empty
        """
        if not self._pending:
            return None

        filename = self._pending.pop(0)
        task_id = self._extract_task_id(filename)

        # Move from pending to processing
        src = self._pending_path / filename
        dest = self._processing_path / filename

        try:
            task = json.loads(src.read_text())
            src.rename(dest)
            self._processing[task_id] = filename
            _LOGGER.debug('Dequeued task %s', task_id)
            return task_id, task
        except FileNotFoundError:
            _LOGGER.warning('Task file not found: %s', filename)
            return self.pop()  # Try next task
        except json.JSONDecodeError as exc:
            _LOGGER.error('Failed to decode task %s: %s', filename, exc)
            src.unlink(missing_ok=True)  # Remove corrupted file
            return self.pop()  # Try next task

    def peek(self) -> tuple[str, dict[str, Any]] | None:
        """Peek at the next task without removing it.

        :return: Tuple of (task_id, task_data) or None if queue is empty
        """
        if not self._pending:
            return None

        filename = self._pending[0]
        task_id = self._extract_task_id(filename)
        task_file = self._pending_path / filename

        try:
            task = json.loads(task_file.read_text())
            return task_id, task
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def ack(self, task_id: str) -> bool:
        """Acknowledge successful processing of a task.

        Removes the task from disk.

        :param task_id: ID of the task to acknowledge
        :return: True if task was acknowledged, False if not found
        """
        filename = self._processing.pop(task_id, None)
        if filename is None:
            _LOGGER.warning('Cannot ack unknown task: %s', task_id)
            return False

        task_file = self._processing_path / filename
        task_file.unlink(missing_ok=True)
        _LOGGER.debug('Acked task %s', task_id)
        return True

    def nack(self, task_id: str, requeue: bool = True) -> bool:
        """Negative acknowledgment - task processing failed.

        :param task_id: ID of the task
        :param requeue: If True, put task back in queue; if False, discard it
        :return: True if task was nacked, False if not found
        """
        filename = self._processing.pop(task_id, None)
        if filename is None:
            _LOGGER.warning('Cannot nack unknown task: %s', task_id)
            return False

        task_file = self._processing_path / filename

        if requeue:
            # Move back to pending (at the front for retry)
            dest = self._pending_path / filename
            try:
                task_file.rename(dest)
                self._pending.insert(0, filename)
                _LOGGER.debug('Nacked and requeued task %s', task_id)
            except FileNotFoundError:
                _LOGGER.warning('Task file not found for nack: %s', task_id)
                return False
        else:
            # Just remove it
            task_file.unlink(missing_ok=True)
            _LOGGER.debug('Nacked and discarded task %s', task_id)

        return True

    def size(self) -> int:
        """Return the number of pending tasks."""
        return len(self._pending)

    def processing_count(self) -> int:
        """Return the number of tasks currently being processed."""
        return len(self._processing)

    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return len(self._pending) == 0

    def clear(self) -> int:
        """Remove all pending tasks from the queue.

        Does not affect tasks currently being processed.

        :return: Number of tasks removed
        """
        count = len(self._pending)
        for filename in self._pending:
            task_file = self._pending_path / filename
            task_file.unlink(missing_ok=True)
        self._pending.clear()
        _LOGGER.info('Cleared %d pending tasks', count)
        return count

    def get_all_pending(self) -> list[tuple[str, dict[str, Any]]]:
        """Get all pending tasks without removing them.

        :return: List of (task_id, task_data) tuples
        """
        tasks = []
        for filename in self._pending:
            task_id = self._extract_task_id(filename)
            task_file = self._pending_path / filename
            try:
                task = json.loads(task_file.read_text())
                tasks.append((task_id, task))
            except (FileNotFoundError, json.JSONDecodeError):
                continue
        return tasks

    def get_all_processing(self) -> list[tuple[str, dict[str, Any]]]:
        """Get all tasks currently being processed.

        :return: List of (task_id, task_data) tuples
        """
        tasks = []
        for task_id, filename in self._processing.items():
            task_file = self._processing_path / filename
            try:
                task = json.loads(task_file.read_text())
                tasks.append((task_id, task))
            except (FileNotFoundError, json.JSONDecodeError):
                continue
        return tasks
