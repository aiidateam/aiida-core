"""Additional tests to cover the new check_migration_needed functionality."""

import json
import shutil
import zipfile
from unittest.mock import patch

import pytest

from aiida import __version__
from aiida.common.exceptions import CorruptStorage, StorageMigrationError
from aiida.storage.sqlite_zip.backend import SqliteZipBackend
from aiida.storage.sqlite_zip.migrator import check_migration_needed, migrate


def test_check_migration_needed_same_version(tmp_path):
    """Test check_migration_needed when versions are the same."""
    # Create a valid zip file with metadata
    zip_path = tmp_path / 'test.zip'
    target_version = 'main_0001'

    metadata = {
        'export_version': target_version,
        'aiida_version': __version__,
        'key_format': 'sha256',
    }

    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('metadata.json', json.dumps(metadata))

    # Should return False since versions are the same
    assert not check_migration_needed(zip_path, target_version)


def test_check_migration_needed_different_version(tmp_path):
    """Test check_migration_needed when versions are different."""
    # Create a valid zip file with metadata
    zip_path = tmp_path / 'test.zip'
    current_version = '0.9'
    target_version = 'main_0001'

    metadata = {
        'export_version': current_version,
        'aiida_version': __version__,
        'key_format': 'sha256',
    }

    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('metadata.json', json.dumps(metadata))

    # Should return True since versions are different
    assert check_migration_needed(zip_path, target_version)


def test_check_migration_needed_invalid_file(tmp_path):
    """Test check_migration_needed with invalid file format."""
    # Create a text file (not tar or zip)
    invalid_path = tmp_path / 'invalid.txt'
    invalid_path.write_text('not a zip or tar file')

    with pytest.raises(CorruptStorage, match='neither a tar nor a zip file'):
        check_migration_needed(invalid_path, '1.0.0')


def test_check_migration_needed_missing_export_version(tmp_path):
    """Test check_migration_needed with missing export_version in metadata."""
    zip_path = tmp_path / 'test.zip'

    # Create metadata without export_version
    metadata = {
        'aiida_version': __version__,
        'key_format': 'sha256',
    }

    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('metadata.json', json.dumps(metadata))

    with pytest.raises(CorruptStorage, match='No export_version found in metadata'):
        check_migration_needed(zip_path, 'main_0001')


def test_check_migration_needed_legacy_versions(tmp_path):
    """Test check_migration_needed with unsupported legacy versions."""
    zip_path = tmp_path / 'test.zip'

    metadata = {
        'export_version': '0.3',  # Legacy unsupported version
        'aiida_version': '1.0.0',
    }

    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('metadata.json', json.dumps(metadata))

    with pytest.raises(StorageMigrationError, match='Legacy migration.*not supported in aiida-core v2'):
        check_migration_needed(zip_path, '1.0.0')


def test_check_migration_needed_unknown_current_version(tmp_path):
    """Test check_migration_needed with unknown current version."""
    zip_path = tmp_path / 'test.zip'

    metadata = {
        'export_version': 'unknown_version',
        'aiida_version': __version__,
    }

    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('metadata.json', json.dumps(metadata))

    with patch('aiida.storage.sqlite_zip.migrator.list_versions') as mock_list:
        mock_list.return_value = ['1.0.0', '1.1.0']
        with pytest.raises(StorageMigrationError, match='Unknown current version'):
            check_migration_needed(zip_path, '1.0.0')


def test_check_migration_needed_unknown_target_version(tmp_path):
    """Test check_migration_needed with unknown target version."""
    zip_path = tmp_path / 'test.zip'

    metadata = {
        'export_version': '1.0.0',
        'aiida_version': __version__,
    }

    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('metadata.json', json.dumps(metadata))

    with patch('aiida.storage.sqlite_zip.migrator.list_versions') as mock_list:
        mock_list.return_value = ['1.0.0', '1.1.0']
        with pytest.raises(StorageMigrationError, match='Unknown target version'):
            check_migration_needed(zip_path, 'unknown_target')


def test_initialise_no_migration_needed(tmp_path, caplog):
    """Test initialise when no migration is needed."""
    filepath_archive = tmp_path / 'archive.zip'

    # Create an archive that's already at the target version
    profile = SqliteZipBackend.create_profile(filepath_archive)

    # First initialise to create the archive
    SqliteZipBackend.initialise(profile)

    # Clear the log
    caplog.clear()

    # Try to initialise again - should detect no migration needed
    initialised = SqliteZipBackend.initialise(profile, reset=False)
    assert not initialised

    # Should log that it's already at target version
    assert any('is already at target version' in record.message for record in caplog.records)
    assert not any('Migrating existing' in record.message for record in caplog.records)


