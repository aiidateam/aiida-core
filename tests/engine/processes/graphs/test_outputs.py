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
    PortModel,
    WorkChain,
    graph_execution,
    graph_source,
    run_get_node,
    task_execution,
    task_source,
)
from aiida.engine.processes.graphs.inputs import dump_port, namespace_for_outputs
from aiida.engine.processes.graphs.spec import Endpoint, GraphSpec
from aiida.engine.processes.ports import OutputPort
from aiida.orm import Int

pytestmark = pytest.mark.presto


class Values(PortModel):
    total: int
    extra: int = 0


class Results(PortModel):
    values: Values
    count: int


@task_source
def make_values(value: int) -> Values:
    return {'total': value + 1}


@graph_source
def named_source(value: int) -> Results:
    result = make_values(value=value)
    return Results(values=Values(total=result.total), count=result.total)


@graph_execution
def named_execution(value: int) -> Results:
    result = make_values(value=value)
    return {'values': {'total': result.total}, 'count': result.total}


@graph_source
def selected_source(value: int) -> Values:
    result = make_values(value=value)
    return {'total': result.total, 'extra': result.extra}


@graph_execution
def whole_execution(value: int) -> Values:
    return make_values(value=value)


@graph_source
def whole_source(value: int) -> Values:
    return make_values(value=value)


@graph_source
def nested_source(value: int) -> Values:
    result = named_source(value=value)
    return {'total': result.values.total}


@graph_execution
def nested_execution(value: int) -> Values:
    result = named_execution(value=value)
    return {'total': result.values.total}


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


def test_legacy_namespace_and_independent_snapshots():
    spec = selected_source.build()
    legacy = spec.to_dict()
    legacy.pop('output_namespace')
    assert GraphSpec.from_dict(legacy).output_spec().dynamic
    snapshot = spec.to_dict()
    snapshot['output_namespace']['ports'].clear()
    assert spec.output_spec()['total'].required
    assert GraphProcess.spec().outputs.dynamic
