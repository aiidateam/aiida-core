
from test.util import DbTestCase
import aiida.work.util as util
from aiida.orm.data.base import Str, Int
from aiida.workflows.test import WorkflowTestEmpty


class TestJobProcess(DbTestCase):
    def setUp(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def tearDown(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_build(self):
        DummyProc = WorkflowTestEmpty.process()
        self.assertEqual(DummyProc._WF_CLASS, WorkflowTestEmpty)

    def test_instantiate(self):
        DummyProc = WorkflowTestEmpty.process()
        p = DummyProc.new_instance()
        self.assertTrue(isinstance(p._wf, WorkflowTestEmpty))

    def test_parameters(self):
        """
        Test the inputs get passed as workflow parameters.
        """
        inputs = {'a': Int(1), 'b': Str('b')}
        DummyProc = WorkflowTestEmpty.process()
        p = DummyProc.new_instance(inputs=inputs)
        self.assertEqual(p._wf.get_parameters(), p.inputs)

