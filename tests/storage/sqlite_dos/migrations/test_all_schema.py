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

from aiida.storage.sqlite_dos.backend import SqliteDosMigrator
from aiida.storage.sqlite_zip.models import SqliteBase


@pytest.mark.parametrize('version', list(v for v in SqliteDosMigrator.get_schema_versions() if v.startswith('main')))
def test_main(version, uninitialised_profile, reflect_schema, data_regression):
    """Test that the migrations produce the expected database schema.

    Each parametrized case starts with an empty database and targets one
    migration revision:

      empty storage with no database schema
      -> migrate_up(main@<revision>)
      -> reopen storage
      -> compare resulting database schema with <revision> snapshot

    Reopening verifies that the Alembic revision was committed to the database,
    rather than only being available through the migration connection.
    """
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        migrator.migrate_up(f'main@{version}')

    with SqliteDosMigrator(uninitialised_profile) as migrator:
        assert migrator.get_schema_version_profile() == version
        data_regression.check(reflect_schema(uninitialised_profile), basename=f'test_{version}')


def test_initialised_schema_matches_head(uninitialised_profile, reflect_schema, data_regression):
    """Test that the initialized database schema matches the Alembic head.

    Fresh storage initialization follows a separate path from applying the
    migration chain:

      empty storage with no database schema
      -> initialise storage with schema from current code
      -> compare resulting database schema with Alembic-head snapshot
    """
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        head_version = migrator.get_schema_version_head()
        migrator.initialise()
        data_regression.check(reflect_schema(uninitialised_profile), basename=f'test_{head_version}')


def test_main_0003_with_db_setting(uninitialised_profile, reflect_schema, data_regression):
    """Test upgrading a historically initialized database with the settings table.

    Before ``main_0003``, fresh ``sqlite_dos`` initialization created
    ``db_dbsetting`` through ORM metadata, while the migration schema omitted
    it. This models that database state before upgrading it to ``main_0003``.
    """
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        SqliteBase.metadata.tables['db_dbsetting'].create(migrator.connection)
        migrator.connection.commit()
        migrator.migrate_up('main@main_0003')
        data_regression.check(reflect_schema(uninitialised_profile), basename='test_main_0003')
