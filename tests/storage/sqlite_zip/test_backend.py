"""Tests for :mod:`aiida.storage.sqlite_zip.backend`."""

import os
import pathlib
import sqlite3
from contextlib import closing

import pytest
from pydantic_core import ValidationError
from sqlalchemy import text

from aiida.common.exceptions import CorruptStorage, IncompatibleExternalDependencies
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
    """Test :class:`aiida.storage.sqlite_zip.backend.SqliteZipBackend.CliModel`."""
    with pytest.raises(ValidationError, match=r'.*The archive `non-existent` does not exist.*'):
        SqliteZipBackend.CliModel(filepath='non-existent')

    filepath = pathlib.Path.cwd() / 'archive.aiida'
    filepath.touch()

    model = SqliteZipBackend.CliModel(filepath=filepath.name)
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


@pytest.fixture
def zipped_archive(tmp_path, monkeypatch):
    """Return an empty zipped archive, with the extracted-database cache redirected to ``tmp_path / 'cache'``."""
    monkeypatch.setattr('aiida.storage.sqlite_zip.backend.DATABASE_CACHE_DIR', tmp_path / 'cache')
    filepath = tmp_path / 'archive.aiida'
    assert SqliteZipBackend.initialise(SqliteZipBackend.create_profile(filepath))
    return filepath


def _open_archive(filepath: pathlib.Path) -> None:
    """Open the archive, query its database and close it, as a single ``verdi`` command does."""
    backend = SqliteZipBackend(SqliteZipBackend.create_profile(filepath))
    try:
        backend.get_session().execute(text('SELECT count(*) FROM db_dbnode')).scalar_one()
    finally:
        backend.close()


def test_zipped_database_extracted_once(zipped_archive, tmp_path):
    """The database of a zipped archive is extracted on first open and reused, also after the backend is closed."""
    _open_archive(zipped_archive)
    cached = sorted((tmp_path / 'cache').iterdir())
    assert len(cached) == 1
    assert cached[0].suffix == '.sqlite3'
    mtime = cached[0].stat().st_mtime_ns

    _open_archive(zipped_archive)
    assert sorted((tmp_path / 'cache').iterdir()) == cached
    assert cached[0].stat().st_mtime_ns == mtime


def test_zipped_database_cache_optimized(zipped_archive, tmp_path):
    """The cached database carries the extra indexes and planner statistics; the archive file is left untouched."""
    content = zipped_archive.read_bytes()
    _open_archive(zipped_archive)

    (cached,) = (tmp_path / 'cache').iterdir()
    with closing(sqlite3.connect(cached)) as connection:
        names = {row[0] for row in connection.execute('SELECT name FROM sqlite_master')}
    assert {'ix_cache_db_dbnode_node_type_ctime', 'ix_cache_db_dbnode_process_type_ctime', 'sqlite_stat1'} <= names
    assert zipped_archive.read_bytes() == content


def test_zipped_database_cache_invalidated(zipped_archive, tmp_path):
    """A modified archive file is extracted anew rather than served from the stale cache entry."""
    _open_archive(zipped_archive)
    os.utime(zipped_archive, ns=(0, 0))
    _open_archive(zipped_archive)
    assert len(list((tmp_path / 'cache').iterdir())) == 2


def test_zipped_database_extraction_failure(zipped_archive, tmp_path, monkeypatch):
    """A failed extraction raises ``CorruptStorage`` and leaves no partial database in the cache."""

    def fail_extraction(*args, **kwargs):
        raise OSError('disk full')

    monkeypatch.setattr('archive_path.extract_file_in_zip', fail_extraction)
    with pytest.raises(CorruptStorage, match='disk full'):
        _open_archive(zipped_archive)
    assert list((tmp_path / 'cache').iterdir()) == []
