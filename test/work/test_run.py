# -*- coding: utf-8 -*-

from test.util import DbTestCase
import shutil
import tempfile

from aiida.orm.data.base import Int, Str
from aiida.work.run import queue_up
from aiida.work.test_utils import DummyProcess
from aiida.work.persistence import Persistence

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


class TestRun(DbTestCase):
    def setUp(self):
        self.storedir = tempfile.mkdtemp()
        self.storage = Persistence.create_from_basedir(self.storedir)

    def tearDown(self):
        shutil.rmtree(self.storedir)

    def test_queue_up(self):
        inputs = {'a': Int(2), 'b': Str('test')}

        # Queue up the process
        pid = queue_up(DummyProcess, inputs, self.storage)

        # Then load the checkpoint and instantiate the class
        cp = self.storage.load_checkpoint(pid)

        dp = DummyProcess.create_from(cp)
        self.assertIsInstance(dp, DummyProcess)
        self.assertEqual(dp.raw_inputs, inputs)
