# -*- coding: utf-8 -*-

import uuid
import threading
from plum.process_monitor import ProcessMonitorListener, MONITOR
from aiida.backends.testbase import AiidaTestCase
import aiida.work.globals as globals
import aiida.work.test_utils as test_utils
import aiida.work.rmq
from plum.process_manager import ProcessManager

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"


class CaptureProcess(ProcessMonitorListener):
    def __init__(self):
        super(CaptureProcess, self).__init__()
        self.got_it = threading.Event()
        self.process = None

    def on_monitored_process_registered(self, process):
        self.process = process
        self.got_it.set()


class TestProcess(AiidaTestCase):
    """
    Test AiiDA's RabbitMQ functionalities.
    """

    def setUp(self):
        super(TestProcess, self).setUp()
        self.procman = ProcessManager()
        prefix = "{}.{}".format(self.__class__.__name__, uuid.uuid4())
        self._subscribers = aiida.work.rmq.enable_subscribers(self.procman, prefix)
        self.control_panel = aiida.work.rmq.ProcessControlPanel(prefix)

    def tearDown(self):
        self.procman.abort_all(timeout=10)
        self.assertEqual(self.procman.get_num_processes(), 0, "Not all processes are finished")
        self._subscribers.stop()

    def test_launch_simple(self):
        # Monitor launched processes
        capture = CaptureProcess()
        MONITOR.start_listening(capture)

        # Launch the process
        self.control_panel.launch.launch(test_utils.DummyProcess)

        self.assertTrue(capture.got_it.wait(5.), "The process wasn't launched in the timeout")
        self.assertIsInstance(capture.process, test_utils.DummyProcess)

    def test_launch_and_get_status(self):
        from plum.rmq.status import PROCS_KEY

        # Monitor launched processes
        capture = CaptureProcess()
        MONITOR.start_listening(capture)

        # Launch the process
        self.control_panel.launch.launch(test_utils.WaitChain)

        self.assertTrue(capture.got_it.wait(5.), "The process wasn't launched in the timeout")
        self.assertIsInstance(capture.process, test_utils.WaitChain)

        responses = self.control_panel.status.request(timeout=2.)
        self.assertEqual(len(responses), 1)
        procs = responses[0][PROCS_KEY]
        self.assertIn(capture.process.pid, procs)
        self.assertTrue(capture.process.abort(timeout=2.), "Process didn't abort in time")
