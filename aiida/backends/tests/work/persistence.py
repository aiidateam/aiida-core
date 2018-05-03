# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import tempfile

from aiida.backends.testbase import AiidaTestCase
from aiida.work.persistence import AiiDAPersister
import aiida.work.utils as util
from aiida.work.test_utils import DummyProcess
from aiida import work


class TestProcess(AiidaTestCase):
    """ Test the basic saving and loading of process states """

    def setUp(self):
        super(TestProcess, self).setUp()
        work.runners.set_runner(None)
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def tearDown(self):
        super(TestProcess, self).tearDown()
        self.assertEquals(len(util.ProcessStack.stack()), 0)

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
        self.assertTrue(isinstance(process.calc.checkpoint, basestring))

        self.persister.delete_checkpoint(process.pid)
        self.assertEquals(process.calc.checkpoint, None)