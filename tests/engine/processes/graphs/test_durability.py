###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# in the top-level directory of this distribution.                        #
###########################################################################
"""Tests for checkpoint-only ports and their provenance."""

import typing as t

import pytest

from aiida import orm
from aiida.common.exceptions import GraphTypeCheckError, GraphValidationError
from aiida.engine import PortField, PortModel, graph, run_get_node, task
from aiida.engine.persistence import AiidaCheckpointPersister
from aiida.engine.processes.graphs.process import GraphProcess

pytestmark = [pytest.mark.presto, pytest.mark.usefixtures('aiida_profile_clean')]

Scratch = t.Annotated[float, PortField(durable=False)]


@task
def estimate(seed: float) -> Scratch:
    return 2 * seed


@graph
def prepare(seed: float) -> Scratch:
    return estimate(seed=seed)


@task
def normalize(estimate: Scratch) -> float:
    return estimate / 10


class Report(PortModel):
    score: float


@graph
def report(seed: float) -> Report:
    scratch = prepare(seed=seed)
    score = normalize(estimate=scratch)
    return {'score': score}


@task
def durable_consumer(value: float) -> float:
    return value


@graph
def implicit_promotion(seed: float) -> float:
    scratch = prepare(seed=seed)
    return durable_consumer(value=scratch)


class CheckpointInputs(PortModel):
    estimate: Scratch


@graph
def launch_scratch(bundle: CheckpointInputs) -> float:
    return normalize(estimate=bundle.estimate)


class MixedOutputs(PortModel):
    buffer: t.Annotated[bytes, PortField(durable=False)]
    length: int


@task
def make_buffer() -> MixedOutputs:
    return MixedOutputs(buffer=b'checkpoint', length=10)


@task
def buffer_length(buffer: t.Annotated[bytes, PortField(durable=False)]) -> int:
    return len(buffer)


@graph
def measure_buffer() -> int:
    prepared = make_buffer()
    return buffer_length(buffer=prepared.buffer)


@task
def invalid_estimate() -> t.Annotated[orm.Float, PortField(durable=False)]:
    return orm.Float(6.0)


@graph
def invalid_checkpoint() -> float:
    scratch = invalid_estimate()
    return normalize(estimate=scratch)


@task
def fail_after_reading(value: Scratch) -> float:
    msg = f'cannot normalize {value}'
    raise RuntimeError(msg)


@graph
def failing_workflow(seed: float) -> float:
    scratch = estimate(seed=seed)
    return fail_after_reading(value=scratch)


def test_checkpoint_only_provenance() -> None:
    outputs, node = run_get_node(report, seed=3.0)
    assert node.is_finished_ok
    assert outputs['score'].value == 0.6
    producer, consumer = sorted(node.called, key=lambda child: child.process_label)
    assert producer.process_label == 'estimate'
    assert consumer.process_label == 'normalize'
    assert producer.inputs.seed.uuid == node.inputs.seed.uuid
    assert list(producer.outputs) == []
    assert list(consumer.inputs) == []
    assert outputs['score'].creator.uuid == consumer.uuid
    assert not producer.base.caching.is_valid_cache
    assert not consumer.base.caching.is_valid_cache
    assert not list(node.backend.checkpoint_store.iter_files(node_uuid=node.uuid))
    assert {row[0] for row in orm.QueryBuilder().append(orm.Float, project='attributes.value').all()} == {3.0, 0.6}


def test_checkpoint_only_boundary_rules() -> None:
    with pytest.raises(GraphTypeCheckError, match='checkpoint-only value to a durable port'):
        implicit_promotion.build()
    with pytest.raises(GraphValidationError, match='root graph outputs cannot be checkpoint-only'):
        run_get_node(prepare, seed=3.0)
    with pytest.raises(GraphValidationError, match='require a calling graph'):
        run_get_node(estimate, seed=3.0)


def test_checkpoint_only_graph_input_does_not_link_stored_node() -> None:
    original = orm.Float(6.0).store()
    outputs, node = run_get_node(launch_scratch, bundle={'estimate': original})
    assert node.is_finished_ok
    assert outputs['result'].value == 0.6
    assert list(node.inputs) == []
    assert list(node.called[0].inputs) == []
    assert orm.load_node(original.uuid).value == 6.0


def test_checkpoint_only_port_model_field_can_carry_bytes() -> None:
    outputs, node = run_get_node(measure_buffer)
    assert node.is_finished_ok
    assert outputs['result'].value == 10
    producer = next(child for child in node.called if child.process_label == 'make_buffer')
    assert list(producer.outputs) == ['length']
    assert producer.outputs.length.value == 10


def test_checkpoint_only_output_does_not_store_unstored_orm_node() -> None:
    _, node = run_get_node(invalid_checkpoint)
    (producer,) = node.called
    assert producer.is_excepted
    assert 'checkpoint-only port `result` cannot checkpoint a `Float`' in producer.exception
    assert not orm.QueryBuilder().append(orm.Float).count()
    assert not list(node.backend.checkpoint_store.iter_files(node_uuid=node.uuid))


def test_graph_failure_cleans_up_published_checkpoint_only_results() -> None:
    _, node = run_get_node(failing_workflow, seed=3.0)
    assert node.is_failed
    producer, consumer = sorted(node.called, key=lambda child: child.process_label)
    assert producer.is_finished_ok
    assert 'cannot normalize 6.0' in consumer.exception
    assert not list(node.backend.checkpoint_store.iter_files(node_uuid=node.uuid))


@pytest.mark.requires_broker
def test_checkpoint_only_results_on_daemon(submit_and_await) -> None:
    node = submit_and_await(GraphProcess, **report.get_launch_inputs(seed=3.0))
    assert node.is_finished_ok
    assert node.outputs.score.value == 0.6


@pytest.mark.parametrize('restart', [True, False], ids=['restart', 'kill'])
def test_checkpoint_only_output_outlives_the_child(runner, restart: bool) -> None:
    persister = AiidaCheckpointPersister()
    process = GraphProcess(inputs=report.get_launch_inputs(seed=3.0), runner=runner)
    restored = None
    try:
        persister.save_checkpoint(process)
        with process._process_scope():
            process._do_step()
        (producer,) = process.node.called
        runner.loop.run_until_complete(runner._local_process_tasks[producer.pk])
        producer = orm.load_node(producer.pk)
        assert producer.is_finished_ok
        assert producer.checkpoint is None
        assert list(producer.outputs) == []
        assert list(process.node.backend.checkpoint_store.iter_files(node_uuid=process.node.uuid))

        if not restart:
            assert process.kill() is True
            assert process.node.is_killed
            assert not list(process.node.backend.checkpoint_store.iter_files(node_uuid=process.node.uuid))
            return

        process.close()
        restored = persister.load_checkpoint(process.pid).decode()
        restored.execute()
        assert restored.node.is_finished_ok
        assert restored.outputs['score'].value == 0.6
        assert [child.uuid for child in restored.node.called if child.process_label == 'estimate'] == [producer.uuid]
        assert not list(restored.node.backend.checkpoint_store.iter_files(node_uuid=restored.node.uuid))
    finally:
        if restored is not None:
            restored.close()
        process.close()
