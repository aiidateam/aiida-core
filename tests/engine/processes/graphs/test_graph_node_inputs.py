###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Flattened workflow arguments on `GraphNode.inputs`.

The stored `INPUT_WORK` links keep the engine layout (`graph`, `graph_inputs`, optional `task_metadata`) so existing
nodes and checkpoints need no migration; `GraphNode.inputs` projects the `graph_inputs` namespace to the top level.
"""

import pytest

from aiida import orm
from aiida.common.exceptions import NotExistent
from aiida.common.links import LinkType
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.lowering import compile_graph, graph, task
from aiida.engine.processes.graphs.process import GraphProcess
from aiida.orm import Dict, Int
from aiida.orm.nodes.process.workflow.graph import GraphNode
from tests.engine.processes.graphs.programs import calls as call_programs
from tests.engine.processes.graphs.programs import parameters, ports
from tests.engine.processes.graphs.programs.tasks import add

pytestmark = pytest.mark.presto


@task
def echo(value: int) -> int:
    """Return the received value unchanged."""
    return value


@graph
def no_inputs() -> int:
    """Declare a graph taking no workflow arguments."""
    return add(x=1, y=2)


@graph
def shadow_graph(graph: int) -> int:
    """Declare a workflow argument colliding with the stored declaration link."""
    return echo(value=graph)


@graph
def shadow_graph_inputs(graph_inputs: int) -> int:
    """Declare a workflow argument colliding with the stored namespace link."""
    return echo(value=graph_inputs)


@graph
def shadow_task_metadata(task_metadata: int) -> int:
    """Declare a workflow argument colliding with the stored placement-metadata link."""
    return echo(value=task_metadata)


def _stored_labels(node: GraphNode) -> set[str]:
    """Return the raw stored incoming link labels, bypassing the flattened view."""
    return {triple.link_label for triple in node.base.links.get_incoming(link_type=LinkType.INPUT_WORK).all()}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_flat_inputs_expose_declared_arguments() -> None:
    """The manager projects workflow arguments flat, hiding engine bookkeeping links."""
    original = Int(2)
    outputs, node = run_get_node(call_programs.multiply_add, x=original, y=3, z=4)
    assert node.is_finished_ok
    assert isinstance(node, GraphNode)
    assert outputs['result'].value == 10
    assert node.inputs.x.uuid == original.uuid
    assert node.inputs['y'].value == 3
    assert node.inputs['z'].value == 4
    assert set(node.inputs) == {'x', 'y', 'z'}
    assert 'graph' not in node.inputs
    assert 'graph_inputs' not in node.inputs
    assert 'task_metadata' not in node.inputs
    assert getattr(node.inputs, 'graph', None) is None
    with pytest.raises(KeyError):
        node.inputs['graph']
    assert sorted(dir(node.inputs)) == sorted({*dir(type(node.inputs)), 'x', 'y', 'z'})


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_namespace_inputs_traverse() -> None:
    """Nested workflow namespaces traverse by attribute and item access alike."""
    _, node = run_get_node(ports.namespace_return, config={'settings': {'count': 5, 'nullable': 3}})
    assert node.is_finished_ok
    assert node.inputs.config.settings.count.value == 5
    assert node.inputs['config']['settings']['count'].value == 5
    assert node.inputs.config['settings'].count.value == 5
    assert 'config' in node.inputs
    assert 'settings' in node.inputs.config
    assert 'graph_inputs' not in node.inputs
    assert 'graph' not in node.inputs
    assert set(node.inputs) == {'config'}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_zero_inputs_expose_empty_manager() -> None:
    """A graph without parameters stores no argument links and exposes an empty view."""
    outputs, node = run_get_node(no_inputs)
    assert node.is_finished_ok
    assert outputs['result'].value == 3
    assert set(node.inputs) == set()
    assert list(node.inputs) == []
    assert 'x' not in node.inputs
    assert 'graph' not in node.inputs
    assert 'graph_inputs' not in node.inputs
    assert 'task_metadata' not in node.inputs
    assert _stored_labels(node) == {'graph'}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_missing_optional_inputs_stay_absent() -> None:
    """Unprovided optional arguments stay absent without leaking engine keys."""
    outputs, node = run_get_node(parameters.default_parameter)
    assert node.is_finished_ok
    assert outputs['result'].value == 3
    assert 'graph' not in node.inputs
    assert 'graph_inputs' not in node.inputs
    assert 'task_metadata' not in node.inputs
    assert set(node.inputs) == {
        label.removeprefix('graph_inputs__') for label in _stored_labels(node) if label.startswith('graph_inputs__')
    }


@pytest.mark.usefixtures('aiida_profile_clean')
def test_inputs_survive_orm_reload_and_seal() -> None:
    """Reloaded and sealed nodes expose the same flattened arguments."""
    original = Int(2)
    _, node = run_get_node(call_programs.multiply_add, x=original, y=3, z=4)
    assert node.is_finished_ok
    assert node.is_sealed
    reloaded = orm.load_node(node.pk)
    assert isinstance(reloaded, GraphNode)
    assert reloaded.inputs.x.uuid == original.uuid
    assert reloaded.inputs['y'].value == 3
    assert set(reloaded.inputs) == {'x', 'y', 'z'}
    assert 'graph' not in reloaded.inputs


@pytest.mark.usefixtures('aiida_profile_clean')
def test_shadowed_engine_names_resolve_to_user_inputs() -> None:
    """Workflow arguments named like engine keys shadow the bookkeeping links."""
    _, graph_node = run_get_node(shadow_graph, graph=7)
    assert graph_node.is_finished_ok
    assert graph_node.inputs.graph.value == 7
    assert graph_node.inputs['graph'].value == 7

    _, namespace_node = run_get_node(shadow_graph_inputs, graph_inputs=8)
    assert namespace_node.is_finished_ok
    assert namespace_node.inputs.graph_inputs.value == 8

    spec = compile_graph(shadow_task_metadata)
    outputs, metadata_node = run_get_node(
        GraphProcess, graph=Dict(dict=spec.to_dict()), graph_inputs={'task_metadata': 9}
    )
    assert metadata_node.is_finished_ok
    assert outputs['result'].value == 9
    assert metadata_node.inputs.task_metadata.value == 9
    for node in (graph_node, namespace_node, metadata_node):
        stored = _stored_labels(node)
        assert 'graph' in stored
        assert any(label.startswith('graph_inputs__') for label in stored)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_low_level_links_keep_engine_layout() -> None:
    """`base.links` still exposes the stored namespace layout for engine introspection."""
    original = Int(2)
    _, node = run_get_node(call_programs.multiply_add, x=original, y=3, z=4)
    assert node.is_finished_ok
    nested = node.base.links.get_incoming(link_type=LinkType.INPUT_WORK).nested()
    assert set(nested) == {'graph', 'graph_inputs'}
    assert isinstance(nested['graph'], Dict)
    assert nested['graph_inputs']['x'].uuid == original.uuid
    assert (
        node.base.links.get_incoming(link_type=LinkType.INPUT_WORK).get_node_by_label('graph_inputs__x').uuid
        == original.uuid
    )
    with pytest.raises(NotExistent):
        node.base.links.get_incoming(link_type=LinkType.INPUT_WORK).get_node_by_label('x')


@pytest.mark.usefixtures('aiida_profile_clean')
def test_outputs_unchanged_and_no_graph_accessor() -> None:
    """Standard outputs keep working and no public accessor leaks the compiled template."""
    from aiida.orm.utils.managers import NodeLinksManager

    outputs, node = run_get_node(call_programs.multiply_add, x=2, y=3, z=4)
    assert node.is_finished_ok
    assert set(outputs) == {'result'}
    assert outputs['result'].value == 10
    assert node.outputs.result.value == 10
    assert type(node.inputs) is NodeLinksManager
    assert not hasattr(node, 'graph')
    assert 'graph' not in dir(type(node))
    restart = node.get_builder_restart()
    assert restart.process_class is GraphProcess
    assert 'graph' in restart
    assert 'graph_inputs' in restart
    assert restart['graph_inputs']['x'].value == 2


@pytest.mark.usefixtures('aiida_profile_clean')
def test_child_calcjob_inputs_keep_plain_semantics(aiida_code_installed) -> None:
    """Per-placement metadata reaches the child without entering the flattened view."""
    from tests.engine.processes.graphs.programs import calcjobs

    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    outputs, node = run_get_node(
        calcjobs.add_single,
        x=2,
        y=3,
        code=code,
        task_metadata={'add_calc': {'options': {'custom_scheduler_commands': '# sentinel'}}},
    )
    assert node.is_finished_ok
    assert outputs['result'].value == 5
    assert set(node.inputs) == {'x', 'y', 'code'}
    assert 'task_metadata' not in node.inputs
    assert node.base.links.get_incoming(link_type=LinkType.INPUT_WORK).get_node_by_label('task_metadata') is not None
    (child,) = node.called
    assert set(child.inputs) == {'x', 'y', 'code'}
    assert child.get_option('custom_scheduler_commands') == '# sentinel'
