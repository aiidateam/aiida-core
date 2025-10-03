"""Tests for :mod:`aiida.storage.sqlite_zip.backend`."""

import pathlib

import pytest
from pydantic_core import ValidationError

from aiida.common.exceptions import IncompatibleExternalDependencies
from aiida.storage.sqlite_zip.backend import SqliteZipBackend, validate_sqlite_version
from aiida.storage.sqlite_zip.migrator import validate_storage


def test_initialise(tmp_path, caplog):
    """Test :meth:`aiida.storage.sqlite_zip.backend.SqliteZipBackend.initialise`."""
    filepath_archive = tmp_path / 'archive.zip'
    profile = SqliteZipBackend.create_profile(filepath_archive)
    initialised = SqliteZipBackend.initialise(profile)
    assert initialised

    assert filepath_archive.exists()
    validate_storage(filepath_archive)
    assert any('Initialising a new SqliteZipBackend' in record.message for record in caplog.records)


def test_initialise_reset_true(tmp_path, caplog):
    """Test :meth:`aiida.storage.sqlite_zip.backend.SqliteZipBackend.initialise` with ``reset=True``."""
    filepath_archive = tmp_path / 'archive.zip'
    filepath_archive.touch()
    profile = SqliteZipBackend.create_profile(filepath_archive)
    initialised = SqliteZipBackend.initialise(profile, reset=True)
    assert initialised

    assert filepath_archive.exists()
    validate_storage(filepath_archive)
    assert any('Resetting existing SqliteZipBackend' in record.message for record in caplog.records)


def test_initialise_reset_false(tmp_path, caplog):
    """Test :meth:`aiida.storage.sqlite_zip.backend.SqliteZipBackend.initialise` with ``reset=False``."""
    filepath_archive = tmp_path / 'archive.zip'

    # Initialise the archive
    profile = SqliteZipBackend.create_profile(filepath_archive)
    initialised = SqliteZipBackend.initialise(profile)
    assert initialised

    # Initialise it again with ``reset=False`
    initialised = SqliteZipBackend.initialise(profile, reset=False)
    assert not initialised

    assert filepath_archive.exists()
    validate_storage(filepath_archive)
    assert any('is already at target version' in record.message for record in caplog.records)


@pytest.mark.usefixtures('chdir_tmp_path')
def test_model():
    """Test :class:`aiida.storage.sqlite_zip.backend.SqliteZipBackend.Model`."""
    with pytest.raises(ValidationError, match=r'.*The archive `non-existent` does not exist.*'):
        SqliteZipBackend.Model(filepath='non-existent')

    filepath = pathlib.Path.cwd() / 'archive.aiida'
    filepath.touch()

    model = SqliteZipBackend.Model(filepath=filepath.name)
    assert pathlib.Path(model.filepath).is_absolute()


def test_validate_sqlite_version(monkeypatch):
    """Test :meth:`aiida.storage.sqlite_zip.backend.validate_sqlite_version`."""

    # Test when sqlite version is not supported, should read sqlite version from sqlite3.sqlite_version
    monkeypatch.setattr('sqlite3.sqlite_version', '0.0.0')
    monkeypatch.setattr('aiida.storage.sqlite_zip.backend.SUPPORTED_VERSION', '100.0.0')
    with pytest.raises(
        IncompatibleExternalDependencies, match=r'.*Storage backend requires sqlite 100.0.0 or higher.*'
    ):
        validate_sqlite_version()

    # Test when sqlite version is supported
    monkeypatch.setattr('sqlite3.sqlite_version', '100.0.0')
    monkeypatch.setattr('aiida.storage.sqlite_zip.backend.SUPPORTED_VERSION', '0.0.0')
    validate_sqlite_version()


def test_initialise_migration_needed(tmp_path, caplog, monkeypatch):
    """Test :meth:`aiida.storage.sqlite_zip.backend.SqliteZipBackend.initialise` when migration is triggered."""
    filepath_archive = tmp_path / 'archive.zip'
    profile = SqliteZipBackend.create_profile(filepath_archive)
    target_version = SqliteZipBackend.version_head()
    old_version = '0.9'

    # First create a valid current archive
    assert SqliteZipBackend.initialise(profile)

    # Mock get_current_archive_version to return an old version (forcing migration)
    def mock_get_current_archive_version(inpath):
        return old_version

    monkeypatch.setattr(
        'aiida.storage.sqlite_zip.backend.SqliteZipBackend.get_current_archive_version',
        mock_get_current_archive_version,
    )

    # Mock migrate function to avoid actual migration complexity
    def mock_migrate(source, target, version):
        import shutil

        shutil.copy2(source, target)

    monkeypatch.setattr('aiida.storage.sqlite_zip.migrator.migrate', mock_migrate)

    # Clear logs to focus on this call
    caplog.clear()

    # This should trigger the migration path
    result = SqliteZipBackend.initialise(profile, reset=False)

    assert result is False  # Archive existed, so returns False even after migration

    # Verify migration log message was generated
    log_msg = f'Migrating existing SqliteZipBackend from version {old_version} to version {target_version}'
    assert any(log_msg in record.message for record in caplog.records)
