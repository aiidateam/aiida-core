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
import pickle
import typing as t
from dataclasses import replace

import pytest

from aiida.common.exceptions import MissingInput, MissingRequiredInputsError
from aiida.common.links import LinkType
from aiida.engine import GraphProcess, PortField, PortModel, graph_execution, graph_source, run_get_node, task_source
from aiida.engine.processes.graphs.build_source import UnsupportedSyntax
from aiida.engine.processes.graphs.inputs import merge_ports, port_for_shape, shape_from_port
from aiida.engine.processes.graphs.shapes import dump_shape, shape_for_function
from aiida.engine.processes.graphs.spec import Endpoint, GraphSpec, ProcessTask
from aiida.engine.processes.ports import InputPort, PortNamespace
from aiida.orm import Code, Dict, GraphNode, Int, QueryBuilder, Str

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
def execution_model_route(codes: ModelCodes) -> int:
    return consume_model(codes=codes)


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
    with pytest.raises(MissingRequiredInputsError) as caught:
        spec.prepare_inputs({})
    assert caught.value.missing == (MissingInput(spec.identifier, 'codes.kcp', 'Configure the KCP executable.', True),)
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
def defaulted(value: int = 5) -> int:
    return value


class Executables(PortModel):
    pw: t.Annotated[Code, PortField(help='Required PW code.')]
    optional: t.Annotated[Code | None, PortField(help='Optional code.')] = None


class ExecutableConfiguration(PortModel):
    codes: t.Annotated[Executables, PortField(help='Grouped codes.')]


@task_source
def code_label(code: Code) -> str:
    return code.label


@graph_source
def select_code(codes: t.Annotated[Executables, PortField(help='Workflow codes.')]) -> str:
    return code_label(code=codes.pw)


@graph_source
def select_same_named_field(pw: Executables) -> str:
    return code_label(code=pw.pw)


@graph_source
def select_nested_code(configuration: ExecutableConfiguration) -> str:
    return code_label(code=configuration.codes.pw)


@graph_source
def branch_selected_code(codes: Executables, condition: bool) -> str:
    if condition:
        result = code_label(code=codes.pw)
    else:
        result = code_label(code=codes.pw)
    return result


@graph_source
def unknown_input_field(codes: Executables) -> str:
    return code_label(code=codes.missing)


@graph_source
def dictionary_input_field(values: dict) -> str:
    return code_label(code=values.pw)


@graph_source
def scalar_input_field(code: Code) -> str:
    return code_label(code=code.code)


@pytest.mark.parametrize(
    ('handle', 'path'),
    [
        (select_code, 'codes.pw'),
        (select_nested_code, 'configuration.codes.pw'),
        (select_same_named_field, 'pw.pw'),
    ],
)
def test_selected_input_metadata_and_missing_fields(handle, path):
    spec = restored(handle)
    assert len(spec.tasks) == 1
    assert spec.inputs[path] == (('code_label', 'code'),)
    port = spec.input_spec().get_port(path)
    assert port.required
    assert port.help == 'Required PW code.'
    assert port.valid_type == (Code,)
    optional = spec.input_spec().get_port(f'{path.rsplit(".", 1)[0]}.optional')
    assert not optional.required
    assert optional.help == 'Optional code.'
    spec.validate_typehints()
    with pytest.raises(MissingRequiredInputsError) as caught:
        GraphProcess.launch_inputs(spec, {})
    assert caught.value.missing == (MissingInput(spec.identifier, path, port.help, True),)


@pytest.mark.parametrize('handle', [select_code, select_nested_code, branch_selected_code])
def test_selected_stored_code_routes_without_selector(handle, aiida_code_installed):
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/true')
    code.label = 'original code'
    given = {'codes': {'pw': code}}
    if handle is select_nested_code:
        given = {'configuration': given}
    if handle is branch_selected_code:
        given['condition'] = True
    results, node = run_get_node(GraphProcess, **GraphProcess.launch_inputs(restored(handle), given))
    assert node.is_finished_ok
    assert next(iter(results.values())).value == code.label
    calculations = [
        child for child in node.called_descendants if child.node_type.endswith('calcfunction.CalcFunctionNode.')
    ]
    assert len(calculations) == 1
    assert (
        calculations[0].base.links.get_incoming(link_type=LinkType.INPUT_CALC).get_node_by_label('code').uuid
        == code.uuid
    )
    assert not code.base.links.get_incoming(link_type=LinkType.CREATE).all()


