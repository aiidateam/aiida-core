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
import pytest

from aiida.engine import ProcessState
from aiida.manage import get_manager
from aiida.orm import Int
from tests.utils import processes as test_processes


@pytest.mark.requires_rmq
class TestProcessControl:
    """Test AiiDA's RabbitMQ functionalities."""

    TIMEOUT = 2.0

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        # The coroutine defined in testcase should run in runner's loop
        # and process need submit by runner.submit rather than `submit` import from
        # aiida.engine, since the broad one will create its own loop
        manager = get_manager()
        self.runner = manager.get_runner()

    def test_submit_simple(self):
        """ "Launch the process."""

        async def do_submit():
            calc_node = self.runner.submit(test_processes.DummyProcess)
            await self.wait_for_process(calc_node)

            assert calc_node.is_finished_ok
            assert calc_node.process_state.value == plumpy.ProcessState.FINISHED.value

        self.runner.loop.run_until_complete(do_submit())

    def test_launch_with_inputs(self):
        """Test launch with inputs."""

        async def do_launch():
            term_a = Int(5)
            term_b = Int(10)

            calc_node = self.runner.submit(test_processes.AddProcess, a=term_a, b=term_b)
            await self.wait_for_process(calc_node)
            assert calc_node.is_finished_ok
            assert calc_node.process_state.value == plumpy.ProcessState.FINISHED.value

        self.runner.loop.run_until_complete(do_launch())

    def test_submit_bad_input(self):
        with pytest.raises(ValueError):
            self.runner.submit(test_processes.AddProcess, a=Int(5))

    def test_exception_process(self):
        """Test process excpetion."""

        async def do_exception():
            calc_node = self.runner.submit(test_processes.ExceptionProcess)
            await self.wait_for_process(calc_node)

            assert not calc_node.is_finished_ok
            assert calc_node.process_state.value == plumpy.ProcessState.EXCEPTED.value

        self.runner.loop.run_until_complete(do_exception())

    def test_pause(self):
        """Testing sending a pause message to the process."""
        controller = get_manager().get_process_controller()

        async def do_pause():
            calc_node = self.runner.submit(test_processes.WaitProcess)
            while calc_node.process_state != ProcessState.WAITING:
                await asyncio.sleep(0.1)

            assert not calc_node.paused

            pause_future = controller.pause_process(calc_node.pk)
            future = await with_timeout(asyncio.wrap_future(pause_future))
            result = await self.wait_future(asyncio.wrap_future(future))
            assert result
            assert calc_node.paused

            kill_future = controller.kill_process(calc_node.pk, msg_text='Sorry, you have to go mate')
            future = await with_timeout(asyncio.wrap_future(kill_future))
            result = await self.wait_future(asyncio.wrap_future(future))
            assert result

        self.runner.loop.run_until_complete(do_pause())

    def test_pause_play(self):
        """Test sending a pause and then a play message."""
        controller = get_manager().get_process_controller()

        async def do_pause_play():
            calc_node = self.runner.submit(test_processes.WaitProcess)
            assert not calc_node.paused
            while calc_node.process_state != ProcessState.WAITING:
                await asyncio.sleep(0.1)

            pause_message = 'Take a seat'
            pause_future = controller.pause_process(calc_node.pk, msg_text=pause_message)
            future = await with_timeout(asyncio.wrap_future(pause_future))
            result = await self.wait_future(asyncio.wrap_future(future))
            assert calc_node.paused
            assert calc_node.process_status == pause_message

            play_future = controller.play_process(calc_node.pk)
            future = await with_timeout(asyncio.wrap_future(play_future))
            result = await self.wait_future(asyncio.wrap_future(future))

            assert result
            assert not calc_node.paused
            assert calc_node.process_status is None

            kill_future = controller.kill_process(calc_node.pk, msg_text='Sorry, you have to go mate')
            future = await with_timeout(asyncio.wrap_future(kill_future))
            result = await self.wait_future(asyncio.wrap_future(future))
            assert result

        self.runner.loop.run_until_complete(do_pause_play())

    def test_kill(self):
        """Test sending a kill message."""
        controller = get_manager().get_process_controller()

        async def do_kill():
            calc_node = self.runner.submit(test_processes.WaitProcess)
            assert not calc_node.is_killed
            while calc_node.process_state != ProcessState.WAITING:
                await asyncio.sleep(0.1)

            kill_message = 'Sorry, you have to go mate'
            kill_future = controller.kill_process(calc_node.pk, msg_text=kill_message)
            future = await with_timeout(asyncio.wrap_future(kill_future))
            result = await self.wait_future(asyncio.wrap_future(future))
            assert result

            await self.wait_for_process(calc_node)
            assert calc_node.is_killed
            assert calc_node.process_status == kill_message

        self.runner.loop.run_until_complete(do_kill())

    async def wait_for_process(self, calc_node, timeout=2.0):
        future = self.runner.get_process_future(calc_node.pk)
        result = await with_timeout(future, timeout)
        return result

    @staticmethod
    async def wait_future(future, timeout=2.0):
        result = await with_timeout(future, timeout)
        return result


async def with_timeout(what, timeout=5.0):
    result = await asyncio.wait_for(what, timeout)
    return result
