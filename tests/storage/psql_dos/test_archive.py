###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for generic queries and unit tests for QueryBuilder parameter limit fixes."""

from pathlib import Path

import pytest

from aiida import orm
from aiida.tools.archive import create_archive, import_archive


@pytest.mark.requires_psql
@pytest.mark.usefixtures('aiida_profile_clean')
def test_large_archive_export(tmp_path):
    """Test that large datasets can be exported without parameter limit errors."""
    # Import the 100k node archive
    num_nodes = 100_000
    archive_path = Path(__file__).parent / 'data' / f'{int(num_nodes/1000)}k-int-nodes-2.7.1.post0.aiida'
    import_archive(archive_path)

    # Verify we have the expected number of nodes
    qb = orm.QueryBuilder()
    qb.append(orm.Node)
    all_nodes = qb.all(flat=True)
    assert len(all_nodes) == num_nodes

    # Test archive creation with the large dataset - this should not raise parameter limit errors
    export_file = tmp_path / 'large_export.aiida'
    create_archive(all_nodes, filename=export_file, test_run=True)

    # Test passed if no OperationalError was raised
