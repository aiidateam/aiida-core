"""Tests for :mod:`aiida.storage.sqlite_dos.backend`."""

import pathlib
from unittest.mock import MagicMock

import pytest

from aiida.storage.sqlite_dos.backend import FILENAME_CONTAINER, FILENAME_DATABASE, SqliteDosStorage


@pytest.mark.usefixtures('chdir_tmp_path')
def test_model():
    """Test :class:`aiida.storage.sqlite_dos.backend.SqliteDosStorage.Model`."""
    filepath = pathlib.Path.cwd() / 'archive.aiida'
    model = SqliteDosStorage.Model(filepath=filepath.name)
    assert pathlib.Path(model.filepath).is_absolute()


def test_archive_import(aiida_config, aiida_profile_factory):
    """Test that archives can be imported."""
    from aiida.orm import Node, QueryBuilder
    from aiida.tools.archive.imports import import_archive
    from tests.utils.archives import get_archive_file

    with aiida_profile_factory(aiida_config, storage_backend='core.sqlite_dos'):
        assert QueryBuilder().append(Node).count() == 0
        import_archive(get_archive_file('calcjob/arithmetic.add.aiida'))
        assert QueryBuilder().append(Node).count() > 0


def test_backup(aiida_config, aiida_profile_factory, tmp_path, manager):
    """Test the backup implementation."""
    with aiida_profile_factory(aiida_config, storage_backend='core.sqlite_dos'):
        storage = manager.get_profile_storage()
        storage.backup(str(tmp_path))
        filepath_last = tmp_path / 'last-backup'
        assert (tmp_path / 'config.json').exists()
        assert filepath_last.is_symlink()
        dirpath_backup = filepath_last.resolve()
        assert (dirpath_backup / FILENAME_DATABASE).exists()
        assert (dirpath_backup / FILENAME_CONTAINER).exists()


def test_initialise_version_check(tmp_path, monkeypatch):
    """Test :meth:`aiida.storage.sqlite_zip.backend.SqliteZipBackend.create_profile`
    only if calls on validate_sqlite_version."""

    mock_ = MagicMock()
    monkeypatch.setattr('aiida.storage.sqlite_dos.backend.validate_sqlite_version', mock_)

    # Here, we don't care about functionality of initialise itself, but only that it calls validate_sqlite_version.
    with pytest.raises(AttributeError):
        SqliteDosStorage.initialise('')
    mock_.assert_called_once()
