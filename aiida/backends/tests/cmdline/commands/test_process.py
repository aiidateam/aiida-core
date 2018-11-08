# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi process`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import datetime
import subprocess
import sys
import time
from concurrent.futures import Future

from click.testing import CliRunner
from tornado import gen
import kiwipy
import plumpy

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_process
from aiida.work import test_utils
from aiida import work


class TestVerdiProcess(AiidaTestCase):
    """Tests for `verdi process`."""

    TEST_TIMEOUT = 5.

    def setUp(self):
        super(TestVerdiProcess, self).setUp()
        from aiida.common.profile import get_profile
        from aiida.daemon.client import DaemonClient

        profile = get_profile()
        self.daemon_client = DaemonClient(profile)
        self.daemon_pid = subprocess.Popen(
            self.daemon_client.cmd_string.split(), stderr=sys.stderr, stdout=sys.stdout).pid
        self.runner = work.AiiDAManager.create_runner(rmq_submit=True)
        self.cli_runner = CliRunner()

    def tearDown(self):
        import os
        import signal

        os.kill(self.daemon_pid, signal.SIGTERM)
        super(TestVerdiProcess, self).tearDown()

    def test_pause_play_kill(self):
        """
        Test the pause/play/kill commands
        """
        from aiida.orm import load_node

        calc = self.runner.submit(test_utils.WaitProcess)
        start_time = time.time()
        while calc.process_state is not plumpy.ProcessState.WAITING:
            if time.time() - start_time >= self.TEST_TIMEOUT:
                self.fail('Timed out waiting for process to enter waiting state')

        self.assertFalse(calc.paused)
        result = self.cli_runner.invoke(cmd_process.process_pause, [str(calc.pk)])
        self.assertIsNone(result.exception, result.exception)

        # We need to make sure that the process is picked up by the daemon and put in the Waiting state before we start
        # running the CLI commands, so we add a broadcast subscriber for the state change, which when hit will set the
        # future to True. This will be our signal that we can start testing
        waiting_future = Future()
        filters = kiwipy.BroadcastFilter(
            lambda *args, **kwargs: waiting_future.set_result(True), sender=calc.pk, subject='state_changed.*.waiting')
        self.runner.communicator.add_broadcast_subscriber(filters)

        # The process may already have been picked up by the daemon and put in the waiting state, before the subscriber
        # got the chance to attach itself, making it have missed the broadcast. That's why check if the state is already
        # waiting, and if not, we run the loop of the runner to start waiting for the broadcast message. To make sure
        # that we have the latest state of the node as it is in the database, we force refresh it by reloading it.
        calc = load_node(calc.pk)
        if calc.process_state != plumpy.ProcessState.WAITING:
            self.runner.loop.run_sync(lambda: with_timeout(waiting_future))

        # Here we now that the process is with the daemon runner and in the waiting state so we can starting running
        # the `verdi process` commands that we want to test
        result = self.cli_runner.invoke(cmd_process.process_pause, ['--wait', str(calc.pk)])
        self.assertIsNone(result.exception, result.exception)
        self.assertTrue(calc.paused)

        result = self.cli_runner.invoke(cmd_process.process_play, ['--wait', str(calc.pk)])
        self.assertIsNone(result.exception, result.exception)
        self.assertFalse(calc.paused)

        result = self.cli_runner.invoke(cmd_process.process_kill, ['--wait', str(calc.pk)])
        self.assertIsNone(result.exception, result.exception)
        self.assertTrue(calc.is_terminated)
        self.assertTrue(calc.is_killed)


@gen.coroutine
def with_timeout(what, timeout=5.0):
    raise gen.Return((yield gen.with_timeout(datetime.timedelta(seconds=timeout), what)))
