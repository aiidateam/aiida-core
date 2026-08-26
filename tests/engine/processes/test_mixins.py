"""Tests for process mixins."""

from unittest.mock import Mock

from aiida.engine.processes import persistence
from aiida.engine.processes.mixins import ContextMixin


def test_restore_without_context():
    """Test restoring saved state without a context initializes the attribute."""
    load_context = persistence.LoadSaveContext(loader=Mock())

    restored = ContextMixin.recreate_from({}, load_context)

    assert restored.ctx is None
