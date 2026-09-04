###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test persisting via the AiiDAPersister."""

import asyncio

import pytest

from aiida.common.processes import ProcessState
from aiida.engine import Process, run
from aiida.engine.persistence import AiiDAPersister
from aiida.engine.processes.persistence import Bundle, LoadSaveContext, Savable, SavableFuture
from tests.utils.processes import DummyProcess


class CustomSavable(Savable):
    """Savable that can only be resolved by the custom object loader."""


class CustomObjectLoader:
    """Static custom loader compatible with persistence deserialization."""

    @staticmethod
    def load_object(identifier):
        if identifier == 'custom-savable':
            return CustomSavable
        raise ImportError

    @staticmethod
    def identify_object(obj):
        if obj is CustomSavable:
            return 'custom-savable'
        raise ImportError


def test_cancelled_savable_future():
    """Test a cancelled savable future can be saved and recreated."""
    loop = asyncio.new_event_loop()

    try:
        future = SavableFuture(loop=loop)
        future.cancel()

        restored = Bundle(future).unbundle(LoadSaveContext(loop=loop))

        assert isinstance(restored, SavableFuture)
        assert restored.cancelled()
    finally:
        loop.close()


def test_load_uses_saved_custom_object_loader():
    """Test restoring a bundle uses the saved custom object loader metadata."""
    saved_state = CustomSavable().save(LoadSaveContext(loader=CustomObjectLoader()))

    restored = Savable.load(saved_state)

    assert isinstance(restored, CustomSavable)


@pytest.mark.requires_broker
class TestProcess:
    """Test the basic saving and loading of process states."""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        assert Process.current() is None
        yield
        assert Process.current() is None

    def test_save_load(self):
        """Test load saved state."""
        process = DummyProcess()
        saved_state = Bundle(process)
        process.close()

        loaded_process = saved_state.unbundle()
        run(loaded_process)

        assert loaded_process.state == ProcessState.FINISHED


@pytest.mark.requires_broker
class TestAiiDAPersister:
    """Test AiiDAPersister."""

    maxDiff = 1024

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        self.persister = AiiDAPersister()

    def test_save_load_checkpoint(self):
        """Test checkpoint saving."""
        process = DummyProcess()
        bundle_saved = self.persister.save_checkpoint(process)
        bundle_loaded = self.persister.load_checkpoint(process.node.pk)

        assert bundle_saved == bundle_loaded

    def test_delete_checkpoint(self):
        """Test checkpoint deletion."""
        process = DummyProcess()

        self.persister.save_checkpoint(process)
        assert isinstance(process.node.checkpoint, str)

        self.persister.delete_checkpoint(process.pid)
        assert process.node.checkpoint is None
