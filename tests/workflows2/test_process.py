# -*- coding: utf-8 -*-

from aiida.backends.utils import load_dbenv, is_dbenv_loaded

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"

if not is_dbenv_loaded():
    load_dbenv()

from unittest import TestCase
from aiida.workflows2.process import Process
from aiida.workflows2.db_types import Int
from workflows2.common import ProcessScope, DummyProcess, BadOutput
from aiida.common.lang import override
import uuid
import threading


class ProcessStackTest(Process):
    @override
    def _run(self):
        pass

    @override
    def on_create(self, pid, inputs=None):
        super(ProcessStackTest, self).on_create(pid, inputs)
        self._thread_id = threading.current_thread().ident

    @override
    def on_recreate(self, pid, saved_instance_state):
        super(ProcessStackTest, self).on_recreate(pid, saved_instance_state)
        self._thread_id = threading.current_thread().ident

    @override
    def on_stop(self):
        # The therad must match the one used in on_create because process
        # stack is using thread local storage to keep track of who called who
        super(ProcessStackTest, self).on_stop()
        assert self._thread_id is threading.current_thread().ident


class TestProcess(TestCase):
    def test_process_stack(self):
        ProcessStackTest.run()

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

