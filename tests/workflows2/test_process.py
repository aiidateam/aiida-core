
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from unittest import TestCase
from aiida.orm import load_node
from aiida.workflows2.process import Process
from aiida.workflows2.db_types import make_int
from aiida.workflows2.run import run
import aiida.workflows2.util as util
from aiida.workflows2.test_utils import DummyProcess, BadOutput
from aiida.common.lang import override
import uuid
import threading


class ProcessStackTest(Process):
    @override
    def _run(self):
        pass

    @override
    def on_create(self, pid, inputs, saved_instance_state):
        super(ProcessStackTest, self).on_create(
            pid, inputs, saved_instance_state)
        self._thread_id = threading.current_thread().ident

    @override
    def on_stop(self):
        # The therad must match the one used in on_create because process
        # stack is using thread local storage to keep track of who called who
        super(ProcessStackTest, self).on_stop()
        assert self._thread_id is threading.current_thread().ident


class TestProcess(TestCase):
    def setUp(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def tearDown(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_process_stack(self):
        ProcessStackTest.run()

    def test_inputs(self):
        with self.assertRaises(AssertionError):
            BadOutput.run()

    def test_pid_is_uuid(self):
        p = DummyProcess.new_instance(inputs={'_store_provenance': False})
        self.assertEqual(uuid.UUID(p._calc.uuid), p.pid)
        p.stop()
        p.run_until_complete()

    def test_input_link_creation(self):
        dummy_inputs = ["1", "2", "3", "4"]

        inputs = {l: make_int(l) for l in dummy_inputs}
        inputs['_store_provenance'] = True
        p = DummyProcess.new_instance(inputs)

        for label, value in p._calc.get_inputs_dict().iteritems():
            self.assertTrue(label in inputs)
            self.assertEqual(int(label), int(value.value))
            dummy_inputs.remove(label)

        # Make sure there are no other inputs
        self.assertFalse(dummy_inputs)

        p.stop()
        p.run_until_complete()

    def test_none_input(self):
        # Check that if we pass no input the process runs fine
        DummyProcess.new_instance().run_until_complete()
        # Check that if we explicitly pass None as the input it also runs fine
        DummyProcess.new_instance(inputs=None).run_until_complete()

    def test_seal(self):
        pid = run(DummyProcess, _return_pid=True)[1]
        self.assertTrue(load_node(pk=pid).is_sealed)

    def test_description(self):
        dp = DummyProcess.new_instance(inputs={'_description': 'My description'})
        self.assertEquals(dp.calc.description, 'My description')

        with self.assertRaises(TypeError):
            DummyProcess.new_instance(inputs={'_description': 5})

    def test_label(self):
        dp = DummyProcess.new_instance(inputs={'_label': 'My label'})
        self.assertEquals(dp.calc.label, 'My label')

        with self.assertRaises(TypeError):
            DummyProcess.new_instance(inputs={'_label': 5})
