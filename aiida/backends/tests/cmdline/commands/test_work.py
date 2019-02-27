# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi work`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_work
from aiida.common.links import LinkType
from aiida.common.log import LOG_LEVEL_REPORT
from aiida.orm import WorkChainNode, WorkFunctionNode


def get_result_lines(result):
    return [e for e in result.output.split('\n') if e]


class TestVerdiWork(AiidaTestCase):
    """Tests for `verdi work`."""

    def setUp(self):
        super(TestVerdiWork, self).setUp()
        self.cli_runner = CliRunner()

    def test_status(self):
        """Test the status command."""
        calc = WorkChainNode().store()
        result = self.cli_runner.invoke(cmd_work.work_status, [str(calc.pk)])
        self.assertClickResultNoException(result)

    def test_list(self):
        """Test the list command."""
        from aiida.engine import ProcessState

        # Number of output lines in -r/--raw format should be zero when there are no calculations yet
        result = self.cli_runner.invoke(cmd_work.work_list, ['-r'])
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 0)

        calcs = []

        # Create 6 WorkFunctionNodes and WorkChainNodes (one for each ProcessState)
        for state in ProcessState:

            calc = WorkFunctionNode()
            calc.set_process_state(state)

            # Set the WorkFunctionNode as successful
            if state == ProcessState.FINISHED:
                calc.set_exit_status(0)

            calc.store()
            calcs.append(calc)

            calc = WorkChainNode()
            calc.set_process_state(state)

            # Set the WorkChainNode as failed
            if state == ProcessState.FINISHED:
                calc.set_exit_status(1)

            calc.store()
            calcs.append(calc)

        # Default behavior should yield all active states (CREATED, RUNNING and WAITING) so six in total
        result = self.cli_runner.invoke(cmd_work.work_list, ['-r'])
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 6)

        # Adding the all option should return all entries regardless of process state
        for flag in ['-a', '--all']:
            result = self.cli_runner.invoke(cmd_work.work_list, ['-r', flag])
            self.assertIsNone(result.exception, result.output)
            self.assertEqual(len(get_result_lines(result)), 12)

        # Passing the limit option should limit the results
        for flag in ['-l', '--limit']:
            result = self.cli_runner.invoke(cmd_work.work_list, ['-r', flag, '6'])
            self.assertIsNone(result.exception, result.output)
            self.assertEqual(len(get_result_lines(result)), 6)

        # Filtering for a specific process state
        for flag in ['-S', '--process-state']:
            for flag_value in ['created', 'running', 'waiting', 'killed', 'excepted', 'finished']:
                result = self.cli_runner.invoke(cmd_work.work_list, ['-r', flag, flag_value])
                self.assertIsNone(result.exception, result.output)
                self.assertEqual(len(get_result_lines(result)), 2)

        # Filtering for exit status should only get us one
        for flag in ['-E', '--exit-status']:
            for exit_status in ['0', '1']:
                result = self.cli_runner.invoke(cmd_work.work_list, ['-r', flag, exit_status])
                self.assertIsNone(result.exception, result.output)
                self.assertEqual(len(get_result_lines(result)), 1)

        # Passing the failed flag as a shortcut for FINISHED + non-zero exit status
        for flag in ['-X', '--failed']:
            result = self.cli_runner.invoke(cmd_work.work_list, ['-r', flag])
            self.assertIsNone(result.exception, result.output)
            self.assertEqual(len(get_result_lines(result)), 1)

        # Projecting on pk should allow us to verify all the pks
        for flag in ['-P', '--project']:
            result = self.cli_runner.invoke(cmd_work.work_list, ['-r', flag, 'pk'])
            self.assertIsNone(result.exception, result.output)
            self.assertEqual(len(get_result_lines(result)), 6)

            for line in get_result_lines(result):
                self.assertIn(line.strip(), [str(calc.pk) for calc in calcs])

    def test_report(self):
        """Test the report command."""
        grandparent = WorkChainNode().store()
        parent = WorkChainNode().store()
        child = WorkChainNode().store()

        parent.add_incoming(grandparent, link_type=LinkType.CALL_WORK, link_label='link')
        child.add_incoming(parent, link_type=LinkType.CALL_WORK, link_label='link')

        grandparent.logger.log(LOG_LEVEL_REPORT, 'grandparent_message')
        parent.logger.log(LOG_LEVEL_REPORT, 'parent_message')
        child.logger.log(LOG_LEVEL_REPORT, 'child_message')

        result = self.cli_runner.invoke(cmd_work.work_report, [str(grandparent.pk)])
        self.assertClickResultNoException(result)
        self.assertEqual(len(get_result_lines(result)), 3)

        result = self.cli_runner.invoke(cmd_work.work_report, [str(parent.pk)])
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 2)

        result = self.cli_runner.invoke(cmd_work.work_report, [str(child.pk)])
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 1)

        # Max depth should limit nesting level
        for flag in ['-m', '--max-depth']:
            for flag_value in [1, 2]:
                result = self.cli_runner.invoke(cmd_work.work_report, [str(grandparent.pk), flag, str(flag_value)])
                self.assertIsNone(result.exception, result.output)
                self.assertEqual(len(get_result_lines(result)), flag_value)

        # Filtering for other level name such as WARNING should not have any hits and only print the no log message
        for flag in ['-l', '--levelname']:
            result = self.cli_runner.invoke(cmd_work.work_report, [str(grandparent.pk), flag, 'WARNING'])
            self.assertIsNone(result.exception, result.output)
            self.assertEqual(len(get_result_lines(result)), 1)
            self.assertEqual(get_result_lines(result)[0], 'No log messages recorded for this entry')

    def test_plugins(self):
        """Test the plugins command. As of writing there are no default plugins defined for aiida-core."""
        result = self.cli_runner.invoke(cmd_work.work_plugins, ['non_existent'])
        self.assertIsNotNone(result.exception)

    def test_work_show(self):
        """Test verdi work show"""
        workchain_one = WorkChainNode().store()
        workchain_two = WorkChainNode().store()
        workchains = [workchain_one, workchain_two]

        # Running without identifiers should not except and not print anything
        options = []
        result = self.cli_runner.invoke(cmd_work.work_show, options)
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 0)

        # Giving a single identifier should print a non empty string message
        options = [str(workchain_one.pk)]
        result = self.cli_runner.invoke(cmd_work.work_show, options)
        self.assertClickResultNoException(result)
        self.assertTrue(len(get_result_lines(result)) > 0)

        # Giving multiple identifiers should print a non empty string message
        options = [str(workchain.pk) for workchain in workchains]
        result = self.cli_runner.invoke(cmd_work.work_show, options)
        self.assertIsNone(result.exception, result.output)
        self.assertTrue(len(get_result_lines(result)) > 0)
