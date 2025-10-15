###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Regression test for bulk group operations with PSQL backend."""

import pytest

from aiida import orm


@pytest.mark.requires_psql
@pytest.mark.nightly  # takes ~1 min
@pytest.mark.usefixtures('aiida_profile_clean')
def test_group_bulk_operations():
    """Regression test for the PostgreSQL parameter limit OperationalError on add_nodes."""
    from tests.utils.nodes import create_int_nodes

    num_nodes = 34_000  # Minimum number to reach exception without the fix

    # Create nodes using the efficient bulk_insert method
    node_pks = create_int_nodes(num_nodes)
    assert len(node_pks) == num_nodes

    # Get the actual node objects for group operations
    nodes = orm.QueryBuilder().append(orm.Int).all(flat=True)
    assert len(nodes) == num_nodes

    # Test the group operations that were failing
    group = orm.Group(label='bulk-test').store()
    group.add_nodes(nodes)  # This would fail before the fix
    assert group.count() == num_nodes

    group.remove_nodes(nodes)
    assert group.count() == 0
