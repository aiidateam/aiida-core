###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test using the archive backend directly."""

import pytest

from aiida import orm
from aiida.common.exceptions import NotExistent
from aiida.orm.implementation import StorageBackend
from aiida.tools.archive.abstract import ArchiveReaderAbstract
from aiida.tools.archive.implementations.sqlite_zip.main import ArchiveFormatSqlZip
from tests.utils.archives import get_archive_file


@pytest.fixture()
def archive():
    """Yield the archive open in read mode."""
    archive_format = ArchiveFormatSqlZip()
    filepath_archive = get_archive_file(
        f'export_{archive_format.latest_version}_simple.aiida', filepath='export/migrate'
    )
    with archive_format.open(filepath_archive, 'r') as reader:
        yield reader


def test_get_backend(archive: ArchiveReaderAbstract):
    """Test retrieving the backend"""
    backend = archive.get_backend()
    assert isinstance(backend, StorageBackend)


def test_get(archive: ArchiveReaderAbstract):
    """Test retrieving a Node"""
    with pytest.raises(NotExistent):
        archive.get(orm.Node, uuid='xyz')
    node = archive.get(orm.Node, uuid='d60b7c8a-4808-4f69-a72c-670df4d63700')
    assert isinstance(node, orm.Node)
    assert node.uuid == 'd60b7c8a-4808-4f69-a72c-670df4d63700'


def test_querybuilder(archive: ArchiveReaderAbstract):
    """Test querying the archive"""
    qbuilder = archive.querybuilder()
    assert isinstance(qbuilder, orm.QueryBuilder)
    assert qbuilder.append(orm.Node).count() == 10


def test_graph(archive: ArchiveReaderAbstract):
    """Test creating a provenance graph visualisation."""
    graph = archive.graph()
    graph.recurse_descendants('3b429fd4-601c-4473-add5-7cbb76cf38cb')
    assert 'digraph' in graph.graphviz.source
