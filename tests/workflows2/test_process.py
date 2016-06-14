
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from unittest import TestCase
from aiida.workflows2.process import Process
from aiida.workflows2.db_types import Int
import uuid


class BadOutput(Process):
    @classmethod
    def _define(cls, spec):
        spec.dynamic_output()

    def _run(self):
        self.out("bad_output", 5)


class DummyProcess(Process):
    @classmethod
    def _define(cls, spec):
        spec.dynamic_input()
        spec.dynamic_output()

    def _run(self):
        pass


class ProcessScope(object):
    def __init__(self, process, pid=None, inputs=None):
        self._process = process
        self._pid = pid
        self._inputs = inputs

    def __enter__(self):
        self._process.on_create(self._pid, self._inputs)
        return self._process

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._process.on_stop()


class TestProcess(TestCase):
    def test_inputs(self):
        with self.assertRaises(AssertionError):
            BadOutput.run()

    def test_pid_uuid(self):
        with ProcessScope(DummyProcess(store_provenance=False)) as p:
            self.assertEqual(uuid.UUID(p._calc.uuid), p.pid)

    def test_input_link_creation(self):
        inputs = ["1", "2", "3", "4"]

        with ProcessScope(
                DummyProcess(store_provenance=True),
                inputs={l: Int(l) for l in inputs}) as p:

            for label, value in p._calc.get_inputs_dict().iteritems():
                self.assertTrue(label in inputs)
                self.assertEqual(int(label), int(value.value))
                inputs.remove(label)

            # Make sure there are no other inputs
            self.assertFalse(inputs)


