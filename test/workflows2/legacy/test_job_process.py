
from test.util import DbTestCase

from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation
from aiida.workflows2.class_loader import ClassLoader
import aiida.workflows2.util as util
from aiida.workflows2.legacy.job_process import JobProcess



class TestJobProcess(DbTestCase):
    def setUp(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def tearDown(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_class_loader(self):
        cl = ClassLoader()
        PwProcess = JobProcess.build(PwCalculation)

    # def test_fail(self):
    #     from aiida.orm.computer import Computer
    #
    #     PwProcess = PwCalculation.process()
    #     PwProcess.run(inputs={
    #         '_options': {
    #             'computer': self.computer,
    #             'resources': {
    #                 'num_machines': 1,
    #                 'num_mpiprocs_per_machine': 1}}
    #     })