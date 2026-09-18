###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Basic tests for all migrations"""

import pytest

from aiida.storage.psql_dos.migrator import PsqlDosMigrator


@pytest.mark.nightly
@pytest.mark.parametrize('version', list(v for v in PsqlDosMigrator.get_schema_versions() if v.startswith('django')))
def test_django(version, uninitialised_profile, reflect_schema, data_regression):
    """Test that the migrations (along the legacy django branch) produce the expected database schema."""
    with PsqlDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up(f'django@{version}')

    data_regression.check(reflect_schema(uninitialised_profile))


@pytest.mark.nightly
@pytest.mark.parametrize(
    '_id,version',
    enumerate(v for v in PsqlDosMigrator.get_schema_versions() if not (v.startswith('django') or v.startswith('main'))),
)
def test_sqla(_id, version, uninitialised_profile, reflect_schema, data_regression):
    """Test that the migrations produce the expected database schema."""
    with PsqlDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up(f'sqlalchemy@{version}')

    data_regression.check(reflect_schema(uninitialised_profile))
