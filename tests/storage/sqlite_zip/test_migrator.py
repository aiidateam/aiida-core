"""Tests for :mod:`aiida.storage.sqlite_zip.migrator`."""

import json
import zipfile

import pytest

from aiida import __version__ as aiida_version
from aiida.common.exceptions import CorruptStorage, StorageMigrationError
from aiida.storage.sqlite_zip.backend import SqliteZipBackend
from aiida.storage.sqlite_zip.migrator import check_migration_needed, migrate

latest_version = SqliteZipBackend.version_head()
old_version = '0.9'
default_metadata = {
    'aiida_version': aiida_version,
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

    # Unknown current version
    unknown_current_zip = tmp_path / 'unknown_current.zip'
    unknown_current_metadata = {**default_metadata, 'export_version': 'unknown_current'}

    with zipfile.ZipFile(unknown_current_zip, 'w') as zf:
        zf.writestr('metadata.json', json.dumps(unknown_current_metadata))

    with pytest.raises(StorageMigrationError, match='Unknown current version'):
        check_migration_needed(unknown_current_zip, latest_version)

    # Unknown target version
    valid_zip = tmp_path / 'unknown_target.zip'
    metadata = {**default_metadata, 'export_version': old_version}

    with zipfile.ZipFile(valid_zip, 'w') as zf:
        zf.writestr('metadata.json', json.dumps(metadata))

    with pytest.raises(StorageMigrationError, match='Unknown target version'):
        check_migration_needed(valid_zip, 'unknown_target')


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

    # Test: different paths, should copy file
    migrate(input_path, output_path, latest_version)
    assert output_path.exists()
    assert zipfile.is_zipfile(output_path)

    # Test: force overwrite existing output
    output_path.write_text('existing content')
    migrate(input_path, output_path, latest_version, force=True)
    assert zipfile.is_zipfile(output_path)
