# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=unused-argument,redefined-outer-name
"""Performance benchmark tests for local processes.

The purpose of these tests is to benchmark and compare processes,
which are executed *via* a local runner.
Note, these tests will not touch the daemon or RabbitMQ.
"""
import datetime

import pytest
from tornado import gen

from aiida.engine import run_get_node, submit, ToContext, while_, WorkChain
from aiida.manage.manager import get_manager
from aiida.orm import Code, Int
from aiida.plugins.factories import CalculationFactory

ArithmeticAddCalculation = CalculationFactory('arithmetic.add')


class WorkchainLoop(WorkChain):
    """A basic Workchain to run a looped step n times."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('iterations', required=True)
        spec.input('code', required=False)
        spec.outline(cls.init_loop, while_(cls.terminate_loop)(cls.run_task))
        # spec.output('result')

    def init_loop(self):
        self.ctx.iter = self.inputs.iterations.value
        self.ctx.counter = 0

    def terminate_loop(self):
        if self.ctx.counter >= self.ctx.iter:
            return False
        self.ctx.counter += 1
        return True

    def run_task(self):
        pass


class WorkchainLoopWcSerial(WorkchainLoop):
    """A WorkChain that submits another WorkChain n times in different steps."""

    def run_task(self):
        future = self.submit(WorkchainLoop, iterations=Int(1))
        return ToContext(**{'wkchain' + str(self.ctx.counter): future})


class WorkchainLoopWcThreaded(WorkchainLoop):
    """A WorkChain that submits another WorkChain n times in the same step."""

    def init_loop(self):
        super().init_loop()
        self.ctx.iter = 1

    def run_task(self):

        context = {
            'wkchain' + str(i): self.submit(WorkchainLoop, iterations=Int(1))
            for i in range(self.inputs.iterations.value)
        }
        return ToContext(**context)


class WorkchainLoopCalcSerial(WorkchainLoop):
    """A WorkChain that submits a CalcJob n times in different steps."""

    def run_task(self):
        inputs = {
            'x': Int(1),
            'y': Int(2),
            'code': self.inputs.code,
        }
        future = self.submit(ArithmeticAddCalculation, **inputs)
        return ToContext(addition=future)


class WorkchainLoopCalcThreaded(WorkchainLoop):
    """A WorkChain that submits a CalcJob n times in the same step."""

    def init_loop(self):
        super().init_loop()
        self.ctx.iter = 1

    def run_task(self):
        futures = {}
        for i in range(self.inputs.iterations.value):
            inputs = {
                'x': Int(1),
                'y': Int(2),
                'code': self.inputs.code,
            }
            futures['addition' + str(i)] = self.submit(ArithmeticAddCalculation, **inputs)
        return ToContext(**futures)


WORKCHAINS = {
    'basic-loop': (WorkchainLoop, 4, 0),
    'serial-wc-loop': (WorkchainLoopWcSerial, 4, 4),
    'threaded-wc-loop': (WorkchainLoopWcThreaded, 4, 4),
    'serial-calcjob-loop': (WorkchainLoopCalcSerial, 4, 4),
    'threaded-calcjob-loop': (WorkchainLoopCalcThreaded, 4, 4),
}


@pytest.mark.parametrize('workchain,iterations,outgoing', WORKCHAINS.values(), ids=WORKCHAINS.keys())
@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group='engine')
def test_workchain_local(benchmark, aiida_localhost, workchain, iterations, outgoing):
    """Benchmark Workchains, executed in the local runner."""
    code = Code(input_plugin_name='arithmetic.add', remote_computer_exec=[aiida_localhost, '/bin/true'])

    def _run():
        return run_get_node(workchain, iterations=Int(iterations), code=code)

    result = benchmark.pedantic(_run, iterations=1, rounds=10, warmup_rounds=1)

    assert result.node.is_finished_ok, (result.node.exit_status, result.node.exit_message)
    assert len(result.node.get_outgoing().all()) == outgoing


@gen.coroutine
def with_timeout(what, timeout=60):
    """Coroutine return with timeout."""
    raise gen.Return((yield gen.with_timeout(datetime.timedelta(seconds=timeout), what)))


@gen.coroutine
def wait_for_process(runner, calc_node, timeout=60):
    """Coroutine block with timeout."""
    future = runner.get_process_future(calc_node.pk)
    raise gen.Return((yield with_timeout(future, timeout)))


@pytest.fixture()
def submit_get_node():
    """A test fixture for running a process *via* submission to the daemon,
    and blocking until it is complete.

    Adapted from tests/engine/test_rmq.py
    """
    manager = get_manager()
    runner = manager.get_runner()
    # The daemon runner needs to share a common event loop,
    # otherwise the local runner will never send the message while the daemon is running listening to intercept.
    daemon_runner = manager.create_daemon_runner(loop=runner.loop)

    def _submit(_process, timeout=60, **kwargs):

        @gen.coroutine
        def _do_submit():
            node = submit(_process, **kwargs)
            yield wait_for_process(runner, node)
            return node

        result = runner.loop.run_sync(_do_submit, timeout=timeout)

        return result

    yield _submit

    daemon_runner.close()


@pytest.mark.parametrize('workchain,iterations,outgoing', WORKCHAINS.values(), ids=WORKCHAINS.keys())
@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group='engine')
def test_workchain_daemon(benchmark, submit_get_node, aiida_localhost, workchain, iterations, outgoing):
    """Benchmark Workchains, executed in the via a daemon runner."""
    code = Code(input_plugin_name='arithmetic.add', remote_computer_exec=[aiida_localhost, '/bin/true'])

    def _run():
        return submit_get_node(workchain, iterations=Int(iterations), code=code)

    result = benchmark.pedantic(_run, iterations=1, rounds=10, warmup_rounds=1)

    assert result.is_finished_ok, (result.exit_status, result.exit_message)
    assert len(result.get_outgoing().all()) == outgoing
