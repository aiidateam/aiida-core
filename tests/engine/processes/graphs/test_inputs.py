###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Thin namespaces, boundary metadata, and pre-launch graph input validation."""

from __future__ import annotations

import json
import typing as t
from dataclasses import replace

import pytest

from aiida.common.links import LinkType
from aiida.engine import GraphProcess, PortField, PortModel, graph_execution, graph_source, run_get_node, task_source
from aiida.engine.processes.graphs.inputs import dump_port, load_port, merge_ports, namespace_for_function
from aiida.engine.processes.graphs.spec import Endpoint, GraphSpec, ProcessTask
from aiida.engine.processes.ports import InputPort, PortNamespace
from aiida.orm import Dict, GraphNode, Int, QueryBuilder, Str

pytestmark = pytest.mark.presto


class ModelCodes(PortModel):
    kcp: t.Annotated[Int, PortField(help='Configure the KCP executable.')]
    pw: int = 1


@task_source
def consume_model(codes: ModelCodes) -> int:
    return codes.kcp.value + codes.pw


@graph_source
def model_route(codes: ModelCodes) -> int:
    return consume_model(codes=codes)


@graph_execution
def execution_model_route(codes: ModelCodes):
    return {'result': consume_model(codes=codes)}


@pytest.mark.parametrize('handle', (model_route, execution_model_route))
@pytest.mark.parametrize('as_model', (False, True))
def test_port_model_graph_boundary(handle, as_model):
    spec = restored(handle)
    ports = spec.input_spec()['codes']
    assert ports['kcp'].required
    assert ports['kcp'].help == 'Configure the KCP executable.'
    given = ModelCodes(kcp=Int(2)) if as_model else {'kcp': Int(2)}
    prepared = spec.serialize_inputs({'codes': given})
    assert prepared['codes']['pw'] == 1
    with pytest.raises(ValueError, match=r'inputs\.codes\.kcp.*required value was not provided'):
        spec.prepare_inputs({})
    results, node = run_get_node(GraphProcess, **handle.get_launch_inputs(codes=given))
    assert node.is_finished_ok
    assert next(iter(results.values())) == 3
    assert 'graph_inputs__codes__kcp' in node.base.links.get_incoming().all_link_labels()


class Codes(PortModel):
    kcp: t.Annotated[Int, PortField(help='Configure the KCP executable.')]
    pw: t.Annotated[int, PortField(help='Optional PW executable.')] = 1


class Configuration(PortModel):
    codes: Codes


@task_source
def consume(codes: Codes) -> int:
    return codes.kcp.value


@graph_source
def route(codes: t.Annotated[Codes, PortField(help='Route-specific codes.')], unused: int) -> int:
    return consume(codes=codes)


@graph_source
def untyped_route(codes) -> int:
    return consume(codes=codes)


@graph_source
def passthrough(configuration: Configuration) -> Configuration:
    return configuration


@graph_source
def outer(codes: Codes, unused: int) -> int:
    return route(codes=codes, unused=unused)


@graph_execution
def defaulted(value: int = 5):
    return {'value': value}


def restored(handle):
    spec = handle.build()
    data = json.loads(json.dumps(spec.to_dict(), allow_nan=False))
    result = GraphSpec.from_dict(data)
    assert result.to_dict() == data
    assert data['version'] == '1.0'
    assert 'input_ports' not in data
    return result


def test_boundary_reconstructs_ordinary_ports_and_preserves_help():
    spec = restored(route)
    namespace = spec.input_spec()
    assert isinstance(namespace, PortNamespace)
    assert namespace['codes'].help == 'Route-specific codes.'
    assert namespace['codes']['kcp'].help == 'Configure the KCP executable.'
    assert namespace['codes']['kcp'].required
    assert not namespace['codes']['pw'].required
    assert namespace['codes']['pw'].has_default()
    assert namespace['unused'].required
    assert spec.inputs['unused'] == ()
    assert route.build() == route.build()


