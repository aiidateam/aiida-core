# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test export file migration from old export versions to the newest"""

import os

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.tools.importexport import import_data, EXPORT_VERSION as newest_version
from aiida.tools.importexport.migration import migrate_recursively, verify_metadata_version
from aiida.common.utils import Capturing

from tests.utils.archives import get_archive_file, get_json_files, migrate_archive
from tests.utils.configuration import with_temp_dir


class TestExportFileMigration(AiidaTestCase):
    """Test export file migrations"""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """Add variables (once) to be used by all tests"""
        super().setUpClass(*args, **kwargs)

        # Known export file content used for checks
        cls.node_count = 25
        cls.struct_count = 2
        cls.known_struct_label = ''
        cls.known_cell = [[4, 0, 0], [0, 4, 0], [0, 0, 4]]
        cls.known_kinds = [
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

        # Utility helpers
        cls.external_archive = {'filepath': 'archives', 'external_module': 'aiida-export-migration-tests'}
        cls.core_archive = {'filepath': 'export/migrate'}

    def setUp(self):
        """Reset database before each test"""
        super().setUp()
        self.reset_database()

    def test_migrate_recursively(self):
        """Test function 'migrate_recursively'"""
        import tarfile
        import zipfile

        from aiida.common.exceptions import NotExistent
        from aiida.common.folders import SandboxFolder
        from aiida.common.json import load as jsonload
        from aiida.tools.importexport.common.archive import extract_tar, extract_zip

        # Get metadata.json and data.json as dicts from v0.1 file archive
        # Cannot use 'get_json_files' for 'export_v0.1_simple.aiida',
        # because we need to pass the SandboxFolder to 'migrate_recursively'
        dirpath_archive = get_archive_file('export_v0.1_simple.aiida', **self.core_archive)

        with SandboxFolder(sandbox_in_repo=False) as folder:
            if zipfile.is_zipfile(dirpath_archive):
                extract_zip(dirpath_archive, folder, silent=True)
            elif tarfile.is_tarfile(dirpath_archive):
                extract_tar(dirpath_archive, folder, silent=True)
            else:
                raise ValueError('invalid file format, expected either a zip archive or gzipped tarball')

            try:
                with open(folder.get_abs_path('data.json'), 'r', encoding='utf8') as fhandle:
                    data = jsonload(fhandle)
                with open(folder.get_abs_path('metadata.json'), 'r', encoding='utf8') as fhandle:
                    metadata = jsonload(fhandle)
            except IOError:
                raise NotExistent('export archive does not contain the required file {}'.format(fhandle.filename))

            verify_metadata_version(metadata, version='0.1')

            # Migrate to newest version
            new_version = migrate_recursively(metadata, data, folder)
            verify_metadata_version(metadata, version=newest_version)
            self.assertEqual(new_version, newest_version)

    @with_temp_dir
    def test_no_node_export(self, temp_dir):
        """Test migration of export file that has no Nodes"""
        input_file = get_archive_file('export_v0.3_no_Nodes.aiida', **self.external_archive)
        output_file = os.path.join(temp_dir, 'output_file.aiida')

        # Known entities
        computer_uuids = [self.computer.uuid]  # pylint: disable=no-member
        user_emails = [orm.User.objects.get_default().email]

        # Known export file content used for checks
        node_count = 0
        computer_count = 1 + 1  # localhost is always present
        computer_uuids.append('4f33c6fd-b624-47df-9ffb-a58f05d323af')
        user_emails.append('aiida@localhost')

        # Perform the migration
        migrate_archive(input_file, output_file)

        # Load the migrated file
        import_data(output_file, silent=True)

        # Check known number of entities is present
        self.assertEqual(orm.QueryBuilder().append(orm.Node).count(), node_count)
        self.assertEqual(orm.QueryBuilder().append(orm.Computer).count(), computer_count)

        # Check unique identifiers
        computers = orm.QueryBuilder().append(orm.Computer, project=['uuid']).all()[0][0]
        users = orm.QueryBuilder().append(orm.User, project=['email']).all()[0][0]
        self.assertIn(computers, computer_uuids)
        self.assertIn(users, user_emails)

    def test_wrong_versions(self):
        """Test correct errors are raised if export files have wrong version numbers"""
        from aiida.tools.importexport.migration import MIGRATE_FUNCTIONS

        # Initialization
        wrong_versions = ['0.0', '0.1.0', '0.99']
        old_versions = list(MIGRATE_FUNCTIONS.keys())
        legal_versions = old_versions + [newest_version]
        wrong_version_metadatas = []
        for version in wrong_versions:
            metadata = {'export_version': version}
            wrong_version_metadatas.append(metadata)

        # Checks
        # Make sure the "wrong_versions" are wrong
        for version in wrong_versions:
            self.assertNotIn(
                version,
                legal_versions,
                msg="'{}' was not expected to be a legal version, legal version: {}".format(version, legal_versions)
            )

        # Make sure migrate_recursively throws a critical message and raises SystemExit
        for metadata in wrong_version_metadatas:
            with self.assertRaises(SystemExit) as exception:
                with Capturing(capture_stderr=True):
                    new_version = migrate_recursively(metadata, {}, None)

                self.assertIn(
                    'Critical: Cannot migrate from version {}'.format(metadata['export_version']),
                    exception.exception,
                    msg="Expected a critical statement for the wrong export version '{}', "
                    'instead got {}'.format(metadata['export_version'], exception.exception)
                )
                self.assertIsNone(
                    new_version,
                    msg='migrate_recursively should not return anything, '
                    "hence the 'return' should be None, but instead it is {}".format(new_version)
                )

    def test_migrate_newest_version(self):
        """
        Test critical message and SystemExit is raised, when an export file with the newest export version is migrated
        """
        # Initialization
        metadata = {'export_version': newest_version}

        # Check
        with self.assertRaises(SystemExit) as exception:

            with Capturing(capture_stderr=True):
                new_version = migrate_recursively(metadata, {}, None)

            self.assertIn(
                'Critical: Your export file is already at the newest export version {}'.format(
                    metadata['export_version']
                ),
                exception.exception,
                msg="Expected a critical statement that the export version '{}' is the newest export version '{}', "
                'instead got {}'.format(metadata['export_version'], newest_version, exception.exception)
            )
            self.assertIsNone(
                new_version,
                msg='migrate_recursively should not return anything, '
                "hence the 'return' should be None, but instead it is {}".format(new_version)
            )

    @with_temp_dir
    def test_v02_to_newest(self, temp_dir):
        """Test migration of exported files from v0.2 to newest export version"""
        # Get export file with export version 0.2
        input_file = get_archive_file('export_v0.2.aiida', **self.external_archive)
        output_file = os.path.join(temp_dir, 'output_file.aiida')

        # Perform the migration
        migrate_archive(input_file, output_file)
        metadata, _ = get_json_files(output_file)
        verify_metadata_version(metadata, version=newest_version)

        # Load the migrated file
        import_data(output_file, silent=True)

        # Do the necessary checks
        self.assertEqual(orm.QueryBuilder().append(orm.Node).count(), self.node_count)

        # Verify that CalculationNodes have non-empty attribute dictionaries
        builder = orm.QueryBuilder().append(orm.CalculationNode)
        for [calculation] in builder.iterall():
            self.assertIsInstance(calculation.attributes, dict)
            self.assertNotEqual(len(calculation.attributes), 0)

        # Verify that the StructureData nodes maintained their (same) label, cell, and kinds
        builder = orm.QueryBuilder().append(orm.StructureData)
        self.assertEqual(
            builder.count(),
            self.struct_count,
            msg='There should be {} StructureData, instead {} were/was found'.format(
                self.struct_count, builder.count()
            )
        )
        for structures in builder.all():
            structure = structures[0]
            self.assertEqual(structure.label, self.known_struct_label)
            self.assertEqual(structure.cell, self.known_cell)

        builder = orm.QueryBuilder().append(orm.StructureData, project=['attributes.kinds'])
        for [kinds] in builder.iterall():
            self.assertEqual(len(kinds), len(self.known_kinds))
            for kind in kinds:
                self.assertIn(kind, self.known_kinds, msg="Kind '{}' not found in: {}".format(kind, self.known_kinds))

        # Check that there is a StructureData that is an input of a CalculationNode
        builder = orm.QueryBuilder()
        builder.append(orm.StructureData, tag='structure')
        builder.append(orm.CalculationNode, with_incoming='structure')
        self.assertGreater(len(builder.all()), 0)

        # Check that there is a RemoteData that is the output of a CalculationNode
        builder = orm.QueryBuilder()
        builder.append(orm.CalculationNode, tag='parent')
        builder.append(orm.RemoteData, with_incoming='parent')
        self.assertGreater(len(builder.all()), 0)

    @with_temp_dir
    def test_v03_to_newest(self, temp_dir):
        """Test migration of exported files from v0.3 to newest export version"""
        input_file = get_archive_file('export_v0.3.aiida', **self.external_archive)
        output_file = os.path.join(temp_dir, 'output_file.aiida')

        # Perform the migration
        migrate_archive(input_file, output_file)
        metadata, _ = get_json_files(output_file)
        verify_metadata_version(metadata, version=newest_version)

        # Load the migrated file
        import_data(output_file, silent=True)

        # Do the necessary checks
        self.assertEqual(orm.QueryBuilder().append(orm.Node).count(), self.node_count)

        # Verify that CalculationNodes have non-empty attribute dictionaries
        builder = orm.QueryBuilder().append(orm.CalculationNode)
        for [calculation] in builder.iterall():
            self.assertIsInstance(calculation.attributes, dict)
            self.assertNotEqual(len(calculation.attributes), 0)

        # Verify that the StructureData nodes maintained their (same) label, cell, and kinds
        builder = orm.QueryBuilder().append(orm.StructureData)
        self.assertEqual(
            builder.count(),
            self.struct_count,
            msg='There should be {} StructureData, instead {} were/was found'.format(
                self.struct_count, builder.count()
            )
        )
        for structures in builder.all():
            structure = structures[0]
            self.assertEqual(structure.label, self.known_struct_label)
            self.assertEqual(structure.cell, self.known_cell)

        builder = orm.QueryBuilder().append(orm.StructureData, project=['attributes.kinds'])
        for [kinds] in builder.iterall():
            self.assertEqual(len(kinds), len(self.known_kinds))
            for kind in kinds:
                self.assertIn(kind, self.known_kinds, msg="Kind '{}' not found in: {}".format(kind, self.known_kinds))

        # Check that there is a StructureData that is an input of a CalculationNode
        builder = orm.QueryBuilder()
        builder.append(orm.StructureData, tag='structure')
        builder.append(orm.CalculationNode, with_incoming='structure')
        self.assertGreater(len(builder.all()), 0)

        # Check that there is a RemoteData that is the output of a CalculationNode
        builder = orm.QueryBuilder()
        builder.append(orm.CalculationNode, tag='parent')
        builder.append(orm.RemoteData, with_incoming='parent')
        self.assertGreater(len(builder.all()), 0)

    @with_temp_dir
    def test_v04_to_newest(self, temp_dir):
        """Test migration of exported files from v0.4 to newest export version"""
        input_file = get_archive_file('export_v0.4.aiida', **self.external_archive)
        output_file = os.path.join(temp_dir, 'output_file.aiida')

        # Perform the migration
        migrate_archive(input_file, output_file)
        metadata, _ = get_json_files(output_file)
        verify_metadata_version(metadata, version=newest_version)

        # Load the migrated file
        import_data(output_file, silent=True)

        # Do the necessary checks
        self.assertEqual(orm.QueryBuilder().append(orm.Node).count(), self.node_count + 2)

        # Verify that CalculationNodes have non-empty attribute dictionaries
        builder = orm.QueryBuilder().append(orm.CalculationNode)
        for [calculation] in builder.iterall():
            self.assertIsInstance(calculation.attributes, dict)
            self.assertNotEqual(len(calculation.attributes), 0)

        # Verify that the StructureData nodes maintained their (same) label, cell, and kinds
        builder = orm.QueryBuilder().append(orm.StructureData)
        self.assertEqual(
            builder.count(),
            self.struct_count,
            msg='There should be {} StructureData, instead {} were/was found'.format(
                self.struct_count, builder.count()
            )
        )
        for structures in builder.all():
            structure = structures[0]
            self.assertEqual(structure.label, self.known_struct_label)
            self.assertEqual(structure.cell, self.known_cell)

        builder = orm.QueryBuilder().append(orm.StructureData, project=['attributes.kinds'])
        for [kinds] in builder.iterall():
            self.assertEqual(len(kinds), len(self.known_kinds))
            for kind in kinds:
                self.assertIn(kind, self.known_kinds, msg="Kind '{}' not found in: {}".format(kind, self.known_kinds))

        # Check that there is a StructureData that is an input of a CalculationNode
        builder = orm.QueryBuilder()
        builder.append(orm.StructureData, tag='structure')
        builder.append(orm.CalculationNode, with_incoming='structure')
        self.assertGreater(len(builder.all()), 0)

        # Check that there is a RemoteData that is the output of a CalculationNode
        builder = orm.QueryBuilder()
        builder.append(orm.CalculationNode, tag='parent')
        builder.append(orm.RemoteData, with_incoming='parent')
        self.assertGreater(len(builder.all()), 0)

    @with_temp_dir
    def test_v05_to_newest(self, temp_dir):
        """Test migration of exported files from v0.5 to newest export version"""
        input_file = get_archive_file('export_v0.5_manual.aiida', **self.external_archive)
        output_file = os.path.join(temp_dir, 'output_file.aiida')

        # Perform the migration
        migrate_archive(input_file, output_file)
        metadata, _ = get_json_files(output_file)
        verify_metadata_version(metadata, version=newest_version)

        # Load the migrated file
        import_data(output_file, silent=True)

        # Do the necessary checks
        self.assertEqual(orm.QueryBuilder().append(orm.Node).count(), self.node_count + 2)

        # Verify that CalculationNodes have non-empty attribute dictionaries
        builder = orm.QueryBuilder().append(orm.CalculationNode)
        for [calculation] in builder.iterall():
            self.assertIsInstance(calculation.attributes, dict)
            self.assertNotEqual(len(calculation.attributes), 0)

        # Verify that the StructureData nodes maintained their (same) label, cell, and kinds
        builder = orm.QueryBuilder().append(orm.StructureData)
        self.assertEqual(
            builder.count(),
            self.struct_count,
            msg='There should be {} StructureData, instead {} were/was found'.format(
                self.struct_count, builder.count()
            )
        )
        for structures in builder.all():
            structure = structures[0]
            self.assertEqual(structure.label, self.known_struct_label)
            self.assertEqual(structure.cell, self.known_cell)

        builder = orm.QueryBuilder().append(orm.StructureData, project=['attributes.kinds'])
        for [kinds] in builder.iterall():
            self.assertEqual(len(kinds), len(self.known_kinds))
            for kind in kinds:
                self.assertIn(kind, self.known_kinds, msg="Kind '{}' not found in: {}".format(kind, self.known_kinds))

        # Check that there is a StructureData that is an input of a CalculationNode
        builder = orm.QueryBuilder()
        builder.append(orm.StructureData, tag='structure')
        builder.append(orm.CalculationNode, with_incoming='structure')
        self.assertGreater(len(builder.all()), 0)

        # Check that there is a RemoteData that is the output of a CalculationNode
        builder = orm.QueryBuilder()
        builder.append(orm.CalculationNode, tag='parent')
        builder.append(orm.RemoteData, with_incoming='parent')
        self.assertGreater(len(builder.all()), 0)

    @with_temp_dir
    def test_v06_to_newest(self, temp_dir):
        """Test migration of exported files from v0.6 to newest export version"""
        input_file = get_archive_file('export_v0.6_manual.aiida', **self.external_archive)
        output_file = os.path.join(temp_dir, 'output_file.aiida')

        # Perform the migration
        migrate_archive(input_file, output_file)
        metadata, _ = get_json_files(output_file)
        verify_metadata_version(metadata, version=newest_version)

        # Load the migrated file
        import_data(output_file, silent=True)

        # Do the necessary checks
        self.assertEqual(orm.QueryBuilder().append(orm.Node).count(), self.node_count + 2)

        # Verify that CalculationNodes have non-empty attribute dictionaries
        builder = orm.QueryBuilder().append(orm.CalculationNode)
        for [calculation] in builder.iterall():
            self.assertIsInstance(calculation.attributes, dict)
            self.assertNotEqual(len(calculation.attributes), 0)

        # Verify that the StructureData nodes maintained their (same) label, cell, and kinds
        builder = orm.QueryBuilder().append(orm.StructureData)
        self.assertEqual(
            builder.count(),
            self.struct_count,
            msg='There should be {} StructureData, instead {} were/was found'.format(
                self.struct_count, builder.count()
            )
        )
        for structures in builder.all():
            structure = structures[0]
            self.assertEqual(structure.label, self.known_struct_label)
            self.assertEqual(structure.cell, self.known_cell)

        builder = orm.QueryBuilder().append(orm.StructureData, project=['attributes.kinds'])
        for [kinds] in builder.iterall():
            self.assertEqual(len(kinds), len(self.known_kinds))
            for kind in kinds:
                self.assertIn(kind, self.known_kinds, msg="Kind '{}' not found in: {}".format(kind, self.known_kinds))

        # Check that there is a StructureData that is an input of a CalculationNode
        builder = orm.QueryBuilder()
        builder.append(orm.StructureData, tag='structure')
        builder.append(orm.CalculationNode, with_incoming='structure')
        self.assertGreater(len(builder.all()), 0)

        # Check that there is a RemoteData that is the output of a CalculationNode
        builder = orm.QueryBuilder()
        builder.append(orm.CalculationNode, tag='parent')
        builder.append(orm.RemoteData, with_incoming='parent')
        self.assertGreater(len(builder.all()), 0)

    @with_temp_dir
    def test_v07_to_newest(self, temp_dir):
        """Test migration of exported files from v0.7 to newest export version"""
        input_file = get_archive_file('export_v0.7_manual.aiida', **self.external_archive)
        output_file = os.path.join(temp_dir, 'output_file.aiida')

        # Perform the migration
        migrate_archive(input_file, output_file)
        metadata, _ = get_json_files(output_file)
        verify_metadata_version(metadata, version=newest_version)

        # Load the migrated file
        import_data(output_file, silent=True)

        # Do the necessary checks
        self.assertEqual(orm.QueryBuilder().append(orm.Node).count(), self.node_count + 2)

        # Verify that CalculationNodes have non-empty attribute dictionaries
        builder = orm.QueryBuilder().append(orm.CalculationNode)
        for [calculation] in builder.iterall():
            self.assertIsInstance(calculation.attributes, dict)
            self.assertNotEqual(len(calculation.attributes), 0)

        # Verify that the StructureData nodes maintained their (same) label, cell, and kinds
        builder = orm.QueryBuilder().append(orm.StructureData)
        self.assertEqual(
            builder.count(),
            self.struct_count,
            msg='There should be {} StructureData, instead {} were/was found'.format(
                self.struct_count, builder.count()
            )
        )
        for structures in builder.all():
            structure = structures[0]
            self.assertEqual(structure.label, self.known_struct_label)
            self.assertEqual(structure.cell, self.known_cell)

        builder = orm.QueryBuilder().append(orm.StructureData, project=['attributes.kinds'])
        for [kinds] in builder.iterall():
            self.assertEqual(len(kinds), len(self.known_kinds))
            for kind in kinds:
                self.assertIn(kind, self.known_kinds, msg="Kind '{}' not found in: {}".format(kind, self.known_kinds))

        # Check that there is a StructureData that is an input of a CalculationNode
        builder = orm.QueryBuilder()
        builder.append(orm.StructureData, tag='structure')
        builder.append(orm.CalculationNode, with_incoming='structure')
        self.assertGreater(len(builder.all()), 0)

        # Check that there is a RemoteData that is the output of a CalculationNode
        builder = orm.QueryBuilder()
        builder.append(orm.CalculationNode, tag='parent')
        builder.append(orm.RemoteData, with_incoming='parent')
        self.assertGreater(len(builder.all()), 0)
