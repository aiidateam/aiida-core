###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Regression tests for ``OperationalError``s on archive import/export"""

import pytest

from aiida import orm
from aiida.tools.archive import create_archive


@pytest.mark.timeout(1000)  # Should finish in ~200s
@pytest.mark.nightly
@pytest.mark.usefixtures('aiida_profile_clean')
def test_large_archive_export_operr_regression(pytestconfig, tmp_path, create_int_nodes):
    """Regression test: ensure OperationalError occurs (not) with too large (sufficiently small) filter_size."""

    num_nodes = 66_000  # Minimum value that OpErr is raised

    _ = create_int_nodes(num_nodes)

    # NOTE: Need to obtain a selection of `orm.Node`s, otherwise, with `entities=None`,
    # where the profile is exported in full the `_collect_all_entities` method that
    # doesn't apply any QB filters is called
    orm_nodes = orm.QueryBuilder().append(orm.Node).all(flat=True)

    # NOTE: This passes for both backends
    export_file = tmp_path / 'should_work.aiida'
    create_archive(entities=orm_nodes, filename=export_file, filter_size=1000)
