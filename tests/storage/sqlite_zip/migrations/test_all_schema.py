###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Schema regression tests for the SQLite archive migrations.

Each main revision after ``main_0000`` is either a data migration (replacing
NULLs left by the legacy conversion and enforcing non-nullability) or an empty
marker bringing the schema in line with ``psql_dos``. Since ``main_0000``
already creates the final schema, replaying the chain on an empty database
produces an identical schema for every revision, and so the reference files
are currently identical (stored once and referenced through symlinks). The
later revisions only change databases produced by the legacy conversion path,
which cannot be recreated from an empty database. The snapshots pin the full
chain up to each revision and gain discriminating power as soon as a revision
actually changes the schema.
"""

import pytest

from aiida.storage.sqlite_zip.migrator import alembic_migrator, list_versions
from aiida.storage.sqlite_zip.utils import create_sqla_engine
from tests.storage.sqlite.utils import reflect_schema

# Revisions whose downgrade is not implemented: they raise ``NotImplementedError``.
_LEGACY_MAIN_REVISIONS = ['main_0000', 'main_0000a', 'main_0000b', 'main_0001']


@pytest.mark.parametrize('version', [version for version in list_versions() if version.startswith('main')])
def test_main(version, tmp_path, data_regression):
    """Test that each main migration produces the expected database schema."""
    database_path = tmp_path / 'database.sqlite'

    with create_sqla_engine(database_path).connect() as connection:
        alembic_migrator.migrate_up(connection, version)
        connection.commit()

    data_regression.check(reflect_schema(database_path), basename=f'test_{version}')


@pytest.mark.parametrize('version', _LEGACY_MAIN_REVISIONS)
def test_legacy_downgrade_not_implemented(version, tmp_path):
    """Test that downgrades of the legacy main revisions raise ``NotImplementedError``.

    The revisions leading up to the v3 migration only support upgrades: they are
    no-ops or data migrations applied on top of databases produced by the
    legacy conversion path, so a downgrade is deliberately not implemented.
    """
    database_path = tmp_path / 'database.sqlite'

    with create_sqla_engine(database_path).connect() as connection:
        alembic_migrator.migrate_up(connection, version)
        connection.commit()

        with pytest.raises(NotImplementedError):
            alembic_migrator.migrate_down(connection, '-1')
