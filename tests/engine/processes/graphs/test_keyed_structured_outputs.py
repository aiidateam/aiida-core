###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Runtime keyed namespaces retain each structured entry's field contract."""

import json
import typing as t

import pytest

from aiida import orm
from aiida.common.links import LinkType
from aiida.engine import GraphProcess, Many, PortField, PortModel, graph, run, run_get_node, task
from aiida.engine.processes.graphs.inputs import dump_port, load_port, namespace_for_outputs
from aiida.engine.processes.graphs.process import _stored
from aiida.engine.processes.graphs.spec import GraphSpec

pytestmark = pytest.mark.presto


class Block(PortModel):
    parameters: t.Annotated[orm.Dict, PortField(help='Block parameters.')]
    file: orm.SinglefileData | None = None


class Blocks(PortModel):
    blocks: Many[Block]


class NamedBlocks(PortModel):
    b00: Block


@task
def make_block(value: int) -> Block:
    return Block(parameters=orm.Dict({'value': value}))


@task
def consume_blocks(blocks: Many[Block]) -> int:
    return sum(block.parameters.get_dict()['value'] for block in blocks.values())


@graph
def map_blocks(values: dict) -> int:
    for value in values:
        blocks = make_block(value=value)
    return consume_blocks(blocks=blocks)


@task
def produce_keyed_blocks() -> Blocks:
    return Blocks(blocks={'b00': Block(parameters=orm.Dict({'value': 3}))})


@task
def produce_named_blocks() -> NamedBlocks:
    return NamedBlocks(b00=Block(parameters=orm.Dict({'value': 3})))


@task
def make_leaf(value: int) -> orm.Dict:
    return orm.Dict({'value': value})


@task
def consume_leaves(blocks: Many[orm.Dict]) -> int:
    return sum(block.get_dict()['value'] for block in blocks.values())


@graph
def map_leaves(values: dict) -> int:
    for value in values:
        blocks = make_leaf(value=value)
    return consume_leaves(blocks=blocks)


def test_scalar_map_control(aiida_profile):
    assert run(map_leaves, values={'b00': 3})['result'].value == 3


def test_fixed_namespace_control(aiida_profile):
    outputs = run(produce_named_blocks)
    assert outputs['b00']['parameters'].get_dict() == {'value': 3}
    assert 'file' not in outputs['b00']


@pytest.mark.parametrize('values', [{}, {'b00': 3}, {'b00': 3, 'b01': 4}])
@pytest.mark.parametrize('handle', [map_blocks])
def test_structured_map(aiida_profile, handle, values):
    assert run(handle, values=values)['result'].value == sum(values.values())


def test_keyed_model_output(aiida_profile):
    outputs = run(produce_keyed_blocks)
    assert outputs['blocks']['b00']['parameters'].get_dict() == {'value': 3}
    assert 'file' not in outputs['blocks']['b00']


@graph
def block_graph(value: int) -> Block:
    block = make_block(value=value)
    return block


@graph
def map_subgraphs(values: dict) -> int:
    for value in values:
        blocks = block_graph(value=value)
    return consume_blocks(blocks=blocks)


@graph
def return_keyed_blocks() -> Blocks:
    blocks = produce_keyed_blocks()
    return blocks


@graph
def consume_keyed_blocks() -> int:
    blocks = produce_keyed_blocks()
    return consume_blocks(blocks=blocks.blocks)


@pytest.mark.parametrize('values', [{}, {'b00': 3}, {'b00': 3, 'b01': 4}])
def test_mapped_subgraphs(aiida_profile, values):
    assert run(map_subgraphs, values=values)['result'].value == sum(values.values())


@pytest.mark.parametrize('handle', [map_blocks, map_subgraphs, return_keyed_blocks, consume_keyed_blocks])
def test_roundtrip(aiida_profile, handle):
    spec = handle.build()
    restored = GraphSpec.from_dict(json.loads(json.dumps(spec.to_dict())))
    assert restored == spec
    inputs = {'values': {'b00': 3, 'b01': 4}} if handle in (map_blocks, map_subgraphs) else {}
    outputs, node = run_get_node(GraphProcess, **GraphProcess.launch_inputs(restored, inputs))
    assert node.is_finished_ok
    if handle is return_keyed_blocks:
        port = restored.output_spec()['blocks'].entry_port
        assert port['parameters'].required
        assert port['parameters'].valid_type == (orm.Dict,)
        assert port['parameters'].help == 'Block parameters.'
        assert not port['file'].required
        assert outputs['blocks']['b00']['parameters'].get_dict() == {'value': 3}
    else:
        assert outputs['result'].value == (sum(inputs['values'].values()) if inputs else 3)


def test_individual_links(aiida_profile):
    _, node = run_get_node(produce_keyed_blocks)
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all_link_labels() == ['blocks__b00__parameters']
    _, consumer = run_get_node(consume_blocks, blocks={'b00': Block(parameters=orm.Dict({'value': 3}))})
    assert consumer.base.links.get_incoming(link_type=LinkType.INPUT_CALC).all_link_labels() == [
        'blocks__b00__parameters'
    ]
    assert consumer.outputs.result.value == 3


@pytest.mark.parametrize(
    'value', [{'b00': {}}, {'b00': {'parameters': orm.Str}}, {'b00': {'parameters': orm.Dict, 'extra': orm.Int}}]
)
def test_invalid_entry(aiida_profile, value):
    supplied = {key: {name: kind() for name, kind in fields.items()} for key, fields in value.items()}
    output = load_port(dump_port(namespace_for_outputs(Blocks)), output=True)['blocks']
    assert output.validate(_stored(supplied, output)) is not None
    with pytest.raises((ValueError, TypeError)):
        run(consume_blocks, blocks=supplied)


@task
def produce_blocks(values: dict) -> Blocks:
    return Blocks(blocks={key: Block(parameters=orm.Dict({'value': value})) for key, value in values.items()})


@graph
def consume_collection(values: dict) -> int:
    blocks = produce_blocks(values=values)
    return consume_blocks(blocks=blocks.blocks)


@pytest.mark.parametrize('values', [{}, {'b00': 3}, {'b00': 3, 'b01': 4}])
def test_produced_collection(aiida_profile, values):
    assert run(consume_collection, values=values)['result'].value == sum(values.values())


class SingleField(PortModel):
    parameters: orm.Dict


@task
def make_single(value: int) -> SingleField:
    return SingleField(parameters=orm.Dict({'value': value}))


@task
def consume_single(blocks: Many[SingleField]) -> int:
    return sum(block.parameters.get_dict()['value'] for block in blocks.values())


@graph
def map_single(values: dict) -> int:
    for value in values:
        blocks = make_single(value=value)
    return consume_single(blocks=blocks)


def test_single_field_namespace(aiida_profile):
    assert run(map_single, values={'b00': 3})['result'].value == 3


@graph
def return_mapped_blocks(values: dict) -> Blocks:
    for value in values:
        blocks = make_block(value=value)
    return Blocks(blocks=blocks)


@pytest.mark.parametrize('values', [{}, {'b00': 3}, {'b00': 3, 'b01': 4}])
def test_return_mapped_collection(aiida_profile, values):
    spec = GraphSpec.from_dict(json.loads(json.dumps(return_mapped_blocks.build().to_dict())))
    outputs, node = run_get_node(GraphProcess, **GraphProcess.launch_inputs(spec, {'values': values}))
    assert node.is_finished_ok
    held = outputs.get('blocks', {})
    assert set(held) == set(values)
    for key, value in values.items():
        assert held[key]['parameters'].get_dict() == {'value': value}
        assert 'file' not in held[key]
