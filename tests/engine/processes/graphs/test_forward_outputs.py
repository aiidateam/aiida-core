###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Selective forwarding of existing graph output nodes."""

import json

import pytest

from aiida.common.exceptions import GraphLanguageError
from aiida.common.links import LinkType
from aiida.engine import (
    Err,
    ExitCodeEnum,
    Ok,
    PortModel,
    Result,
    forward_outputs,
    graph,
    run_get_node,
    task,
)
from aiida.engine.processes.graphs.ir import GraphIR
from aiida.engine.processes.graphs.lowering import compile_graph
from aiida.engine.processes.graphs.process import GraphProcess
from aiida.orm import Float, Int, Str

pytestmark = pytest.mark.presto


class Details(PortModel):
    """A static namespace with an optional leaf."""

    value: int
    note: str | None = None


class Report(PortModel):
    """A producer contract with both namespaces and leaves to select."""

    details: Details
    score: float
    report: str


class Errors(ExitCodeEnum):
    """Failure declared by the producer."""

    MISSING = (460, 'Report unavailable.')


class Summary(PortModel):
    """The `Report` fields left after excluding `report`."""

    details: Details
    score: float


class ScoreReport(PortModel):
    """The `Report` fields left after excluding `details`."""

    score: float
    report: str


class Selected(PortModel):
    """A selection of `Report` under `summary`."""

    summary: Summary


class SelectedSubtree(PortModel):
    """A `Report` without `details` under `summary`."""

    summary: ScoreReport


class SelectedAll(PortModel):
    """A whole `Report` under `summary`."""

    summary: Report


class SelectedOptional(PortModel):
    """A selection of an optional `Report` next to its error arm."""

    summary: Summary | None = None
    error: Errors | None = None


class Captured(PortModel):
    """Both arms of a captured `produce` call."""

    value: Report | None = None
    error: Errors | None = None


class CapturedValue(PortModel):
    """The value arm of a captured `produce` call."""

    value: Report | None = None


class SelectedChild(PortModel):
    """The value arm of `captured` under `summary`."""

    summary: CapturedValue


@task
def produce(mode: int) -> Result[Report, Errors]:
    """Produce no report, a report without a note, or a complete report."""
    if mode == 0:
        return Err(Errors.MISSING)
    return Ok(Report(details=Details(value=2, note='kept' if mode == 2 else None), score=0.5, report='excluded'))


@graph
def select(mode: int) -> Selected:
    """Exclude an immediate leaf, keeping the nested fields."""
    result = produce(mode=mode)
    return {'summary': forward_outputs(result, exclude=('report',))}


@graph
def explicit(mode: int) -> Selected:
    """Spell out the same wiring without a selection."""
    result = produce(mode=mode)
    return {'summary': {'details': {'value': result.details.value, 'note': result.details.note}, 'score': result.score}}


@graph
def select_optional(mode: int) -> SelectedOptional:
    """Filter an optional namespace from a captured result."""
    result, error = produce(mode=mode).catch()
    return {'summary': forward_outputs(result, exclude=('report',)), 'error': error}


@graph
def captured(mode: int) -> Captured:
    """Expose both arms of the invocation as one namespace."""
    result, error = produce(mode=mode).catch()
    return {'value': result, 'error': error}


class ShortReport(PortModel):
    """A `Report` without its `report` field."""

    details: Details
    score: float


class CapturedShort(PortModel):
    """Both arms of a captured call with a short value selection."""

    value: ShortReport | None = None
    error: Errors | None = None


@graph
def captured_short(mode: int) -> CapturedShort:
    """Return both arms while declaring fewer value fields than produced."""
    result, error = produce(mode=mode).catch()
    return {'value': result, 'error': error}


class CapturedRequired(PortModel):
    """Both arms of a captured call with a required value arm."""

    value: Report
    error: Errors | None = None


@graph
def captured_required(mode: int) -> CapturedRequired:
    """Return both arms while declaring the optional value arm required."""
    result, error = produce(mode=mode).catch()
    return {'value': result, 'error': error}


@graph
def select_with_optional_child(mode: int) -> SelectedChild:
    """Keep an optional child inside a required output namespace."""
    result = captured(mode=mode)
    return {'summary': forward_outputs(result, exclude=('error',))}


@graph
def nested_selection(mode: int) -> SelectedOptional:
    """Consume a subgraph whose output includes a filtered optional namespace."""
    result = select_optional(mode=mode)
    return {'summary': result.summary, 'error': result.error}


@graph
def select_subtree(mode: int) -> SelectedSubtree:
    """Exclude an entire subtree in an Ok-wrapped output mapping."""
    result = produce(mode=mode)
    return Ok({'summary': forward_outputs(result, exclude=('details',))})


@graph
def select_all(mode: int) -> SelectedAll:
    """Keep every field."""
    result = produce(mode=mode)
    return {'summary': forward_outputs(result, exclude=())}


