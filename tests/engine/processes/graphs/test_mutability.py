###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Exercise writable task copies and graph output provenance end to end."""

import typing as t

import pytest

from aiida import orm
from aiida.common.exceptions import GraphTypeCheckError, ModificationNotAllowed
from aiida.common.links import LinkType
from aiida.engine import PortField, PortModel, graph, run_get_node, task

Writable = t.Annotated[orm.StructureData, PortField(mutable=True)]
UNIT_CELL = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
EXPANDED_CELL = [[5, 0, 0], [0, 5, 0], [0, 0, 5]]


@task
def expand(structure: Writable) -> orm.StructureData:
    structure.set_cell(EXPANDED_CELL)
    return structure


@task
def independent(first: Writable, second: Writable) -> orm.StructureData:
    first.set_cell(EXPANDED_CELL)
    assert first.uuid != second.uuid
    assert not first.is_stored and not second.is_stored
    assert second.get_cell_volume() == pytest.approx(1)
    return second


class MutatingInputs(PortModel):
    structure: Writable
    factor: t.Annotated[int, PortField(mutable=True)]


@task
def mutate_namespace(bundle: MutatingInputs) -> orm.StructureData:
    assert type(bundle.factor) is int
    bundle.structure.set_cell([[bundle.factor, 0, 0], [0, 1, 0], [0, 0, 1]])
    return bundle.structure


@graph
def forward_namespace(bundle: MutatingInputs) -> orm.StructureData:
    return mutate_namespace(bundle=bundle)


@task
def readonly_setter(structure: orm.StructureData) -> orm.StructureData:
    structure.set_cell(EXPANDED_CELL)
    return structure


@task
def readonly_return(structure: orm.StructureData) -> orm.StructureData:
    return structure


@task
def discard(structure: Writable) -> float:
    structure.set_cell(EXPANDED_CELL)
    return structure.get_cell_volume()


@task
def fail(structure: Writable) -> orm.StructureData:
    structure.set_cell(EXPANDED_CELL)
    raise RuntimeError('failed after editing copy')


@graph
def prepare(structure: Writable) -> orm.StructureData:
    return expand(structure=structure)


@graph
def readonly_prepare(structure: orm.StructureData) -> orm.StructureData:
    return expand(structure=structure)


@graph
def missing_outer_opt_in(structure: orm.StructureData) -> orm.StructureData:
    return prepare(structure=structure)


@graph
def missing_inner_opt_in(structure: Writable) -> orm.StructureData:
    return readonly_prepare(structure=structure)


class Report(PortModel):
    original: orm.StructureData
    expanded: orm.StructureData
    count: int


@graph
def report(structure: Writable) -> Report:
    expanded = prepare(structure=structure)
    count = 1
    return {'original': structure, 'expanded': expanded, 'count': count}


@graph
def one() -> int:
    return 1


@graph
def forward(value: orm.Int) -> orm.Int:
    return value


@graph
def condition_only(value: orm.Int) -> orm.Int:
    count = one()
    if count == 1:
        return value
    return value


@graph
def readonly_passthrough(structure: orm.StructureData) -> orm.StructureData:
    return structure


@graph
def cannot_upgrade_at_scope_exit(structure: Writable) -> orm.StructureData:
    reference = readonly_passthrough(structure=structure)
    return expand(structure=reference)


@graph
def selected_permission(readonly: orm.StructureData, writable: Writable, take_readonly: bool) -> orm.StructureData:
    selected = readonly if take_readonly else writable
    return expand(structure=selected)


@graph
def fresh_source(structure: Writable) -> orm.StructureData:
    expanded = expand(structure=structure)
    return expand(structure=expanded).alias('expand_again')