def test_initialise_migration_needed(tmp_path, caplog):
    """Test initialise when migration is needed."""
    filepath_archive = tmp_path / 'archive.zip'

    # Create a zip file with an older version
    old_version = '0.9'
    target_version = 'main_0001'
    metadata = {
        'export_version': old_version,
        'aiida_version': __version__,
        'key_format': 'sha256',
    }

    with zipfile.ZipFile(filepath_archive, 'w') as zf:
        zf.writestr('metadata.json', json.dumps(metadata))
        # Add a minimal database file to avoid corruption errors
        zf.writestr('db.sqlite3', b'fake db content')

    profile = SqliteZipBackend.create_profile(filepath_archive)

    # Create a mock migrate function that actually creates the migrated file
    def mock_migrate_func(inpath, outpath, version):
        """Mock migrate function that creates the expected output file."""
        # Copy the input file to output path to simulate successful migration
        shutil.copy2(inpath, outpath)

    # Mock the migration functions to avoid actual migration complexity
    with (
        patch('aiida.storage.sqlite_zip.migrator.list_versions') as mock_list,
        patch('aiida.storage.sqlite_zip.migrator.migrate', side_effect=mock_migrate_func) as mock_migrate,
        patch('aiida.storage.sqlite_zip.backend.SqliteZipBackend.version_head') as mock_version,
    ):
        mock_list.return_value = ['0.9', '1.0', target_version]
        mock_version.return_value = target_version

        # Should detect migration is needed and call migrate
        initialised = SqliteZipBackend.initialise(profile, reset=False)
        assert not initialised

        # Should log migration attempt
        assert any(
            f'Migrating existing SqliteZipBackend to {target_version}' in record.message for record in caplog.records
        )
        mock_migrate.assert_called_once()


def test_migrate_no_migration_needed_different_path(tmp_path):
    """Test migrate when no migration is needed but input/output paths differ."""
    input_path = tmp_path / 'input.zip'
    output_path = tmp_path / 'output.zip'
    target_version = 'main_0001'

    metadata = {
        'export_version': target_version,
        'aiida_version': __version__,
        'key_format': 'sha256',
    }

    with zipfile.ZipFile(input_path, 'w') as zf:
        zf.writestr('metadata.json', json.dumps(metadata))

    # Should copy the file to output path
    migrate(input_path, output_path, target_version)

    # Both files should exist
    assert input_path.exists()
    assert output_path.exists()


def test_migrate_no_migration_needed_force_overwrite(tmp_path):
    """Test migrate when no migration is needed, paths differ, and force=True."""
    input_path = tmp_path / 'input.zip'
    output_path = tmp_path / 'output.zip'
    target_version = 'main_0001'

    # Create input file
    metadata = {
        'export_version': target_version,
        'aiida_version': '2.0.0',
        'key_format': 'sha256',
    }

    with zipfile.ZipFile(input_path, 'w') as zf:
        zf.writestr('metadata.json', json.dumps(metadata))

    # Create existing output file
    output_path.write_text('existing content')

    # Should overwrite the existing output file
    migrate(input_path, output_path, target_version, force=True)

    # Output should be a copy of input, not the original content
    assert output_path.exists()
    assert zipfile.is_zipfile(output_path)


def test_full_initialise_cycle_no_migration(tmp_path, caplog):
    """Test a full cycle of initialise -> re-initialise with no migration needed."""
    filepath_archive = tmp_path / 'archive.zip'
    profile = SqliteZipBackend.create_profile(filepath_archive)

    # First initialisation should create the archive
    result1 = SqliteZipBackend.initialise(profile)
    assert result1 is True
    assert filepath_archive.exists()

    # Clear logs
    caplog.clear()

    # Second initialisation should detect no migration needed
    result2 = SqliteZipBackend.initialise(profile, reset=False)
    assert result2 is False

    # Should log that it's already at target version
    target_version = SqliteZipBackend.version_head()
    assert any(f'is already at target version {target_version}' in record.message for record in caplog.records)


def test_check_migration_needed_with_real_archive(tmp_path):
    """Test check_migration_needed with a real archive created by the backend."""
    filepath_archive = tmp_path / 'archive.zip'
    profile = SqliteZipBackend.create_profile(filepath_archive)

    # Create a real archive
    SqliteZipBackend.initialise(profile)

    # Check migration needed against the current version (should be False)
    target_version = SqliteZipBackend.version_head()
    result = check_migration_needed(filepath_archive, target_version)
    assert result is False

    # Check against a different version (should be True if we mock list_versions)
    with patch('aiida.storage.sqlite_zip.migrator.list_versions') as mock_list:
        mock_list.return_value = [target_version, 'future_version']
        result = check_migration_needed(filepath_archive, 'future_version')
        assert result is True
