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

    from sqlalchemy.exc import OperationalError

    from aiida.manage import get_manager

    num_nodes = 66_000  # Minimum value that OpErr is raised

    _ = create_int_nodes(num_nodes)

    # NOTE: Need to obtain a selection of `orm.Node`s, otherwise, with `entities=None`, where the profile is exported in
    # full, no QB filters are applied, as the `_collect_all_entities` method is called
    orm_nodes = orm.QueryBuilder().append(orm.Node).all(flat=True)

    # NOTE: This passes for both backends
    export_file = tmp_path / 'should_work.aiida'
    create_archive(entities=orm_nodes, filename=export_file, filter_size=1000)

    # NOTE: Run the failing test at the end as the exception leaves sqlachemy in an erroneus state,
    # so the `orm_nodes` list cannot be re-used. Trying to do so gives:
    # sqlalchemy.orm.exc.DetachedInstanceError: Instance <DbNode at 0x75d3826f1b40> is not bound to a Session;
    # attribute refresh operation cannot proceed (Background on this error at: https://sqlalche.me/e/20/bhk3)
    # .venv/lib/python3.10/site-packages/sqlalchemy/orm/loading.py:1603: DetachedInstanceError

    db_backend = pytestconfig.getoption('--db-backend')

    if db_backend.value == 'psql':
        export_file_fail = tmp_path / 'should_fail.aiida'
        with pytest.raises(OperationalError, match='number of parameters must be between 0 and 65535'):
            # Using `filter_size=num_nodes` effectively disables it
            create_archive(entities=orm_nodes, filename=export_file_fail, filter_size=num_nodes)

        # Explicitly session clean-up after the error
        get_manager().get_profile_storage().get_session().rollback()
