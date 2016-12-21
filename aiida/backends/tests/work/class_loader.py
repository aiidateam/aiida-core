
from aiida.backends.testbase import AiidaTestCase

from plum.util import fullname
from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation
from aiida.work.defaults import class_loader
import aiida.work.util as util
from aiida.work.legacy.job_process import JobProcess


class TestJobProcess(AiidaTestCase):
    def setUp(self):
        super(TestJobProcess, self).setUp()
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def tearDown(self):
        super(TestJobProcess, self).tearDown()
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_class_loader(self):
        PwProcess = JobProcess.build(PwCalculation)
        LoadedClass = class_loader.load_class(fullname(PwProcess))

        self.assertEqual(PwProcess.__name__, LoadedClass.__name__)
        self.assertEqual(fullname(PwProcess), fullname(LoadedClass))

