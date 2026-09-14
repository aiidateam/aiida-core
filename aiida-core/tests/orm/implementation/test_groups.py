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
