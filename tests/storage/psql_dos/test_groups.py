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
@pytest.mark.usefixtures('aiida_profile_clean')
def test_group_bulk_operations():
    """Regression test for PostgreSQL parameter limit issue (6545) using pre-created archive."""
    archive_path = Path(__file__).parent / 'data' / '40k-int-nodes.aiida'
    import_archive(archive_path)

    qb = orm.QueryBuilder()
    qb.append(orm.Int)
    nodes = qb.all(flat=True)

    # Test the group operations that were failing
    group = orm.Group(label='bulk-test').store()
    group.add_nodes(nodes)  # This would fail before the fix
    assert group.count() == len(nodes)

    group.remove_nodes(nodes)
    assert group.count() == 0
