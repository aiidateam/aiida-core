###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Explicit placement alias contracts: `task.alias('scf')(...)`.

Placement names are independent of reusable declarations and survive control
scopes, process dispatch, and scheduler checkpoints.
"""

import json

import pytest

from aiida.common.exceptions import GraphLanguageError
from aiida.common.links import LinkType
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.ir import BranchControl, GraphIR, LoopControl, SubgraphTask
from aiida.engine.processes.graphs.lowering import GraphHandle, compile_graph
from aiida.engine.processes.graphs.run import GraphRun
from aiida.orm import DataList
from aiida.orm.nodes.data.int import Int
from tests.engine.processes.graphs.programs import aliases, calls, tasks

pytestmark = pytest.mark.presto


def test_aliased_function_builds_named_placement() -> None:
    """An aliased function call compiles to exactly the given placement name."""
    spec = compile_graph(aliases.aliased_function)
    assert spec.task_names == ('scf',)
    assert GraphIR.from_dict(json.loads(json.dumps(spec.to_dict()))).to_dict() == spec.to_dict()


def test_aliased_two_functions_build_distinct_placements() -> None:
    """Two aliases of one function compile to two stable placements."""
    spec = compile_graph(aliases.aliased_two_functions)
    assert spec.task_names == ('scf', 'nscf')


def test_aliased_calcjob_builds_named_placement() -> None:
    """An aliased `CalcJob` call compiles under the alias, not the task name."""
    spec = compile_graph(aliases.aliased_calcjob)
    assert spec.task_names == ('scf',)
    assert GraphIR.from_dict(json.loads(json.dumps(spec.to_dict()))).to_dict() == spec.to_dict()


def test_aliased_workchain_builds_named_placement() -> None:
    """An aliased `WorkChain` call compiles under the alias."""
    spec = compile_graph(aliases.aliased_workchain)
    assert spec.task_names == ('scf',)


def test_aliased_graph_builds_named_subgraph() -> None:
    """An aliased nested graph compiles to one subgraph placement under the alias."""
    spec = compile_graph(aliases.aliased_graph)
    assert spec.task_names == ('stage',)
    [placed] = spec.tasks
    assert isinstance(placed, SubgraphTask)
    assert placed.body.identifier == f'{calls.__name__}:multiply_add'


def test_aliased_nested_descends_through_scopes() -> None:
    """An aliased nested graph keeps its inner alias in the subgraph body."""
    spec = compile_graph(aliases.aliased_nested)
    assert spec.task_names == ('scf',)
    [placed] = spec.tasks
    assert isinstance(placed, SubgraphTask)
    assert placed.body.task_names == ('pw',)


def test_aliased_branch_arms_build() -> None:
    """Branch arms holding the same alias lower with the alias in each body."""
    spec = compile_graph(aliases.aliased_branch)
    [control] = [task for task in spec.tasks if isinstance(task, BranchControl)]
    assert control.body.task_names == ('scf',)
    assert control.otherwise.task_names == ('scf',)
    assert GraphIR.from_dict(json.loads(json.dumps(spec.to_dict()))).to_dict() == spec.to_dict()


def test_aliased_loop_body_builds() -> None:
    """A loop body reusing one alias lowers with that alias in the body."""
    spec = compile_graph(aliases.aliased_loop)
    [control] = [task for task in spec.tasks if isinstance(task, LoopControl)]
    assert 'scf' in control.body.task_names
    assert GraphIR.from_dict(json.loads(json.dumps(spec.to_dict()))).to_dict() == spec.to_dict()


def test_aliased_after_orders_without_value() -> None:
    """An `after` edge between aliases orders placements without wiring a value."""
    spec = compile_graph(aliases.aliased_ordered)
    assert spec.task_names == ('prepare', 'scf')
    assert [(edge.source, edge.target) for edge in spec.dependencies] == [('prepare', 'scf')]


def test_aliased_generic_builds() -> None:
    """A generic task alias compiles; constraints still solve at the alias."""
    spec = compile_graph(aliases.aliased_generic)
    assert spec.task_names == ('scf',)


def test_aliased_dotted_and_module_build() -> None:
    """Dotted and module call targets accept the placement constructor."""
    assert compile_graph(aliases.aliased_dotted).task_names == ('scf',)
    assert compile_graph(aliases.aliased_module).task_names == ('scf',)


def test_aliased_map_builds() -> None:
    """A `par_map` over an aliased callable compiles to one map placement."""
    spec = compile_graph(aliases.aliased_map)
    assert spec.task_names == ('step',)
    assert GraphIR.from_dict(json.loads(json.dumps(spec.to_dict()))).to_dict() == spec.to_dict()


@pytest.mark.parametrize(
    'declaration',
    [
        pytest.param(aliases.alias_empty, id='empty'),
        pytest.param(aliases.alias_invalid, id='invalid'),
        pytest.param(aliases.alias_nonliteral, id='nonliteral'),
    ],
)
def test_aliased_validation_rejects_bad_names(declaration: GraphHandle) -> None:
    """Empty, invalid, and non-literal alias names fail at build time."""
    with pytest.raises(GraphLanguageError, match='alias'):
        declaration.build()


def test_alias_does_not_mutate_task_handle() -> None:
    """Calling `.alias(...)` leaves the original handle reusable under its own name."""
    aliased = tasks.add.alias('scf')
    assert aliased is not tasks.add
    assert compile_graph(aliases.aliased_function).task_names == ('scf',)
    assert compile_graph(calls.chain).task_names == ('add', 'add_2')


@pytest.mark.usefixtures('aiida_profile_clean')
def test_aliased_function_executes() -> None:
    """An aliased function placement runs and returns the scientific result."""
    outputs, node = run_get_node(aliases.aliased_two_functions, x=2, y=3)
    assert node.is_finished_ok
    assert outputs['result'].value == 8
    assert {link.link_label for link in node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()} == {
        'scf',
        'nscf',
    }


@pytest.mark.usefixtures('aiida_profile_clean')
def test_aliased_calcjob_executes(aiida_code_installed) -> None:
    """An aliased `CalcJob` placement runs with metadata keyed by the alias."""
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    outputs, node = run_get_node(
        aliases.aliased_two_calcjobs,
        x=2,
        y=3,
        code=code,
        task_metadata={'scf': {'options': {}}, 'nscf': {'options': {}}},
    )
    assert node.is_finished_ok
    assert outputs['result'].value == 8
    assert {link.link_label for link in node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()} == {
        'scf',
        'nscf',
    }


@pytest.mark.usefixtures('aiida_profile_clean')
def test_aliased_workchain_executes() -> None:
    """An aliased `WorkChain` placement runs under its alias label."""
    outputs, node = run_get_node(aliases.aliased_two_workchains, x=Int(2), y=Int(3))
    assert node.is_finished_ok
    assert outputs['result'].value == 8
    assert {link.link_label for link in node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).all()} == {
        'scf',
        'nscf',
    }


@pytest.mark.usefixtures('aiida_profile_clean')
def test_aliased_graph_executes() -> None:
    """An aliased nested graph runs and keeps the inner placements scoped beneath it."""
    outputs, node = run_get_node(aliases.aliased_nested, x=2, y=3)
    assert node.is_finished_ok
    assert outputs['result'].value == 5
    labels = {link.link_label for link in node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()}
    assert labels == {'scf__pw'}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_aliased_branch_executes() -> None:
    """The taken branch arm dispatches its alias; the scientific result matches the plain form."""
    for flag, expected in ((True, 3), (False, 4)):
        outputs, node = run_get_node(aliases.aliased_branch, value=2, flag=flag)
        assert node.is_finished_ok
        assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
def test_aliased_loop_executes() -> None:
    """Loop iterations reuse one alias entry and accumulate the scientific result."""
    outputs, node = run_get_node(aliases.aliased_loop, value=2, count=3)
    assert node.is_finished_ok
    assert outputs['result'].value == 5


@pytest.mark.usefixtures('aiida_profile_clean')
def test_aliased_generic_executes() -> None:
    """A generic alias solves its type variable and returns the scientific result."""
    outputs, node = run_get_node(aliases.aliased_generic, x=2, y=3)
    assert node.is_finished_ok
    assert outputs['result'].value == 5


@pytest.mark.usefixtures('aiida_profile_clean')
def test_aliased_dotted_and_module_execute() -> None:
    """Dotted and module alias targets run the same scientific result."""
    for declaration in (aliases.aliased_dotted, aliases.aliased_module):
        outputs, node = run_get_node(declaration, x=2, y=3)
        assert node.is_finished_ok
        assert outputs['result'].value == 5


@pytest.mark.usefixtures('aiida_profile_clean')
def test_aliased_map_executes() -> None:
    """A `par_map` over an aliased callable maps every element in order."""
    original = DataList([Int(3), Int(1)])
    outputs, node = run_get_node(aliases.aliased_map, values=original)
    assert node.is_finished_ok
    assert [member.value for member in outputs['result']] == [2, 0]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_aliased_checkpoint_restores_scope_names() -> None:
    """Checkpointing between alias dispatches resumes without redispatching."""
    state = GraphRun(compile_graph(aliases.aliased_two_functions), given={'x': Int(2), 'y': Int(3)})
    assert [start.instance for start in state.step().starts] == ['scf']
    _, first_node = run_get_node(tasks.add, x=2, y=3)
    state.started('scf', first_node.pk)
    restored = GraphRun.from_dict(state.graph, state.given, state.to_dict())
    assert restored.step().starts == []
    restored.completed('scf', first_node.pk)
    assert [start.instance for start in restored.step().starts] == ['nscf']
