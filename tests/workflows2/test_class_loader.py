import unittest

from plum.util import fullname
from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation
from aiida.workflows2.defaults import class_loader
import aiida.workflows2.util as util
from aiida.workflows2.legacy.job_process import JobProcess


class TestJobProcess(unittest.TestCase):
    def setUp(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def tearDown(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_class_loader(self):
        PwProcess = JobProcess.build(PwCalculation)
        LoadedClass = class_loader.load_class(fullname(PwProcess))

        self.assertEqual(PwProcess.__name__, LoadedClass.__name__)
        self.assertEqual(fullname(PwProcess), fullname(LoadedClass))

