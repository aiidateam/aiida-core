# -*- coding: utf-8 -*-
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

from aiida.backends.testbase import AiidaTestCase
from aiida.engine.persistence import AiiDAPersister
from aiida.engine import Process, run

from tests.utils.processes import DummyProcess


class TestProcess(AiidaTestCase):
    """Test the basic saving and loading of process states."""

    def setUp(self):
        super().setUp()
        self.assertIsNone(Process.current())

    def tearDown(self):
        super().tearDown()
        self.assertIsNone(Process.current())

    def test_save_load(self):
        """Test load saved state."""
        process = DummyProcess()
        saved_state = plumpy.Bundle(process)
        process.close()

        loaded_process = saved_state.unbundle()
        run(loaded_process)

        self.assertEqual(loaded_process.state, plumpy.ProcessState.FINISHED)


class TestAiiDAPersister(AiidaTestCase):
    """Test AiiDAPersister."""
    maxDiff = 1024

    def setUp(self):
        super().setUp()
        self.persister = AiiDAPersister()

    def test_save_load_checkpoint(self):
        """Test checkpoint saving."""
        process = DummyProcess()
        bundle_saved = self.persister.save_checkpoint(process)
        bundle_loaded = self.persister.load_checkpoint(process.node.pk)

        self.assertDictEqual(bundle_saved, bundle_loaded)

    def test_delete_checkpoint(self):
        """Test checkpoint deletion."""
        process = DummyProcess()

        self.persister.save_checkpoint(process)
        self.assertTrue(isinstance(process.node.checkpoint, str))

        self.persister.delete_checkpoint(process.pid)
        self.assertEqual(process.node.checkpoint, None)
