# -*- coding: utf-8 -*-

import plumpy
import uuid

from aiida.backends.testbase import AiidaTestCase
import aiida.work.test_utils as test_utils
from aiida.orm.data import base
import aiida.work as work
from aiida.orm.calculation.work import WorkCalculation

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"


class TestProcessControl(AiidaTestCase):
    """
    Test AiiDA's RabbitMQ functionalities.
    """

    def setUp(self):
        super(TestProcessControl, self).setUp()
        prefix = "{}.{}".format(self.__class__.__name__, uuid.uuid4())

        self.loop = plumpy.new_event_loop()

        rmq_config = {
            'url': 'amqp://localhost',
            'prefix': prefix,
            'testing_mode': True
        }
        self.runner = work.Runner(
            rmq_config=rmq_config, rmq_submit=True, loop=self.loop, poll_interval=0.)
        self.daemon_runner = work.DaemonRunner(
            rmq_config=rmq_config, rmq_submit=True, loop=self.loop, poll_interval=0.)

    def tearDown(self):
        self.daemon_runner.close()
        self.runner.close()

    def test_submit_simple(self):
        # Launch the process
        calc_node = self.runner.submit(test_utils.DummyProcess)
        self._wait_for_calc(calc_node)

        self.assertTrue(calc_node.has_finished_ok())
        self.assertEqual(
            calc_node.get_attr(WorkCalculation.PROCESS_STATE_KEY),
            work.ProcessState.FINISHED.value
        )

    def test_launch_with_inputs(self):
        a = base.Int(5)
        b = base.Int(10)

        calc_node = self.runner.submit(test_utils.AddProcess, a=a, b=b)
        self._wait_for_calc(calc_node)
        self.assertTrue(calc_node.has_finished_ok())
        self.assertEqual(
            calc_node.get_attr(WorkCalculation.PROCESS_STATE_KEY),
            work.ProcessState.FINISHED.value
        )

    def test_submit_bad_input(self):
        with self.assertRaises(ValueError):
            self.runner.submit(test_utils.AddProcess, a=base.Int(5))

    def test_exception_process(self):
        calc_node = self.runner.submit(test_utils.ExceptionProcess)
        self._wait_for_calc(calc_node)

        self.assertFalse(calc_node.has_finished_ok())
        self.assertEqual(
            calc_node.get_attr(WorkCalculation.PROCESS_STATE_KEY),
            work.ProcessState.EXCEPTED.value
        )

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
