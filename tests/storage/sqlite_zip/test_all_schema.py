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
marker bringing the revisions in line with the profile database backends. Since
``main_0000`` already creates the final schema, replaying the chain on an empty
database produces an identical schema for every
revision, and so the reference files are currently identical (stored once and
referenced through symlinks). The data migrations only change databases containing
the affected content, which cannot be recreated from an empty database. The
snapshots pin the full chain up to each revision and gain discriminating power as
soon as a revision actually changes the schema.
"""

import pytest
from alembic.command import downgrade, upgrade

from aiida.storage.sqlite_zip.migrator import _alembic_connect, list_versions
from tests.storage.sqlite.utils import reflect_schema

# Revisions whose downgrade is not implemented: they raise ``NotImplementedError``.
_MAIN_REVISIONS_WITHOUT_DOWNGRADE = ['main_0000', 'main_0000a', 'main_0000b']


@pytest.mark.parametrize('version', [version for version in list_versions() if version.startswith('main')])
def test_main(version, tmp_path, data_regression):
    """Test that each main migration produces the expected database schema."""
    database_path = tmp_path / 'database.sqlite'

    with _alembic_connect(database_path) as config:
        upgrade(config, version)

    data_regression.check(reflect_schema(database_path), basename=f'test_{version}')


@pytest.mark.parametrize('version', _MAIN_REVISIONS_WITHOUT_DOWNGRADE)
def test_legacy_downgrade_not_implemented(version, tmp_path):
    """Test that downgrades of the main revisions raise ``NotImplementedError``.

    The main revisions only support upgrades: they are no-ops or data migrations
    that cannot be reversed, so a downgrade is deliberately not implemented.
    """
    database_path = tmp_path / 'database.sqlite'

    with _alembic_connect(database_path) as config:
        upgrade(config, version)

        with pytest.raises(NotImplementedError):
            downgrade(config, '-1')