@pytest.mark.parametrize(
    ('handle', 'path'),
    [(unknown_input_field, 'codes.missing'), (dictionary_input_field, 'values.pw'), (scalar_input_field, 'code.code')],
)
def test_input_selection_rejects_unknown_fields_and_leaves(handle, path):
    with pytest.raises(UnsupportedSyntax, match=path):
        handle.build()


def restored(handle):
    spec = handle.build()
    data = json.loads(json.dumps(spec.to_dict(), allow_nan=False))
    result = GraphSpec.from_dict(data)
    assert result.to_dict() == data
    assert data['version'] == '1.1'
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
    with pytest.raises(MissingRequiredInputsError) as caught:
        GraphProcess.launch_inputs(spec, {'codes': {}})
    assert [item.socket_path for item in caught.value.missing] == ['codes.kcp']
    node = Int(7)
    assert GraphProcess.launch_inputs(spec, {'codes': {'kcp': node}})['graph_inputs'] == {'codes': {'kcp': node}}


def test_nested_graph_boundary_metadata_round_trips():
    spec = restored(outer)
    assert spec.tasks[0].body.input_spec()['codes'].help == 'Route-specific codes.'


@pytest.mark.parametrize('launch', ['handle', 'direct', 'raw'])
def test_missing_inputs_report_identical_diagnostics_before_storage(launch):
    spec = restored(route)
    count = QueryBuilder().append(GraphNode).count()
    with pytest.raises(MissingRequiredInputsError) as caught:
        if launch == 'handle':
            route.get_launch_inputs(codes={})
        elif launch == 'direct':
            GraphProcess.launch_inputs(spec, {'codes': {}})
        else:
            GraphProcess(inputs={'graph': Dict(dict=spec.to_dict()), 'graph_inputs': {'codes': {}}})
    assert caught.value.missing == (
        MissingInput(spec.identifier, 'codes.kcp', 'Configure the KCP executable.', True),
        MissingInput(spec.identifier, 'unused', None, True),
    )
    assert QueryBuilder().append(GraphNode).count() == count


def test_missing_scalar_graph_input_has_structured_diagnostics():
    with pytest.raises(MissingRequiredInputsError) as caught:
        route.get_launch_inputs(codes={'kcp': Int(1)})
    assert caught.value.missing == (MissingInput(route.build().identifier, 'unused', None, True),)


def test_omitted_required_namespace_reports_its_leaf():
    with pytest.raises(MissingRequiredInputsError) as caught:
        passthrough.get_launch_inputs()
    assert [item.socket_path for item in caught.value.missing] == ['configuration.codes.kcp']


def test_optional_namespace_is_checked_only_when_supplied():
    node = Int(7)
    spec = restored(passthrough)
    namespace = spec.input_spec()
    optional = port_for_shape('optional_codes', shape_from_port(namespace['configuration']['codes']))
    optional.required = False
    namespace['configuration']['optional_codes'] = optional
    spec = replace(spec, input_namespace=dump_shape(shape_from_port(namespace)))
    supplied = {'configuration': {'codes': {'kcp': node}}}
    inputs = GraphProcess.launch_inputs(spec, supplied)
    assert 'optional_codes' not in inputs['graph_inputs']['configuration']
    assert supplied == {'configuration': {'codes': {'kcp': node}}}
    with pytest.raises(MissingRequiredInputsError) as caught:
        GraphProcess.launch_inputs(spec, {'configuration': {'codes': {'kcp': node}, 'optional_codes': {}}})
    assert [item.socket_path for item in caught.value.missing] == ['configuration.optional_codes.kcp']


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
    with pytest.raises(MissingRequiredInputsError) as caught:
        GraphProcess.launch_inputs(spec, {'codes': {}})
    assert [item.socket_path for item in caught.value.missing] == ['codes.kcp']


