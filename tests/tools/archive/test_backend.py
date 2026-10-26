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


@pytest.fixture()
def archive(archive_head):
    """Yield the archive open in read mode."""
    archive_format = ArchiveFormatSqlZip()
    with archive_format.open(archive_head, 'r') as reader:
        yield reader


def test_get_backend(archive: ArchiveReaderAbstract):
    """Test retrieving the backend"""
    backend = archive.get_backend()
    assert isinstance(backend, StorageBackend)


def test_get(archive: ArchiveReaderAbstract):
    """Test retrieving a Node"""
    with pytest.raises(NotExistent):
        archive.get(orm.Node, uuid='xyz')
    (uuid,) = archive.querybuilder().append(orm.CalcJobNode, project='uuid').all(flat=True)
    node = archive.get(orm.Node, uuid=uuid)
    assert isinstance(node, orm.Node)
    assert node.uuid == uuid


def test_querybuilder(archive: ArchiveReaderAbstract):
    """Test querying the archive"""
    qbuilder = archive.querybuilder()
    assert isinstance(qbuilder, orm.QueryBuilder)
    assert qbuilder.append(orm.Node).count() == 10


def test_graph(archive: ArchiveReaderAbstract):
    """Test creating a provenance graph visualisation."""
    (uuid,) = archive.querybuilder().append(orm.CalcJobNode, project='uuid').all(flat=True)
    graph = archive.graph()
    graph.recurse_descendants(uuid)
    assert 'digraph' in graph.graphviz.source