@pytest.mark.usefixtures('aiida_profile_clean')
def test_writable_ports_copy_independently() -> None:
    """Two ports link the same original, but only the returned copy is stored."""
    original = orm.StructureData(cell=UNIT_CELL)
    copy, node = run_get_node(independent, first=original, second=original)
    assert original.is_stored
    assert node.inputs.first.uuid == node.inputs.second.uuid == original.uuid
    assert copy.uuid != original.uuid
    assert copy.creator.uuid == node.uuid
    assert copy.get_cell_volume() == original.get_cell_volume() == pytest.approx(1)
    assert orm.QueryBuilder().append(orm.StructureData).count() == 2


@pytest.mark.usefixtures('aiida_profile_clean')
def test_namespace_leaf_contract_with_scalar() -> None:
    """A namespace carries permissions per leaf, while Python scalar arguments stay plain."""
    source = orm.StructureData(cell=UNIT_CELL)
    outputs, node = run_get_node(forward_namespace, bundle={'structure': source, 'factor': orm.Int(3)})
    assert node.is_finished_ok
    assert node.called[0].inputs.bundle.structure.uuid == source.uuid
    assert outputs['result'].get_cell_volume() == pytest.approx(3)
    assert source.get_cell_volume() == pytest.approx(1)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_readonly_task_enforces_stored_node_rules() -> None:
    """Read-only inputs are stored, and cannot be used as fresh outputs."""
    original = orm.StructureData(cell=UNIT_CELL)
    with pytest.raises(ModificationNotAllowed):
        readonly_setter.run_get_node(structure=original)
    with pytest.raises(ValueError, match=r'cycle|stored'):
        readonly_return.run_get_node(structure=original)
    assert original.is_stored and original.get_cell_volume() == pytest.approx(1)
    assert orm.QueryBuilder().append(orm.StructureData).count() == 1


@pytest.mark.usefixtures('aiida_profile_clean')
def test_discarded_and_failed_copies_stay_unstored() -> None:
    """A private copy does not persist unless the task publishes it."""
    original = orm.StructureData(cell=UNIT_CELL)
    result, node = run_get_node(discard, structure=original)
    assert node.inputs.structure.uuid == original.uuid
    assert result.value == pytest.approx(125)
    with pytest.raises(RuntimeError, match='failed after editing copy'):
        fail.run_get_node(structure=original)
    assert orm.QueryBuilder().append(orm.StructureData).count() == 1


@pytest.mark.parametrize('invalid', [missing_outer_opt_in, missing_inner_opt_in, cannot_upgrade_at_scope_exit])
def test_known_readonly_bindings_fail_at_build(invalid) -> None:
    """Each declared graph input can restrict a binding, including passthrough outputs."""
    with pytest.raises(GraphTypeCheckError, match='read-only binding to mutable input'):
        invalid.build()


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('take_readonly', [False, True])
def test_conditional_permission_checked_before_dispatch(take_readonly: bool) -> None:
    """A shared UUID does not let the selected read-only binding borrow write permission."""
    assert selected_permission.build() is None
    original = orm.StructureData(cell=UNIT_CELL)
    outputs, node = run_get_node(selected_permission, readonly=original, writable=original, take_readonly=take_readonly)
    if take_readonly:
        assert node.is_failed
        assert 'read-only binding to mutable input' in node.exit_message
        assert not node.called
    else:
        assert node.is_finished_ok
        assert outputs['result'].creator.inputs.structure.uuid == original.uuid


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_report_provenance(monkeypatch) -> None:
    """One executor records both graph invocations; only the task copies the input."""
    from aiida.engine.processes.graphs.process import GraphProcess

    init = GraphProcess.__init__
    executors = []

    def count_executor(self, *args, **kwargs):
        executors.append(self)
        init(self, *args, **kwargs)

    monkeypatch.setattr(GraphProcess, '__init__', count_executor)
    assert report.build() is None
    original = orm.StructureData(cell=UNIT_CELL)
    outputs, node = run_get_node(report, structure=original)
    assert node.is_finished_ok
    assert node.inputs.structure.uuid == outputs['original'].uuid == original.uuid
    assert len(executors) == 1
    (nested_link,) = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).all()
    nested = nested_link.node
    assert nested_link.link_label == 'prepare'
    assert node.called == [nested]
    assert isinstance(nested, orm.GraphNode) and nested.is_finished_ok and nested.is_sealed
    assert nested.inputs.structure.uuid == original.uuid
    assert nested.outputs.result.uuid == outputs['expanded'].uuid
    (child_link,) = nested.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()
    assert child_link.link_label == 'expand'
    child = child_link.node
    assert child.inputs.structure.uuid == original.uuid
    assert outputs['expanded'].creator.uuid == child.uuid
    assert outputs['expanded'].get_cell_volume() == pytest.approx(125)
    assert original.get_cell_volume() == pytest.approx(1)
    assert orm.QueryBuilder().append(orm.StructureData).count() == 2
    created = node.base.links.get_outgoing(link_type=LinkType.CREATE).nested()
    assert set(created) == {'count'}
    assert outputs['count'].value == 1
    assert created['count'].uuid == node.outputs.count.uuid == outputs['count'].uuid
    assert outputs['count'].creator.uuid == node.uuid


