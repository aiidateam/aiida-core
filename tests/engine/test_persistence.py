###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test persisting via the AiiDAPersister."""

import plumpy
import pytest

from aiida.engine import Process, run
from aiida.engine.persistence import AiiDAPersister
from tests.utils.processes import DummyProcess


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
        saved_state = plumpy.Bundle(process)
        process.close()

        loaded_process = saved_state.unbundle()
        run(loaded_process)

        assert loaded_process.state == plumpy.ProcessState.FINISHED


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
