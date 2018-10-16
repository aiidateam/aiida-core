# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
import uuid

import plumpy

from aiida.backends.testbase import AiidaTestCase
from aiida.orm.data.int import Int
from aiida.work import runners, rmq, test_utils


class TestProcessControl(AiidaTestCase):
    """
    Test AiiDA's RabbitMQ functionalities.
    """

    def setUp(self):
        super(TestProcessControl, self).setUp()
        prefix = '{}.{}'.format(self.__class__.__name__, uuid.uuid4())
        rmq_config = rmq.get_rmq_config(prefix)

        # These two need to share a common event loop otherwise the first will never send
        # the message while the daemon is running listening to intercept
        self.runner = runners.Runner(
            rmq_config=rmq_config,
            rmq_submit=True,
            poll_interval=0.)
        self.daemon_runner = runners.DaemonRunner(
            rmq_config=rmq_config,
            rmq_submit=True,
            loop=self.runner.loop,
            poll_interval=0.)

    def tearDown(self):
        self.daemon_runner.close()
        self.runner.close()
        super(TestProcessControl, self).tearDown()

    def test_submit_simple(self):
        # Launch the process
        calc_node = self.runner.submit(test_utils.DummyProcess)
        self._wait_for_calc(calc_node)

        self.assertTrue(calc_node.is_finished_ok)
        self.assertEqual(calc_node.process_state.value, plumpy.ProcessState.FINISHED.value)

    def test_launch_with_inputs(self):
        a = Int(5)
        b = Int(10)

        calc_node = self.runner.submit(test_utils.AddProcess, a=a, b=b)
        self._wait_for_calc(calc_node)
        self.assertTrue(calc_node.is_finished_ok)
        self.assertEqual(calc_node.process_state.value, plumpy.ProcessState.FINISHED.value)

    def test_submit_bad_input(self):
        with self.assertRaises(ValueError):
            self.runner.submit(test_utils.AddProcess, a=Int(5))

    def test_exception_process(self):
        calc_node = self.runner.submit(test_utils.ExceptionProcess)
        self._wait_for_calc(calc_node)

        self.assertFalse(calc_node.is_finished_ok)
        self.assertEqual(calc_node.process_state.value, plumpy.ProcessState.EXCEPTED.value)

    def test_pause(self):
        """ Testing sending a pause message to the process """
        calc_node = self.runner.submit(test_utils.WaitProcess)
        future = self.runner.rmq.pause_process(calc_node.pk)
        result = self.runner.run_until_complete(future)
        self.assertTrue(result)

    def test_pause_play(self):
        """ Test sending a pause and then a play message """
        calc_node = self.runner.submit(test_utils.WaitProcess)
        future = self.runner.rmq.pause_process(calc_node.pk)
        result = self.runner.run_until_complete(future)
        self.assertTrue(result)

        future = self.runner.rmq.play_process(calc_node.pk)
        result = self.runner.run_until_complete(future)
        self.assertTrue(result)

    def test_kill(self):
        """ Test sending a kill message """
        calc_node = self.runner.submit(test_utils.WaitProcess)
        future = self.runner.rmq.kill_process(calc_node.pk, "Sorry, you have to go mate")
        result = self.runner.run_until_complete(future)
        # TODO: Check kill message
        self.assertTrue(result)

    def _wait_for_calc(self, calc_node, timeout=2.):
        future = self.runner.get_calculation_future(calc_node.pk)
        self.runner.run_until_complete(future)
