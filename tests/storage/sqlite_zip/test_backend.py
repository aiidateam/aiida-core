"""Tests for :mod:`aiida.storage.sqlite_zip.backend`."""

import contextlib
import functools
import gc
import hashlib
import http.server
import pathlib
import re
import threading
import zipfile

import pytest
from pydantic_core import ValidationError

from aiida.common.exceptions import IncompatibleExternalDependencies, StorageMigrationError, UnreachableStorage
from aiida.storage.sqlite_zip.backend import FolderBackendRepository, SqliteZipBackend, validate_sqlite_version
from aiida.storage.sqlite_zip.migrator import validate_storage
from aiida.storage.sqlite_zip.utils import ReadOnlyError, open_remote_zip


class RangeRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Minimal HTTP handler supporting single byte-range requests, as required by ``remotezip``."""

    protocol_version = 'HTTP/1.1'

    def log_message(self, format, *args):
        """Silence request logging."""

    def do_GET(self):  # noqa: N802
        filepath = pathlib.Path(self.translate_path(self.path))
        if not filepath.is_file():
            self.send_error(404)
            return
        data = filepath.read_bytes()
        range_header = self.headers.get('Range')

        if range_header is None:
            self.send_response(200)
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        match = re.fullmatch(r'bytes=(\d*)-(\d*)', range_header.strip())
        if match is None:
            self.send_error(400)
            return
        start_str, end_str = match.groups()
        if start_str:
            start = int(start_str)
            end = int(end_str) if end_str else len(data) - 1
        else:
            # Suffix range, e.g. ``bytes=-100`` requests the last 100 bytes
            start = max(0, len(data) - int(end_str))
            end = len(data) - 1
        end = min(end, len(data) - 1)
        chunk = data[start : end + 1]

        self.send_response(206)
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Range', f'bytes {start}-{end}/{len(data)}')
        self.send_header('Content-Length', str(len(chunk)))
        self.end_headers()
        self.wfile.write(chunk)


class NoRangeRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Minimal HTTP handler that ignores range requests, always responding with the full content."""

    def log_message(self, format, *args):
        """Silence request logging."""


@contextlib.contextmanager
def serve_directory(handler_cls, directory):
    """Serve ``directory`` over HTTP with the given request handler class, yielding the base URL."""
    handler = functools.partial(handler_cls, directory=str(directory))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_address[1]}'
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.fixture
def serve_over_http(tmp_path):
    """Serve ``tmp_path`` over HTTP with support for byte-range requests, yielding the base URL."""
    with serve_directory(RangeRequestHandler, tmp_path) as url:
        yield url


@pytest.fixture
def serve_over_http_no_ranges(tmp_path):
    """Serve ``tmp_path`` over HTTP without support for byte-range requests, yielding the base URL."""
    with serve_directory(NoRangeRequestHandler, tmp_path) as url:
        yield url


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


def test_model_url():
    """Test :class:`aiida.storage.sqlite_zip.backend.SqliteZipBackend.CliModel` accepts URLs verbatim."""
    url = 'https://example.com/archive.aiida'
    model = SqliteZipBackend.CliModel(filepath=url)
    assert model.filepath == url


def test_remote_archive(tmp_path, serve_over_http):
    """Test creating a profile from a remote archive URL and reading data and repository files from it."""
    filepath_archive = tmp_path / 'archive.aiida'
    SqliteZipBackend.initialise(SqliteZipBackend.create_profile(filepath_archive))

    # Add a repository file to the archive
    content = b'some repository content'
    key = hashlib.sha256(content).hexdigest()
    with zipfile.ZipFile(filepath_archive, 'a') as zip_handle:
        zip_handle.writestr(f'repo/{key}', content)

    url = f'{serve_over_http}/archive.aiida'
    profile = SqliteZipBackend.create_profile(url)
    assert profile.storage_config['filepath'] == url

    # The archive is already at the head version, so no initialisation or migration is required
    assert SqliteZipBackend.initialise(profile) is False

    validate_storage(url)
    backend = SqliteZipBackend(profile)

    # The database is fetched from the remote zip and can be queried
    from aiida.orm import QueryBuilder, User

    assert QueryBuilder(backend=backend).append(User).count() == 0

    # Repository files are streamed directly from the remote zip
    repository = backend.get_repository()
    assert list(repository.list_objects()) == [key]
    assert repository.has_object(key)
    with repository.open(key) as handle:
        assert handle.read() == content

    # The remote zip handle opened by the backend is reused by the repository, instead of fetching the central
    # directory of the remote zip file again
    assert repository._zipfile is backend._resources.remote_zip

    backend.close()


