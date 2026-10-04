###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Graph return declarations use ordinary output ports and provenance links."""

import json
from dataclasses import replace

import pytest

from aiida.common.links import LinkType
from aiida.engine import (
    CalcJob,
    GraphProcess,
    Met,
    PortModel,
    WorkChain,
    graph_execution,
    graph_source,
    monitor,
    run_get_node,
    task_execution,
    task_source,
)
from aiida.engine.processes.graphs.build_source import UnsupportedSyntax
from aiida.engine.processes.graphs.inputs import dump_port, namespace_for_outputs
from aiida.engine.processes.graphs.spec import Endpoint, GraphSpec
from aiida.engine.processes.ports import OutputPort
from aiida.orm import Dict, Int

pytestmark = pytest.mark.presto


class Values(PortModel):
    total: int
    extra: int = 0


class Results(PortModel):
    values: Values
    count: int


@task_source
def make_values(value: int) -> Values:
    return Values(total=value + 1)


@graph_source
def named_source(value: int) -> Results:
    result = make_values(value=value)
    return Results(values=Values(total=result.total), count=result.total)


@graph_execution
def named_execution(value: int) -> Results:
    result = make_values(value=value)
    return Results(values=Values(total=result.total), count=result.total)


@graph_source
def selected_source(value: int) -> Values:
    result = make_values(value=value)
    return Values(total=result.total, extra=result.extra)


@graph_execution
def whole_execution(value: int) -> Values:
    return make_values(value=value)


@graph_source
def whole_source(value: int) -> Values:
    return make_values(value=value)


@graph_source
def nested_source(value: int) -> Values:
    result = named_source(value=value)
    return Values(total=result.values.total)


@graph_execution
def nested_execution(value: int) -> Values:
    result = named_execution(value=value)
    return Values(total=result.values.total)


@pytest.mark.parametrize(
    'handle',
    (named_source, named_execution, selected_source, whole_execution, whole_source, nested_source, nested_execution),
)
def test_outputs_roundtrip_and_provenance(handle):
    spec = handle.build()
    restored = GraphSpec.from_dict(json.loads(json.dumps(spec.to_dict())))
    assert restored == spec
    ports = restored.output_spec()
    leaf = ports['values']['total'] if 'values' in ports else ports['total']
    assert isinstance(leaf, OutputPort)
    outputs, node = run_get_node(GraphProcess, **GraphProcess.launch_inputs(restored, {'value': 2}))
    assert node.is_finished_ok
    values = outputs.get('values', outputs)
    assert values['total'] == 3
    assert 'extra' not in values
    labels = node.base.links.get_outgoing(link_type=LinkType.RETURN).all_link_labels()
    assert ('values__total' if 'values' in outputs else 'total') in labels
    assert values['total'].creator is not None
    assert node.called


def test_invalid_paths_types_and_missing_required():
    spec = named_source.build()
    with pytest.raises(ValueError, match='not declared'):
        replace(spec, outputs={'unknown': Endpoint(task='make_values', port='total')})
    with pytest.raises(ValueError, match='required graph output'):
        replace(spec, outputs={})

    class Wrong(PortModel):
        total: str

    with pytest.raises(ValueError, match='incompatible types'):
        replace(selected_source.build(), output_namespace=dump_port(namespace_for_outputs(Wrong)))


def test_optional_omission_is_not_none():
    ports = namespace_for_outputs(Values)
    assert ports.validate({'total': Int(1)}) is None
    assert ports.validate({'total': Int(1), 'extra': None}) is not None

    class OptionalResults(PortModel):
        values: Values = None

    spec = GraphSpec(tasks=(), output_namespace=dump_port(namespace_for_outputs(OptionalResults)))
    assert not spec.output_required('values.total')
    assert spec.output_spec().validate({}) is None


class OrdinaryCalculation(CalcJob):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.output('results.energy', valid_type=Int)


