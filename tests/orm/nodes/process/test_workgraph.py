"""Tests for :mod:`aiida.orm.nodes.process.workflow.workgraph`."""

import pytest

from aiida.orm import WorkChainNode, WorkGraphNode


def test_is_workchain_node_subclass():
    """A work graph is executed as a work chain, so its node specialises `WorkChainNode`."""
    assert issubclass(WorkGraphNode, WorkChainNode)


def test_node_type_is_stable():
    """The entry point keeps the `node_type` that existing work graph nodes were stored with.

    The class moved from aiida-workgraph into core under the same `aiida.node` entry point name, so nodes written
    by the standalone package stay loadable. This pins that string against an accidental rename.
    """
    assert WorkGraphNode().node_type == 'process.workflow.workgraph.WorkGraphNode.'


@pytest.mark.parametrize(
    'setter, getter, value',
    [
        ('set_task_state', 'get_task_state', 'RUNNING'),
        ('set_task_process', 'get_task_process', 12345),
        ('set_task_action', 'get_task_action', 'pause'),
        ('set_task_execution_count', 'get_task_execution_count', 3),
        ('set_task_map_info', 'get_task_map_info', 'parent'),
    ],
    ids=['state', 'process', 'action', 'execution_count', 'map_info'],
)
def test_task_accessor_roundtrip(setter, getter, value):
    """Each per-task accessor stores a value under a task name and reads the same value back."""
    node = WorkGraphNode()
    getattr(node, setter)('task_a', value)
    assert getattr(node, getter)('task_a') == value


def test_per_task_accessor_writes_the_bulk_attribute():
    """The per-task setter and the bulk dict property are two views of the same stored attribute."""
    node = WorkGraphNode()
    node.set_task_state('task_a', 'RUNNING')
    node.set_task_state('task_b', 'FINISHED')
    assert node.task_states == {'task_a': 'RUNNING', 'task_b': 'FINISHED'}
