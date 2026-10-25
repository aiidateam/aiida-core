###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Keyed task outputs are namespaces, not dictionary nodes."""

import json

import pytest

from aiida import orm
from aiida.common.links import LinkType
from aiida.engine import (
    GraphProcess,
    Many,
    PortModel,
    WorkChain,
    graph_execution,
    graph_source,
    run_get_node,
    task_from_workchain,
    task_source,
)
from aiida.engine.processes.graphs.inputs import port_for_shape
from aiida.engine.processes.graphs.process import _stored
from aiida.engine.processes.graphs.shapes import dump_shape, load_shape, shape_for_annotation
from aiida.engine.processes.graphs.spec import GraphSpec

pytestmark = pytest.mark.presto


class Prepared(PortModel):
    values: Many[orm.Int]


@task_source
def prepare_values() -> Prepared:
    return Prepared(values={'a': orm.Int(1), 'b': orm.Int(2)})


class EchoWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input_namespace('values', dynamic=True, valid_type=orm.Int)
        spec.output('result', valid_type=orm.Int)
        spec.outline(cls.echo)

    def echo(self):
        assert set(self.inputs['values']) == {'a', 'b'}
        self.out('result', self.inputs['values']['a'])


EchoStep = task_from_workchain(EchoWorkChain)


@graph_source
def prepared_source() -> orm.Int:
    prepared = prepare_values()
    echoed = EchoStep(values=prepared.values)
    return echoed.result


@graph_execution
def prepared_execution() -> orm.Int:
    prepared = prepare_values()
    echoed = EchoStep(values=prepared.values)
    return echoed.result


@graph_source
def return_namespace() -> Prepared:
    prepared = prepare_values()
    return Prepared(values=prepared.values)


@task_source
def make_node(value: int) -> orm.Int:
    return orm.Int(value)


@graph_source
def gather_control(values: dict) -> orm.Int:
    for value in values:
        nodes = make_node(value=value)
    echoed = EchoStep(values=nodes)
    return echoed.result


@pytest.mark.parametrize('handle', [prepared_source, prepared_execution, return_namespace])
def test_dynamic_graph_roundtrip(handle):
    spec = handle.build()
    restored = GraphSpec.from_dict(json.loads(json.dumps(spec.to_dict())))
    assert restored == spec
    outputs, node = run_get_node(GraphProcess, **GraphProcess.launch_inputs(restored, {}))
    assert node.is_finished_ok
    task_node = next(child for child in node.called if child.process_label == 'prepare_values')
    assert sorted(task_node.base.links.get_outgoing(link_type=LinkType.CREATE).all_link_labels()) == [
        'values__a',
        'values__b',
    ]
    assert task_node.outputs.values.a.value == 1
    assert task_node.outputs.values.b.value == 2
    result = outputs['values']['a'] if handle is return_namespace else outputs['result']
    assert result.uuid == task_node.outputs.values.a.uuid
    if handle is return_namespace:
        port = restored.output_spec()['values']
        assert port.dynamic
        assert port.valid_type == (orm.Int,)


def test_controls():
    first = orm.Int(1)
    outputs, _ = run_get_node(EchoWorkChain, values={'a': first, 'b': orm.Int(2)})
    assert outputs['result'].uuid == first.uuid
    outputs, _ = run_get_node(gather_control, values={'a': 1, 'b': 2})
    assert outputs['result'].value == 1


class Nested(PortModel):
    prepared: Prepared


@task_source
def nested_values(empty: bool) -> Nested:
    return Nested(prepared=Prepared(values={} if empty else {'a': orm.Int(1)}))


@pytest.mark.parametrize('empty', [False, True])
def test_direct_nested_task(empty):
    _, node = run_get_node(nested_values, empty=empty)
    assert node.is_finished_ok
    links = node.base.links.get_outgoing(link_type=LinkType.CREATE).all()
    assert [link.link_label for link in links] == ([] if empty else ['prepared__values__a'])


@task_source
def return_stored(uuid: str) -> Prepared:
    return Prepared(values={'a': orm.load_node(uuid)})


def test_stored_outputs_preserve_calcfunction_provenance_rules():
    original = orm.Int(1).store()
    with pytest.raises(ValueError, match='already stored Data node'):
        run_get_node(return_stored, uuid=original.uuid)
    assert original.creator is None


@task_source
def count_values(values: Many[orm.Int]) -> int:
    return len(values)


@task_source
def empty_values() -> Prepared:
    return Prepared(values={})


@graph_source
def empty_graph() -> int:
    prepared = empty_values()
    return count_values(values=prepared.values)


def test_empty_collection_wiring():
    outputs, node = run_get_node(empty_graph)
    assert node.is_finished_ok
    assert outputs['result'].value == 0


def test_namespace_validation_and_identity():
    shape = load_shape(json.loads(json.dumps(dump_shape(shape_for_annotation(Prepared)))))
    restored = port_for_shape('outputs', shape, output=True)
    port = restored['values']
    assert port.dynamic
    assert port.valid_type == (orm.Int,)
    node = orm.Int(1).store()
    assert _stored({'a': node}, port)['a'] is node
    assert _stored({}, port) == {}
    assert _stored({'a': 1}, port)['a'].value == 1


@pytest.mark.parametrize('key', ['a.b', 'a__b', '_a', 'a-', '', 1])
def test_invalid_keys(key):
    port = port_for_shape('outputs', shape_for_annotation(Prepared), output=True)['values']
    with pytest.raises((TypeError, ValueError)):
        _stored({key: orm.Int(1)}, port)


@pytest.mark.parametrize('value', [lambda: orm.Str('wrong'), lambda: 'wrong', lambda: {'nested': 1}])
def test_invalid_leaves(value):
    port = port_for_shape('outputs', shape_for_annotation(Prepared), output=True)['values']
    with pytest.raises(TypeError, match='Invalid type'):
        _stored({'a': value()}, port)


def test_requires_mapping():
    port = port_for_shape('outputs', shape_for_annotation(Prepared), output=True)['values']
    with pytest.raises(TypeError, match='requires a mapping'):
        _stored(orm.Int(1), port)
