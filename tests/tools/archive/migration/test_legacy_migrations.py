###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test archive file migration from old export versions to the newest"""

import pytest

from aiida import orm
from aiida.common.exceptions import StorageMigrationError
from aiida.tools.archive import ArchiveFormatSqlZip
from tests.utils.archives import get_archive_file

# archives to test migration against
# name, node count
ARCHIVE_DATA = {
    '0.4': ('export_v0.4.aiida', 27),
    '0.5': ('export_v0.5_manual.aiida', 27),
    '0.6': ('export_v0.6_manual.aiida', 27),
    '0.7': ('export_v0.7_manual.aiida', 27),
    '0.8': ('export_v0.8_manual.aiida', 27),
    '0.9': ('export_v0.9_manual.aiida', 27),
}

# mapping of uuid to repository content for simple archive
NODE_REPOS = {
    'd60b7c8a-4808-4f69-a72c-670df4d63700': {'.gitignore'},
    '9d73cf46-b8df-4fbb-af66-ac797194c24f': {'forces.npy', 'energy.npy', 'energy_accuracy.npy'},
    '3b429fd4-601c-4473-add5-7cbb76cf38cb': {
        '.aiida',
        '.aiida/calcinfo.json',
        'pseudo',
        'pseudo/.gitignore',
        'aiida.in',
        '_aiidasubmit.sh',
        '.aiida/job_tmpl.json',
        'out',
        '.gitignore',
        'out/.gitignore',
    },
    'c03f49a0-f1b4-4792-bf7b-7a5330074dc1': {'.gitignore'},
    '4ff5a907-78a6-4b40-99b4-c69b51f0c3b0': {'.gitignore'},
    '37007e25-f37c-47dd-b2af-b17748274e6f': {'.gitignore'},
    'b4197406-cf07-4c89-a6da-a1f6ec75ab80': {'.gitignore'},
    'c1879cbe-8f6f-4343-b3f7-df8ecbd4d403': {'.gitignore'},
    'f75aaf40-f952-488c-be84-488a183a03d4': {
        'K00003',
        'K00001/eigenval.xml',
        'K00004/eigenval.xml',
        'K00002',
        '_scheduler-stderr.txt',
        'K00001',
        '_scheduler-stdout.txt',
        'K00004',
        'data-file.xml',
        'aiida.out',
        'K00003/eigenval.xml',
        'K00002/eigenval.xml',
    },
    'e5098e78-8430-4e2d-a494-357686eb63dc': {'.gitignore'},
}


@pytest.mark.parametrize('archive_name', ('export_0.4_simple.aiida', 'export_0.4_simple.tar.gz'))
def test_full_migration(tmp_path, core_archive, archive_name):
    """Test a migration from the first to newest archive version."""
    filepath_archive = get_archive_file(archive_name, **core_archive)
    archive_format = ArchiveFormatSqlZip()

    assert archive_format.read_version(filepath_archive) == '0.4'

    new_archive = tmp_path / 'out.aiida'
    archive_format.migrate(filepath_archive, new_archive, archive_format.latest_version)
    assert archive_format.read_version(new_archive) == archive_format.latest_version
    with archive_format.open(new_archive, 'r') as reader:
        # test all nodes were migrated
        assert reader.querybuilder().append(orm.Node).count() == 10
        # test all repository files were migrated
        repository = reader.get_backend().get_repository()
        assert sum(1 for _ in repository.list_objects()) == 16
        # test all node repositories were migrated
        uuids = reader.querybuilder().append(orm.Node, project='uuid').all(flat=True)
        assert set(uuids) == set(NODE_REPOS)
        assert {
            uuid: {p.as_posix() for p in reader.get(orm.Node, uuid=uuid).base.repository.glob()} for uuid in uuids
        } == NODE_REPOS
        # test we can read a node repository file
        node = reader.get(orm.Node, uuid='3b429fd4-601c-4473-add5-7cbb76cf38cb')
        content = node.base.repository.get_object_content('_aiidasubmit.sh').encode('utf8')
        assert content.startswith(b'#!/bin/bash')


def test_partial_migrations(core_archive, tmp_path):
    """Test migrations from a specific version (0.5) to other versions."""
    filepath_archive = get_archive_file('export_0.5_simple.aiida', **core_archive)
    archive_format = ArchiveFormatSqlZip()

    assert archive_format.read_version(filepath_archive) == '0.5'

    new_archive = tmp_path / 'out.aiida'

    with pytest.raises(StorageMigrationError, match='Unknown target version'):
        archive_format.migrate(filepath_archive, new_archive, 0.2)

    with pytest.raises(StorageMigrationError, match='No migration pathway available'):
        archive_format.migrate(filepath_archive, new_archive, '0.4')

    archive_format.migrate(filepath_archive, new_archive, '0.7')
    assert archive_format.read_version(new_archive) == '0.7'


