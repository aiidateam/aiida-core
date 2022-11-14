# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the BackendGroup and BackendGroupCollection classes."""
from aiida import orm


def test_creation_from_dbgroup(backend):
    """Test creation of a group from another group."""
    node = orm.Data().store()

    default_user = backend.users.create('test@aiida.net').store()
    group = backend.groups.create(label='testgroup_from_dbgroup', user=default_user).store()

    group.store()
    group.add_nodes([node.backend_entity])

    gcopy = group.__class__.from_dbmodel(group.bare_model, backend)

    assert group.pk == gcopy.pk
    assert group.uuid == gcopy.uuid


def test_add_nodes_skip_orm():
    """Test the `SqlaGroup.add_nodes` method with the `skip_orm=True` flag."""
    group = orm.Group(label='test_adding_nodes').store().backend_entity

    node_01 = orm.Data().store().backend_entity
    node_02 = orm.Data().store().backend_entity
    node_03 = orm.Data().store().backend_entity
    node_04 = orm.Data().store().backend_entity
    node_05 = orm.Data().store().backend_entity
    nodes = [node_01, node_02, node_03, node_04, node_05]

    group.add_nodes([node_01], skip_orm=True)
    group.add_nodes([node_02, node_03], skip_orm=True)
    group.add_nodes((node_04, node_05), skip_orm=True)

    assert set(_.pk for _ in nodes) == set(_.pk for _ in group.nodes)

    # Try to add a node that is already present: there should be no problem
    group.add_nodes([node_01], skip_orm=True)
    assert set(_.pk for _ in nodes) == set(_.pk for _ in group.nodes)


def test_add_nodes_skip_orm_batch():
    """Test the `SqlaGroup.add_nodes` method with the `skip_orm=True` flag and batches."""
    nodes = [orm.Data().store().backend_entity for _ in range(100)]

    # Add nodes to groups using different batch size. Check in the end the correct addition.
    batch_sizes = (1, 3, 10, 1000)
    for batch_size in batch_sizes:
        group = orm.Group(label=f'test_batches_{str(batch_size)}').store()
        group.backend_entity.add_nodes(nodes, skip_orm=True, batch_size=batch_size)
        assert set(_.pk for _ in nodes) == set(_.pk for _ in group.nodes)


def test_remove_nodes_bulk():
    """Test node removal with `skip_orm=True`."""
    group = orm.Group(label='test_removing_nodes').store().backend_entity

    node_01 = orm.Data().store().backend_entity
    node_02 = orm.Data().store().backend_entity
    node_03 = orm.Data().store().backend_entity
    node_04 = orm.Data().store().backend_entity
    nodes = [node_01, node_02, node_03]

    group.add_nodes(nodes)
    assert set(_.pk for _ in nodes) == set(_.pk for _ in group.nodes)

    # Remove a node that is not in the group: nothing should happen
    group.remove_nodes([node_04], skip_orm=True)
    assert set(_.pk for _ in nodes) == set(_.pk for _ in group.nodes)

    # Remove one Node
    nodes.remove(node_03)
    group.remove_nodes([node_03], skip_orm=True)
    assert set(_.pk for _ in nodes) == set(_.pk for _ in group.nodes)

    # Remove a list of Nodes and check
    nodes.remove(node_01)
    nodes.remove(node_02)
    group.remove_nodes([node_01, node_02], skip_orm=True)
    assert set(_.pk for _ in nodes) == set(_.pk for _ in group.nodes)