class OrdinaryWorkflow(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.output('results.energy', valid_type=Int)


@pytest.mark.parametrize('process', (OrdinaryCalculation, OrdinaryWorkflow))
def test_registered_process_output_declarations_are_preserved(process):
    original = process.spec().outputs
    handle = task_execution(process)
    assert handle.task_spec.outputs is original
    leaf = original['results']['energy']
    assert leaf.valid_type is Int
    assert leaf.required


@graph_source
def unannotated_dictionary(value: int):
    result = make_values(value=value)
    return {'total': result.total}


@graph_source
def scalar_dictionary_namespace(value: int) -> dict:
    result = make_values(value=value)
    return {'total': result.total}


@graph_execution
def unannotated_execution_dictionary(value: int):
    result = make_values(value=value)
    return {'total': result.total}


@graph_execution
def scalar_execution_dictionary_namespace(value: int) -> dict:
    result = make_values(value=value)
    return {'total': result.total}


@graph_source
def annotated_source_dictionary(value: int) -> Values:
    result = make_values(value=value)
    return {'total': result.total}


@graph_execution
def annotated_execution_dictionary(value: int) -> Values:
    result = make_values(value=value)
    return {'total': result.total}


@pytest.mark.parametrize(
    'handle',
    [
        unannotated_dictionary,
        scalar_dictionary_namespace,
        unannotated_execution_dictionary,
        scalar_execution_dictionary_namespace,
        annotated_source_dictionary,
        annotated_execution_dictionary,
    ],
)
def test_dictionaries_do_not_declare_graph_namespaces(handle):
    with pytest.raises((TypeError, UnsupportedSyntax), match='PortModel return annotation'):
        handle.build()


class DictionaryResults(PortModel):
    values: dict[str, int]


@task_source
def make_dictionary(value: int) -> dict[str, int]:
    return {'value': value, 'nested': {'value': value + 1}}


@graph_source
def dictionary_source(value: int) -> dict[str, int]:
    return make_dictionary(value=value)


@graph_execution
def dictionary_execution(value: int) -> dict[str, int]:
    return make_dictionary(value=value)


@graph_source
def named_dictionary_source(value: int) -> DictionaryResults:
    return DictionaryResults(values=make_dictionary(value=value))


@graph_execution
def named_dictionary_execution(value: int) -> DictionaryResults:
    return DictionaryResults(values=make_dictionary(value=value))


@pytest.mark.parametrize(
    'handle,name',
    [
        (dictionary_source, 'result'),
        (dictionary_execution, 'result'),
        (named_dictionary_source, 'values'),
        (named_dictionary_execution, 'values'),
    ],
)
def test_dictionary_annotation_is_one_data_output(handle, name):
    assert list(make_dictionary.task_spec.outputs) == ['result']
    spec = handle.build()
    assert list(spec.outputs) == [name]
    results, node = run_get_node(handle, value=2)
    assert node.is_finished_ok, node.exit_message
    assert isinstance(results[name], Dict)
    assert results[name].get_dict() == {'value': 2, 'nested': {'value': 3}}


@graph_source
def undeclared_source_field(value: int) -> Values:
    result = make_values(value=value)
    return Values(unknown=result.total)


@graph_execution
def undeclared_execution_field(value: int) -> Values:
    result = make_values(value=value)
    return Values(unknown=result.total)


@pytest.mark.parametrize('handle', [undeclared_source_field, undeclared_execution_field])
def test_returned_fields_must_be_declared(handle):
    with pytest.raises((TypeError, ValueError, UnsupportedSyntax), match=r'not declared|unknown'):
        handle.build()


@graph_source
def undeclared_nested_namespace(value: int) -> Values:
    result = make_values(value=value)
    return Values(total={'hidden': result.total})


@graph_execution
def undeclared_execution_namespace(value: int) -> Values:
    result = make_values(value=value)
    return Values(total={'hidden': result.total})


@pytest.mark.parametrize('handle', [undeclared_nested_namespace, undeclared_execution_namespace])
def test_dictionary_shape_cannot_turn_a_leaf_into_a_namespace(handle):
    with pytest.raises((ValueError, UnsupportedSyntax), match=r'PortModel|not the output'):
        handle.build()


@task_source
def unannotated_task_dictionary(value: int):
    return {'total': value, 'nested': {'extra': value + 1}}


@task_execution(outputs=['payload'])
def named_task_dictionary(value: int) -> dict:
    return {'total': value, 'nested': {'extra': value + 1}}


@pytest.mark.parametrize('handle,name', [(unannotated_task_dictionary, 'result'), (named_task_dictionary, 'payload')])
def test_task_dictionary_is_data_without_namespace_inference(handle, name):
    _, node = run_get_node(handle, value=2)
    assert node.is_finished_ok
    assert list(node.outputs) == [name]
    assert isinstance(node.outputs[name], Dict)
    assert node.outputs[name].get_dict() == {'total': 2, 'nested': {'extra': 3}}


@task_source
def dictionary_instead_of_model(value: int) -> Values:
    return {'total': value}


@task_source
def dictionary_instead_of_nested_model(value: int) -> Results:
    return Results(values={'total': value}, count=value)


@task_source
def unannotated_task_model(value: int):
    return Values(total=value)


@pytest.mark.parametrize(
    'handle', [dictionary_instead_of_model, dictionary_instead_of_nested_model, unannotated_task_model]
)
def test_task_namespaces_require_model_declarations_and_values(handle):
    with pytest.raises(TypeError, match='PortModel'):
        run_get_node(handle, value=2)


@task_source
def nested_task_model(value: int) -> Results:
    return Results(values=Values(total=value), count=value + 1)


@task_source
def dictionary_field_model(value: int) -> DictionaryResults:
    return DictionaryResults(values={'total': value, 'nested': {'extra': value + 1}})


def test_nested_task_model_values_are_stored_under_declared_ports():
    _, node = run_get_node(nested_task_model, value=2)
    assert node.is_finished_ok
    assert node.outputs.values.total == 2
    assert 'extra' not in node.outputs.values
    assert node.outputs.count == 3
    assert sorted(node.base.links.get_outgoing(link_type=LinkType.CREATE).all_link_labels()) == [
        'count',
        'values__total',
    ]


def test_model_dictionary_field_remains_one_data_node():
    _, node = run_get_node(dictionary_field_model, value=2)
    assert node.is_finished_ok
    assert isinstance(node.outputs.values, Dict)
    assert node.outputs.values.get_dict() == {'total': 2, 'nested': {'extra': 3}}
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all_link_labels() == ['values']


@monitor(outputs=['payload', 'total'])
def declared_monitor_outputs(value: int) -> Met:
    return Met(payload={'total': value}, total=value)


def test_monitor_keeps_explicit_output_bindings():
    _, node = run_get_node(declared_monitor_outputs, value=2)
    assert node.is_finished_ok
    assert isinstance(node.outputs.payload, Dict)
    assert node.outputs.payload.get_dict() == {'total': 2}
    assert node.outputs.total == 2


def test_legacy_namespace_and_independent_snapshots():
    spec = selected_source.build()
    legacy = spec.to_dict()
    legacy.pop('output_namespace')
    assert GraphSpec.from_dict(legacy).output_spec().dynamic
    snapshot = spec.to_dict()
    snapshot['output_namespace']['ports'].clear()
    assert spec.output_spec()['total'].required
    assert GraphProcess.spec().outputs.dynamic
