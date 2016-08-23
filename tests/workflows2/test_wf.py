import unittest

from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from aiida.workflows2.wf import wf
from aiida.workflows2.run import async, run
from aiida.orm.data.simple import TRUE
import aiida.workflows2.util as util


@wf
def simple_wf():
    return {'result': TRUE}

@wf
def return_input(inp):
    return {'result': inp}


class TestWf(unittest.TestCase):
    def setUp(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def tearDown(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_blocking(self):
        self.assertTrue(simple_wf()['result'])
        self.assertTrue(return_input(TRUE)['result'])

    def test_async(self):
        self.assertTrue(async(simple_wf).result()['result'])
        self.assertTrue(async(return_input, TRUE).result()['result'])

    def test_run(self):
        self.assertTrue(run(simple_wf)['result'])
        self.assertTrue(run(return_input, TRUE)['result'])