def test_no_node_migration(tmp_path, core_archive):
    """Test migration of archive file that has no Node entities."""
    filepath_archive = get_archive_file('export_0.4_no_Nodes.aiida', **core_archive)
    archive_format = ArchiveFormatSqlZip()
    new_archive = tmp_path / 'output_file.aiida'

    # Perform the migration
    archive_format.migrate(filepath_archive, new_archive, archive_format.latest_version)
    assert archive_format.read_version(new_archive) == archive_format.latest_version

    # Check known entities
    with archive_format.open(new_archive, 'r') as reader:
        assert reader.querybuilder().append(orm.Node).count() == 0
        computer_query = reader.querybuilder().append(orm.Computer, project=['uuid'])
        assert computer_query.all(flat=True) == ['4f33c6fd-b624-47df-9ffb-a58f05d323af']
        user_query = reader.querybuilder().append(orm.User, project=['email'])
        assert set(user_query.all(flat=True)) == {'aiida@localhost'}


@pytest.mark.parametrize('version', ['0.0', '0.1.0', '0.99'])
def test_wrong_versions(core_archive, tmp_path, version):
    """Test correct errors are raised if archive files have wrong version numbers"""
    filepath_archive = get_archive_file('export_0.4_simple.aiida', **core_archive)
    archive_format = ArchiveFormatSqlZip()
    new_archive = tmp_path / 'out.aiida'
    with pytest.raises(StorageMigrationError, match='Unknown target version'):
        archive_format.migrate(filepath_archive, new_archive, version)
    assert not new_archive.exists()


@pytest.mark.parametrize('filename,nodes', ARCHIVE_DATA.values(), ids=ARCHIVE_DATA.keys())
def test_migrate_to_newest(external_archive, tmp_path, filename, nodes):
    """Test migrations from old archives to newest version."""
    filepath_archive = get_archive_file(filename, **external_archive)
    archive_format = ArchiveFormatSqlZip()

    new_archive = tmp_path / 'out.aiida'

    archive_format.migrate(filepath_archive, new_archive, archive_format.latest_version)
    assert archive_format.read_version(new_archive) == archive_format.latest_version

    with archive_format.open(new_archive, 'r') as reader:
        # count nodes
        archive_node_count = reader.querybuilder().append(orm.Node).count()
        assert archive_node_count == nodes

        # Verify that CalculationNodes have non-empty attribute dictionaries
        calc_query = reader.querybuilder().append(orm.CalculationNode, project=['attributes'])
        for [attributes] in calc_query.iterall():
            assert isinstance(attributes, dict)
            assert len(attributes) > 0

        # Verify that the StructureData nodes maintained their (same) label, cell, and kinds
        struct_query = reader.querybuilder().append(orm.StructureData, project=['label', 'attributes.cell'])
        assert struct_query.count() == 2
        for [label, cell] in struct_query.all():
            assert label == ''
            assert cell == [[4, 0, 0], [0, 4, 0], [0, 0, 4]]

        known_kinds = [
            {'name': 'Ba', 'mass': 137.327, 'weights': [1], 'symbols': ['Ba']},
            {'name': 'Ti', 'mass': 47.867, 'weights': [1], 'symbols': ['Ti']},
            {'name': 'O', 'mass': 15.9994, 'weights': [1], 'symbols': ['O']},
        ]
        kind_query = reader.querybuilder().append(orm.StructureData, project=['attributes.kinds'])
        for kinds in kind_query.all(flat=True):
            assert len(kinds) == len(known_kinds)
            for kind in kinds:
                assert kind in known_kinds

        # Check that there is a StructureData that is an input of a CalculationNode
        builder = reader.querybuilder()
        builder.append(orm.StructureData, tag='structure')
        builder.append(orm.CalculationNode, with_incoming='structure', project=['id'])
        assert len(builder.all()) > 0

        # Check that there is a RemoteData that is the output of a CalculationNode
        builder = reader.querybuilder()
        builder.append(orm.CalculationNode, tag='parent')
        builder.append(orm.RemoteData, with_incoming='parent', project=['id'])
        assert len(builder.all()) > 0
