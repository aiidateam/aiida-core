# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six
import plumpy

from aiida.backends.testbase import AiidaTestCase
from aiida.backends.tests.utils.processes import DummyProcess
from aiida.engine.persistence import AiiDAPersister
from aiida.engine import Process, run


class TestProcess(AiidaTestCase):
    """Test the basic saving and loading of process states."""

    def setUp(self):
        super(TestProcess, self).setUp()
        self.assertIsNone(Process.current())

    def tearDown(self):
        super(TestProcess, self).tearDown()
        self.assertIsNone(Process.current())

    def test_save_load(self):
        process = DummyProcess()
        saved_state = plumpy.Bundle(process)
        process.close()

        loaded_process = saved_state.unbundle()
        run(loaded_process)

        self.assertEqual(loaded_process.state, plumpy.ProcessState.FINISHED)


class TestAiiDAPersister(AiidaTestCase):

    maxDiff = 1024

    def setUp(self):
        super(TestAiiDAPersister, self).setUp()
        self.persister = AiiDAPersister()

    def test_save_load_checkpoint(self):
        process = DummyProcess()
        bundle_saved = self.persister.save_checkpoint(process)
        bundle_loaded = self.persister.load_checkpoint(process.node.pk)

        self.assertDictEqual(bundle_saved, bundle_loaded)

    def test_delete_checkpoint(self):
        process = DummyProcess()

        self.persister.save_checkpoint(process)
        self.assertTrue(isinstance(process.node.checkpoint, six.string_types))

        self.persister.delete_checkpoint(process.pid)
        self.assertEquals(process.node.checkpoint, None)
