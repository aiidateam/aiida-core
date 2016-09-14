
import tempfile

from test.util import DbTestCase
from aiida.workflows2.persistence import Persistence
import aiida.workflows2.util as util
from aiida.workflows2.test_utils import DummyProcess


class TestProcess(DbTestCase):
    def setUp(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

        self.persistence = Persistence(running_directory=tempfile.mkdtemp())

    def tearDown(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_save_load(self):
        dp = DummyProcess.new_instance()

        # Create a bundle
        b = self.persistence.create_bundle(dp)
        # Save a bundle and reload it
        self.persistence.save(dp)
        b2 = self.persistence.load_checkpoint(dp.pid)
        # Now check that they are equal
        self.assertEqual(b, b2)
