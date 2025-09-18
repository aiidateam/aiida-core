###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Regression test for bulk group operations with PSQL backend."""

from pathlib import Path

import pytest

from aiida import orm
from aiida.tools.archive import import_archive


@pytest.mark.requires_psql
@pytest.mark.nightly
@pytest.mark.usefixtures('aiida_profile_clean')
def test_group_bulk_operations():
    """
    Regression test for the PostgreSQL parameter limit OperationalError on add_nodes using a pre-created archive.
    """
    num_nodes = 50_000
    archive_path = Path(__file__).parents[2] / 'data' / f'{int(num_nodes/1000)}k-int-nodes-2.7.1.post0.aiida'
    import_archive(archive_path)

    qb = orm.QueryBuilder()
    qb.append(orm.Int)
    nodes = qb.all(flat=True)
    assert len(nodes) == num_nodes

    # Test the group operations that were failing
    group = orm.Group(label='bulk-test').store()
    group.add_nodes(nodes)  # This would fail before the fix
    assert group.count() == num_nodes

    group.remove_nodes(nodes)
    assert group.count() == 0