class Options(PortModel):
    iterations: t.Annotated[int, PortField(help='Iteration limit.')] = 5


class DefaultInputs(PortModel):
    required: int
    nullable: int | None
    defaulted: int = 5
    optional: int | None = None


class NestedDefaultInputs(PortModel):
    values: DefaultInputs
    options: Options = Options(iterations=9)


@task_source
def consume_defaults(values: DefaultInputs) -> int:
    assert values.nullable is None
    assert values.optional is None
    return values.required + values.defaulted


@graph_source
def forward_defaults(values: DefaultInputs) -> int:
    return consume_defaults(values=values)


@task_source
def consume_nested_defaults(configuration: NestedDefaultInputs) -> int:
    assert configuration.options.iterations == 9
    assert configuration['values'].nullable is None
    assert configuration['values'].optional is None
    return configuration['values'].required + configuration['values'].defaulted


@graph_source
def forward_nested_defaults(configuration: NestedDefaultInputs) -> int:
    return consume_nested_defaults(configuration=configuration)


@graph_source
def structured_passthrough(options: Options) -> Options:
    return options


@pytest.mark.parametrize(
    'handle, path', [(forward_defaults, 'values'), (forward_nested_defaults, 'configuration.values')]
)
def test_model_defaults_and_nullable_fields_forward_to_tasks(handle, path):
    spec = restored(handle)
    values = {'required': 2, 'nullable': None}
    given = {'values': values} if path == 'values' else {'configuration': {'values': values}}
    prepared = spec.prepare_inputs(given)
    held = prepared
    for segment in path.split('.'):
        held = held[segment]
    assert held == {'required': 2, 'nullable': None, 'defaulted': 5, 'optional': None}
    if path != 'values':
        assert prepared['configuration']['options'] == {'iterations': 9}
    assert values == {'required': 2, 'nullable': None}
    results, node = run_get_node(GraphProcess, **GraphProcess.launch_inputs(spec, given))
    assert node.is_finished_ok
    assert results['result'] == 7
    task_values = node.called[0].inputs
    for segment in path.split('.'):
        task_values = task_values[segment]
    assert task_values.required.value == 2
    assert task_values.defaulted.value == 5


@pytest.mark.parametrize(
    'handle, prefix', [(forward_defaults, 'values'), (forward_nested_defaults, 'configuration.values')]
)
def test_model_omission_is_not_explicit_none(handle, prefix):
    given = {'values': {}} if prefix == 'values' else {'configuration': {'values': {}}}
    with pytest.raises(MissingRequiredInputsError) as caught:
        GraphProcess.launch_inputs(restored(handle), given)
    assert [item.socket_path for item in caught.value.missing] == [f'{prefix}.nullable', f'{prefix}.required']


@pytest.mark.parametrize('handle', [forward_defaults, forward_nested_defaults])
@pytest.mark.parametrize('field', ['required', 'defaulted'])
@pytest.mark.parametrize('round_trip', [False, True])
def test_nonnullable_model_fields_reject_explicit_none(handle, field, round_trip):
    spec = restored(handle) if round_trip else handle.build()
    values = {'required': 2, 'nullable': None, field: None}
    given = {'values': values} if handle is forward_defaults else {'configuration': {'values': values}}
    with pytest.raises(ValueError, match='not of the right type'):
        GraphProcess.launch_inputs(spec, given)


def test_model_declaration_semantics_round_trip():
    ports = restored(forward_nested_defaults).input_spec()['configuration']
    assert ports.required
    assert ports['values']['required'].required
    assert ports['values']['nullable'].required
    assert ports['values']['nullable'].valid_type == (int, type(None))
    assert not ports['values']['defaulted'].required
    assert ports['values']['defaulted'].valid_type == (int,)
    assert ports['values']['defaulted'].has_default()
    assert not ports['values']['optional'].required
    assert ports['values']['optional'].has_default()
    assert not ports['options'].required
    assert ports['options'].default == {'iterations': 9}