@pytest.mark.usefixtures('aiida_profile_clean')
def test_graph_creates_inline_output_but_reuses_stored_identity() -> None:
    """Literal output and stored equal value follow distinct provenance paths."""
    existing = orm.Int(1).store()
    outputs, node = run_get_node(one)
    assert outputs['result'].value == existing.value
    assert outputs['result'].uuid != existing.uuid
    assert node.outputs.result.uuid == outputs['result'].uuid
    assert outputs['result'].creator.uuid == node.uuid
    assert not node.called
    outputs, node = run_get_node(forward, value=existing)
    assert outputs['result'].uuid == existing.uuid and existing.creator is None
    assert not node.base.links.get_outgoing(link_type=LinkType.CREATE).all()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_create_links_still_restricted() -> None:
    """Other workflows cannot create data, and a graph cannot claim an existing node."""
    workchain = orm.WorkChainNode().store()
    with pytest.raises(ValueError, match='cannot add'):
        orm.Int(1).base.links.add_incoming(workchain, LinkType.CREATE, 'value')
    graph_node = orm.GraphNode().store()
    with pytest.raises(ValueError, match='already stored'):
        orm.Int(1).store().base.links.add_incoming(graph_node, LinkType.CREATE, 'value')
    created = orm.Int(1)
    created.base.links.add_incoming(graph_node, LinkType.CREATE, 'value')
    created.store()
    assert created.creator.uuid == graph_node.uuid
    assert list(graph_node.outputs) == []  # Graph output lookup follows RETURN, not CREATE.


@pytest.mark.usefixtures('aiida_profile_clean')
def test_condition_value_materializes_only_at_subgraph_boundary() -> None:
    """A returned inline value belongs to the subgraph; the comparison stays internal."""
    existing = orm.Int(5).store()
    outputs, node = run_get_node(condition_only, value=existing)
    assert node.is_finished_ok
    assert outputs['result'].uuid == existing.uuid
    (inner,) = node.called
    assert not inner.called
    assert inner.outputs.result.value == 1
    assert inner.outputs.result.creator.uuid == inner.uuid
    assert orm.QueryBuilder().append(orm.Int).count() == 2
    assert orm.QueryBuilder().append(orm.Bool).count() == 0


@pytest.mark.usefixtures('aiida_profile_clean')
def test_task_output_can_feed_writable_input() -> None:
    """A fresh task output starts a new binding without needing another graph opt-in."""
    outputs, node = run_get_node(fresh_source, structure=orm.StructureData(cell=UNIT_CELL))
    assert node.is_finished_ok
    first, second = node.called
    assert first.outputs.result.uuid == second.inputs.structure.uuid
    assert outputs['result'].uuid != first.outputs.result.uuid
    assert outputs['result'].creator.uuid == second.uuid