def test_remote_archive_range_not_supported(tmp_path, serve_over_http_no_ranges):
    """Test that a server without support for HTTP range requests results in a clear error message."""
    filepath_archive = tmp_path / 'archive.aiida'
    SqliteZipBackend.initialise(SqliteZipBackend.create_profile(filepath_archive))

    url = f'{serve_over_http_no_ranges}/archive.aiida'
    with pytest.raises(UnreachableStorage, match='does not support HTTP range requests'):
        open_remote_zip(url)


def test_remote_archive_timeout(monkeypatch):
    """Test that ``open_remote_zip`` passes the ``storage.remote_archive_timeout`` option to ``RemoteZip``."""
    from aiida.manage import get_config_option

    captured = {}

    def mock_remote_zip(url, **kwargs):
        captured.update(kwargs)
        raise zipfile.BadZipFile(url)

    monkeypatch.setattr('remotezip.RemoteZip', mock_remote_zip)

    with pytest.raises(Exception, match='not a valid zip file'):
        open_remote_zip('https://example.com/archive.aiida')
    assert captured['timeout'] == get_config_option('storage.remote_archive_timeout')

    with pytest.raises(Exception, match='not a valid zip file'):
        open_remote_zip('https://example.com/archive.aiida', timeout=1.5)
    assert captured['timeout'] == 1.5


def test_folder_repository(tmp_path):
    """Test reading repository files from an unpacked (folder-format) archive.

    This is a regression test for ``FolderBackendRepository.open``, which used to pass an ``encoding`` argument to a
    binary-mode ``open`` call, raising a ``ValueError`` for any file access.
    """
    filepath_archive = tmp_path / 'archive.aiida'
    SqliteZipBackend.initialise(SqliteZipBackend.create_profile(filepath_archive))

    content = b'some repository content'
    key = hashlib.sha256(content).hexdigest()
    with zipfile.ZipFile(filepath_archive, 'a') as zip_handle:
        zip_handle.writestr(f'repo/{key}', content)

    # Unpack the archive to a folder and create a backend directly from the folder
    dirpath_archive = tmp_path / 'unpacked'
    with zipfile.ZipFile(filepath_archive) as zip_handle:
        zip_handle.extractall(dirpath_archive)

    backend = SqliteZipBackend(SqliteZipBackend.create_profile(dirpath_archive))
    repository = backend.get_repository()
    assert isinstance(repository, FolderBackendRepository)

    assert list(repository.list_objects()) == [key]
    assert repository.has_object(key)
    with repository.open(key) as handle:
        assert handle.read() == content

    backend.close()


def test_backend_cleanup_on_garbage_collection(tmp_path):
    """Test that the temporary database file is deleted when an unclosed backend is garbage collected."""
    filepath_archive = tmp_path / 'archive.aiida'
    SqliteZipBackend.initialise(SqliteZipBackend.create_profile(filepath_archive))

    backend = SqliteZipBackend(SqliteZipBackend.create_profile(filepath_archive))
    backend.get_session()
    db_file = backend._resources.db_file
    assert db_file is not None and db_file.exists()

    del backend
    gc.collect()
    assert not db_file.exists()


def test_initialise_remote_migration_needed(monkeypatch):
    """Test that ``initialise`` raises for a remote archive that is not at the target version."""
    profile = SqliteZipBackend.create_profile('https://example.com/archive.aiida')

    monkeypatch.setattr(
        'aiida.storage.sqlite_zip.backend.SqliteZipBackend.get_current_archive_version',
        lambda inpath: '0.9',
    )

    with pytest.raises(StorageMigrationError, match='cannot be migrated in place'):
        SqliteZipBackend.initialise(profile)


