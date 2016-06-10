
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from unittest import TestCase
from aiida.workflows2.process import Process


class BadOutput(Process):
    @staticmethod
    def _define(spec):
        spec.dynamic_output()

    def _run(self):
        self.out("bad_output", 5)


class TestProcess(TestCase):
    def test_inputs(self):
        with self.assertRaises(AssertionError):
            BadOutput.run()
