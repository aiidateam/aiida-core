# -*- coding: utf-8 -*-
"""Tests for :mod:`aiida.storage.sqlite_dos.backend`."""
import pathlib

import pytest

from aiida.storage.sqlite_dos.backend import SqliteDosStorage


@pytest.mark.usefixtures('chdir_tmp_path')
def test_configuration():
    """Test :class:`aiida.storage.sqlite_dos.backend.SqliteDosStorage.Configuration`."""
    filepath = pathlib.Path.cwd() / 'archive.aiida'
    configuration = SqliteDosStorage.Configuration(filepath=filepath.name)
    assert pathlib.Path(configuration.filepath).is_absolute()
