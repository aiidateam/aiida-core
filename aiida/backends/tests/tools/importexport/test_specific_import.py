# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the export and import routines"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import with_statement

import os
import shutil
import tempfile

import numpy as np

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.backends.tests.utils.configuration import with_temp_dir
from aiida.common.folders import RepositoryFolder
from aiida.orm.utils.repository import Repository
from aiida.tools.importexport import import_data, export
from aiida.tools.importexport.common import exceptions


class TestSpecificImport(AiidaTestCase):
    """Test specific ex-/import cases"""

    def setUp(self):
        super(TestSpecificImport, self).setUp()
        self.reset_database()

    def tearDown(self):
        self.reset_database()

    def test_simple_import(self):
        """
        This is a very simple test which checks that an export file with nodes
        that are not associated to a computer is imported correctly. In Django
        when such nodes are exported, there is an empty set for computers
        in the export file. In SQLA there is such a set only when a computer is
        associated with the exported nodes. When an empty computer set is
        found at the export file (when imported to an SQLA profile), the SQLA
        import code used to crash. This test demonstrates this problem.
        """
        parameters = orm.Dict(
            dict={
                'Pr': {
                    'cutoff': 50.0,
                    'pseudo_type': 'Wentzcovitch',
                    'dual': 8,
                    'cutoff_units': 'Ry'
                },
                'Ru': {
                    'cutoff': 40.0,
                    'pseudo_type': 'SG15',
                    'dual': 4,
                    'cutoff_units': 'Ry'
                },
            }
        ).store()

        with tempfile.NamedTemporaryFile() as handle:
            nodes = [parameters]
            export(nodes, outfile=handle.name, overwrite=True, silent=True)

            # Check that we have the expected number of nodes in the database
            self.assertEqual(orm.QueryBuilder().append(orm.Node).count(), len(nodes))

            # Clean the database and verify there are no nodes left
            self.clean_db()
            self.create_user()
            self.assertEqual(orm.QueryBuilder().append(orm.Node).count(), 0)

            # After importing we should have the original number of nodes again
            import_data(handle.name, silent=True)
            self.assertEqual(orm.QueryBuilder().append(orm.Node).count(), len(nodes))

    def test_cycle_structure_data(self):
        """
        Create an export with some orm.CalculationNode and Data nodes and import it after having
        cleaned the database. Verify that the nodes and their attributes are restored
        properly after importing the created export archive
        """
        from aiida.common.links import LinkType

        test_label = 'Test structure'
        test_cell = [[8.34, 0.0, 0.0], [0.298041701839357, 8.53479766274308, 0.0],
                     [0.842650688117053, 0.47118495164127, 10.6965192730702]]
        test_kinds = [{
            'symbols': [u'Fe'],
            'weights': [1.0],
            'mass': 55.845,
            'name': u'Fe'
        }, {
            'symbols': [u'S'],
            'weights': [1.0],
            'mass': 32.065,
            'name': u'S'
        }]

        structure = orm.StructureData(cell=test_cell)
        structure.append_atom(symbols=['Fe'], position=[0, 0, 0])
        structure.append_atom(symbols=['S'], position=[2, 2, 2])
        structure.label = test_label
        structure.store()

        parent_process = orm.CalculationNode()
        parent_process.set_attribute('key', 'value')
        parent_process.store()
        child_calculation = orm.CalculationNode()
        child_calculation.set_attribute('key', 'value')
        remote_folder = orm.RemoteData(computer=self.computer, remote_path='/').store()

        remote_folder.add_incoming(parent_process, link_type=LinkType.CREATE, link_label='link')
        child_calculation.add_incoming(remote_folder, link_type=LinkType.INPUT_CALC, link_label='link')
        child_calculation.store()
        structure.add_incoming(child_calculation, link_type=LinkType.CREATE, link_label='link')

        parent_process.seal()
        child_calculation.seal()

        with tempfile.NamedTemporaryFile() as handle:

            nodes = [structure, child_calculation, parent_process, remote_folder]
            export(nodes, outfile=handle.name, overwrite=True, silent=True)

            # Check that we have the expected number of nodes in the database
            self.assertEqual(orm.QueryBuilder().append(orm.Node).count(), len(nodes))

            # Clean the database and verify there are no nodes left
            self.clean_db()
            self.create_user()
            self.assertEqual(orm.QueryBuilder().append(orm.Node).count(), 0)

            # After importing we should have the original number of nodes again
            import_data(handle.name, silent=True)
            self.assertEqual(orm.QueryBuilder().append(orm.Node).count(), len(nodes))

            # Verify that orm.CalculationNodes have non-empty attribute dictionaries
            builder = orm.QueryBuilder().append(orm.CalculationNode)
            for [calculation] in builder.iterall():
                self.assertIsInstance(calculation.attributes, dict)
                self.assertNotEqual(len(calculation.attributes), 0)

            # Verify that the structure data maintained its label, cell and kinds
            builder = orm.QueryBuilder().append(orm.StructureData)
            for [structure] in builder.iterall():
                self.assertEqual(structure.label, test_label)
                # Check that they are almost the same, within numerical precision
                self.assertTrue(np.abs(np.array(structure.cell) - np.array(test_cell)).max() < 1.e-12)

            builder = orm.QueryBuilder().append(orm.StructureData, project=['attributes.kinds'])
            for [kinds] in builder.iterall():
                self.assertEqual(len(kinds), 2)
                for kind in kinds:
                    self.assertIn(kind, test_kinds)

            # Check that there is a StructureData that is an output of a orm.CalculationNode
            builder = orm.QueryBuilder()
            builder.append(orm.CalculationNode, project=['uuid'], tag='calculation')
            builder.append(orm.StructureData, with_incoming='calculation')
            self.assertGreater(len(builder.all()), 0)

            # Check that there is a RemoteData that is a child and parent of a orm.CalculationNode
            builder = orm.QueryBuilder()
            builder.append(orm.CalculationNode, tag='parent')
            builder.append(orm.RemoteData, project=['uuid'], with_incoming='parent', tag='remote')
            builder.append(orm.CalculationNode, with_incoming='remote')
            self.assertGreater(len(builder.all()), 0)

    @with_temp_dir
    def test_missing_node_repo_folder_export(self, temp_dir):
        """
        Make sure `~aiida.tools.importexport.common.exceptions.ArchiveExportError` is raised during export when missing
        Node repository folder.
        Create and store a new Node and manually remove its repository folder.
        Attempt to export it and make sure `~aiida.tools.importexport.common.exceptions.ArchiveExportError` is raised,
        due to the missing folder.
        """
        node = orm.CalculationNode().store()
        node.seal()
        node_uuid = node.uuid

        node_repo = RepositoryFolder(section=Repository._section_name, uuid=node_uuid)  # pylint: disable=protected-access
        self.assertTrue(
            node_repo.exists(), msg='Newly created and stored Node should have had an existing repository folder'
        )

        # Removing the Node's local repository folder
        shutil.rmtree(node_repo.abspath, ignore_errors=True)
        self.assertFalse(
            node_repo.exists(), msg='Newly created and stored Node should have had its repository folder removed'
        )

        # Try to export, check it raises and check the raise message
        filename = os.path.join(temp_dir, 'export.tar.gz')
        with self.assertRaises(exceptions.ArchiveExportError) as exc:
            export([node], outfile=filename, silent=True)

        self.assertIn(
            'Unable to find the repository folder for Node with UUID={}'.format(node_uuid), str(exc.exception)
        )
        self.assertFalse(os.path.exists(filename), msg='The export file should not exist')

    @with_temp_dir
    def test_missing_node_repo_folder_import(self, temp_dir):
        """
        Make sure `~aiida.tools.importexport.common.exceptions.CorruptArchive` is raised during import when missing
        Node repository folder.
        Create and export a Node and manually remove its repository folder in the export file.
        Attempt to import it and make sure `~aiida.tools.importexport.common.exceptions.CorruptArchive` is raised,
        due to the missing folder.
        """
        import tarfile

        from aiida.common.folders import SandboxFolder
        from aiida.tools.importexport.common.archive import extract_tar
        from aiida.tools.importexport.common.config import NODES_EXPORT_SUBFOLDER
        from aiida.tools.importexport.common.utils import export_shard_uuid

        node = orm.CalculationNode().store()
        node.seal()
        node_uuid = node.uuid

        node_repo = RepositoryFolder(section=Repository._section_name, uuid=node_uuid)  # pylint: disable=protected-access
        self.assertTrue(
            node_repo.exists(), msg='Newly created and stored Node should have had an existing repository folder'
        )

        # Export and reset db
        filename = os.path.join(temp_dir, 'export.tar.gz')
        export([node], outfile=filename, silent=True)
        self.reset_database()

        # Untar export file, remove repository folder, re-tar
        node_shard_uuid = export_shard_uuid(node_uuid)
        node_top_folder = node_shard_uuid.split('/')[0]
        with SandboxFolder() as folder:
            extract_tar(filename, folder, silent=True, nodes_export_subfolder=NODES_EXPORT_SUBFOLDER)
            node_folder = folder.get_subfolder(os.path.join(NODES_EXPORT_SUBFOLDER, node_shard_uuid))
            self.assertTrue(
                node_folder.exists(), msg="The Node's repository folder should still exist in the export file"
            )

            # Removing the Node's repository folder from the export file
            shutil.rmtree(
                folder.get_subfolder(os.path.join(NODES_EXPORT_SUBFOLDER, node_top_folder)).abspath, ignore_errors=True
            )
            self.assertFalse(
                node_folder.exists(),
                msg="The Node's repository folder should now have been removed in the export file"
            )

            filename_corrupt = os.path.join(temp_dir, 'export_corrupt.tar.gz')
            with tarfile.open(filename_corrupt, 'w:gz', format=tarfile.PAX_FORMAT, dereference=True) as tar:
                tar.add(folder.abspath, arcname='')

        # Try to import, check it raises and check the raise message
        with self.assertRaises(exceptions.CorruptArchive) as exc:
            import_data(filename_corrupt, silent=True)

        self.assertIn(
            'Unable to find the repository folder for Node with UUID={}'.format(node_uuid), str(exc.exception)
        )
