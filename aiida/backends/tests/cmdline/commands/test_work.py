# -*- coding: utf-8 -*-
import uuid

import click
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import work
from aiida.common.links import LinkType
from aiida.common.log import LOG_LEVEL_REPORT
from aiida.orm.calculation.function import FunctionCalculation
from aiida.orm.calculation.work import WorkCalculation
from aiida.work import runners, rmq, test_utils

class TestVerdiWork(AiidaTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestVerdiWork, cls).setUpClass()
        rmq_config = rmq.get_rmq_config()

        # These two need to share a common event loop otherwise the first will never send
        # the message while the daemon is running listening to intercept
        cls.runner = runners.Runner(
            rmq_config=rmq_config,
            rmq_submit=True,
            poll_interval=0.)

        cls.daemon_runner = runners.DaemonRunner(
            rmq_config=rmq_config,
            rmq_submit=True,
            poll_interval=0.)

    def setUp(self):
        super(TestVerdiWork, self).setUp()
        self.cli_runner = CliRunner()

    def tearDown(self):
        super(TestVerdiWork, self).tearDown()

    def get_lines(self, result):
        return [e for e in result.output.split('\n') if e]

    def test_help(self):
        """
        Verify that all subcommands support both of the -h/--help options to show the help string
        """
        for sub_command in work.verdi_work.commands.values():
            for option in ['-h', '--help']:
                result = self.cli_runner.invoke(sub_command, [option])
                self.assertIsNone(result.exception)

    def test_pause_play_kill(self):
        """
        Test the pause/play/kill commands
        """
        from concurrent.futures import ThreadPoolExecutor

        calc = self.runner.submit(test_utils.WaitProcess)
        executor = ThreadPoolExecutor(max_workers=1)

        try:
            future = executor.submit(self.daemon_runner.start)

            self.assertFalse(calc.paused)
            result = self.cli_runner.invoke(work.pause, [str(calc.pk)])

            self.assertTrue(calc.paused)
            self.assertIsNone(result.exception)

            result = self.cli_runner.invoke(work.play, [str(calc.pk)])

            self.assertFalse(calc.paused)
            self.assertIsNone(result.exception)

            result = self.cli_runner.invoke(work.kill, [str(calc.pk)])

            self.assertTrue(calc.is_terminated)
            self.assertTrue(calc.is_killed)
            self.assertIsNone(result.exception)
        finally:
            self.daemon_runner.stop()
            executor.shutdown()

    def test_status(self):
        """
        Test the status command
        """
        calc = self.runner.submit(test_utils.WaitProcess)
        result = self.cli_runner.invoke(work.status, [str(calc.pk)])
        self.assertIsNone(result.exception)

    def test_list(self):
        """
        Test the list command
        """
        from aiida.work.processes import ProcessState

        # Number of output lines in -r/--raw format should be zero when there are no calculations yet
        result = self.cli_runner.invoke(work.do_list, ['-r'])
        self.assertIsNone(result.exception)
        self.assertEquals(len(self.get_lines(result)), 0)

        calcs = []

        # Create 6 FunctionCalculations and WorkCalculations (one for each ProcessState)
        for index, state in enumerate(ProcessState):

            calc = FunctionCalculation()
            calc._set_process_state(state)

            # Set the FunctionCalculation as successful
            if state == ProcessState.FINISHED:
                calc._set_finish_status(0)

            calc.store()
            calcs.append(calc)

            calc = WorkCalculation()
            calc._set_process_state(state)

            # Set the WorkCalculation as failed
            if state == ProcessState.FINISHED:
                calc._set_finish_status(1)

            calc.store()
            calcs.append(calc)

        # Default behavior should yield all active states (CREATED, RUNNING and WAITING) so six in total
        result = self.cli_runner.invoke(work.do_list, ['-r'])
        self.assertIsNone(result.exception)
        self.assertEquals(len(self.get_lines(result)), 6)

        # Adding the all option should return all entries regardless of process state
        for flag in ['-a', '--all']:
            result = self.cli_runner.invoke(work.do_list, ['-r', flag])
            self.assertIsNone(result.exception)
            self.assertEquals(len(self.get_lines(result)), 12)

        # Passing the limit option should limit the results
        for flag in ['-l', '--limit']:
            result = self.cli_runner.invoke(work.do_list, ['-r', flag, '6'])
            self.assertIsNone(result.exception)
            self.assertEquals(len(self.get_lines(result)), 6)

        # Filtering for a specific process state
        for flag in ['-S', '--process-state']:
            for flag_value in ['created', 'running', 'waiting', 'killed', 'excepted', 'finished']:
                result = self.cli_runner.invoke(work.do_list, ['-r', flag, flag_value])
                self.assertIsNone(result.exception)
                self.assertEquals(len(self.get_lines(result)), 2)

        # Filtering for finish status should only get us one
        for flag in ['-F', '--finish-status']:
            for finish_status in ['0', '1']:
                result = self.cli_runner.invoke(work.do_list, ['-r', flag, finish_status])
                self.assertIsNone(result.exception)
                self.assertEquals(len(self.get_lines(result)), 1)

        # Passing the failed flag as a shortcut for FINISHED + non-zero finish status
        for flag in ['-x', '--failed']:
            result = self.cli_runner.invoke(work.do_list, ['-r', flag])
            self.assertIsNone(result.exception)
            self.assertEquals(len(self.get_lines(result)), 1)

        # Projecting on pk should allow us to verify all the pks
        for flag in ['-P', '--project']:
            result = self.cli_runner.invoke(work.do_list, ['-r', flag, 'pk'])
            self.assertIsNone(result.exception)
            self.assertEquals(len(self.get_lines(result)), 6)

            for line in self.get_lines(result):
                self.assertIn(line, [str(calc.pk) for calc in calcs])

    def test_report(self):
        """
        Test the report command
        """
        grandparent = WorkCalculation().store()
        parent = WorkCalculation().store()
        child = WorkCalculation().store()

        parent.add_link_from(grandparent, link_type=LinkType.CALL)
        child.add_link_from(parent, link_type=LinkType.CALL)

        grandparent.logger.log(LOG_LEVEL_REPORT, 'grandparent_message')
        parent.logger.log(LOG_LEVEL_REPORT, 'parent_message')
        child.logger.log(LOG_LEVEL_REPORT, 'child_message')

        result = self.cli_runner.invoke(work.report, [str(grandparent.pk)])
        self.assertIsNone(result.exception)
        self.assertEquals(len(self.get_lines(result)), 3)

        result = self.cli_runner.invoke(work.report, [str(parent.pk)])
        self.assertIsNone(result.exception)
        self.assertEquals(len(self.get_lines(result)), 2)

        result = self.cli_runner.invoke(work.report, [str(child.pk)])
        self.assertIsNone(result.exception)
        self.assertEquals(len(self.get_lines(result)), 1)

        # Max depth should limit nesting level
        for flag in ['-m', '--max-depth']:
            for flag_value in [1, 2]:
                result = self.cli_runner.invoke(work.report, [str(grandparent.pk), flag, str(flag_value)])
                self.assertIsNone(result.exception)
                self.assertEquals(len(self.get_lines(result)), flag_value)

        # Filtering for other level name such as WARNING should not have any hits and only print the no log message
        for flag in ['-l', '--levelname']:
            result = self.cli_runner.invoke(work.report, [str(grandparent.pk), flag, 'WARNING'])
            self.assertIsNone(result.exception)
            self.assertEquals(len(self.get_lines(result)), 1)
            self.assertEquals(self.get_lines(result)[0], 'No log messages recorded for this work calculation')

    def test_plugins(self):
        """
        Test the plugins command. As of writing there are no default plugins defined for aiida-core
        """
        result = self.cli_runner.invoke(work.plugins, ['aiida.workflows:non_existent'])
        self.assertIsNotNone(result.exception)