def test_unannotated_graph_input_infers_the_connected_task_namespace():
    spec = restored(untyped_route)
    assert isinstance(spec.input_spec()['codes'], PortNamespace)
    with pytest.raises(ValueError, match=r'inputs\.codes\.kcp.*required value was not provided'):
        GraphProcess.launch_inputs(spec, {'codes': {}})
    node = Int(7)
    assert GraphProcess.launch_inputs(spec, {'codes': {'kcp': node}})['graph_inputs'] == {'codes': {'kcp': node}}


def test_nested_graph_boundary_metadata_round_trips():
    spec = restored(outer)
    assert spec.tasks[0].body.input_spec()['codes'].help == 'Route-specific codes.'


@pytest.mark.parametrize('launch', ['handle', 'direct', 'raw'])
def test_missing_inputs_report_the_same_port_error_before_storage(launch):
    spec = restored(route)
    count = QueryBuilder().append(GraphNode).count()
    with pytest.raises(ValueError, match=r'inputs\.codes\.kcp.*required value was not provided'):
        if launch == 'handle':
            route.get_launch_inputs(codes={})
        elif launch == 'direct':
            GraphProcess.launch_inputs(spec, {'codes': {}})
        else:
            GraphProcess(inputs={'graph': Dict(dict=spec.to_dict()), 'graph_inputs': {'codes': {}}})
    assert QueryBuilder().append(GraphNode).count() == count


def test_missing_scalar_graph_input_reports_a_port_error():
    with pytest.raises(ValueError, match=r'inputs\.unused.*required value was not provided'):
        route.get_launch_inputs(codes={'kcp': Int(1)})


def test_omitted_required_namespace_reports_its_leaf():
    with pytest.raises(ValueError, match=r'inputs\.configuration\.codes\.kcp.*required value was not provided'):
        passthrough.get_launch_inputs()


def test_optional_namespace_is_checked_only_when_supplied():
    node = Int(7)
    spec = restored(passthrough)
    namespace = spec.input_spec()
    optional = load_port(dump_port(namespace['configuration']['codes']))
    optional.required = False
    namespace['configuration']['optional_codes'] = optional
    spec = replace(spec, input_namespace=dump_port(namespace))
    supplied = {'configuration': {'codes': {'kcp': node}}}
    inputs = GraphProcess.launch_inputs(spec, supplied)
    assert 'optional_codes' not in inputs['graph_inputs']['configuration']
    assert supplied == {'configuration': {'codes': {'kcp': node}}}
    with pytest.raises(
        ValueError, match=r'inputs\.configuration\.optional_codes\.kcp.*required value was not provided'
    ):
        GraphProcess.launch_inputs(spec, {'configuration': {'codes': {'kcp': node}, 'optional_codes': {}}})


def test_defaults_work_without_the_live_graph_handle():
    inputs = GraphProcess.launch_inputs(restored(defaulted), {})
    assert inputs['graph_inputs']['value'].value == 5
    assert defaulted.get_launch_inputs()['graph_inputs']['value'].value == 5


@pytest.mark.parametrize('given', [{'codes': None, 'unused': 1}, {'codes': {'kcp': Int}, 'unused': 1}])
def test_wrong_shapes_and_types_are_rejected(given):
    with pytest.raises((TypeError, ValueError)):
        GraphProcess.launch_inputs(restored(route), given)


def test_unknown_arguments_and_duplicate_binding_remain_type_errors():
    with pytest.raises(TypeError):
        route.get_launch_inputs(unknown=1)
    with pytest.raises(TypeError):
        route.get_launch_inputs({}, codes={})