@graph
def whole(mode: int) -> SelectedAll:
    """Forward the same namespace without using the intrinsic."""
    result = produce(mode=mode)
    return {'summary': result}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_forward_outputs_round_trip_and_provenance():
    """The selected endpoints match explicit wiring and return the original nodes."""
    assert select.build() is None
    template = compile_graph(select)
    restored = GraphIR.from_dict(json.loads(json.dumps(template.to_dict())))
    assert restored.outputs == compile_graph(explicit).outputs
    ports = restored.build_output_namespace()['summary']
    assert set(ports) == {'details', 'score'}
    assert ports['details']['value'].valid_type == (Int,)
    assert ports['details']['note'].valid_type == (Str, type(None))
    assert not ports['details']['note'].required
    assert ports['score'].valid_type == (Float,)

    outputs, node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(restored, {'mode': 2}))
    assert node.is_finished_ok
    (child,) = node.called
    assert set(outputs['summary']) == {'details', 'score'}
    for path, data in {
        'details__value': outputs['summary']['details']['value'],
        'details__note': outputs['summary']['details']['note'],
        'score': outputs['summary']['score'],
    }.items():
        assert (
            data.uuid
            == child.base.links.get_outgoing(link_type=LinkType.CREATE).get_node_by_label(f'value__{path}').uuid
        )
    assert not node.base.links.get_outgoing(link_type=LinkType.CREATE).all()


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('mode', [0, 1, 2])
@pytest.mark.parametrize('declaration', [select_optional, nested_selection, select_with_optional_child])
def test_forward_outputs_optional(mode, declaration):
    """Missing namespaces and leaves stay absent across the compiled template round trip."""
    restored = GraphIR.from_dict(json.loads(json.dumps(compile_graph(declaration).to_dict())))
    outputs, node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(restored, {'mode': mode}))
    assert node.is_finished_ok
    if declaration is not select_with_optional_child:
        parent, key = outputs, 'summary'
        port = restored.build_output_namespace()['summary']
    else:
        parent, key = outputs['summary'], 'value'
        port = restored.build_output_namespace()['summary']['value']
    assert not port.required
    assert port['score'].required
    if mode == 0:
        assert key not in parent
    else:
        assert parent[key]['details']['value'].value == 2
        assert ('note' in parent[key]['details']) is (mode == 2)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_forward_outputs_subtree_in_ok():
    """Ok wraps a graph return mapping without introducing another output namespace."""
    assert select_subtree.build() is None
    outputs, node = run_get_node(select_subtree, mode=2)
    assert node.is_finished_ok
    assert {name: output.value for name, output in outputs['summary'].items()} == {'score': 0.5, 'report': 'excluded'}


def test_forward_outputs_empty_exclusions():
    """An empty exclusion tuple lowers to the unfiltered wiring."""
    assert compile_graph(select_all).outputs == compile_graph(whole).outputs


EXCLUDED = ('report',)


@graph
def unknown() -> Selected:
    result = produce(mode=2)
    return {'summary': forward_outputs(result, exclude=('details.note',))}


@graph
def duplicate() -> Selected:
    result = produce(mode=2)
    return {'summary': forward_outputs(result, exclude=('report', 'report'))}


@graph
def nonliteral() -> Selected:
    result = produce(mode=2)
    return {'summary': forward_outputs(result, exclude=EXCLUDED)}


@graph
def literal_list() -> Selected:
    result = produce(mode=2)
    return {'summary': forward_outputs(result, exclude=['report'])}  # type: ignore[arg-type]


@graph
def nonstring() -> Selected:
    result = produce(mode=2)
    return {'summary': forward_outputs(result, exclude=(1,))}  # type: ignore[arg-type]


@graph
def none_left() -> Selected:
    result = produce(mode=2)
    return {'summary': forward_outputs(result, exclude=('details', 'score', 'report'))}


@graph
def scalar() -> Selected:
    result = produce(mode=2)
    return {'summary': forward_outputs(result.score, exclude=())}


@graph
def assigned() -> Selected:
    result = produce(mode=2)
    outputs = forward_outputs(result, exclude=('report',))
    return outputs


@pytest.mark.parametrize(
    'declaration, message',
    [
        (unknown, 'unknown immediate output field'),
        (duplicate, 'duplicate exclusion'),
        (nonliteral, 'tuple of literal field names'),
        (literal_list, 'tuple of literal field names'),
        (nonstring, 'tuple of literal field names'),
        (none_left, 'retain at least one field'),
        (scalar, 'reference to a static output namespace'),
        (assigned, 'final graph return mapping'),
    ],
)
def test_forward_outputs_rejects_invalid_selection(declaration, message):
    """Invalid selection syntax cannot become part of a built graph."""
    with pytest.raises(GraphLanguageError, match=message):
        declaration.build()


@pytest.mark.parametrize(
    'declaration, message',
    [
        (captured_short, '`value.report` is not declared'),
        (captured_required, 'mark `value` nullable'),
    ],
)
def test_forward_outputs_rejects_mismatched_optional_namespace(declaration, message):
    """Preserved optional namespaces check keys and requiredness against the annotation."""
    with pytest.raises(GraphLanguageError, match=message):
        declaration.build()
