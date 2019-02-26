# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import datetime

import plumpy
from tornado import gen

from aiida.backends.testbase import AiidaTestCase
from aiida.backends.tests.utils import processes as test_processes
from aiida.engine import ProcessState, submit
from aiida.manage.manager import get_manager
from aiida.orm import Int


class TestProcessControl(AiidaTestCase):
    """
    Test AiiDA's RabbitMQ functionalities.
    """

    TIMEOUT = 2.

    def setUp(self):
        super(TestProcessControl, self).setUp()

        # These two need to share a common event loop otherwise the first will never send
        # the message while the daemon is running listening to intercept
        manager = get_manager()
        self.runner = manager.get_runner()
        self.daemon_runner = manager.create_daemon_runner(loop=self.runner.loop)

    def tearDown(self):
        self.daemon_runner.close()
        super(TestProcessControl, self).tearDown()

    def test_submit_simple(self):
        # Launch the process
        @gen.coroutine
        def do_submit():
            calc_node = submit(test_processes.DummyProcess)
            yield self.wait_for_calc(calc_node)

            self.assertTrue(calc_node.is_finished_ok)
            self.assertEqual(calc_node.process_state.value, plumpy.ProcessState.FINISHED.value)

        self.runner.loop.run_sync(do_submit)

    def test_launch_with_inputs(self):

        @gen.coroutine
        def do_launch():
            a = Int(5)
            b = Int(10)

            calc_node = submit(test_processes.AddProcess, a=a, b=b)
            yield self.wait_for_calc(calc_node)
            self.assertTrue(calc_node.is_finished_ok)
            self.assertEqual(calc_node.process_state.value, plumpy.ProcessState.FINISHED.value)

        self.runner.loop.run_sync(do_launch)

    def test_submit_bad_input(self):
        with self.assertRaises(ValueError):
            submit(test_processes.AddProcess, a=Int(5))

    def test_exception_process(self):

        @gen.coroutine
        def do_exception():
            calc_node = submit(test_processes.ExceptionProcess)
            yield self.wait_for_calc(calc_node)

            self.assertFalse(calc_node.is_finished_ok)
            self.assertEqual(calc_node.process_state.value, plumpy.ProcessState.EXCEPTED.value)

        self.runner.loop.run_sync(do_exception)

    def test_pause(self):
        """Testing sending a pause message to the process."""

        controller = get_manager().get_process_controller()

        @gen.coroutine
        def do_pause():
            calc_node = submit(test_processes.WaitProcess)
            while calc_node.process_state != ProcessState.WAITING:
                yield

            self.assertFalse(calc_node.paused)

            future = yield with_timeout(controller.pause_process(calc_node.pk))
            result = yield self.wait_future(future)
            self.assertTrue(result)
            self.assertTrue(calc_node.paused)

        self.runner.loop.run_sync(do_pause)

    def test_pause_play(self):
        """Test sending a pause and then a play message."""

        controller = get_manager().get_process_controller()

        @gen.coroutine
        def do_pause_play():
            calc_node = submit(test_processes.WaitProcess)
            self.assertFalse(calc_node.paused)
            while calc_node.process_state != ProcessState.WAITING:
                yield

            pause_message = 'Take a seat'
            future = yield with_timeout(controller.pause_process(calc_node.pk, msg=pause_message))
            result = yield self.wait_future(future)
            self.assertTrue(calc_node.paused)
            self.assertEqual(calc_node.process_status, pause_message)

            future = yield with_timeout(controller.play_process(calc_node.pk))
            result = yield self.wait_future(future)
            self.assertTrue(result)
            self.assertFalse(calc_node.paused)
            self.assertEqual(calc_node.process_status, None)

        self.runner.loop.run_sync(do_pause_play)

    def test_kill(self):
        """Test sending a kill message."""

        controller = get_manager().get_process_controller()

        @gen.coroutine
        def do_kill():
            calc_node = submit(test_processes.WaitProcess)
            self.assertFalse(calc_node.is_killed)
            while calc_node.process_state != ProcessState.WAITING:
                yield

            kill_message = 'Sorry, you have to go mate'
            future = yield with_timeout(controller.kill_process(calc_node.pk, msg=kill_message))
            result = yield self.wait_future(future)
            self.assertTrue(result)

            self.wait_for_calc(calc_node)
            self.assertTrue(calc_node.is_killed)
            self.assertEqual(calc_node.process_status, kill_message)

        self.runner.loop.run_sync(do_kill)

    @gen.coroutine
    def wait_for_calc(self, calc_node, timeout=2.):
        future = self.runner.get_calculation_future(calc_node.pk)
        raise gen.Return((yield with_timeout(future, timeout)))

    @gen.coroutine
    def wait_future(self, future, timeout=2.):
        raise gen.Return((yield with_timeout(future, timeout)))


@gen.coroutine
def with_timeout(what, timeout=5.0):
    raise gen.Return((yield gen.with_timeout(datetime.timedelta(seconds=timeout), what)))