def test_initialise_remote_reset():
    """Test that ``initialise`` with ``reset=True`` raises for a remote archive."""
    profile = SqliteZipBackend.create_profile('https://example.com/archive.aiida')

    with pytest.raises(ReadOnlyError, match='cannot reset a remote archive'):
        SqliteZipBackend.initialise(profile, reset=True)


@pytest.fixture
def cache_dirpath(tmp_path, monkeypatch):
    """Redirect the ``sqlite_zip`` database cache to a temporary directory and return its path."""
    dirpath = tmp_path / 'cache'
    monkeypatch.setattr('aiida.storage.sqlite_zip.cache.get_cache_dirpath', lambda: dirpath)
    return dirpath


@pytest.fixture
def filepath_archive(tmp_path):
    """Return the filepath of an initialised, empty archive."""
    filepath = tmp_path / 'archive.aiida'
    SqliteZipBackend.initialise(SqliteZipBackend.create_profile(filepath))
    return filepath


def test_cache_use_cache(filepath_archive, cache_dirpath):
    """Test that with ``use_cache`` the database is cached, and subsequent loads use the cache."""
    profile = SqliteZipBackend.create_profile(filepath_archive)
    profile.storage_config['use_cache'] = True

    backend = SqliteZipBackend(profile)
    backend.get_session()
    assert backend._resources.db_file is None, 'the database should have been cached, not extracted to a temporary file'
    filepaths_cached = list(cache_dirpath.iterdir())
    assert len(filepaths_cached) == 1
    backend.close()

    # The cached file survives closing the backend and is reused, not rewritten, by a second backend
    assert filepaths_cached[0].is_file()
    mtime = filepaths_cached[0].stat().st_mtime_ns

    backend = SqliteZipBackend(profile)
    backend.get_session()
    assert backend._resources.db_file is None
    assert filepaths_cached[0].stat().st_mtime_ns == mtime
    backend.close()


def test_cache_default_disabled(filepath_archive, cache_dirpath):
    """Test that without ``use_cache`` the database is extracted to a temporary file and the cache is not written."""
    backend = SqliteZipBackend(SqliteZipBackend.create_profile(filepath_archive))
    backend.get_session()
    assert backend._resources.db_file is not None
    assert not cache_dirpath.exists()
    backend.close()


def test_cache_read_always(filepath_archive, cache_dirpath):
    """Test that an existing cache entry is used even when ``use_cache`` is not set."""
    profile = SqliteZipBackend.create_profile(filepath_archive)
    SqliteZipBackend.refresh_cache(profile)

    backend = SqliteZipBackend(SqliteZipBackend.create_profile(filepath_archive))
    backend.get_session()
    assert backend._resources.db_file is None, 'the cached database should have been used'
    backend.close()


def test_initialise_use_cache(tmp_path, cache_dirpath):
    """Test that ``initialise`` with ``use_cache`` populates the cache and records the ``cached_database``."""
    profile = SqliteZipBackend.create_profile(tmp_path / 'archive.aiida')
    profile.storage_config['use_cache'] = True
    SqliteZipBackend.initialise(profile)

    filename = profile.storage_config['cached_database']
    assert (cache_dirpath / filename).is_file()


def test_cache_pointer_refill(filepath_archive, cache_dirpath):
    """Test that a missing cache file is repopulated for a profile that records a ``cached_database``."""
    profile = SqliteZipBackend.create_profile(filepath_archive)
    filename = SqliteZipBackend.refresh_cache(profile)

    (cache_dirpath / filename).unlink()

    backend = SqliteZipBackend(profile)
    backend.get_session()
    assert (cache_dirpath / filename).is_file()
    assert backend._resources.db_file is None
    backend.close()


def test_cache_pointer_mismatch(filepath_archive, cache_dirpath):
    """Test that a recorded ``cached_database`` that does not correspond to the archive content raises."""
    from aiida.common.exceptions import ConfigurationError

    profile = SqliteZipBackend.create_profile(filepath_archive)
    profile.storage_config['cached_database'] = '00000000-1.sqlite3'

    backend = SqliteZipBackend(profile)
    with pytest.raises(ConfigurationError, match=r'.*verdi profile cache-refresh.*'):
        backend.get_session()
    backend.close()


