# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to test RabbitMQ."""
import asyncio

import plumpy

from aiida.backends.testbase import AiidaTestCase
from aiida.engine import ProcessState, submit
from aiida.manage.manager import get_manager
from aiida.orm import Int

from tests.utils import processes as test_processes


class TestProcessControl(AiidaTestCase):
    """Test AiiDA's RabbitMQ functionalities."""

    TIMEOUT = 2.

    def setUp(self):
        super().setUp()

        # These two need to share a common event loop otherwise the first will never send
        # the message while the daemon is running listening to intercept
        manager = get_manager()
        self.runner = manager.get_runner()
        self.daemon_runner = manager.create_daemon_runner(loop=self.runner.loop)

    def tearDown(self):
        self.daemon_runner.close()
        super().tearDown()

    def test_submit_simple(self):
        """"Launch the process."""

        async def do_submit():
            calc_node = submit(test_processes.DummyProcess)
            await self.wait_for_process(calc_node)

            self.assertTrue(calc_node.is_finished_ok)
            self.assertEqual(calc_node.process_state.value, plumpy.ProcessState.FINISHED.value)

        self.runner.loop.run_until_complete(do_submit())

    def test_launch_with_inputs(self):
        """Test launch with inputs."""

        async def do_launch():
            term_a = Int(5)
            term_b = Int(10)

            calc_node = submit(test_processes.AddProcess, a=term_a, b=term_b)
            await self.wait_for_process(calc_node)
            self.assertTrue(calc_node.is_finished_ok)
            self.assertEqual(calc_node.process_state.value, plumpy.ProcessState.FINISHED.value)

        self.runner.loop.run_until_complete(do_launch())

    def test_submit_bad_input(self):
        with self.assertRaises(ValueError):
            submit(test_processes.AddProcess, a=Int(5))

    def test_exception_process(self):
        """Test process excpetion."""

        async def do_exception():
            calc_node = submit(test_processes.ExceptionProcess)
            await self.wait_for_process(calc_node)

            self.assertFalse(calc_node.is_finished_ok)
            self.assertEqual(calc_node.process_state.value, plumpy.ProcessState.EXCEPTED.value)

        self.runner.loop.run_until_complete(do_exception())

    def test_pause(self):
        """Testing sending a pause message to the process."""

        controller = get_manager().get_process_controller()

        async def do_pause():
            calc_node = submit(test_processes.WaitProcess)
            while calc_node.process_state != ProcessState.WAITING:
                await asyncio.sleep(0.1)

            self.assertFalse(calc_node.paused)

            pause_future = controller.pause_process(calc_node.pk)
            future = await with_timeout(asyncio.wrap_future(pause_future))
            result = await self.wait_future(asyncio.wrap_future(future))
            self.assertTrue(result)
            self.assertTrue(calc_node.paused)

        self.runner.loop.run_until_complete(do_pause())

    def test_pause_play(self):
        """Test sending a pause and then a play message."""

        controller = get_manager().get_process_controller()

        async def do_pause_play():
            calc_node = submit(test_processes.WaitProcess)
            self.assertFalse(calc_node.paused)
            while calc_node.process_state != ProcessState.WAITING:
                await asyncio.sleep(0.1)

            pause_message = 'Take a seat'
            pause_future = controller.pause_process(calc_node.pk, msg=pause_message)
            future = await with_timeout(asyncio.wrap_future(pause_future))
            result = await self.wait_future(asyncio.wrap_future(future))
            self.assertTrue(calc_node.paused)
            self.assertEqual(calc_node.process_status, pause_message)

            play_future = controller.play_process(calc_node.pk)
            future = await with_timeout(asyncio.wrap_future(play_future))
            result = await self.wait_future(asyncio.wrap_future(future))

            self.assertTrue(result)
            self.assertFalse(calc_node.paused)
            self.assertEqual(calc_node.process_status, None)

        self.runner.loop.run_until_complete(do_pause_play())

    def test_kill(self):
        """Test sending a kill message."""

        controller = get_manager().get_process_controller()

        async def do_kill():
            calc_node = submit(test_processes.WaitProcess)
            self.assertFalse(calc_node.is_killed)
            while calc_node.process_state != ProcessState.WAITING:
                await asyncio.sleep(0.1)

            kill_message = 'Sorry, you have to go mate'
            kill_future = controller.kill_process(calc_node.pk, msg=kill_message)
            future = await with_timeout(asyncio.wrap_future(kill_future))
            result = await self.wait_future(asyncio.wrap_future(future))
            self.assertTrue(result)

            await self.wait_for_process(calc_node)
            self.assertTrue(calc_node.is_killed)
            self.assertEqual(calc_node.process_status, kill_message)

        self.runner.loop.run_until_complete(do_kill())

    async def wait_for_process(self, calc_node, timeout=2.):
        future = self.runner.get_process_future(calc_node.pk)
        result = await with_timeout(future, timeout)
        return result

    @staticmethod
    async def wait_future(future, timeout=2.):
        result = await with_timeout(future, timeout)
        return result


async def with_timeout(what, timeout=5.0):
    result = await asyncio.wait_for(what, timeout)
    return result
