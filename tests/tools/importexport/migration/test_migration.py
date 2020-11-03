# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test archive file migration from old export versions to the newest"""
# pylint: disable=no-self-use
import pytest

from aiida import orm
from aiida.tools.importexport import detect_archive_type, get_migrator
from aiida.tools.importexport import import_data, ArchiveMigrationError, EXPORT_VERSION as newest_version
from aiida.tools.importexport.archive.migrations.utils import verify_metadata_version

from tests.utils.archives import get_archive_file, read_json_files

# archives to test migration against
# name, node count
ARCHIVE_DATA = {
    '0.2': ('export_v0.2.aiida', 25),
    '0.3': ('export_v0.3.aiida', 25),
    '0.4': ('export_v0.4.aiida', 27),
    '0.5': ('export_v0.5_manual.aiida', 27),
    '0.6': ('export_v0.6_manual.aiida', 27),
    '0.7': ('export_v0.7_manual.aiida', 27),
    '0.8': ('export_v0.8_manual.aiida', 27),
    '0.9': ('export_v0.9_manual.aiida', 27),
}


@pytest.mark.usefixtures('clear_database_before_test')
class TestExportFileMigration:
    """Test archive file migrations"""

    def test_full_migration(self, tmp_path, core_archive):
        """Test a migration from the first to newest archive version."""

        filepath_archive = get_archive_file('export_v0.1_simple.aiida', **core_archive)

        metadata = read_json_files(filepath_archive, names=['metadata.json'])[0]
        verify_metadata_version(metadata, version='0.1')

        migrator_cls = get_migrator(detect_archive_type(filepath_archive))
        migrator = migrator_cls(filepath_archive)

        migrator.migrate(newest_version, tmp_path / 'out.aiida')
        assert detect_archive_type(tmp_path / 'out.aiida') == 'zip'
        metadata = read_json_files(tmp_path / 'out.aiida', names=['metadata.json'])[0]
        verify_metadata_version(metadata, version=newest_version)

    def test_tar_migration(self, tmp_path, core_archive):
        """Test a migration using a tar compressed in/out file."""

        filepath_archive = get_archive_file('export_v0.2_simple.tar.gz', **core_archive)

        metadata = read_json_files(filepath_archive, names=['metadata.json'])[0]
        verify_metadata_version(metadata, version='0.2')

        migrator_cls = get_migrator(detect_archive_type(filepath_archive))
        migrator = migrator_cls(filepath_archive)

        migrator.migrate(newest_version, tmp_path / 'out.aiida', out_compression='tar.gz')
        assert detect_archive_type(tmp_path / 'out.aiida') == 'tar.gz'
        metadata = read_json_files(tmp_path / 'out.aiida', names=['metadata.json'])[0]
        verify_metadata_version(metadata, version=newest_version)

    def test_partial_migrations(self, core_archive, tmp_path):
        """Test migrations from a specific version (0.3) to other versions."""
        filepath_archive = get_archive_file('export_v0.3_simple.aiida', **core_archive)

        metadata = read_json_files(filepath_archive, names=['metadata.json'])[0]
        verify_metadata_version(metadata, version='0.3')

        migrator_cls = get_migrator(detect_archive_type(filepath_archive))
        migrator = migrator_cls(filepath_archive)

        with pytest.raises(TypeError, match='version must be a string'):
            migrator.migrate(0.2, tmp_path / 'v02.aiida')

        with pytest.raises(ArchiveMigrationError, match='No migration pathway available'):
            migrator.migrate('0.2', tmp_path / 'v02.aiida')

        # same version migration
        out_path = migrator.migrate('0.3', tmp_path / 'v03.aiida')
        # if no migration performed the output path is None
        assert out_path is None

        # newer version migration
        migrator.migrate('0.5', tmp_path / 'v05.aiida')
        assert (tmp_path / 'v05.aiida').exists()

        metadata = read_json_files(tmp_path / 'v05.aiida', names=['metadata.json'])[0]
        verify_metadata_version(metadata, version='0.5')

    def test_no_node_migration(self, tmp_path, external_archive):
        """Test migration of archive file that has no Node entities."""
        input_file = get_archive_file('export_v0.3_no_Nodes.aiida', **external_archive)
        output_file = tmp_path / 'output_file.aiida'

        migrator_cls = get_migrator(detect_archive_type(input_file))
        migrator = migrator_cls(input_file)

        # Perform the migration
        migrator.migrate(newest_version, output_file)

        # Load the migrated file
        import_data(output_file)

        # Check known entities
        assert orm.QueryBuilder().append(orm.Node).count() == 0
        computer_query = orm.QueryBuilder().append(orm.Computer, project=['uuid'])
        assert computer_query.all(flat=True) == ['4f33c6fd-b624-47df-9ffb-a58f05d323af']
        user_query = orm.QueryBuilder().append(orm.User, project=['email'])
        assert set(user_query.all(flat=True)) == {orm.User.objects.get_default().email, 'aiida@localhost'}

    @pytest.mark.parametrize('version', ['0.0', '0.1.0', '0.99'])
    def test_wrong_versions(self, core_archive, tmp_path, version):
        """Test correct errors are raised if archive files have wrong version numbers"""
        filepath_archive = get_archive_file('export_v0.1_simple.aiida', **core_archive)
        migrator_cls = get_migrator(detect_archive_type(filepath_archive))
        migrator = migrator_cls(filepath_archive)

        with pytest.raises(ArchiveMigrationError, match='No migration pathway available'):
            migrator.migrate(version, tmp_path / 'out.aiida')
        assert not (tmp_path / 'out.aiida').exists()

    @pytest.mark.parametrize('filename,nodes', ARCHIVE_DATA.values(), ids=ARCHIVE_DATA.keys())
    def test_migrate_to_newest(self, external_archive, tmp_path, filename, nodes):
        """Test migrations from old archives to newest version."""
        filepath_archive = get_archive_file(filename, **external_archive)

        out_path = tmp_path / 'out.aiida'

        migrator_cls = get_migrator(detect_archive_type(filepath_archive))
        migrator = migrator_cls(filepath_archive)
        out_path = migrator.migrate(newest_version, out_path) or filepath_archive

        metadata = read_json_files(out_path, names=['metadata.json'])[0]
        verify_metadata_version(metadata, version=newest_version)

        # Load the migrated file
        import_data(out_path)

        # count nodes
        archive_node_count = orm.QueryBuilder().append(orm.Node).count()
        assert archive_node_count == nodes

        # Verify that CalculationNodes have non-empty attribute dictionaries
        calc_query = orm.QueryBuilder().append(orm.CalculationNode)
        for [calculation] in calc_query.iterall():
            assert isinstance(calculation.attributes, dict)
            assert len(calculation.attributes) > 0

        # Verify that the StructureData nodes maintained their (same) label, cell, and kinds
        struct_query = orm.QueryBuilder().append(orm.StructureData)
        assert struct_query.count() == 2
        for structure in struct_query.all(flat=True):
            assert structure.label == ''
            assert structure.cell == [[4, 0, 0], [0, 4, 0], [0, 0, 4]]

        known_kinds = [
            {
                'name': 'Ba',
                'mass': 137.327,
                'weights': [1],
                'symbols': ['Ba']
            },
            {
                'name': 'Ti',
                'mass': 47.867,
                'weights': [1],
                'symbols': ['Ti']
            },
            {
                'name': 'O',
                'mass': 15.9994,
                'weights': [1],
                'symbols': ['O']
            },
        ]
        kind_query = orm.QueryBuilder().append(orm.StructureData, project=['attributes.kinds'])
        for kinds in kind_query.all(flat=True):
            assert len(kinds) == len(known_kinds)
            for kind in kinds:
                assert kind in known_kinds

        # Check that there is a StructureData that is an input of a CalculationNode
        builder = orm.QueryBuilder()
        builder.append(orm.StructureData, tag='structure')
        builder.append(orm.CalculationNode, with_incoming='structure')
        assert len(builder.all()) > 0

        # Check that there is a RemoteData that is the output of a CalculationNode
        builder = orm.QueryBuilder()
        builder.append(orm.CalculationNode, tag='parent')
        builder.append(orm.RemoteData, with_incoming='parent')
        assert len(builder.all()) > 0
