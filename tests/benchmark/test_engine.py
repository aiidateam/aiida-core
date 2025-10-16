###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Performance benchmark tests for local processes.

The purpose of these tests is to benchmark and compare processes,
which are executed *via* both a local runner and the daemon.
"""

import pytest

from aiida.engine import WorkChain, run_get_node, while_
from aiida.orm import InstalledCode, Int
from aiida.plugins.factories import CalculationFactory

ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')


class WorkchainLoop(WorkChain):
    """A basic Workchain to run a looped step n times."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('iterations', required=True)
        spec.input('code', required=False)
        spec.outline(cls.init_loop, while_(cls.terminate_loop)(cls.run_task))

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
        return self.to_context(**{f'wkchain{self.ctx.counter!s}': future})


class WorkchainLoopWcThreaded(WorkchainLoop):
    """A WorkChain that submits another WorkChain n times in the same step."""

    def init_loop(self):
        super().init_loop()
        self.ctx.iter = 1

    def run_task(self):
        context = {
            f'wkchain{i!s}': self.submit(WorkchainLoop, iterations=Int(1)) for i in range(self.inputs.iterations.value)
        }
        return self.to_context(**context)


class WorkchainLoopCalcSerial(WorkchainLoop):
    """A WorkChain that submits a CalcJob n times in different steps."""

    def run_task(self):
        inputs = {
            'x': Int(1),
            'y': Int(2),
            'code': self.inputs.code,
        }
        future = self.submit(ArithmeticAddCalculation, **inputs)
        return self.to_context(addition=future)


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
            futures[f'addition{i!s}'] = self.submit(ArithmeticAddCalculation, **inputs)
        return self.to_context(**futures)


WORKCHAINS = {
    'basic-loop': (WorkchainLoop, 4, 0),
    'serial-wc-loop': (WorkchainLoopWcSerial, 4, 4),
    'threaded-wc-loop': (WorkchainLoopWcThreaded, 4, 4),
    'serial-calcjob-loop': (WorkchainLoopCalcSerial, 4, 4),
    'threaded-calcjob-loop': (WorkchainLoopCalcThreaded, 4, 4),
}


@pytest.mark.parametrize('workchain,iterations,outgoing', WORKCHAINS.values(), ids=WORKCHAINS.keys())
@pytest.mark.benchmark(group='engine')
def test_workchain_local(benchmark, aiida_localhost, workchain, iterations, outgoing):
    """Benchmark Workchains, executed in the local runner."""
    code = InstalledCode(
        default_calc_job_plugin='core.arithmetic.add', computer=aiida_localhost, filepath_executable='/bin/true'
    )

    def _run():
        return run_get_node(workchain, iterations=Int(iterations), code=code)

    result = benchmark.pedantic(_run, iterations=1, rounds=10, warmup_rounds=1)

    assert result.node.is_finished_ok, (result.node.exit_status, result.node.exit_message)
    assert len(result.node.base.links.get_outgoing().all()) == outgoing


@pytest.mark.parametrize('workchain,iterations,outgoing', WORKCHAINS.values(), ids=WORKCHAINS.keys())
@pytest.mark.usefixtures('started_daemon_client')
@pytest.mark.benchmark(group='engine')
def test_workchain_daemon(benchmark, submit_and_await, aiida_localhost, workchain, iterations, outgoing):
    """Benchmark Workchains, executed in the via a daemon runner."""
    code = InstalledCode(
        default_calc_job_plugin='core.arithmetic.add', computer=aiida_localhost, filepath_executable='/bin/true'
    )

    def _run():
        builder = workchain.get_builder()
        builder.code = code
        builder.iterations = Int(iterations)
        return submit_and_await(builder, timeout=30)

    result = benchmark.pedantic(_run, iterations=1, rounds=10, warmup_rounds=1)

    assert result.is_finished_ok, (result.exit_status, result.exit_message)
    assert len(result.base.links.get_outgoing().all()) == outgoing
