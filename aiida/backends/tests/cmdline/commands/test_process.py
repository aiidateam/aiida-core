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
from __future__ import absolute_import
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_process
from aiida.work import runners, rmq, test_utils


def get_result_lines(result):
    return [e for e in result.output.split('\n') if e]


class TestVerdiProcess(AiidaTestCase):
    """Tests for `verdi process`."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestVerdiProcess, cls).setUpClass(*args, **kwargs)
        rmq_config = rmq.get_rmq_config()

        # These two need to share a common event loop otherwise the first will never send
        # the message while the daemon is running listening to intercept
        cls.runner = runners.Runner(rmq_config=rmq_config, rmq_submit=True, poll_interval=0.)

        cls.daemon_runner = runners.DaemonRunner(rmq_config=rmq_config, rmq_submit=True, poll_interval=0.)

    def setUp(self):
        super(TestVerdiProcess, self).setUp()
        self.cli_runner = CliRunner()

    def test_pause_play_kill(self):
        """
        Test the pause/play/kill commands
        """
        from concurrent.futures import ThreadPoolExecutor

        calc = self.runner.submit(test_utils.WaitProcess)
        executor = ThreadPoolExecutor(max_workers=1)

        try:
            _ = executor.submit(self.daemon_runner.start)

            self.assertFalse(calc.paused)
            result = self.cli_runner.invoke(cmd_process.process_pause, [str(calc.pk)])

            self.assertTrue(calc.paused)
            self.assertIsNone(result.exception)

            result = self.cli_runner.invoke(cmd_process.process_play, [str(calc.pk)])

            self.assertFalse(calc.paused)
            self.assertIsNone(result.exception)

            result = self.cli_runner.invoke(cmd_process.process_kill, [str(calc.pk)])

            self.assertTrue(calc.is_terminated)
            self.assertTrue(calc.is_killed)
            self.assertIsNone(result.exception)
        finally:
            self.daemon_runner.stop()
            executor.shutdown()
