"""Tests for :mod:`aiida.storage.sqlite_dos.backend`."""

import pathlib

import pytest
from aiida.storage.sqlite_dos.backend import SqliteDosStorage


@pytest.mark.usefixtures('chdir_tmp_path')
def test_model():
    """Test :class:`aiida.storage.sqlite_dos.backend.SqliteDosStorage.Model`."""
    filepath = pathlib.Path.cwd() / 'archive.aiida'
    model = SqliteDosStorage.Model(filepath=filepath.name)
    assert pathlib.Path(model.filepath).is_absolute()
