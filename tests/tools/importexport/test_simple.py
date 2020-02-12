# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Simple tests for the export and import routines"""
import os
import shutil
import tarfile
import tempfile

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common import json
from aiida.common.exceptions import LicensingException
from aiida.tools.importexport import import_data, export
from aiida.tools.importexport.common import exceptions

from tests.utils.configuration import with_temp_dir


class TestSimple(AiidaTestCase):
    """Test simple ex-/import cases"""

    def setUp(self):
        self.reset_database()

    def tearDown(self):
        self.reset_database()

    @with_temp_dir
    def test_base_data_nodes(self, temp_dir):
        """Test ex-/import of Base Data nodes"""
        # producing values for each base type
        values = ('Hello', 6, -1.2399834e12, False)  # , ["Bla", 1, 1e-10])
        filename = os.path.join(temp_dir, 'export.tar.gz')

        # producing nodes:
        nodes = [cls(val).store() for val, cls in zip(values, (orm.Str, orm.Int, orm.Float, orm.Bool))]
        # my uuid - list to reload the node:
        uuids = [n.uuid for n in nodes]
        # exporting the nodes:
        export(nodes, outfile=filename, silent=True)
        # cleaning:
        self.clean_db()
        self.create_user()
        # Importing back the data:
        import_data(filename, silent=True)
        # Checking whether values are preserved:
        for uuid, refval in zip(uuids, values):
            self.assertEqual(orm.load_node(uuid).value, refval)

    @with_temp_dir
    def test_calc_of_structuredata(self, temp_dir):
        """Simple ex-/import of CalcJobNode with input StructureData"""
        from aiida.common.links import LinkType

        struct = orm.StructureData()
        struct.store()

        calc = orm.CalcJobNode()
        calc.computer = self.computer
        calc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})

        calc.add_incoming(struct, link_type=LinkType.INPUT_CALC, link_label='link')
        calc.store()
        calc.seal()

        pks = [struct.pk, calc.pk]

        attrs = {}
        for pk in pks:
            node = orm.load_node(pk)
            attrs[node.uuid] = dict()
            for k in node.attributes.keys():
                attrs[node.uuid][k] = node.get_attribute(k)

        filename = os.path.join(temp_dir, 'export.tar.gz')

        export([calc], outfile=filename, silent=True)

        self.clean_db()
        self.create_user()

        # NOTE: it is better to load new nodes by uuid, rather than assuming
        # that they will have the first 3 pks. In fact, a recommended policy in
        # databases is that pk always increment, even if you've deleted elements
        import_data(filename, silent=True)
        for uuid in attrs:
            node = orm.load_node(uuid)
            for k in attrs[uuid].keys():
                self.assertEqual(attrs[uuid][k], node.get_attribute(k))

    def test_check_for_export_format_version(self):
        """Test the check for the export format version."""
        # Creating a folder for the import/export files
        export_file_tmp_folder = tempfile.mkdtemp()
        unpack_tmp_folder = tempfile.mkdtemp()
        try:
            struct = orm.StructureData()
            struct.store()

            filename = os.path.join(export_file_tmp_folder, 'export.tar.gz')
            export([struct], outfile=filename, silent=True)

            with tarfile.open(filename, 'r:gz', format=tarfile.PAX_FORMAT) as tar:
                tar.extractall(unpack_tmp_folder)

            with open(os.path.join(unpack_tmp_folder, 'metadata.json'), 'r', encoding='utf8') as fhandle:
                metadata = json.load(fhandle)
            metadata['export_version'] = 0.0

            with open(os.path.join(unpack_tmp_folder, 'metadata.json'), 'wb') as fhandle:
                json.dump(metadata, fhandle)

            with tarfile.open(filename, 'w:gz', format=tarfile.PAX_FORMAT) as tar:
                tar.add(unpack_tmp_folder, arcname='')

            self.tearDownClass()
            self.setUpClass()

            with self.assertRaises(exceptions.IncompatibleArchiveVersionError):
                import_data(filename, silent=True)
        finally:
            # Deleting the created temporary folders
            shutil.rmtree(export_file_tmp_folder, ignore_errors=True)
            shutil.rmtree(unpack_tmp_folder, ignore_errors=True)

    def test_control_of_licenses(self):
        """Test control of licenses."""
        from aiida.common.folders import SandboxFolder
        from aiida.tools.importexport.dbexport import export_tree

        struct = orm.StructureData()
        struct.source = {'license': 'GPL'}
        struct.store()

        folder = SandboxFolder()
        export_tree([struct], folder=folder, silent=True, allowed_licenses=['GPL'])
        # Folder should contain two files of metadata + nodes/
        self.assertEqual(len(folder.get_content_list()), 3)

        folder = SandboxFolder()
        export_tree([struct], folder=folder, silent=True, forbidden_licenses=['Academic'])
        # Folder should contain two files of metadata + nodes/
        self.assertEqual(len(folder.get_content_list()), 3)

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([struct], folder=folder, silent=True, allowed_licenses=['CC0'])

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([struct], folder=folder, silent=True, forbidden_licenses=['GPL'])

        def cc_filter(license_):
            return license_.startswith('CC')

        def gpl_filter(license_):
            return license_ == 'GPL'

        def crashing_filter():
            raise NotImplementedError('not implemented yet')

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([struct], folder=folder, silent=True, allowed_licenses=cc_filter)

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([struct], folder=folder, silent=True, forbidden_licenses=gpl_filter)

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([struct], folder=folder, silent=True, allowed_licenses=crashing_filter)

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([struct], folder=folder, silent=True, forbidden_licenses=crashing_filter)
