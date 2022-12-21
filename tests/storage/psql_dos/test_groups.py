# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.storage.psql_dos.orm.groups` module."""
from sqlalchemy import inspect

from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.models.group import DbGroup
from aiida.storage.psql_dos.orm.groups import SqlaGroup
from aiida.storage.psql_dos.orm.nodes import SqlaNode


def test_add_nodes_disable_expire_on_commit(backend):
    """Test that ``SqlaGroup.add_nodes`` will not expire the database model instances."""
    session = backend.get_session()
    assert session.expire_on_commit is True

    user = backend.users.create(get_new_uuid()).store()
    node = SqlaNode(backend, None, user).store()
    group = SqlaGroup(backend, get_new_uuid(), user).store()

    assert not inspect(user.bare_model).expired
    assert not inspect(node.bare_model).expired
    assert not inspect(group.bare_model).expired

    session.commit()
    assert inspect(user.bare_model).expired
    assert inspect(node.bare_model).expired
    assert inspect(group.bare_model).expired

    session.refresh(node.bare_model)
    assert not inspect(node.bare_model).expired

    # Now add the node to the group and check that this does commit but does not expire the node
    group.add_nodes([node])

    assert not inspect(node.bare_model).expired
    assert not inspect(group.bare_model).expired

    # Load the group and verify the changes of ``add_nodes`` have been commited
    group_loaded = session.query(DbGroup).filter(DbGroup.id == group.id).one()
    nodes = list(group_loaded.dbnodes)
    assert len(nodes) == 1
    assert nodes[0].id == node.id
