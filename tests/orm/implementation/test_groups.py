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
import pytest

from aiida import orm


@pytest.mark.usefixtures('clear_database_before_test')
def test_query(backend):
    """Test if queries are working."""
    from aiida.common.exceptions import NotExistent, MultipleObjectsError

    default_user = backend.users.create('simple@ton.com')

    g_1 = backend.groups.create(label='testquery1', user=default_user).store()
    g_2 = backend.groups.create(label='testquery2', user=default_user).store()

    n_1 = orm.Data().store().backend_entity
    n_2 = orm.Data().store().backend_entity
    n_3 = orm.Data().store().backend_entity
    n_4 = orm.Data().store().backend_entity

    g_1.add_nodes([n_1, n_2])
    g_2.add_nodes([n_1, n_3])

    newuser = backend.users.create(email='test@email.xx')
    g_3 = backend.groups.create(label='testquery3', user=newuser).store()

    # I should find it
    g_1copy = backend.groups.get(uuid=g_1.uuid)
    assert g_1.pk == g_1copy.pk

    # Try queries
    res = backend.groups.query(nodes=n_4)
    assert [_.pk for _ in res] == []

    res = backend.groups.query(nodes=n_1)
    assert [_.pk for _ in res] == [_.pk for _ in [g_1, g_2]]

    res = backend.groups.query(nodes=n_2)
    assert [_.pk for _ in res] == [_.pk for _ in [g_1]]

    # I try to use 'get' with zero or multiple results
    with pytest.raises(NotExistent):
        backend.groups.get(nodes=n_4)
    with pytest.raises(MultipleObjectsError):
        backend.groups.get(nodes=n_1)

    assert backend.groups.get(nodes=n_2).pk == g_1.pk

    # Query by user
    res = backend.groups.query(user=newuser)
    assert set(_.pk for _ in res) == set(_.pk for _ in [g_3])

    # Same query, but using a string (the username=email) instead of a DbUser object
    res = backend.groups.query(user=newuser)
    assert set(_.pk for _ in res) == set(_.pk for _ in [g_3])

    res = backend.groups.query(user=default_user)

    assert set(_.pk for _ in res) == set(_.pk for _ in [g_1, g_2])


@pytest.mark.usefixtures('clear_database_before_test')
def test_creation_from_dbgroup(backend):
    """Test creation of a group from another group."""
    node = orm.Data().store()

    default_user = backend.users.create('test@aiida.net').store()
    group = backend.groups.create(label='testgroup_from_dbgroup', user=default_user).store()

    group.store()
    group.add_nodes([node.backend_entity])

    dbgroup = group.dbmodel
    gcopy = backend.groups.from_dbmodel(dbgroup)

    assert group.pk == gcopy.pk
    assert group.uuid == gcopy.uuid


@pytest.mark.usefixtures('clear_database_before_test', 'skip_if_not_sqlalchemy')
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


@pytest.mark.usefixtures('clear_database_before_test', 'skip_if_not_sqlalchemy')
def test_add_nodes_skip_orm_batch():
    """Test the `SqlaGroup.add_nodes` method with the `skip_orm=True` flag and batches."""
    nodes = [orm.Data().store().backend_entity for _ in range(100)]

    # Add nodes to groups using different batch size. Check in the end the correct addition.
    batch_sizes = (1, 3, 10, 1000)
    for batch_size in batch_sizes:
        group = orm.Group(label=f'test_batches_{str(batch_size)}').store()
        group.backend_entity.add_nodes(nodes, skip_orm=True, batch_size=batch_size)
        assert set(_.pk for _ in nodes) == set(_.pk for _ in group.nodes)


@pytest.mark.usefixtures('clear_database_before_test', 'skip_if_not_sqlalchemy')
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
