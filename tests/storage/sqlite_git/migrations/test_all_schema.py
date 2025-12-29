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

from aiida.storage.sqlite_git.backend import SqliteGitMigrator


@pytest.mark.parametrize('version', list(v for v in SqliteGitMigrator.get_schema_versions() if v.startswith('main')))
def test_main(version, uninitialised_profile, reflect_schema, data_regression):
    """Test that the migrations produce the expected database schema."""
    migrator = SqliteGitMigrator(uninitialised_profile)
    migrator.migrate_up(f'main@{version}')
    data_regression.check(reflect_schema(uninitialised_profile))


def test_main_initialized(uninitialised_profile):
    """Test that ``migrate`` properly stamps the new schema version when updating database with existing schema."""
    migrator = SqliteGitMigrator(uninitialised_profile)

    # Initialize database at first version of main branch
    migrator.migrate_up('main@main_0001')
    assert migrator.get_schema_version_profile() == 'main_0001'
    migrator.close()

    # Reinitialize the migrator to make sure we are fetching actual state of database and not in-memory state and then
    # migrate to head schema version.
    migrator = SqliteGitMigrator(uninitialised_profile)
    migrator.migrate()
    migrator.close()

    # Reinitialize the migrator to make sure we are fetching actual state of database and not in-memory state and then
    # assert that the database version is properly set to the head schema version
    migrator = SqliteGitMigrator(uninitialised_profile)
    assert migrator.get_schema_version_profile() == migrator.get_schema_version_head()


def test_head_vs_orm(uninitialised_profile, reflect_schema, data_regression):
    """Test that the migrations produce the same database schema as the models."""
    migrator = SqliteGitMigrator(uninitialised_profile)
    head_version = migrator.get_schema_version_head()
    migrator.initialise()
    data_regression.check(reflect_schema(uninitialised_profile), basename=f'test_head_vs_orm_{head_version}_')