def test_manual_graph_uses_task_namespace_without_lifting_task_defaults():
    spec = GraphSpec(
        tasks=(ProcessTask(name='consume', spec=consume.task_spec),),
        inputs={'codes': (('consume', 'codes'),)},
        outputs={'value': Endpoint(task='consume', port='result')},
    )
    spec = GraphSpec.from_dict(spec.to_dict())
    assert spec.input_spec()['codes']['kcp'].help == 'Configure the KCP executable.'
    with pytest.raises(ValueError, match=r'inputs\.codes\.kcp.*required value was not provided'):
        GraphProcess.launch_inputs(spec, {'codes': {}})


class Options(PortModel):
    iterations: t.Annotated[int, PortField(help='Iteration limit.')] = 5


@graph_source
def structured_passthrough(options: Options) -> Options:
    return options


def test_structured_value_and_nested_defaults_use_leaf_nodes():
    given = {'options': {}}
    inputs = GraphProcess.launch_inputs(restored(structured_passthrough), given)
    assert inputs['graph_inputs']['options']['iterations'].value == 5
    assert given == {'options': {}}
    inputs = structured_passthrough.get_launch_inputs(options=Options(iterations=7))
    assert inputs['graph_inputs']['options']['iterations'].value == 7
    assert restored(structured_passthrough).input_spec()['options']['iterations'].help == 'Iteration limit.'


def test_required_namespace_with_only_defaulted_children_is_still_required():
    with pytest.raises(ValueError, match=r'inputs\.options.*required value was not provided'):
        structured_passthrough.get_launch_inputs()


def test_raw_launch_applies_defaults_before_provenance_links():
    spec = restored(defaulted)
    process = GraphProcess(inputs={'graph': Dict(dict=spec.to_dict())})
    try:
        assert process.node.inputs.graph_inputs.value.value == 5
        assert process.run_state.given['value'].uuid == process.node.inputs.graph_inputs.value.uuid
    finally:
        process.close()


def test_namespace_snapshot_is_not_aliased_to_serialized_dictionary():
    spec = restored(route)
    data = spec.to_dict()
    data['input_namespace']['ports']['codes']['help'] = 'Changed.'
    assert spec.input_spec()['codes'].help == 'Route-specific codes.'


@pytest.mark.parametrize('default', [object(), lambda: 5, float('nan'), Int])
def test_unstorable_graph_defaults_are_rejected(default):
    def function(value=default):
        pass

    with pytest.raises(TypeError, match='cannot declare graph input `value`'):
        namespace_for_function(function)


def test_shared_consumer_metadata_is_deterministic_and_task_defaults_stay_local():
    required = InputPort('kcp', valid_type=Int, help='Z help.')
    optional = InputPort('pw', valid_type=Int, required=False, help='A help.', default=lambda: Int(5))
    forward = merge_ports('code', [required, optional])
    backward = merge_ports('code', [optional, required])
    assert dump_port(forward) == dump_port(backward)
    assert forward.required
    assert forward.help == 'A help.'
    assert not forward.has_default()
    with pytest.raises(ValueError, match='incompatible'):
        merge_ports('codes', [required, PortNamespace('codes')])


def test_wrong_leaf_type_reports_a_type_error():
    with pytest.raises(ValueError, match='not of the right type'):
        route.get_launch_inputs(codes={'kcp': Str('wrong')}, unused=1)


def test_passthrough_namespace_has_leaf_links_not_a_container_node():
    leaf = Int(7)
    inputs = passthrough.get_launch_inputs(configuration={'codes': {'kcp': leaf}})
    results, process_node = run_get_node(GraphProcess, **inputs)
    assert results['configuration']['codes']['kcp'].uuid == leaf.uuid
    incoming = process_node.base.links.get_incoming(link_type=LinkType.INPUT_WORK)
    assert {entry.link_label for entry in incoming.all()} == {
        'graph',
        'graph_inputs__configuration__codes__kcp',
        'graph_inputs__configuration__codes__pw',
    }
    assert process_node.inputs.graph_inputs.configuration.codes.kcp.uuid == leaf.uuid
    assert not isinstance(inputs['graph_inputs']['configuration'], Dict)
