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
import asyncio
import threading

import plumpy
import pytest

from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.engine import Process, launch
from aiida.manage import get_manager
from aiida.manage.caching import enable_caching
from aiida.orm import Int, Str, WorkflowNode


@pytest.fixture
def runner():
    """Construct and return a `Runner`."""
    loop = asyncio.new_event_loop()
    return get_manager().create_runner(poll_interval=0.5, loop=loop)


class Proc(Process):
    """Process class."""

    _node_class = WorkflowNode

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('a')

    def run(self):
        pass


def the_hans_klok_comeback(loop):
    loop.stop()


@pytest.mark.requires_rmq
def test_call_on_process_finish(runner):
    """Test call on calculation finish."""
    loop = runner.loop
    proc = Proc(runner=runner, inputs={'a': Str('input')})
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


def test_submit_args(runner):
    """Test that a useful exception is raised when the inputs are passed as a dictionary instead of expanded kwargs.

    Regression test for #3609. Before, it would throw the validation exception of the first port to be validated. If
    a user accidentally forgot to expand the inputs with `**` it would be a misleading error.
    """
    with pytest.raises(TypeError, match=r'takes 2 positional arguments but 3 were given'):
        runner.submit(Proc, {'a': Str('input')})


def test_run_return_value_cached(aiida_local_code_factory):
    """Test that :meth:`aiida.engine.runners.Runner._run` return process results even when cached.

    Regression test for https://github.com/aiidateam/aiida-core/issues/5994.
    """
    inputs = {
        'code': aiida_local_code_factory('core.arithmetic.add', '/bin/bash'),
        'x': Int(1),
        'y': Int(-2),
    }
    results_source, node_source = launch.run_get_node(ArithmeticAddCalculation, **inputs)
    assert node_source.is_valid_cache

    with enable_caching():
        results_cached, node_cached = launch.run_get_node(ArithmeticAddCalculation, **inputs)

    assert node_cached.base.caching.get_cache_source() == node_source.uuid
    assert sorted(results_cached.keys()) == sorted(results_source.keys())
    assert sorted(results_cached.keys()) == ['remote_folder', 'retrieved', 'sum']
