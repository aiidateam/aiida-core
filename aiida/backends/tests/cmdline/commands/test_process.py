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
from aiida.common.links import LinkType
from aiida.common.log import LOG_LEVEL_REPORT
from aiida.orm.node.process import ProcessNode, WorkFunctionNode, WorkChainNode
from aiida.work import test_utils
from aiida import work


def get_result_lines(result):
    return [e for e in result.output.split('\n') if e]


class TestVerdiProcessDaemon(AiidaTestCase):
    """Tests for `verdi process` that require a running daemon."""

    TEST_TIMEOUT = 5.

    def setUp(self):
        super(TestVerdiProcessDaemon, self).setUp()
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
        super(TestVerdiProcessDaemon, self).tearDown()

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
        self.assertIsNone(result.exception, result.output)

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
        self.assertIsNone(result.exception, result.output)
        self.assertTrue(calc.paused)

        result = self.cli_runner.invoke(cmd_process.process_play, ['--wait', str(calc.pk)])
        self.assertIsNone(result.exception, result.output)
        self.assertFalse(calc.paused)

        result = self.cli_runner.invoke(cmd_process.process_kill, ['--wait', str(calc.pk)])
        self.assertIsNone(result.exception, result.output)
        self.assertTrue(calc.is_terminated)
        self.assertTrue(calc.is_killed)


