###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Regression tests for large archive import/exports, e.g., to capture ``OperationalError``s."""

import pytest

from aiida import orm
from aiida.tools.archive import create_archive, import_archive


@pytest.mark.timeout(1000)  # Should finish in ~300s
@pytest.mark.nightly
def test_large_archive_export_operr_regression(pytestconfig, tmp_path, create_int_nodes, aiida_profile_clean):
    """Regression test: ensure OperationalError occurs (not) with too large (sufficiently small) filter_size."""

    num_nodes = 66_000  # Minimum value that OpErr is raised

    _ = create_int_nodes(num_nodes)

    # NOTE: Need to obtain a selection of `orm.Node`s, otherwise, with `entities=None`,
    # where the profile is exported in full the `_collect_all_entities` method that
    # doesn't apply any QB filters is called
    orm_nodes = orm.QueryBuilder().append(orm.Node).all(flat=True)

    # NOTE: Both, import and export should pass with both backends
    export_file = tmp_path / 'should_work.aiida'
    create_archive(entities=orm_nodes, filename=export_file)

    aiida_profile_clean.reset_storage()
    import_archive(path=export_file)
