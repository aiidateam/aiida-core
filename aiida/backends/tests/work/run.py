# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.backends.testbase import AiidaTestCase
import shutil
import tempfile

import plum.process_monitor
from aiida.orm.data.base import Int, Str
from aiida.work.run import queue_up
from aiida.work.test_utils import DummyProcess
from aiida.work.persistence import Persistence



class TestRun(AiidaTestCase):
    def setUp(self):
        super(TestRun, self).setUp()
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)
        self.storedir = tempfile.mkdtemp()
        self.storage = Persistence.create_from_basedir(self.storedir)

    def tearDown(self):
        super(TestRun, self).tearDown()
        shutil.rmtree(self.storedir)
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

    def test_queue_up(self):
        inputs = {'a': Int(2), 'b': Str('test')}

        # Queue up the process
        pid = queue_up(DummyProcess, inputs, self.storage)

        # Then load the checkpoint and instantiate the class
        cp = self.storage.load_checkpoint(pid)

        dp = DummyProcess.create_from(cp)
        self.assertIsInstance(dp, DummyProcess)
        self.assertEqual(dp.raw_inputs, inputs)
        dp.run_until_complete()