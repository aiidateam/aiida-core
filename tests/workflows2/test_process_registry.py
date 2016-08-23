
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from unittest import TestCase
from aiida.workflows2.process import Process
from aiida.workflows2.defaults import registry
from aiida.workflows2.wf import wf
from aiida.common.lang import override
from aiida.workflows2.run import async
from aiida.orm.data.simple import Int
import aiida.workflows2.util as util


class RegistryTester(Process):
    @override
    def _run(self):
        assert registry.current_pid == self.pid
        assert registry.current_calc_node is self.calc
        nested_tester()

@wf
def registry_tester():
    # Call a wf
    future = async(nested_tester)
    out = future.result()
    assert future.pid == out['pid']
    assert future.pid == out['node_pk']

    # Call a Process
    RegistryTester.run()

    return {'pid': Int(registry.current_pid),
            'node_pk': Int(registry.current_calc_node.pk)}


@wf
def nested_tester():
    return {'pid': Int(registry.current_pid),
            'node_pk': Int(registry.current_calc_node.pk)}


class TestProcessRegistry(TestCase):
    """
    These these check that the registry is giving out the right pid which when
    using storage is equal to the node pk.
    """
    def setUp(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def tearDown(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_process_pid_and_calc(self):
        RegistryTester.run()

    def test_wf_pid_and_calc(self):
        future = async(registry_tester)
        out = future.result()

        self.assertEqual(out['pid'], future.pid)
        self.assertEqual(out['node_pk'], future.pid)





