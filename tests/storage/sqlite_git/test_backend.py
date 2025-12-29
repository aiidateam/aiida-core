"""Tests for :mod:`aiida.storage.sqlite_git.backend`."""

import pathlib
from unittest.mock import MagicMock

import pytest

from aiida.storage.sqlite_git.backend import FILENAME_DATABASE, FILENAME_GIT_REPO, SqliteGitStorage


@pytest.mark.usefixtures('chdir_tmp_path')
def test_model():
    """Test :class:`aiida.storage.sqlite_git.backend.SqliteGitStorage.Model`."""
    filepath = pathlib.Path.cwd() / 'archive.aiida'
    model = SqliteGitStorage.Model(filepath=filepath.name)
    assert pathlib.Path(model.filepath).is_absolute()


@pytest.mark.skip(reason='Archive import not compatible with SHA-1 keys (Git backend uses SHA-1, archives use SHA-256)')
def test_archive_import(aiida_config, aiida_profile_factory):
    """Test that archives can be imported.

    Note: This test is skipped because the Git backend uses SHA-1 keys while existing
    AiiDA archives use SHA-256 keys. This is a known limitation of the Git backend.
    Archives created with sqlite_git backend would need to be imported to sqlite_git
    profiles (not tested here).
    """
    from aiida.orm import Node, QueryBuilder
    from aiida.tools.archive.imports import import_archive
    from tests.utils.archives import get_archive_file

    with aiida_profile_factory(aiida_config, storage_backend='core.sqlite_git'):
        assert QueryBuilder().append(Node).count() == 0
        import_archive(get_archive_file('calcjob/arithmetic.add.aiida'))
        assert QueryBuilder().append(Node).count() > 0


def test_git_repository(aiida_config, aiida_profile_factory, manager):
    """Test that the Git repository backend is used."""
    from aiida.repository.backend import GitRepositoryBackend

    with aiida_profile_factory(aiida_config, storage_backend='core.sqlite_git'):
        storage = manager.get_profile_storage()
        repo = storage.get_repository()

        # Verify it's a GitRepositoryBackend
        assert isinstance(repo, GitRepositoryBackend)

        # Verify it uses SHA-1 keys
        assert repo.key_format == 'sha1'

        # Verify repository is initialized
        assert repo.is_initialised
        assert repo.uuid is not None


def test_git_repository_storage(aiida_config, aiida_profile_factory, manager):
    """Test that objects can be stored and retrieved from Git repository."""
    import io
    from aiida.orm import Data

    with aiida_profile_factory(aiida_config, storage_backend='core.sqlite_git'):
        storage = manager.get_profile_storage()
        repo = storage.get_repository()

        # Store a test object directly in the repository
        content = b'Test content for Git repository'
        handle = io.BytesIO(content)
        key = repo.put_object_from_filelike(handle)

        # Verify it's a SHA-1 key (40 hex characters)
        assert len(key) == 40
        assert all(c in '0123456789abcdef' for c in key)

        # Verify we can retrieve the content
        with repo.open(key) as stream:
            retrieved = stream.read()
            assert retrieved == content

        # Test with actual AiiDA Data node
        node = Data()
        node.label = 'test_git_node'
        node.store()

        # Verify the node was stored
        assert node.is_stored
        assert node.pk is not None


def test_storage_paths(aiida_config, aiida_profile_factory, manager):
    """Test that storage paths are correctly configured."""
    with aiida_profile_factory(aiida_config, storage_backend='core.sqlite_git'):
        storage = manager.get_profile_storage()

        # Verify database path exists
        assert storage.filepath_database.exists()
        assert storage.filepath_database.name == FILENAME_DATABASE

        # Verify git repository path exists
        assert storage.filepath_git_repo.exists()
        assert storage.filepath_git_repo.name == FILENAME_GIT_REPO

        # Verify git repository has correct structure
        assert (storage.filepath_git_repo / 'objects').exists()
        assert (storage.filepath_git_repo / 'refs').exists()


def test_initialise_version_check(tmp_path, monkeypatch):
    """Test :meth:`aiida.storage.sqlite_git.backend.SqliteGitStorage.initialise`
    calls validate_sqlite_version."""

    mock_ = MagicMock()
    monkeypatch.setattr('aiida.storage.sqlite_git.backend.validate_sqlite_version', mock_)

    # Here, we don't care about functionality of initialise itself, but only that it calls validate_sqlite_version.
    with pytest.raises(AttributeError):
        SqliteGitStorage.initialise('')
    mock_.assert_called_once()
