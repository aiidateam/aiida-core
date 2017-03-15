# -*- coding: utf-8 -*-

from aiida.backends.testbase import AiidaTestCase

from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation
from aiida.work.class_loader import ClassLoader
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
        cl = ClassLoader()
        PwProcess = JobProcess.build(PwCalculation)