class TestVerdiProcess(AiidaTestCase):
    """Tests for `verdi process`."""

    TEST_TIMEOUT = 5.

    def setUp(self):
        super(TestVerdiProcess, self).setUp()
        self.cli_runner = CliRunner()

    def test_list(self):
        """Test the list command."""
        # pylint: disable=protected-access
        from aiida.work.processes import ProcessState

        # Number of output lines in -r/--raw format should be zero when there are no calculations yet
        result = self.cli_runner.invoke(cmd_process.process_list, ['-r'])
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 0)

        calcs = []

        # Create 6 WorkFunctionNodes and WorkChainNodes (one for each ProcessState)
        for state in ProcessState:

            calc = WorkFunctionNode()
            calc._set_process_state(state)

            # Set the WorkFunctionNode as successful
            if state == ProcessState.FINISHED:
                calc._set_exit_status(0)

            calc.store()
            calcs.append(calc)

            calc = WorkChainNode()
            calc._set_process_state(state)

            # Set the WorkChainNode as failed
            if state == ProcessState.FINISHED:
                calc._set_exit_status(1)

            calc.store()
            calcs.append(calc)

        # Default behavior should yield all active states (CREATED, RUNNING and WAITING) so six in total
        result = self.cli_runner.invoke(cmd_process.process_list, ['-r'])
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 6)

        # Adding the all option should return all entries regardless of process state
        for flag in ['-a', '--all']:
            result = self.cli_runner.invoke(cmd_process.process_list, ['-r', flag])
            self.assertIsNone(result.exception, result.output)
            self.assertEqual(len(get_result_lines(result)), 12)

        # Passing the limit option should limit the results
        for flag in ['-l', '--limit']:
            result = self.cli_runner.invoke(cmd_process.process_list, ['-r', flag, '6'])
            self.assertIsNone(result.exception, result.output)
            self.assertEqual(len(get_result_lines(result)), 6)

        # Filtering for a specific process state
        for flag in ['-S', '--process-state']:
            for flag_value in ['created', 'running', 'waiting', 'killed', 'excepted', 'finished']:
                result = self.cli_runner.invoke(cmd_process.process_list, ['-r', flag, flag_value])
                self.assertIsNone(result.exception, result.output)
                self.assertEqual(len(get_result_lines(result)), 2)

        # Filtering for exit status should only get us one
        for flag in ['-E', '--exit-status']:
            for exit_status in ['0', '1']:
                result = self.cli_runner.invoke(cmd_process.process_list, ['-r', flag, exit_status])
                self.assertIsNone(result.exception, result.output)
                self.assertEqual(len(get_result_lines(result)), 1)

        # Passing the failed flag as a shortcut for FINISHED + non-zero exit status
        for flag in ['-X', '--failed']:
            result = self.cli_runner.invoke(cmd_process.process_list, ['-r', flag])
            self.assertIsNone(result.exception, result.output)
            self.assertEqual(len(get_result_lines(result)), 1)

        # Projecting on pk should allow us to verify all the pks
        for flag in ['-P', '--project']:
            result = self.cli_runner.invoke(cmd_process.process_list, ['-r', flag, 'pk'])
            self.assertIsNone(result.exception, result.output)
            self.assertEqual(len(get_result_lines(result)), 6)

            for line in get_result_lines(result):
                self.assertIn(line.strip(), [str(calc.pk) for calc in calcs])

    def test_process_show(self):
        """Test verdi process show"""
        node = ProcessNode().store()

        # Running without identifiers should not except and not print anything
        options = []
        result = self.cli_runner.invoke(cmd_process.process_show, options)
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 0)

        # Giving a single identifier should print a non empty string message
        options = [str(node.pk)]
        result = self.cli_runner.invoke(cmd_process.process_show, options)
        self.assertIsNone(result.exception, result.output)
        self.assertTrue(len(get_result_lines(result)) > 0)

        # Giving multiple identifiers should print a non empty string message
        options = [str(calc.pk) for calc in [node]]
        result = self.cli_runner.invoke(cmd_process.process_show, options)
        self.assertIsNone(result.exception, result.output)
        self.assertTrue(len(get_result_lines(result)) > 0)

    def test_process_report(self):
        """Test verdi process report"""
        node = ProcessNode().store()

        # Running without identifiers should not except and not print anything
        options = []
        result = self.cli_runner.invoke(cmd_process.process_report, options)
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 0)

        # Giving a single identifier should print a non empty string message
        options = [str(node.pk)]
        result = self.cli_runner.invoke(cmd_process.process_report, options)
        self.assertIsNone(result.exception, result.output)
        self.assertTrue(len(get_result_lines(result)) > 0)

        # Giving multiple identifiers should print a non empty string message
        options = [str(calc.pk) for calc in [node]]
        result = self.cli_runner.invoke(cmd_process.process_report, options)
        self.assertIsNone(result.exception, result.output)
        self.assertTrue(len(get_result_lines(result)) > 0)

    def test_report(self):
        """Test the report command."""
        grandparent = WorkChainNode().store()
        parent = WorkChainNode().store()
        child = WorkChainNode().store()

        parent.add_link_from(grandparent, link_type=LinkType.CALL)
        child.add_link_from(parent, link_type=LinkType.CALL)

        grandparent.logger.log(LOG_LEVEL_REPORT, 'grandparent_message')
        parent.logger.log(LOG_LEVEL_REPORT, 'parent_message')
        child.logger.log(LOG_LEVEL_REPORT, 'child_message')

        result = self.cli_runner.invoke(cmd_process.process_report, [str(grandparent.pk)])
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 3)

        result = self.cli_runner.invoke(cmd_process.process_report, [str(parent.pk)])
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 2)

        result = self.cli_runner.invoke(cmd_process.process_report, [str(child.pk)])
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 1)

        # Max depth should limit nesting level
        for flag in ['-m', '--max-depth']:
            for flag_value in [1, 2]:
                result = self.cli_runner.invoke(cmd_process.process_report,
                                                [str(grandparent.pk), flag, str(flag_value)])
                self.assertIsNone(result.exception, result.output)
                self.assertEqual(len(get_result_lines(result)), flag_value)

        # Filtering for other level name such as WARNING should not have any hits and only print the no log message
        for flag in ['-l', '--levelname']:
            result = self.cli_runner.invoke(cmd_process.process_report, [str(grandparent.pk), flag, 'WARNING'])
            self.assertIsNone(result.exception, result.output)
            self.assertEqual(len(get_result_lines(result)), 1)
            self.assertEqual(get_result_lines(result)[0], 'No log messages recorded for this entry')

    def test_work_show(self):
        """Test verdi process show"""
        workchain_one = WorkChainNode().store()
        workchain_two = WorkChainNode().store()
        workchains = [workchain_one, workchain_two]

        # Running without identifiers should not except and not print anything
        options = []
        result = self.cli_runner.invoke(cmd_process.process_show, options)
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 0)

        # Giving a single identifier should print a non empty string message
        options = [str(workchain_one.pk)]
        result = self.cli_runner.invoke(cmd_process.process_show, options)
        self.assertIsNone(result.exception, result.output)
        self.assertTrue(len(get_result_lines(result)) > 0)

        # Giving multiple identifiers should print a non empty string message
        options = [str(workchain.pk) for workchain in workchains]
        result = self.cli_runner.invoke(cmd_process.process_show, options)
        self.assertIsNone(result.exception, result.output)
        self.assertTrue(len(get_result_lines(result)) > 0)


@gen.coroutine
def with_timeout(what, timeout=5.0):
    raise gen.Return((yield gen.with_timeout(datetime.timedelta(seconds=timeout), what)))
