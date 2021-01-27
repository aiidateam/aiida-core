# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name
"""Module to test process runners."""
import threading
import asyncio

import plumpy
import pytest

from aiida.engine import Process
from aiida.manage.manager import get_manager
from aiida.orm import WorkflowNode


@pytest.fixture
def create_runner():
    """Construct and return a `Runner`."""

    def _create_runner(poll_interval=0.5):
        loop = asyncio.new_event_loop()
        return get_manager().create_runner(poll_interval=poll_interval, loop=loop)

    return _create_runner


class Proc(Process):
    """Process class."""

    _node_class = WorkflowNode

    def run(self):
        pass


def the_hans_klok_comeback(loop):
    loop.stop()


@pytest.mark.usefixtures('clear_database_before_test')
def test_call_on_process_finish(create_runner):
    """Test call on calculation finish."""
    runner = create_runner()
    loop = runner.loop
    proc = Proc(runner=runner)
    future = plumpy.Future()
    event = threading.Event()

    def calc_done():
        if event.is_set():
            future.set_exception(AssertionError('the callback was called twice, which should never happen'))

        future.set_result(True)
        event.set()
        loop.stop()

    runner.call_on_process_finish(proc.node.pk, calc_done)

    # Run the calculation
    runner.loop.create_task(proc.step_until_terminated())
    loop.call_later(5, the_hans_klok_comeback, runner.loop)
    loop.run_forever()

    assert not future.exception()
    assert future.result()
