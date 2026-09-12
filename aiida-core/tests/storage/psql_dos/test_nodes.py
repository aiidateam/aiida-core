###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for nodes, attributes and links."""

import pytest

from aiida import orm
from aiida.orm import Data, load_node


class TestNodeBasicSQLA:
    """These tests check the basic features of nodes(setting of attributes, copying of files, ...)."""

    @pytest.fixture(autouse=True)
    def init_profile(self, backend):
        """Initialize the profile."""
        self.backend = backend

    def test_load_nodes(self):
        """Test for load_node() function."""
        a_obj = Data()
        a_obj.store()

        assert a_obj.pk == load_node(identifier=a_obj.pk).pk
        assert a_obj.pk == load_node(identifier=a_obj.uuid).pk
        assert a_obj.pk == load_node(pk=a_obj.pk).pk
        assert a_obj.pk == load_node(uuid=a_obj.uuid).pk

        session = self.backend.get_session()

        try:
            session.begin_nested()
            with pytest.raises(ValueError):
                load_node(identifier=a_obj.pk, pk=a_obj.pk)
        finally:
            session.rollback()

        try:
            session.begin_nested()
            with pytest.raises(ValueError):
                load_node(pk=a_obj.pk, uuid=a_obj.uuid)
        finally:
            session.rollback()

        try:
            session.begin_nested()
            with pytest.raises(TypeError):
                load_node(pk=a_obj.uuid)
        finally:
            session.rollback()

        try:
            session.begin_nested()
            with pytest.raises(TypeError):
                load_node(uuid=a_obj.pk)
        finally:
            session.rollback()

        try:
            session.begin_nested()
            with pytest.raises(ValueError):
                load_node()
        finally:
            session.rollback()

    def test_multiple_node_creation(self):
        """This test checks that a node is not added automatically to the session
        (and subsequently committed) when a user is in the session.
        It tests the fix for the issue #234
        """
        from aiida.common.utils import get_new_uuid
        from aiida.storage.psql_dos.models.node import DbNode

        # Get the automatic user
        dbuser = self.backend.users.create('user@aiida.net').store().bare_model
        # Create a new node but don't add it to the session
        node_uuid = get_new_uuid()
        DbNode(user=dbuser, uuid=node_uuid, node_type=None)

        session = self.backend.get_session()

        # Query the session before commit
        res = session.query(DbNode.uuid).filter(DbNode.uuid == node_uuid).all()
        assert len(res) == 0, 'There should not be any nodes with this UUID in the session/DB.'

        # Commit the transaction
        session.commit()

        # Check again that the node is not in the DB
        res = session.query(DbNode.uuid).filter(DbNode.uuid == node_uuid).all()
        assert len(res) == 0, 'There should not be any nodes with this UUID in the session/DB.'

        # Get the automatic user
        dbuser = orm.User.collection.get_default().backend_entity.bare_model
        # Create a new node but now add it to the session
        node_uuid = get_new_uuid()
        node = DbNode(user=dbuser, uuid=node_uuid, node_type=None)
        session.add(node)

        # Query the session before commit
        res = session.query(DbNode.uuid).filter(DbNode.uuid == node_uuid).all()
        assert len(res) == 1, f'There should be a node in the session/DB with the UUID {node_uuid}'

        # Commit the transaction
        session.commit()

        # Check again that the node is in the db
        res = session.query(DbNode.uuid).filter(DbNode.uuid == node_uuid).all()
        assert len(res) == 1, f'There should be a node in the session/DB with the UUID {node_uuid}'


@pytest.mark.requires_psql
@pytest.mark.nightly
@pytest.mark.usefixtures('aiida_profile_clean')
def test_bulk_delete_nodes():
    """Regression test for the PostgreSQL 65535 parameter limit in delete_nodes_and_connections.

    Without the fix, DELETE statements using plain `.in_(pks)` generate one SQL parameter per PK,
    hitting PostgreSQL's wire-protocol limit of 65535 parameters for any num_nodes > 65535.
    """
    from aiida.manage import get_manager
    from aiida.tools.graph.deletions import delete_nodes
    from tests.utils.nodes import create_int_nodes

    num_nodes = 65_536  # Minimum number to exceed PostgreSQL's 65535 parameter limit

    node_pks = create_int_nodes(num_nodes)
    assert len(node_pks) == num_nodes

    storage_backend = get_manager().get_profile_storage()
    delete_nodes(pks=node_pks, dry_run=False, backend=storage_backend)
    assert orm.QueryBuilder().append(orm.Int).count() == 0
