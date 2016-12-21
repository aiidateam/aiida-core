
import tempfile

import plum.process_monitor
from aiida.backends.testbase import AiidaTestCase
from aiida.work.persistence import Persistence
import aiida.work.util as util
from aiida.work.test_utils import DummyProcess


class TestProcess(AiidaTestCase):
    def setUp(self):
        super(TestProcess, self).setUp()
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

        self.persistence = Persistence(running_directory=tempfile.mkdtemp())

    def tearDown(self):
        super(TestProcess, self).tearDown()
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

    def test_save_load(self):
        dp = DummyProcess.new_instance()

        # Create a bundle
        b = self.persistence.create_bundle(dp)
        # Save a bundle and reload it
        self.persistence.save(dp)
        b2 = self.persistence.load_checkpoint(dp.pid)
        # Now check that they are equal
        self.assertEqual(b, b2)

        dp.run_until_complete()
