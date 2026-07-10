###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.storage.sqlite_zip.migrator`."""

import json
import pathlib
import sqlite3
import zipfile

import pytest

from aiida import __version__ as aiida_version
from aiida.common.exceptions import CorruptStorage, StorageMigrationError
from aiida.storage.sqlite_zip.backend import SqliteZipBackend
from aiida.storage.sqlite_zip.migrator import migrate
from aiida.storage.sqlite_zip.utils import DB_FILENAME
from tests.utils.archives import get_archive_file

latest_version = SqliteZipBackend.version_head()
old_version = '0.9'
default_metadata = {
    'aiida_version': aiida_version,
    'key_format': 'sha256',
}


def test_get_current_archive_version(tmp_path):
    """Test get_current_archive_version with valid archive and error cases."""
    # Valid case
    zip_path = tmp_path / 'test.zip'
    metadata = {**default_metadata, 'export_version': latest_version}

    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('metadata.json', json.dumps(metadata))

    version = SqliteZipBackend.get_current_archive_version(zip_path)
    assert version == latest_version

    # Invalid file format
    invalid_path = tmp_path / 'invalid.txt'
    invalid_path.write_text('not a zip or tar file')

    with pytest.raises(CorruptStorage, match='neither a tar nor a zip file'):
        SqliteZipBackend.get_current_archive_version(invalid_path)

    # Missing export_version
    missing_version_path = tmp_path / 'missing_version.zip'

    with zipfile.ZipFile(missing_version_path, 'w') as zf:
        zf.writestr('metadata.json', json.dumps(default_metadata))

    with pytest.raises(CorruptStorage, match='No export_version found'):
        SqliteZipBackend.get_current_archive_version(missing_version_path)


def test_validate_archive_versions():
    """Test validate_archive_versions with various scenarios."""
    # Valid versions - should not raise
    SqliteZipBackend.validate_archive_versions(latest_version, latest_version)
    SqliteZipBackend.validate_archive_versions(old_version, latest_version)

    # Legacy current version
    with pytest.raises(StorageMigrationError, match=r'Legacy migration.*not supported'):
        SqliteZipBackend.validate_archive_versions('0.3', latest_version)

    # Legacy target version
    with pytest.raises(StorageMigrationError, match=r'Legacy migration.*not supported'):
        SqliteZipBackend.validate_archive_versions(latest_version, '0.2')

    # Both legacy
    with pytest.raises(StorageMigrationError, match=r'Legacy migration.*not supported'):
        SqliteZipBackend.validate_archive_versions('0.1', '0.3')

    # Unknown target version
    with pytest.raises(StorageMigrationError, match='Unknown target version'):
        SqliteZipBackend.validate_archive_versions(old_version, 'unknown_target')

    # Unknown current version
    with pytest.raises(StorageMigrationError, match='Unknown current version'):
        SqliteZipBackend.validate_archive_versions('unknown_current', latest_version)


def test_migrate_no_migration_needed_file_operations(tmp_path):
    """Test migrate function when no migration is needed but file operations are required."""
    input_path = tmp_path / 'input.zip'
    output_path = tmp_path / 'output.zip'

    # Create input file with current version
    metadata = {
        'export_version': latest_version,
        'aiida_version': aiida_version,
        'key_format': 'sha256',
    }

    with zipfile.ZipFile(input_path, 'w') as zf:
        zf.writestr('metadata.json', json.dumps(metadata))
    assert input_path.exists()

    # Test: identical paths, file should remain unchanged
    before_content = input_path.read_bytes()

    with pytest.raises(StorageMigrationError, match='Output path already exists and force'):
        migrate(input_path, input_path, latest_version)

    migrate(input_path, input_path, latest_version, force=True)
    after_content = input_path.read_bytes()
    assert before_content == after_content, 'File should remain unchanged when inpath == outpath'
    assert zipfile.is_zipfile(input_path)

    # Test: different paths, should copy file
    migrate(input_path, output_path, latest_version)
    assert output_path.exists()
    assert zipfile.is_zipfile(output_path)

    # Test: force overwrite existing output
    output_path.write_text('existing content')
    # Assertion fails with original text file before migration
    with pytest.raises(AssertionError):
        assert zipfile.is_zipfile(output_path)
    # Migration overwrites the original text file with the zip file
    migrate(input_path, output_path, latest_version, force=True)
    assert zipfile.is_zipfile(output_path)


def _read_transport_types(archive_path) -> list:
    """Return the transport types of the computers stored in an archive."""
    import sqlite3
    import tempfile

    with zipfile.ZipFile(archive_path) as zip_file:
        database = zip_file.read(DB_FILENAME)

    with tempfile.TemporaryDirectory() as dirpath:
        filepath = pathlib.Path(dirpath) / DB_FILENAME
        filepath.write_bytes(database)
        with sqlite3.connect(filepath) as connection:
            return [row[0] for row in connection.execute('SELECT transport_type FROM db_dbcomputer')]


def test_migrate_renames_ssh_async_transport(tmp_path):
    """An archive holding a ``core.ssh_async`` computer is migrated to the renamed ``core.ssh``."""
    original = get_archive_file('export_main_0001_simple.aiida', filepath='export/migrate')
    input_path = tmp_path / 'input.aiida'
    output_path = tmp_path / 'output.aiida'

    # Rewrite the archive with a computer that uses the old entry point name.
    with zipfile.ZipFile(original) as source, zipfile.ZipFile(input_path, 'w') as target:
        for info in source.infolist():
            content = source.read(info.filename)
            if info.filename == DB_FILENAME:
                filepath = tmp_path / DB_FILENAME
                filepath.write_bytes(content)
                with sqlite3.connect(filepath) as connection:
                    connection.execute("UPDATE db_dbcomputer SET transport_type = 'core.ssh_async'")
                content = filepath.read_bytes()
            target.writestr(info, content)

    assert _read_transport_types(input_path) == ['core.ssh_async']

    migrate(input_path, output_path, latest_version)

    assert _read_transport_types(output_path) == ['core.ssh']
