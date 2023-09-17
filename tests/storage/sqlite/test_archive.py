# -*- coding: utf-8 -*-
"""Test export and import of AiiDA archives to/from a temporary profile."""
from pathlib import Path

from aiida import orm
from aiida.storage.sqlite_temp import SqliteTempBackend
from aiida.tools.archive import create_archive, import_archive


def test_basic(tmp_path):
    """Test the creation of an archive and re-import."""
    filename = Path(tmp_path / 'export.aiida')

    # generate a temporary backend
    profile1 = SqliteTempBackend.create_profile(repo_path=str(tmp_path / 'repo1'))
    backend1 = SqliteTempBackend(profile1)

    # add simple node
    dict_data = {'key1': 'value1'}
    node = orm.Dict(dict_data, backend=backend1).store()
    # add a comment to the node
    node.base.comments.add('test comment', backend1.default_user)
    # add node with repository data
    path = Path(tmp_path / 'test.txt')
    text_data = 'test'
    path.write_text(text_data, encoding='utf-8')
    orm.SinglefileData(str(path), backend=backend1).store()

    # export to archive
    create_archive(None, backend=backend1, filename=filename)

    # create a new temporary backend and import
    profile2 = SqliteTempBackend.create_profile(repo_path=str(tmp_path / 'repo2'))
    backend2 = SqliteTempBackend(profile2)
    import_archive(filename, backend=backend2)

    # check that the nodes are there
    assert orm.QueryBuilder(backend=backend2).append(orm.Data).count() == 2

    # check that we can retrieve the attributes and comment data
    node = orm.QueryBuilder(backend=backend2).append(orm.Dict).first(flat=True)
    assert node.get_dict() == dict_data
    assert len(node.base.comments.all()) == 1

    # check that we can retrieve the repository data
    node = orm.QueryBuilder(backend=backend2).append(orm.SinglefileData).first(flat=True)
    assert node.get_content() == text_data
