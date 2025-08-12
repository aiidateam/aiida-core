"""Tests for :mod:`aiida.storage.sqlite_zip.migrator`."""

import json
import zipfile

import pytest

from aiida import __version__
from aiida.common.exceptions import CorruptStorage, StorageMigrationError
from aiida.storage.sqlite_zip.backend import SqliteZipBackend
from aiida.storage.sqlite_zip.migrator import check_migration_needed

latest_version = SqliteZipBackend.version_head()
old_version = '0.9'
default_metadata = {
    'aiida_version': __version__,
    'key_format': 'sha256',
}


def test_check_migration_needed_same_version(tmp_path):
    """Test check_migration_needed when no migration is needed."""
    zip_path = tmp_path / 'test.zip'

    metadata = {**default_metadata, 'export_version': latest_version}

    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('metadata.json', json.dumps(metadata))

    assert not check_migration_needed(zip_path, latest_version)


def test_check_migration_needed_different_version(tmp_path):
    """Test check_migration_needed when migration is needed."""
    zip_path = tmp_path / 'test.zip'
    old_version = '0.9'

    metadata = {**default_metadata, 'export_version': old_version}

    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('metadata.json', json.dumps(metadata))

    assert check_migration_needed(zip_path, latest_version)


def test_check_migration_needed_error_cases(tmp_path):
    """Test error cases for check_migration_needed."""
    # Invalid file format
    invalid_path = tmp_path / 'invalid.txt'
    invalid_path.write_text('not a zip or tar file')

    with pytest.raises(CorruptStorage, match='neither a tar nor a zip file'):
        check_migration_needed(invalid_path, 'main_0001')

    # Missing export_version
    zip_path = tmp_path / 'missing_version.zip'

    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('metadata.json', json.dumps(default_metadata))

    with pytest.raises(CorruptStorage, match='No export_version found'):
        check_migration_needed(zip_path, 'main_0001')

    # Legacy version
    legacy_zip = tmp_path / 'legacy.zip'
    legacy_metadata = {'export_version': '0.3', 'aiida_version': '1.0.0'}

    with zipfile.ZipFile(legacy_zip, 'w') as zf:
        zf.writestr('metadata.json', json.dumps(legacy_metadata))

    with pytest.raises(StorageMigrationError, match='Legacy migration.*not supported'):
        check_migration_needed(legacy_zip, 'main_0001')
