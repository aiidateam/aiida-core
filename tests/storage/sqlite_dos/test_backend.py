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


def test_archive_import(aiida_config, aiida_profile_factory):
    """Test that archives can be imported."""
    from aiida.orm import Node, QueryBuilder
    from aiida.tools.archive.imports import import_archive

    from tests.utils.archives import get_archive_file

    with aiida_profile_factory(aiida_config, storage_backend='core.sqlite_dos'):
        assert QueryBuilder().append(Node).count() == 0
        import_archive(get_archive_file('calcjob/arithmetic.add.aiida'))
        assert QueryBuilder().append(Node).count() > 0
