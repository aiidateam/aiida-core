###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Schema regression tests shared by storage migration backends."""

from pathlib import Path

import pytest
from alembic.command import downgrade, upgrade

from aiida.storage.sqlite_zip.migrator import _alembic_connect, list_versions
from aiida.storage.sqlite_zip.utils import create_sqla_engine
from tests.storage.migrations.utils import reflect_schema

PROFILE_MAIN_VERSIONS = ('main_0001', 'main_0002', 'main_0003')
SQLITE_ZIP_LEGACY_MAIN_REVISIONS = ('main_0000', 'main_0000a', 'main_0000b')
REFERENCE_SCHEMAS = Path(__file__).parent / 'reference_schemas'


def _check_main_schema(version: str, backend: str, profile, data_regression) -> None:
    """Check the schema produced by a profile storage main revision."""
    migrator_class = profile.storage_cls.migrator
    with migrator_class(profile) as migrator:
        migrator.migrate_up(f'main@{version}')

    with migrator_class(profile) as migrator:
        assert migrator.get_schema_version_profile() == version
        data_regression.check(
            reflect_schema(migrator.connection),
            fullpath=REFERENCE_SCHEMAS / f'{backend}_{version}.yml',
        )


def _check_initialised_schema(backend: str, profile, data_regression) -> None:
    """Check that a freshly initialised profile storage matches its migration head."""
    migrator_class = profile.storage_cls.migrator
    with migrator_class(profile) as migrator:
        head_version = migrator.get_schema_version_head()
        migrator.initialise()
        data_regression.check(
            reflect_schema(migrator.connection),
            fullpath=REFERENCE_SCHEMAS / f'{backend}_{head_version}.yml',
        )


@pytest.mark.parametrize('version', PROFILE_MAIN_VERSIONS)
def test_profile_main(version, migration_backend, migration_profile, data_regression):
    """Test that every main revision produces its reference schema."""
    _check_main_schema(version, migration_backend, migration_profile, data_regression)


def test_initialised_schema_matches_head(migration_backend, migration_profile, data_regression):
    """Test that a freshly initialized storage matches its migration head schema."""
    _check_initialised_schema(migration_backend, migration_profile, data_regression)


@pytest.mark.parametrize('version', [version for version in list_versions() if version.startswith('main')])
def test_sqlite_zip_main(version, tmp_path, data_regression):
    """Test that each SQLite archive migration produces its reference schema."""
    database_path = tmp_path / 'database.sqlite'

    with _alembic_connect(database_path) as config:
        upgrade(config, version)

    data_regression.check(
        reflect_schema(create_sqla_engine(database_path)),
        fullpath=REFERENCE_SCHEMAS / f'sqlite_zip_{version}.yml',
    )


@pytest.mark.parametrize('version', SQLITE_ZIP_LEGACY_MAIN_REVISIONS)
def test_sqlite_zip_legacy_main_downgrade_not_implemented(version, tmp_path):
    """Test that legacy SQLite archive main revisions cannot be downgraded."""
    database_path = tmp_path / 'database.sqlite'

    with _alembic_connect(database_path) as config:
        upgrade(config, version)

        with pytest.raises(NotImplementedError):
            downgrade(config, '-1')
