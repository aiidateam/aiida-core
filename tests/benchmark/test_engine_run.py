# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=unused-argument,protected-access
"""Performance benchmark tests for local processes.

The purpose of these tests is to benchmark and compare processes,
which are executed *via* a local runner.
Note, these tests will not touch the daemon or RabbitMQ.
"""
import pytest

from aiida.engine import run_get_node, ToContext, while_, WorkChain
from aiida.orm import Code, Int
from aiida.plugins.factories import CalculationFactory

ArithmeticAddCalculation = CalculationFactory('arithmetic.add')

GROUP_NAME = 'engine-run'
ITERATIONS = 4


class WorkchainLoop(WorkChain):

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

    def run_task(self):
        future = self.submit(WorkchainLoop, iterations=Int(1))
        return ToContext(**{"wkchain" + str(self.ctx.counter): future})


class WorkchainLoopWcThreaded(WorkchainLoop):

    def init_loop(self):
        super().init_loop()
        self.ctx.iter = 1

    def run_task(self):

        context = {
            "wkchain" + str(i): self.submit(WorkchainLoop, iterations=Int(1))
            for i in range(self.inputs.iterations.value)
        }
        return ToContext(**context)


class WorkchainLoopCalcSerial(WorkchainLoop):

    def run_task(self):
        inputs = {
            'x': Int(1),
            'y': Int(2),
            'code': self.inputs.code,
        }
        future = self.submit(ArithmeticAddCalculation, **inputs)
        return ToContext(addition=future)


class WorkchainLoopCalcThreaded(WorkchainLoop):

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
            futures["addition" + str(i)] = self.submit(ArithmeticAddCalculation, **inputs)
        return ToContext(**futures)


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group=GROUP_NAME)
def test_basic_loop(benchmark):

    def _run():
        return run_get_node(WorkchainLoop, iterations=Int(ITERATIONS))

    result = benchmark.pedantic(_run, iterations=1, rounds=10, warmup_rounds=1)

    assert result.node.is_finished_ok, (result.node.exit_status, result.node.exit_message)


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group=GROUP_NAME)
def test_wkchain_loop_serial(benchmark):

    def _run():
        return run_get_node(WorkchainLoopWcSerial, iterations=Int(ITERATIONS))

    result = benchmark.pedantic(_run, iterations=1, rounds=10, warmup_rounds=1)

    assert result.node.is_finished_ok, (result.node.exit_status, result.node.exit_message)
    assert len(result.node.get_outgoing().all()) == ITERATIONS


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group=GROUP_NAME)
def test_wkchain_loop_threaded(benchmark):

    def _run():
        return run_get_node(WorkchainLoopWcThreaded, iterations=Int(ITERATIONS))

    result = benchmark.pedantic(_run, iterations=1, rounds=10, warmup_rounds=1)

    assert result.node.is_finished_ok, (result.node.exit_status, result.node.exit_message)
    assert len(result.node.get_outgoing().all()) == ITERATIONS


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group=GROUP_NAME)
def test_calc_loop_serial(benchmark, aiida_localhost):
    code = Code(input_plugin_name='arithmetic.add', remote_computer_exec=[aiida_localhost, '/bin/true'])

    def _run():
        return run_get_node(WorkchainLoopCalcSerial, iterations=Int(ITERATIONS), code=code)

    result = benchmark.pedantic(_run, iterations=1, rounds=10, warmup_rounds=1)

    assert result.node.is_finished_ok, (result.node.exit_status, result.node.exit_message)
    assert len(result.node.get_outgoing().all()) == ITERATIONS


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group=GROUP_NAME)
def test_calc_loop_threaded(benchmark, aiida_localhost):
    code = Code(input_plugin_name='arithmetic.add', remote_computer_exec=[aiida_localhost, '/bin/true'])

    def _run():
        return run_get_node(WorkchainLoopCalcThreaded, iterations=Int(ITERATIONS), code=code)

    result = benchmark.pedantic(_run, iterations=1, rounds=10, warmup_rounds=1)

    assert result.node.is_finished_ok, (result.node.exit_status, result.node.exit_message)
    assert len(result.node.get_outgoing().all()) == ITERATIONS
