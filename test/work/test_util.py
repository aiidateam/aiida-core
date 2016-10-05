# -*- coding: utf-8 -*-

from test.util import DbTestCase

from aiida.work.process import Process
from aiida.work.workfunction import workfunction
from aiida.common.lang import override
from aiida.work.run import async
from aiida.orm.data.base import Int
from aiida.work.util import ProcessStack

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"


class StackTester(Process):
    @override
    def _run(self):
        assert ProcessStack.get_active_process_id() == self.pid
        assert ProcessStack.get_active_process_calc_node() is self.calc
        nested_tester()


@workfunction
def registry_tester():
    # Call a wf
    future = async(nested_tester)
    out = future.result()
    assert future.pid == out['pid']
    assert future.pid == out['node_pk']

    # Call a Process
    StackTester.run()

    return {'pid': Int(ProcessStack.get_active_process_id()),
            'node_pk': Int(ProcessStack.get_active_process_calc_node().pk)}


@workfunction
def nested_tester():
    return {'pid': Int(ProcessStack.get_active_process_id()),
            'node_pk': Int(ProcessStack.get_active_process_calc_node().pk)}


class TestProcessRegistry(DbTestCase):
    """
    These these check that the registry is giving out the right pid which when
    using storage is equal to the node pk.
    """
    def setUp(self):
        self.assertEquals(len(ProcessStack.stack()), 0)

    def tearDown(self):
        self.assertEquals(len(ProcessStack.stack()), 0)

    def test_process_pid_and_calc(self):
        StackTester.run()

    def test_wf_pid_and_calc(self):
        future = async(registry_tester)
        out = future.result()

        self.assertEqual(out['pid'], future.pid)
        self.assertEqual(out['node_pk'], future.pid)





