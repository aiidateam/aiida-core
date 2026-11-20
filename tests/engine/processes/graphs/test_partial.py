###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Execution and rejection contracts for general ``partial(...)`` input binding.

A ``partial`` binds some inputs of a task or graph without running anything; each
use merges the fixed values with its own arguments into one ordinary placement.
``par_map`` over a partial fans out with the single remaining input as its
element. Direct task and graph invocations below demonstrate the binding without
any map; the later cases show mapping as one consumer among others.
"""

import json
import typing as t

import pytest

from aiida.common.exceptions import GraphLanguageError, GraphTypeCheckError
from aiida.common.links import LinkType
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.ir import GraphIR
from aiida.engine.processes.graphs.lowering import GraphHandle, compile_graph
from aiida.engine.processes.graphs.process import GraphProcess
from aiida.engine.processes.graphs.validate import validate_graph
from aiida.orm import DataDict, DataList
from aiida.orm.nodes.data.int import Int
from aiida.orm.nodes.process.process import ProcessNode
from tests.engine.processes.graphs.programs import partials

pytestmark = pytest.mark.presto


def _launch(
    declaration: GraphHandle, inputs: dict[str, t.Any], serialized: bool
) -> tuple[dict[str, t.Any], ProcessNode]:
    """Run a graph declaration directly or from its serialized IR."""
    if serialized:
        spec = GraphIR.from_dict(json.loads(json.dumps(compile_graph(declaration).to_dict())))
        return run_get_node(GraphProcess, **GraphProcess._launch_inputs(spec, inputs))
    return run_get_node(declaration, **inputs)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_task_executes() -> None:
    """A task partial merges its fixed input with the call-time input."""
    outputs, node = run_get_node(partials.partial_task, x=3, y=4)
    assert node.is_finished_ok
    assert outputs['result'].value == 7


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_positional_executes() -> None:
    """A partial use takes the remaining input positionally or by keyword alike."""
    outputs, node = run_get_node(partials.partial_positional, x=3, y=4)
    assert node.is_finished_ok
    assert outputs['result'].value == 7


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_reused_shares_fixed_wire() -> None:
    """One binding serves two placements; both children read the same fixed node."""
    outputs, node = run_get_node(partials.partial_reused, x=1, y=10, z=2)
    assert node.is_finished_ok
    assert outputs['result'].value == 23
    children = {link.link_label: link.node for link in node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()}
    assert set(children) == {'add', 'second_add', 'total_add'}
    assert children['add'].inputs.y.uuid == children['second_add'].inputs.y.uuid


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_composed_executes() -> None:
    """A partial of a partial fixes one input at each level."""
    outputs, node = run_get_node(partials.partial_composed, x=1, y=2)
    assert node.is_finished_ok
    assert outputs['result'].value == 3


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_inline_executes() -> None:
    """An inline-constructed partial calls without binding a name."""
    outputs, node = run_get_node(partials.partial_inline, x=3, y=4)
    assert node.is_finished_ok
    assert outputs['result'].value == 7


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_graph_inlines() -> None:
    """A graph partial lowers exactly like the graph, inlining both steps."""
    outputs, node = run_get_node(partials.partial_graph, x=2, factor=10)
    assert node.is_finished_ok
    assert outputs['result'].value == 14
    assert node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).all() == []
    calls = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all_link_labels()
    assert set(calls) == {'scaled__add', 'scaled__scaled_add'}


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('flag,expected', [pytest.param(True, 7, id='taken'), pytest.param(False, 8, id='otherwise')])
def test_partial_branch_executes(flag: bool, expected: int) -> None:
    """One binding serves both branch arms, aliased where placements would collide."""
    outputs, node = run_get_node(partials.partial_branch, x=3, y=4, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_loop_executes() -> None:
    """A binding defined outside the loop serves every iteration."""
    outputs, node = run_get_node(partials.partial_loop, start=0, step=5, limit=3)
    assert node.is_finished_ok
    assert outputs['result'].value == 20


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_rebound_keeps_declaration_time_reference() -> None:
    """Fixed values capture the declaration-time wire, not the later rebinding."""
    outputs, node = run_get_node(partials.partial_rebound, start=1, step=100, limit=2)
    assert node.is_finished_ok
    # Fixed `y` stays the pre-loop seed (1); the call-time `x` follows the loop to 201.
    assert outputs['result'].value == 202


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_workchain_executes() -> None:
    """A `WorkChain` partial binds under the existing admissibility rules."""
    outputs, node = run_get_node(partials.partial_workchain, x=3, y=4)
    assert node.is_finished_ok
    assert outputs['result'].value == 7


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_calcjob_executes(aiida_code_installed) -> None:
    """A `CalcJob` partial wires the remaining inputs at the call."""
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    outputs, node = run_get_node(partials.partial_calcjob, x=2, y=3, code=code)
    assert node.is_finished_ok
    assert outputs['result'].value == 5


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_generic_fixed_executes() -> None:
    """A generic target solves its type variable from the fixed input."""
    outputs, node = run_get_node(partials.partial_generic_fixed, a=3, flag=True)
    assert node.is_finished_ok
    assert outputs['result'].value == 3


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_aliased_target_executes() -> None:
    """A partial over an aliased target keeps the target alias at every use."""
    outputs, node = run_get_node(partials.partial_aliased_target, x=3, y=4)
    assert node.is_finished_ok
    assert outputs['result'].value == 7
    calls = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all_link_labels()
    assert calls == ['aliased_add']


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_partial_map_list_executes(serialized: bool) -> None:
    """A task partial mapped over a list fixes its graph input for every element."""
    original = DataList([Int(1), Int(2), Int(3)])
    outputs, node = _launch(partials.partial_map_list, {'values': original, 'y': 10}, serialized)
    assert node.is_finished_ok
    assert [member.value for member in outputs['result']] == [11, 12, 13]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_map_mapping_executes() -> None:
    """A task partial mapped over a mapping keeps keys and insertion order."""
    original = DataDict({'zeta': Int(1), 'alpha': Int(2), 'mid': Int(3)})
    outputs, node = run_get_node(partials.partial_map_mapping, values=original, y=10)
    assert node.is_finished_ok
    result = outputs['result']
    assert isinstance(result, DataDict)
    assert list(result) == ['zeta', 'alpha', 'mid']
    assert {key: member.value for key, member in result.items()} == {'zeta': 11, 'alpha': 12, 'mid': 13}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_map_upstream_fixed_waits() -> None:
    """A fixed upstream task output reaches every element; the map waits for it."""
    outputs, node = run_get_node(partials.partial_map_upstream, a=1, b=2, c=3, y=10)
    assert node.is_finished_ok
    assert [member.value for member in outputs['result']] == [12, 13, 14]


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_partial_map_graph_executes(serialized: bool) -> None:
    """A multi-step graph partial maps with one `GraphProcess` and per-element scopes."""
    original = DataList([Int(1), Int(2)])
    outputs, node = _launch(partials.partial_map_graph, {'values': original, 'factor': 10}, serialized)
    assert node.is_finished_ok
    assert [member.value for member in outputs['result']] == [12, 14]
    assert node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).all() == []
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []
    calls = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all_link_labels()
    assert set(calls) == {
        'map_scaled_0__add',
        'map_scaled_0__scaled_add',
        'map_scaled_1__add',
        'map_scaled_1__scaled_add',
        'map_scaled_collect',
    }
    collector = node.base.links.get_outgoing(link_label_filter='map_scaled_collect').one().node
    assert collector.outputs.result.uuid == outputs['result'].uuid


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_map_empty_executes() -> None:
    """A partial mapped over an empty list stores an empty container without items."""
    outputs, node = run_get_node(partials.partial_map_empty, y=10)
    assert node.is_finished_ok
    result = outputs['result']
    assert isinstance(result, DataList)
    assert len(result) == 0


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_map_chained_executes() -> None:
    """A downstream task consumes the mapped container of a partial."""
    original = DataList([Int(1), Int(2), Int(3)])
    outputs, node = run_get_node(partials.partial_map_chained, values=original, y=10)
    assert node.is_finished_ok
    assert outputs['result'].value == 36


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_map_after_executes() -> None:
    """A partial map orders after an earlier placement like ordinary calls."""
    original = DataList([Int(1), Int(2)])
    outputs, node = run_get_node(partials.partial_map_after, x=0, values=original, y=5)
    assert node.is_finished_ok
    assert [member.value for member in outputs['result']] == [6, 7]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_map_inline_executes() -> None:
    """An inline-constructed partial maps without binding a name."""
    original = DataList([Int(1), Int(2)])
    outputs, node = run_get_node(partials.partial_map_inline, values=original, y=5)
    assert node.is_finished_ok
    assert [member.value for member in outputs['result']] == [6, 7]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_namespace_merge_executes() -> None:
    """Disjoint namespaced leaves fixed and called under one top-level input combine."""
    outputs, node = run_get_node(partials.partial_namespace_merge, first=3, second=4)
    assert node.is_finished_ok
    assert outputs['result'].value == 7


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_map_collection_element_executes() -> None:
    """A mapped element input literally named `collection` does not false-reject."""
    original = DataList([Int(1), Int(2)])
    outputs, node = run_get_node(partials.partial_map_collection_element, values=original, other=10)
    assert node.is_finished_ok
    assert [member.value for member in outputs['result']] == [11, 12]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_inline_alias_executes() -> None:
    """An inline partial with a use-site alias places under that alias."""
    outputs, node = run_get_node(partials.partial_inline_alias, x=3, y=4)
    assert node.is_finished_ok
    assert outputs['result'].value == 7
    assert node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all_link_labels() == ['inline_add']


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_map_inline_alias_executes() -> None:
    """An inline partial alias maps under that alias."""
    original = DataList([Int(1), Int(2)])
    outputs, node = run_get_node(partials.partial_map_inline_alias, values=original, y=5)
    assert node.is_finished_ok
    assert [member.value for member in outputs['result']] == [6, 7]
    labels = set(node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all_link_labels())
    assert labels == {'map_inline_add_0', 'map_inline_add_1', 'map_inline_add_collect'}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_nested_alias_executes() -> None:
    """A partial composed over an aliased inline partial keeps the inner alias."""
    outputs, node = run_get_node(partials.partial_nested_alias, x=1, y=2)
    assert node.is_finished_ok
    assert outputs['result'].value == 3
    assert node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all_link_labels() == ['inner_add']


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_generic_combined_same_executes() -> None:
    """Matching fixed and call-time evidence solves the shared type variable."""
    template = compile_graph(partials.partial_generic_combined_same)
    narrowed = next(task for task in template.tasks if task.name == 'pick_either')
    assert narrowed.spec.declared_outputs.select('result').types == (Int,)  # type: ignore[union-attr]
    outputs, node = run_get_node(partials.partial_generic_combined_same, a=3, b=4)
    assert node.is_finished_ok
    assert outputs['result'].value == 4


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_generic_combined_mixed_executes() -> None:
    """Conflicting fixed and call-time evidence stays unsolved but still runs."""
    template = compile_graph(partials.partial_generic_combined_mixed)
    narrowed = next(task for task in template.tasks if task.name == 'pick_either')
    assert narrowed.spec is not None and narrowed.spec.declared_outputs.fields == ()  # type: ignore[union-attr]
    outputs, node = run_get_node(partials.partial_generic_combined_mixed, a=3, b=4.5)
    assert node.is_finished_ok
    assert outputs['result'].value == 3


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_map_generic_fixed_executes() -> None:
    """A generic partial map solved from its fixed input feeds a typed consumer."""
    template = compile_graph(partials.partial_map_generic_fixed)
    mapped = next(task for task in template.tasks if task.kind == 'map')
    assert mapped.spec is not None and mapped.spec.declared_outputs.select('result').types == (Int,)  # type: ignore[union-attr]
    original = DataList([Int(1), Int(2)])
    outputs, node = run_get_node(partials.partial_map_generic_fixed, values=original, delta=10)
    assert node.is_finished_ok
    assert outputs['result'].value == 23


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('flag,expected', [pytest.param(True, 4, id='taken'), pytest.param(False, 5, id='otherwise')])
def test_partial_branch_upstream_executes(flag: bool, expected: int) -> None:
    """A task-output fixed value captured outside the branch reaches both arms."""
    outputs, node = run_get_node(partials.partial_branch_upstream, a=1, b=2, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_loop_upstream_executes() -> None:
    """A task-output fixed value captured outside the loop reaches every iteration."""
    outputs, node = run_get_node(partials.partial_loop_upstream, start=0, step=5, limit=3)
    # Shared `start + step` (5) stays fixed while `value` runs 0 -> 5 -> 10 -> 15.
    assert node.is_finished_ok
    assert outputs['result'].value == 15


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_after_direct_executes() -> None:
    """A direct partial use orders after an earlier placement."""
    outputs, node = run_get_node(partials.partial_after_direct, x=1, y=2, z=10)
    assert node.is_finished_ok
    assert outputs['result'].value == 13


@pytest.mark.usefixtures('aiida_profile_clean')
def test_partial_map_workchain_executes() -> None:
    """A `WorkChain` partial maps over a list, fixing a graph input."""
    original = DataList([Int(1), Int(2)])
    outputs, node = run_get_node(partials.partial_map_workchain, values=original, y=10)
    assert node.is_finished_ok
    assert [member.value for member in outputs['result']] == [11, 12]


def test_partial_map_serialized_invalid_element() -> None:
    """A serialized map naming an unknown element fails type checking, not an assertion."""
    data = compile_graph(partials.partial_map_list).to_dict()
    for entry in data['tasks']:
        if entry.get('kind') == 'map':
            entry['element'] = 'nope'
    with pytest.raises(GraphTypeCheckError):
        validate_graph(GraphIR.from_dict(data))


@pytest.mark.parametrize(
    'declaration',
    [
        pytest.param(partials.partial_duplicate_fixed, id='duplicate-fixed'),
        pytest.param(partials.partial_unknown_input, id='unknown-input'),
        pytest.param(partials.partial_missing_required, id='missing-required'),
        pytest.param(partials.partial_no_fixed, id='no-fixed'),
        pytest.param(partials.partial_positional_fixed, id='positional-fixed'),
        pytest.param(partials.partial_illegal_target, id='illegal-target'),
        pytest.param(partials.partial_after_binding, id='after-binding'),
        pytest.param(partials.partial_call_fixed_again, id='call-fixed-again'),
        pytest.param(partials.partial_namespace_conflict, id='namespace-conflict'),
        pytest.param(partials.partial_map_two_remaining, id='two-remaining'),
        pytest.param(partials.partial_map_no_output, id='no-output'),
        pytest.param(partials.partial_map_unknown_fixed, id='unknown-fixed'),
        pytest.param(partials.partial_map_calcjob, id='calcjob-map'),
    ],
)
def test_partial_rejections(declaration: GraphHandle) -> None:
    """Invalid bindings and uses fail at build time with a diagnostic."""
    with pytest.raises(GraphLanguageError):
        declaration.build()