def test_explicit_values_override_model_defaults():
    given = {'values': {'required': 2, 'nullable': None, 'defaulted': 8, 'optional': None}}
    results, node = run_get_node(GraphProcess, **forward_defaults.get_launch_inputs(**given))
    assert node.is_finished_ok
    assert results['result'] == 10


def test_structured_value_and_nested_defaults_use_leaf_nodes():
    given = {'options': {}}
    inputs = GraphProcess.launch_inputs(restored(structured_passthrough), given)
    assert inputs['graph_inputs']['options']['iterations'].value == 5
    assert given == {'options': {}}
    inputs = structured_passthrough.get_launch_inputs(options=Options(iterations=7))
    assert inputs['graph_inputs']['options']['iterations'].value == 7
    assert restored(structured_passthrough).input_spec()['options']['iterations'].help == 'Iteration limit.'


def test_required_namespace_with_only_defaulted_children_is_still_required():
    with pytest.raises(MissingRequiredInputsError) as caught:
        structured_passthrough.get_launch_inputs()
    assert [item.socket_path for item in caught.value.missing] == ['options']


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
    data['input_namespace']['fields']['codes']['help'] = 'Changed.'
    assert spec.input_spec()['codes'].help == 'Route-specific codes.'


@pytest.mark.parametrize('default', [object(), lambda: 5, float('nan'), Int])
def test_unstorable_graph_defaults_are_rejected(default):
    def function(value=default):
        pass

    with pytest.raises(TypeError, match='cannot declare graph input `value`'):
        shape_for_function(function)


def test_shared_consumer_metadata_is_deterministic_and_task_defaults_stay_local():
    required = InputPort('kcp', valid_type=Int, help='Z help.')
    optional = InputPort('pw', valid_type=Int, required=False, help='A help.', default=lambda: Int(5))
    forward = merge_ports('code', [required, optional])
    backward = merge_ports('code', [optional, required])
    assert shape_from_port(forward) == shape_from_port(backward)
    assert forward.required
    assert forward.help == 'A help.'
    assert not forward.has_default()
    with pytest.raises(ValueError, match='incompatible'):
        merge_ports('codes', [required, PortNamespace('codes')])


def test_missing_diagnostics_are_pickleable_and_do_not_mutate_inputs():
    given = {'codes': {}}
    spec = restored(route)
    with pytest.raises(MissingRequiredInputsError) as caught:
        spec.prepare_inputs(given)
    assert given == {'codes': {}}
    error = caught.value
    restored_error = pickle.loads(pickle.dumps(error))
    assert restored_error.missing == error.missing
    assert str(restored_error) == str(error)
    with pytest.raises(AttributeError):
        error.missing[0].socket_path = 'changed'


def test_wrong_leaf_type_reports_a_type_error():
    with pytest.raises(ValueError, match='not of the right type'):
        route.get_launch_inputs(codes={'kcp': Str('wrong')}, unused=1)


def test_passthrough_namespace_has_leaf_links_not_a_container_node():
    leaf = Int(7)
    inputs = passthrough.get_launch_inputs(configuration={'codes': {'kcp': leaf}})
    results, process_node = run_get_node(GraphProcess, **inputs)
    assert results['codes']['kcp'].uuid == leaf.uuid
    incoming = process_node.base.links.get_incoming(link_type=LinkType.INPUT_WORK)
    assert {entry.link_label for entry in incoming.all()} == {
        'graph',
        'graph_inputs__configuration__codes__kcp',
        'graph_inputs__configuration__codes__pw',
    }
    assert process_node.inputs.graph_inputs.configuration.codes.kcp.uuid == leaf.uuid
    assert not isinstance(inputs['graph_inputs']['configuration'], Dict)