def test_cache_force(filepath_archive, tmp_path, cache_dirpath):
    """Test that with ``force_cache`` the recorded cached database is used without accessing the archive."""
    profile = SqliteZipBackend.create_profile(filepath_archive)
    SqliteZipBackend.refresh_cache(profile)
    profile.storage_config['force_cache'] = True

    # Move the archive away: with ``force_cache`` it should not be accessed at all
    filepath_archive.rename(tmp_path / 'moved-away.aiida')

    backend = SqliteZipBackend(profile)
    backend.get_session()
    assert backend._resources.db_file is None
    backend.close()


def test_cache_force_no_pointer(filepath_archive, cache_dirpath):
    """Test that ``force_cache`` raises if the profile does not record a ``cached_database``."""
    from aiida.common.exceptions import ConfigurationError

    profile = SqliteZipBackend.create_profile(filepath_archive)
    profile.storage_config['force_cache'] = True

    backend = SqliteZipBackend(profile)
    with pytest.raises(ConfigurationError, match=r'.*does not record one.*'):
        backend.get_session()
    backend.close()


def test_cache_force_missing_file(filepath_archive, cache_dirpath):
    """Test that ``force_cache`` raises if the recorded cached database file does not exist."""
    from aiida.common.exceptions import UnreachableStorage

    profile = SqliteZipBackend.create_profile(filepath_archive)
    filename = SqliteZipBackend.refresh_cache(profile)
    profile.storage_config['force_cache'] = True

    (cache_dirpath / filename).unlink()

    backend = SqliteZipBackend(profile)
    with pytest.raises(UnreachableStorage, match=r'.*does not exist.*'):
        backend.get_session()
    backend.close()


def test_cache_entry_read_only(filepath_archive, cache_dirpath):
    """Test that a session over a cached database cannot write to it.

    Cache entries are shared between all profiles and processes whose archives have the same content, so a stray
    write must not be able to corrupt them.
    """
    from sqlalchemy import text
    from sqlalchemy.exc import OperationalError

    profile = SqliteZipBackend.create_profile(filepath_archive)
    profile.storage_config['use_cache'] = True

    backend = SqliteZipBackend(profile)
    session = backend.get_session()
    with pytest.raises(OperationalError, match='readonly database'):
        session.execute(text('CREATE TABLE sneaky (id INTEGER)'))
    session.rollback()
    backend.close()


def test_cache_force_stale_version(filepath_archive, cache_dirpath):
    """Test that ``force_cache`` raises if the cached database was recorded for a different archive schema version."""
    from aiida.common.exceptions import IncompatibleStorageSchema

    profile = SqliteZipBackend.create_profile(filepath_archive)
    SqliteZipBackend.refresh_cache(profile)
    assert profile.storage_config['cached_database_version'] == SqliteZipBackend.version_head()

    # Simulate an aiida-core upgrade since the cache was recorded, i.e. the recorded version is no longer current
    profile.storage_config['cached_database_version'] = '0.1'
    profile.storage_config['force_cache'] = True

    backend = SqliteZipBackend(profile)
    with pytest.raises(IncompatibleStorageSchema, match=r'.*verdi profile cache-refresh.*'):
        backend.get_session()
    backend.close()


def test_cache_remote(tmp_path, cache_dirpath, serve_over_http):
    """Test caching of the database of a remote archive."""
    filepath_archive = tmp_path / 'archive.aiida'
    SqliteZipBackend.initialise(SqliteZipBackend.create_profile(filepath_archive))

    url = f'{serve_over_http}/archive.aiida'
    profile = SqliteZipBackend.create_profile(url)
    profile.storage_config['use_cache'] = True

    backend = SqliteZipBackend(profile)
    backend.get_session()
    assert backend._resources.db_file is None
    assert len(list(cache_dirpath.iterdir())) == 1
    backend.close()

    backend = SqliteZipBackend(profile)
    backend.get_session()
    assert backend._resources.db_file is None
    backend.close()


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
