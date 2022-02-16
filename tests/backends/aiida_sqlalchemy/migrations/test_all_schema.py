# -*- coding: utf-8 -*-
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

from aiida.backends.sqlalchemy.migrator import PsqlDostoreMigrator


@pytest.mark.parametrize('version', list(v for v in PsqlDostoreMigrator.get_schema_versions() if v.startswith('main')))
def test_main(version, uninitialised_profile, schema_generator, data_regression):
    """Test that the migrations produce the expected database schema."""
    migrator = PsqlDostoreMigrator(uninitialised_profile)
    migrator.migrate_up(f'main@{version}')
    data_regression.check(schema_generator(uninitialised_profile))


@pytest.mark.parametrize(
    'version', list(v for v in PsqlDostoreMigrator.get_schema_versions() if v.startswith('django'))
)
def test_django(version, uninitialised_profile, schema_generator, data_regression):
    """Test that the migrations (along the legacy django branch) produce the expected database schema."""
    migrator = PsqlDostoreMigrator(uninitialised_profile)
    migrator.migrate_up(f'django@{version}')
    data_regression.check(schema_generator(uninitialised_profile))


@pytest.mark.parametrize(
    '_id,version',
    enumerate(
        v for v in PsqlDostoreMigrator.get_schema_versions() if not (v.startswith('django') or v.startswith('main'))
    )
)
def test_sqla(_id, version, uninitialised_profile, schema_generator, data_regression):
    """Test that the migrations produce the expected database schema."""
    migrator = PsqlDostoreMigrator(uninitialised_profile)
    migrator.migrate_up(f'sqlalchemy@{version}')
    data_regression.check(schema_generator(uninitialised_profile))


def test_head_vs_orm(uninitialised_profile, schema_generator, data_regression):
    """Test that the migrations produce the same database schema as the models."""
    migrator = PsqlDostoreMigrator(uninitialised_profile)
    head_version = migrator.get_schema_version_head()
    migrator.initialise()
    data_regression.check(schema_generator(uninitialised_profile), basename=f'test_main_{head_version}_')
