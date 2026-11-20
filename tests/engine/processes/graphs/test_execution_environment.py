###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Graph launch, CalcJob/Slurm recovery, and attempt provenance."""

import pytest

from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.common.exceptions import GraphValidationError
from aiida.common.links import LinkType
from aiida.engine import (
    ExecutionEnvironment,
    ExitCode,
    ExitCodeEnum,
    IncreaseMemory,
    PreparedRun,
    RetryPolicy,
    SchedulerFailure,
    graph,
    run_get_node,
    submit,
    task,
)
from aiida.engine.processes.persistence import CheckpointPayload
from aiida.orm import FolderData, Int, Node, QueryBuilder

pytestmark = pytest.mark.presto


class SimulatedSlurmJob(ArithmeticAddCalculation):
    """Exercise ordinary CalcJob output handling without allocating real Slurm jobs."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.output('sum', valid_type=Int)

    def parse_retrieved_output(self, retrieved_temporary_folder=None):
        return None

    async def run(self):
        memory = self.options.max_memory_kb
        threshold = self.inputs.y.value
        if threshold < 0:
            # A parser or process producing the same exit status is not a classifier.
            return self.exit_codes.ERROR_SCHEDULER_OUT_OF_MEMORY
        state = 'OUT_OF_MEMORY' if memory < threshold else 'COMPLETED'
        self.out(self.node.link_label_retrieved, FolderData())
        self.out('sum', Int(memory))
        self.node.set_detailed_job_info({'retval': 0, 'stdout': f'JobID|State\n42|{state}\n', 'stderr': ''})
        self.update_outputs()
        return self.parse()


class JobErrors(ExitCodeEnum):
    OUT_OF_MEMORY = ExitCode(110, 'The job ran out of memory.')


simulated = task(SimulatedSlurmJob)
mapped = task(SimulatedSlurmJob, errors=JobErrors)


@task
def preprocess(x: Int) -> Int:
    return Int(x.value + 1)


@task
def consume(x: Int) -> Int:
    return Int(x.value)


@graph
def calculation(x: int, threshold: int) -> Int:
    result = simulated(x=x, y=threshold).alias('solver')
    return result.sum


@task
def observe_error(error: JobErrors | None, partial_sum: Int | None) -> Int:
    assert error is JobErrors.OUT_OF_MEMORY
    assert partial_sum is not None
    return Int(partial_sum.value)


@graph
def mapped_failure(x: int, threshold: int) -> Int:
    result = mapped(x=x, y=threshold).alias('solver')
    return observe_error(error=result.error, partial_sum=result.sum)


@graph
def workflow(x: int, threshold: int) -> Int:
    prepared = preprocess(x=x)
    result = calculation(x=prepared, threshold=threshold).alias('stage')
    return consume(x=result)


@graph
def iterated(x: int, threshold: int, count: int) -> int:
    index = 0
    while index < count:
        result = simulated(x=x, y=threshold).alias('solver')
        x = result.sum
        index = index + 1
    return x


@pytest.fixture
def code(aiida_computer, aiida_code_installed):
    computer = aiida_computer(hostname='localhost', transport_type='core.local', scheduler_type='core.slurm')
    return aiida_code_installed(computer=computer, filepath_executable='/bin/bash')


def environment(code, *, initial=2048, ceiling=8192, budget=3, nested=True):
    config = {
        'solver': {
            'code': code,
            'metadata': {
                'options': {
                    'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1},
                    'max_memory_kb': initial,
                }
            },
        }
    }
    policy = {
        'solver': RetryPolicy(
            max_attempts=budget,
            on={SchedulerFailure.OUT_OF_MEMORY: IncreaseMemory(factor=2, maximum_kb=ceiling)},
        )
    }
    return ExecutionEnvironment(
        runtime_config={'stage': config} if nested else config,
        execution_policy={'stage': policy} if nested else policy,
    )


@pytest.mark.parametrize(
    'threshold,initial,ceiling,budget,requests,success',
    [
        pytest.param(2048, 2048, 8192, 3, [2048], True, id='first-success'),
        pytest.param(4096, 2048, 8192, 3, [2048, 4096], True, id='recovery'),
        pytest.param(7500, 2048, 7500, 3, [2048, 4096, 7500], True, id='clamp'),
        pytest.param(8192, 2048, 8192, 2, [2048, 4096], False, id='budget'),
        pytest.param(8192, 2048, 2500, 3, [2048], False, id='no-effective-increase'),
        pytest.param(-1, 2048, 8192, 3, [2048], False, id='unclassified-exit-status'),
    ],
)
def test_nested_attempts(code, threshold, initial, ceiling, budget, requests, success):
    env = environment(code, initial=initial, ceiling=ceiling, budget=budget)
    outputs, node = run_get_node(workflow, inputs={'x': 1, 'threshold': threshold}, execution_environment=env)
    assert set(node.inputs) == {'x', 'threshold'}
    assert node.is_finished_ok is success
    children = {
        entry.link_label: entry.node for entry in node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()
    }
    attempts = [children.pop(f'graph_attempt_{n}__stage__solver') for n in range(1, len(requests) + 1)]
    assert set(children) == ({'preprocess', 'consume'} if success else {'preprocess'})
    assert [child.get_option('max_memory_kb') for child in attempts] == requests
    assert {child.inputs.x.uuid for child in attempts} == {children['preprocess'].outputs.result.uuid}
    assert {child.inputs.y.uuid for child in attempts} == {node.inputs.threshold.uuid}
    assert {child.inputs.code.uuid for child in attempts} == {code.uuid}
    history = node.execution_attempts['stage__solver']
    assert [record['child_uuid'] for record in history] == [child.uuid for child in attempts]
    assert [record['decision'] for record in history] == ['increase_memory'] * (len(requests) - 1) + ['terminal']
    assert history[-1]['failure'] == ('out_of_memory' if not success and threshold > 0 else None)
    if success:
        assert outputs['result'].value == requests[-1]
        assert children['consume'].inputs.x.uuid == attempts[-1].outputs.sum.uuid
    else:
        assert node.exit_status == 400
        assert outputs == {}


def test_mapped_failure_is_terminal_only(code):
    env = environment(code, nested=False, budget=2)
    outputs, node = run_get_node(mapped_failure, x=1, threshold=8192, execution_environment=env)
    assert node.is_finished_ok
    assert len(node.called) == 3
    assert outputs['result'].value == 4096


@pytest.mark.requires_broker
def test_submit_environment(code, submit_and_await):
    node = submit(
        calculation, inputs={'x': 1, 'threshold': 4096}, execution_environment=environment(code, nested=False)
    )
    submit_and_await(node)
    assert node.is_finished_ok
    assert node.outputs.result.value == 4096
    assert len(node.execution_attempts['solver']) == 2


def test_loop_iterations_restart_budget(code):
    env = environment(code, nested=False, budget=2)
    outputs, node = run_get_node(iterated, x=1, threshold=4096, count=2, execution_environment=env)
    assert outputs['result'].value == 4096
    assert len(node.execution_attempts) == 2
    for history in node.execution_attempts.values():
        assert [record['effective_memory_kb'] for record in history] == [2048, 4096]


def test_protocol_preparation_and_restart(code):
    env = environment(code)
    prepared = PreparedRun(
        inputs={'x': 1, 'threshold': 4096},
        execution_environment=env,
        protocol='example:relax',
        version='2',
        overrides={'threshold': 4096},
    )
    _, node = run_get_node(workflow, prepared_run=prepared)
    assert node.base.attributes.get(node.PROTOCOL_KEY) == {
        'protocol': 'example:relax',
        'version': '2',
        'overrides': {'threshold': 4096},
    }
    env.execution_policy.clear()
    env.runtime_config.clear()
    prepared.overrides.clear()
    outputs, restarted = run_get_node(node.get_builder_restart())
    assert outputs['result'].value == 4096
    assert restarted.base.attributes.get(node.PROTOCOL_KEY) == node.base.attributes.get(node.PROTOCOL_KEY)


def test_build_with_prepared_run_previews_known_and_deferred_inputs(code):
    """Preview resolves bound launch inputs, without running any placement or storing nodes."""
    count = QueryBuilder().append(Node).count()
    prepared = PreparedRun(
        inputs={'x': 1, 'threshold': 4096},
        execution_environment=environment(code),
        protocol='example:relax',
        version='2',
    )
    assert workflow.build() is None
    preview = workflow.build(prepared_run=prepared)
    assert QueryBuilder().append(Node).count() == count
    assert [placement.address for placement in preview.placements] == ['preprocess', 'stage.solver', 'consume']
    solver = preview.placements[1]
    assert solver.inputs['code'].state == 'resolved'
    assert solver.inputs['code'].value.uuid == code.uuid
    assert solver.inputs['metadata.options.max_memory_kb'].value == 2048
    assert solver.inputs['y'].value == 4096
    assert solver.inputs['x'].state == 'deferred'
    assert solver.inputs['x'].source == 'preprocess.result'
    assert solver.retry_policy.max_attempts == 3
    assert 'deferred — preprocess.result' in str(preview)


def test_build_preview_does_not_predict_loop_iterations(code):
    """Show one static description of a loop placement even if it may never run."""
    preview = iterated.build(x=1, threshold=4096, count=0, execution_environment=environment(code, nested=False))
    [solver] = preview.placements
    assert solver.address == 'solver'
    assert solver.regions[0].endswith(':loop')
    assert solver.inputs['x'].state == 'deferred'
    assert solver.inputs['y'].value == 4096


def test_build_preview_validates_launch_inputs(code):
    """Reject invalid placement configuration instead of treating it as deferred."""
    with pytest.raises(GraphValidationError, match='unknown placement path'):
        workflow.build(x=1, threshold=4096, runtime_config={'misspelled': {}})
    with pytest.raises(GraphValidationError, match='not of the right type'):
        workflow.build(x='wrong type', threshold=4096, execution_environment=environment(code))


@pytest.mark.parametrize('cut', ['before_initial_dispatch', 'waiting_for_retry'])
def test_checkpoint_recovery(code, aiida_manager, cut):
    """Reattach after a stale checkpoint and preserve the budget of a pending retry."""
    runner = aiida_manager.get_runner()
    env = environment(code, nested=False, budget=2)
    process = runner.instantiate_process(calculation, x=1, threshold=8192, execution_environment=env)

    async def replay():
        # Advance out of Created: the next step is dispatching the initial attempt.
        await process.step()
        checkpoint = CheckpointPayload.from_object(process)
        while not process.node.execution_attempts:
            assert not process.has_terminated()
            await process.step()
        if cut == 'waiting_for_retry':
            while len(process.node.execution_attempts['solver']) < 2:
                assert not process.has_terminated()
                await process.step()
            checkpoint = CheckpointPayload.from_object(process)

        process.close()
        restored = checkpoint.decode()
        try:
            await restored.step_until_terminated()
            assert restored.node.exit_status == 400
            assert len(restored.node.called) == 2
            history = restored.node.execution_attempts['solver']
            assert [attempt['effective_memory_kb'] for attempt in history] == [2048, 4096]
            assert history[-1]['reason'] == 'attempt budget exhausted'
        finally:
            restored.close()

    try:
        runner.run_until_complete(replay())
    finally:
        process.close()


def test_direct_channels(code):
    env = environment(code, nested=False)
    outputs, _ = run_get_node(
        calculation,
        inputs={'x': 3, 'threshold': 4096},
        runtime_config=env.runtime_config,
        execution_policy=env.execution_policy,
    )
    assert outputs['result'].value == 4096


@pytest.mark.parametrize('channel', ['runtime_config', 'execution_policy'])
def test_reject_conflicting_channels(code, channel):
    env = environment(code, nested=False)
    with pytest.raises(GraphValidationError, match='cannot be combined'):
        run_get_node(calculation, x=1, threshold=2, execution_environment=env, **{channel: {}})


@pytest.mark.parametrize(
    'case,match',
    [
        ('address', 'unknown placement'),
        ('process', 'only scheduler-backed CalcJob'),
        ('scheduler', 'does not support memory recovery'),
        ('missing', 'positive explicit'),
        ('ceiling', 'no larger'),
    ],
)
def test_invalid_policy_targets(code, case, match):
    env = environment(code, nested=False)
    if case == 'address':
        env.execution_policy['wrong'] = env.execution_policy['solver']
    elif case == 'process':
        env = environment(code)
        env.execution_policy['preprocess'] = env.execution_policy['stage']['solver']
    elif case == 'scheduler':
        code.computer.scheduler_type = 'core.direct'
    elif case == 'missing':
        del env.runtime_config['solver']['metadata']['options']['max_memory_kb']
    elif case == 'ceiling':
        env.runtime_config['solver']['metadata']['options']['max_memory_kb'] = 8193
    with pytest.raises(GraphValidationError, match=match):
        run_get_node(workflow if case == 'process' else calculation, x=1, threshold=2, execution_environment=env)


@pytest.mark.parametrize(
    'factor,ceiling,budget',
    [
        (1, 1024, 1),
        (float('nan'), 1024, 1),
        (float('inf'), 1024, 1),
        (2, -1, 1),
        (2, 1024, 0),
    ],
)
def test_invalid_limits(factor, ceiling, budget):
    with pytest.raises(ValueError, match=r'factor|maximum_kb|max_attempts'):
        RetryPolicy(
            max_attempts=budget,
            on={SchedulerFailure.OUT_OF_MEMORY: IncreaseMemory(factor=factor, maximum_kb=ceiling)},
        )
