# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import absolute_import
import tempfile

import six

from aiida.backends.testbase import AiidaTestCase
from aiida.work.persistence import AiiDAPersister
from aiida.work import Process
from aiida.work.test_utils import DummyProcess
from aiida import work


class TestProcess(AiidaTestCase):
    """ Test the basic saving and loading of process states """

    def setUp(self):
        super(TestProcess, self).setUp()
        work.runners.set_runner(None)
        self.assertIsNone(Process.current())

    def tearDown(self):
        super(TestProcess, self).tearDown()
        self.assertIsNone(Process.current())

    def test_save_load(self):
        process = DummyProcess()
        saved_state = work.Bundle(process)
        del process

        loaded_process = saved_state.unbundle()
        result_from_loaded = work.launch.run(loaded_process)

        self.assertEqual(loaded_process.state, work.ProcessState.FINISHED)


class TestAiiDAPersister(AiidaTestCase):

    def setUp(self):
        super(TestAiiDAPersister, self).setUp()
        work.runners.set_runner(None)
        self.persister = AiiDAPersister()

    def test_save_load_checkpoint(self):
        process = DummyProcess()
        bundle_saved = self.persister.save_checkpoint(process)
        bundle_loaded = self.persister.load_checkpoint(process.calc.pk)

        self.assertEquals(bundle_saved, bundle_loaded)

    def test_delete_checkpoint(self):
        process = DummyProcess()

        self.persister.save_checkpoint(process)
        self.assertTrue(isinstance(process.calc.checkpoint, six.string_types))

        self.persister.delete_checkpoint(process.pid)
        self.assertEquals(process.calc.checkpoint, None)
