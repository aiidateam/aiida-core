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
from aiida.work.persistence import Persistence
import aiida.work.utils as util
from aiida.work.test_utils import DummyProcess
from aiida import work


class TestProcess(AiidaTestCase):
    """ Test the basic saving and loading of process states """

    def setUp(self):
        super(TestProcess, self).setUp()
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

# class TestProcess(AiidaTestCase):
#     def setUp(self):
#         super(TestProcess, self).setUp()
#         self.assertEquals(len(util.ProcessStack.stack()), 0)
#
#         self.persistence = Persistence(running_directory=tempfile.mkdtemp())
#
#     def tearDown(self):
#         super(TestProcess, self).tearDown()
#         self.assertEquals(len(util.ProcessStack.stack()), 0)
#
#     def test_save_load(self):
#         dp = DummyProcess()
#
#         # Create a bundle
#         b = self.persistence.create_bundle(dp)
#         # Save a bundle and reload it
#         self.persistence.save(dp)
#         b2 = self.persistence._load_checkpoint(dp.pid)
#         # Now check that they are equal
#         self.assertEqual(b, b2)
#
#         work.run(dp)
