###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test ``main_0002.py``."""

import json
import zipfile

from sqlalchemy import text

from aiida import __version__ as aiida_version
from aiida.storage.sqlite_zip.backend import SqliteZipBackend
from aiida.storage.sqlite_zip.migrator import migrate
from aiida.storage.sqlite_zip.utils import create_sqla_engine
from tests.storage.sqlite.utils import reflect_schema

default_metadata = {
    'aiida_version': aiida_version,
    'key_format': 'sha256',
}


def test_migrate_main_0001_to_main_0002(tmp_path):
    """Test the empty migration leaves the schema untouched."""
    from alembic.command import downgrade, upgrade

    from aiida.storage.sqlite_zip.migrator import _alembic_connect, _migration_context
    from aiida.storage.sqlite_zip.utils import DB_FILENAME, META_FILENAME

    # Alembic-level: empty migration leaves the schema untouched but bumps the revision,
    # and downgrades cleanly since there is nothing to revert.
    database_path = tmp_path / 'database.sqlite'

    with _alembic_connect(database_path) as config:
        upgrade(config, 'main_0001')

    schema_before = reflect_schema(database_path)

    with _alembic_connect(database_path) as config:
        upgrade(config, 'main_0002')

    with _migration_context(database_path) as context:
        assert context.get_current_revision() == 'main_0002'

    assert reflect_schema(database_path) == schema_before

    with create_sqla_engine(database_path).connect() as connection:
        version = connection.execute(text('SELECT version_num FROM alembic_version')).scalar_one()
        assert version == 'main_0002'

    with _alembic_connect(database_path) as config:
        downgrade(config, 'main_0001')

    with _migration_context(database_path) as context:
        assert context.get_current_revision() == 'main_0001'

    assert reflect_schema(database_path) == schema_before

    # Archive-level: ``migrate`` streams the same upgrade through a zip archive
    # and stamps the new ``export_version`` in the metadata.
    db_path = tmp_path / DB_FILENAME
    with _alembic_connect(db_path) as config:
        upgrade(config, 'main_0001')

    input_path = tmp_path / 'input.zip'
    output_path = tmp_path / 'output.zip'
    metadata = {**default_metadata, 'export_version': 'main_0001'}

    with zipfile.ZipFile(input_path, 'w') as zf:
        zf.writestr(META_FILENAME, json.dumps(metadata))
        zf.write(db_path, DB_FILENAME)

    migrate(input_path, output_path, 'main_0002')

    assert SqliteZipBackend.get_current_archive_version(output_path) == 'main_0002'

    with zipfile.ZipFile(output_path) as zf:
        assert json.loads(zf.read(META_FILENAME))['export_version'] == 'main_0002'
        zf.extract(DB_FILENAME, tmp_path / 'out')

    with _migration_context(tmp_path / 'out' / DB_FILENAME) as context:
        assert context.get_current_revision() == 'main_0002'
