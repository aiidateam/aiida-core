# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Tests for the export and import routines.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import io
import six
from six.moves import range, zip
import unittest

from aiida.backends.testbase import AiidaTestCase
from aiida.orm.importexport import import_data
from aiida.common.utils import get_new_uuid
from aiida import orm


class TestSpecificImport(AiidaTestCase):

    def setUp(self):
        super(TestSpecificImport, self).setUp()
        self.clean_db()
        self.insert_data()

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
        import tempfile
        from aiida.orm.node.data.parameter import ParameterData
        from aiida.orm.importexport import export, import_data
        from aiida.orm.node import Node
        from aiida.orm.querybuilder import QueryBuilder

        parameters = ParameterData(dict={
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
        }).store()

        with tempfile.NamedTemporaryFile() as handle:
            nodes = [parameters]
            export(nodes, outfile=handle.name, overwrite=True, silent=True)

            # Check that we have the expected number of nodes in the database
            self.assertEquals(QueryBuilder().append(Node).count(), len(nodes))

            # Clean the database and verify there are no nodes left
            self.clean_db()
            self.assertEquals(QueryBuilder().append(Node).count(), 0)

            # After importing we should have the original number of nodes again
            import_data(handle.name, silent=True)
            self.assertEquals(QueryBuilder().append(Node).count(), len(nodes))

    def test_cycle_structure_data(self):
        """
        Create an export with some CalculationNode and Data nodes and import it after having
        cleaned the database. Verify that the nodes and their attributes are restored
        properly after importing the created export archive
        """
        import tempfile
        from aiida.common.links import LinkType
        from aiida.orm.node import CalculationNode
        from aiida.orm.node.data.structure import StructureData
        from aiida.orm.node.data.remote import RemoteData
        from aiida.orm.importexport import export, import_data
        from aiida.orm.node import Node
        from aiida.orm.querybuilder import QueryBuilder

        test_label = 'Test structure'
        test_cell = [
            [8.34, 0.0, 0.0],
            [0.298041701839357, 8.53479766274308, 0.0],
            [0.842650688117053, 0.47118495164127, 10.6965192730702]
        ]
        test_kinds = [
            {
                'symbols': [u'Fe'],
                'weights': [1.0],
                'mass': 55.845,
                'name': u'Fe'
            },
            {
                'symbols': [u'S'],
                'weights': [1.0],
                'mass': 32.065,
                'name': u'S'
            }
        ]

        structure = StructureData(cell=test_cell)
        structure.append_atom(symbols=['Fe'], position=[0, 0, 0])
        structure.append_atom(symbols=['S'], position=[2, 2, 2])
        structure.label = test_label
        structure.store()

        parent_process = CalculationNode()
        parent_process._set_attr('key', 'value')
        parent_process.store()
        child_calculation = CalculationNode()
        child_calculation._set_attr('key', 'value')
        child_calculation.store()
        remote_folder = RemoteData(computer=self.computer, remote_path='/').store()

        remote_folder.add_incoming(parent_process, link_type=LinkType.CREATE, link_label='link')
        child_calculation.add_incoming(remote_folder, link_type=LinkType.INPUT_CALC, link_label='link')
        structure.add_incoming(child_calculation, link_type=LinkType.CREATE, link_label='link')

        with tempfile.NamedTemporaryFile() as handle:

            nodes = [structure, child_calculation, parent_process, remote_folder]
            export(nodes, outfile=handle.name, overwrite=True, silent=True)

            # Check that we have the expected number of nodes in the database
            self.assertEquals(QueryBuilder().append(Node).count(), len(nodes))

            # Clean the database and verify there are no nodes left
            self.clean_db()
            self.assertEquals(QueryBuilder().append(Node).count(), 0)

            # After importing we should have the original number of nodes again
            import_data(handle.name, silent=True)
            self.assertEquals(QueryBuilder().append(Node).count(), len(nodes))

            # Verify that CalculationNodes have non-empty attribute dictionaries
            qb = QueryBuilder().append(CalculationNode)
            for [calculation] in qb.iterall():
                self.assertIsInstance(calculation.get_attrs(), dict)
                self.assertNotEquals(len(calculation.get_attrs()), 0)

            # Verify that the structure data maintained its label, cell and kinds
            qb = QueryBuilder().append(StructureData)
            for [structure] in qb.iterall():
                self.assertEquals(structure.label, test_label)
                self.assertEquals(structure.cell, test_cell)

            qb = QueryBuilder().append(StructureData, project=['attributes.kinds'])
            for [kinds] in qb.iterall():
                self.assertEqual(len(kinds), 2)
                for kind in kinds:
                    self.assertIn(kind, test_kinds)

            # Check that there is a StructureData that is an output of a CalculationNode
            qb = QueryBuilder()
            qb.append(CalculationNode, project=['uuid'], tag='calculation')
            qb.append(StructureData, with_incoming='calculation')
            self.assertGreater(len(qb.all()), 0)

            # Check that there is a RemoteData that is a child and parent of a CalculationNode
            qb = QueryBuilder()
            qb.append(CalculationNode, tag='parent')
            qb.append(RemoteData, project=['uuid'], with_incoming='parent', tag='remote')
            qb.append(CalculationNode, with_incoming='remote')
            self.assertGreater(len(qb.all()), 0)


class TestSimple(AiidaTestCase):

    def setUp(self):
        self.clean_db()
        self.insert_data()

    def tearDown(self):
        pass

    def test_0(self):
        import os
        import shutil
        import tempfile

        from aiida.orm import load_node
        from aiida.orm.node.data.base import Str, Int, Float, Bool
        from aiida.orm.importexport import export

        # Creating a folder for the import/export files
        temp_folder = tempfile.mkdtemp()
        try:
            # producing values for each base type
            values = ("Hello", 6, -1.2399834e12, False)  # , ["Bla", 1, 1e-10])
            filename = os.path.join(temp_folder, "export.tar.gz")

            # producing nodes:
            nodes = [cls(val).store() for val, cls in zip(values, (Str, Int, Float, Bool))]
            # my uuid - list to reload the node:
            uuids = [n.uuid for n in nodes]
            # exporting the nodes:
            export(nodes, outfile=filename, silent=True)
            # cleaning:
            self.clean_db()
            # Importing back the data:
            import_data(filename, silent=True)
            # Checking whether values are preserved:
            for uuid, refval in zip(uuids, values):
                self.assertEquals(load_node(uuid).value, refval)
        finally:
            # Deleting the created temporary folder
            shutil.rmtree(temp_folder, ignore_errors=True)

    def test_1(self):
        import os
        import shutil
        import tempfile

        from aiida.common.links import LinkType
        from aiida.orm import DataFactory
        from aiida.orm import load_node
        from aiida.orm.node import CalcJobNode
        from aiida.orm.importexport import export

        # Creating a folder for the import/export files
        temp_folder = tempfile.mkdtemp()
        try:
            StructureData = DataFactory('structure')
            sd = StructureData()
            sd.store()

            calc = CalcJobNode()
            calc.set_computer(self.computer)
            calc.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
            calc.store()

            calc.add_incoming(sd, link_type=LinkType.INPUT_CALC, link_label='link')

            pks = [sd.pk, calc.pk]

            attrs = {}
            for pk in pks:
                node = load_node(pk)
                attrs[node.uuid] = dict()
                for k in node.attrs():
                    attrs[node.uuid][k] = node.get_attr(k)

            filename = os.path.join(temp_folder, "export.tar.gz")

            export([calc], outfile=filename, silent=True)

            self.clean_db()

            # NOTE: it is better to load new nodes by uuid, rather than assuming
            # that they will have the first 3 pks. In fact, a recommended policy in
            # databases is that pk always increment, even if you've deleted elements
            import_data(filename, silent=True)
            for uuid in attrs.keys():
                node = load_node(uuid)
                # for k in node.attrs():
                for k in attrs[uuid].keys():
                    self.assertEquals(attrs[uuid][k], node.get_attr(k))
        finally:
            # Deleting the created temporary folder
            shutil.rmtree(temp_folder, ignore_errors=True)
            # print temp_folder

    def test_2(self):
        """
        Test the check for the export format version.
        """
        import tarfile
        import os
        import shutil
        import tempfile

        from aiida.common import exceptions
        from aiida.orm import DataFactory
        from aiida.orm.importexport import export
        import aiida.common.json as json

        # Creating a folder for the import/export files
        export_file_tmp_folder = tempfile.mkdtemp()
        unpack_tmp_folder = tempfile.mkdtemp()
        try:
            StructureData = DataFactory('structure')
            sd = StructureData()
            sd.store()

            filename = os.path.join(export_file_tmp_folder, "export.tar.gz")
            export([sd], outfile=filename, silent=True)

            with tarfile.open(filename, "r:gz", format=tarfile.PAX_FORMAT) as tar:
                tar.extractall(unpack_tmp_folder)

            with io.open(os.path.join(unpack_tmp_folder,
                                      'metadata.json'), 'r', encoding='utf8') as fhandle:
                metadata = json.load(fhandle)
            metadata['export_version'] = 0.0

            with io.open(os.path.join(unpack_tmp_folder, 'metadata.json'),
                         'wb') as fhandle:
                json.dump(metadata, fhandle)

            with tarfile.open(filename, "w:gz", format=tarfile.PAX_FORMAT) as tar:
                tar.add(unpack_tmp_folder, arcname="")

            self.tearDownClass()
            self.setUpClass()

            with self.assertRaises(exceptions.IncompatibleArchiveVersionError):
                import_data(filename, silent=True)
        finally:
            # Deleting the created temporary folders
            shutil.rmtree(export_file_tmp_folder, ignore_errors=True)
            shutil.rmtree(unpack_tmp_folder, ignore_errors=True)

    def test_3(self):
        """
        Test importing of nodes, that have links to unknown nodes.
        """
        import tarfile
        import os
        import shutil
        import tempfile

        from aiida.orm.importexport import export
        from aiida.common.folders import SandboxFolder
        from aiida.orm.node.data.structure import StructureData
        from aiida.orm import load_node
        import aiida.common.json as json

        # Creating a folder for the import/export files
        temp_folder = tempfile.mkdtemp()
        try:
            node_label = "Test structure data"
            sd = StructureData()
            sd.label = str(node_label)
            sd.store()

            filename = os.path.join(temp_folder, "export.tar.gz")
            export([sd], outfile=filename, silent=True)

            unpack = SandboxFolder()
            with tarfile.open(
                    filename, "r:gz", format=tarfile.PAX_FORMAT) as tar:
                tar.extractall(unpack.abspath)

            with io.open(unpack.get_abs_path('data.json'), 'r', encoding='utf8') as fhandle:
                metadata = json.load(fhandle)
            metadata['links_uuid'].append({
                'output': sd.uuid,
                # note: this uuid is supposed to not be in the DB
                'input': get_new_uuid(),
                'label': 'parent'
            })

            with io.open(unpack.get_abs_path('data.json'), 'wb') as fhandle:
                json.dump(metadata, fhandle)

            with tarfile.open(
                    filename, "w:gz", format=tarfile.PAX_FORMAT) as tar:
                tar.add(unpack.abspath, arcname="")

            self.clean_db()

            with self.assertRaises(ValueError):
                import_data(filename, silent=True)

            import_data(filename, ignore_unknown_nodes=True, silent=True)
            self.assertEquals(load_node(sd.uuid).label, node_label)

        finally:
            # Deleting the created temporary folder
            shutil.rmtree(temp_folder, ignore_errors=True)

    def test_4(self):
        """
        Test control of licenses.
        """
        from aiida.common.exceptions import LicensingException
        from aiida.common.folders import SandboxFolder
        from aiida.orm.importexport import export_tree

        from aiida.orm import DataFactory

        StructureData = DataFactory('structure')
        sd = StructureData()
        sd.source = {'license': 'GPL'}
        sd.store()

        folder = SandboxFolder()
        export_tree([sd], folder=folder, silent=True,
                    allowed_licenses=['GPL'])
        # Folder should contain two files of metadata + nodes/
        self.assertEquals(len(folder.get_content_list()), 3)

        folder = SandboxFolder()
        export_tree([sd], folder=folder, silent=True,
                    forbidden_licenses=['Academic'])
        # Folder should contain two files of metadata + nodes/
        self.assertEquals(len(folder.get_content_list()), 3)

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([sd], folder=folder, silent=True,
                        allowed_licenses=['CC0'])

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([sd], folder=folder, silent=True,
                        forbidden_licenses=['GPL'])

        def cc_filter(license):
            return license.startswith('CC')

        def gpl_filter(license):
            return license == 'GPL'

        def crashing_filter(license):
            raise NotImplementedError("not implemented yet")

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([sd], folder=folder, silent=True,
                        allowed_licenses=cc_filter)

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([sd], folder=folder, silent=True,
                        forbidden_licenses=gpl_filter)

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([sd], folder=folder, silent=True,
                        allowed_licenses=crashing_filter)

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([sd], folder=folder, silent=True,
                        forbidden_licenses=crashing_filter)

    def test_5(self):
        """
        This test checks that nodes belonging to different users are correctly
        exported & imported.
        """
        import os
        import shutil
        import tempfile

        from aiida.orm import load_node
        from aiida.orm.node import CalcJobNode
        from aiida.orm.node.data.structure import StructureData
        from aiida.orm.importexport import export
        from aiida.common.links import LinkType
        from aiida.manage import get_manager

        manager = get_manager()

        # Creating a folder for the import/export files
        temp_folder = tempfile.mkdtemp()
        try:
            # Create another user
            new_email = "newuser@new.n"
            user = orm.User(email=new_email).store()

            # Create a structure data node that has a calculation as output
            sd1 = StructureData()
            sd1.set_user(user)
            sd1.label = 'sd1'
            sd1.store()

            jc1 = CalcJobNode()
            jc1.set_computer(self.computer)
            jc1.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
            jc1.set_user(user)
            jc1.label = 'jc1'
            jc1.store()
            jc1.add_incoming(sd1, link_type=LinkType.INPUT_CALC, link_label='link')

            # Create some nodes from a different user
            sd2 = StructureData()
            sd2.set_user(user)
            sd2.label = 'sd2'
            sd2.store()
            sd2.add_incoming(jc1, link_type=LinkType.CREATE, link_label='l1')  # I assume jc1 CREATED sd2

            jc2 = CalcJobNode()
            jc2.set_computer(self.computer)
            jc2.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
            jc2.label = 'jc2'
            jc2.store()
            jc2.add_incoming(sd2, link_type=LinkType.INPUT_CALC, link_label='l2')

            sd3 = StructureData()
            sd3.label = 'sd3'
            sd3.store()
            sd3.add_incoming(jc2, link_type=LinkType.CREATE, link_label='l3')

            uuids_u1 = [sd1.uuid, jc1.uuid, sd2.uuid]
            uuids_u2 = [jc2.uuid, sd3.uuid]

            filename = os.path.join(temp_folder, "export.tar.gz")

            export([sd3], outfile=filename, silent=True)
            self.clean_db()
            import_data(filename, silent=True)

            # Check that the imported nodes are correctly imported and that
            # the user assigned to the nodes is the right one
            for uuid in uuids_u1:
                node = load_node(uuid=uuid)
                self.assertEquals(node.get_user().email, new_email)
            for uuid in uuids_u2:
                self.assertEquals(load_node(uuid).get_user().email, manager.get_profile().default_user_email)
        finally:
            # Deleting the created temporary folder
            shutil.rmtree(temp_folder, ignore_errors=True)

    def test_6(self):
        """
        This test checks that nodes belonging to user A (which is not the
        default user) can be correctly exported, imported, enriched with nodes
        from the default user, re-exported & re-imported and that in the end
        all the nodes that have been finally imported belonging to the right
        users.
        """
        import os
        import shutil
        import tempfile

        from aiida.orm import load_node
        from aiida.orm.node import CalcJobNode
        from aiida.orm.node.data.structure import StructureData
        from aiida.orm.importexport import export
        from aiida.common.links import LinkType
        from aiida.manage import get_manager

        manager = get_manager()

        # Creating a folder for the import/export files
        temp_folder = tempfile.mkdtemp()
        try:
            # Create another user
            new_email = "newuser@new.n"
            user = orm.User(email=new_email).store()

            # Create a structure data node that has a calculation as output
            sd1 = StructureData()
            sd1.set_user(user)
            sd1.label = 'sd1'
            sd1.store()

            jc1 = CalcJobNode()
            jc1.set_computer(self.computer)
            jc1.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
            jc1.set_user(user)
            jc1.label = 'jc1'
            jc1.store()
            jc1.add_incoming(sd1, link_type=LinkType.INPUT_CALC, link_label='link')

            # Create some nodes from a different user
            sd2 = StructureData()
            sd2.set_user(user)
            sd2.label = 'sd2'
            sd2.store()
            sd2.add_incoming(jc1, link_type=LinkType.CREATE, link_label='l1')

            # At this point we export the generated data
            filename1 = os.path.join(temp_folder, "export1.tar.gz")
            export([sd2], outfile=filename1, silent=True)
            uuids1 = [sd1.uuid, jc1.uuid, sd2.uuid]
            self.clean_db()
            self.insert_data()
            import_data(filename1, silent=True)

            # Check that the imported nodes are correctly imported and that
            # the user assigned to the nodes is the right one
            for uuid in uuids1:
                self.assertEquals(load_node(uuid).get_user().email, new_email)

            # Now we continue to generate more data based on the imported
            # data
            sd2_imp = load_node(sd2.uuid)

            jc2 = CalcJobNode()
            jc2.set_computer(self.computer)
            jc2.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
            jc2.label = 'jc2'
            jc2.store()
            jc2.add_incoming(sd2_imp, link_type=LinkType.INPUT_CALC, link_label='l2')

            sd3 = StructureData()
            sd3.label = 'sd3'
            sd3.store()
            sd3.add_incoming(jc2, link_type=LinkType.CREATE, link_label='l3')

            # Store the UUIDs of the nodes that should be checked
            # if they can be imported correctly.
            uuids2 = [jc2.uuid, sd3.uuid]

            filename2 = os.path.join(temp_folder, "export2.tar.gz")
            export([sd3], outfile=filename2, silent=True)
            self.clean_db()
            self.insert_data()
            import_data(filename2, silent=True)

            # Check that the imported nodes are correctly imported and that
            # the user assigned to the nodes is the right one
            for uuid in uuids1:
                self.assertEquals(load_node(uuid).get_user().email, new_email)
            for uuid in uuids2:
                self.assertEquals(load_node(uuid).get_user().email, manager.get_profile().default_user_email)

        finally:
            # Deleting the created temporary folder
            shutil.rmtree(temp_folder, ignore_errors=True)

    def test_7(self):
        """
        This test checks that nodes that belong to a specific group are
        correctly imported and exported.
        """
        import os
        import shutil
        import tempfile

        from aiida.common.links import LinkType
        from aiida.orm import load_node
        from aiida.orm.node import CalcJobNode
        from aiida.orm.node.data.structure import StructureData
        from aiida.orm.importexport import export
        from aiida.orm.querybuilder import QueryBuilder

        # Creating a folder for the import/export files
        temp_folder = tempfile.mkdtemp()
        try:
            # Create another user
            new_email = "newuser@new.n"
            user = orm.User(email=new_email)
            user.store()

            # Create a structure data node that has a calculation as output
            sd1 = StructureData()
            sd1.set_user(user)
            sd1.label = 'sd1'
            sd1.store()

            jc1 = CalcJobNode()
            jc1.set_computer(self.computer)
            jc1.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
            jc1.set_user(user)
            jc1.label = 'jc1'
            jc1.store()
            jc1.add_incoming(sd1, link_type=LinkType.INPUT_CALC, link_label='link')

            # Create a group and add the data inside
            from aiida.orm.groups import Group
            g1 = Group(label="node_group")
            g1.store()
            g1.add_nodes([sd1, jc1])
            g1_uuid = g1.uuid

            # At this point we export the generated data
            filename1 = os.path.join(temp_folder, "export1.tar.gz")
            export([sd1, jc1, g1], outfile=filename1,
                   silent=True)
            n_uuids = [sd1.uuid, jc1.uuid]
            self.clean_db()
            self.insert_data()
            import_data(filename1, silent=True)

            # Check that the imported nodes are correctly imported and that
            # the user assigned to the nodes is the right one
            for uuid in n_uuids:
                self.assertEquals(load_node(uuid).get_user().email, new_email)

            # Check that the exported group is imported correctly
            qb = QueryBuilder()
            qb.append(Group, filters={'uuid': {'==': g1_uuid}})
            self.assertEquals(qb.count(), 1, "The group was not found.")
        finally:
            # Deleting the created temporary folder
            shutil.rmtree(temp_folder, ignore_errors=True)

    def test_group_export(self):
        """
        Test that when exporting just a group, its nodes are also exported
        """
        import os
        import shutil
        import tempfile

        from aiida.orm import load_node
        from aiida.orm.node.data.structure import StructureData
        from aiida.orm.importexport import export
        from aiida.orm.querybuilder import QueryBuilder

        # Creating a folder for the import/export files
        temp_folder = tempfile.mkdtemp()
        try:
            # Create another user
            new_email = "newuser@new.n"
            user = orm.User(email=new_email)
            user.store()

            # Create a structure data node
            sd1 = StructureData()
            sd1.set_user(user)
            sd1.label = 'sd1'
            sd1.store()

            # Create a group and add the data inside
            from aiida.orm.groups import Group
            g1 = Group(label="node_group")
            g1.store()
            g1.add_nodes([sd1])
            g1_uuid = g1.uuid

            # At this point we export the generated data
            filename1 = os.path.join(temp_folder, "export1.tar.gz")
            export([g1], outfile=filename1, silent=True)
            n_uuids = [sd1.uuid]
            self.clean_db()
            self.insert_data()
            import_data(filename1, silent=True)

            # Check that the imported nodes are correctly imported and that
            # the user assigned to the nodes is the right one
            for uuid in n_uuids:
                self.assertEquals(load_node(uuid).get_user().email, new_email)

            # Check that the exported group is imported correctly
            qb = QueryBuilder()
            qb.append(Group, filters={'uuid': {'==': g1_uuid}})
            self.assertEquals(qb.count(), 1, "The group was not found.")
        finally:
            # Deleting the created temporary folder
            shutil.rmtree(temp_folder, ignore_errors=True)

    def test_group_import_existing(self):
        """
        Testing what happens when I try to import a group that already exists in the
        database. This should raise an appropriate exception
        """
        import os
        import shutil
        import tempfile

        from aiida.orm.groups import Group
        from aiida.orm.node.data.structure import StructureData
        from aiida.orm.importexport import export
        from aiida.orm.querybuilder import QueryBuilder

        grouplabel = "node_group_existing"
        # Creating a folder for the import/export files
        temp_folder = tempfile.mkdtemp()
        try:
            # Create another user
            new_email = "newuser@new.n"
            user = orm.User(email=new_email)
            user.store()

            # Create a structure data node
            sd1 = StructureData()
            sd1.set_user(user)
            sd1.label = 'sd'
            sd1.store()

            # Create a group and add the data inside
            g1 = Group(label=grouplabel)
            g1.store()
            g1.add_nodes([sd1])

            # At this point we export the generated data
            filename1 = os.path.join(temp_folder, "export1.tar.gz")
            export([g1], outfile=filename1, silent=True)
            self.clean_db()
            self.insert_data()

            # Creating a group of the same name
            g1 = Group(label="node_group_existing")
            g1.store()
            import_data(filename1, silent=True)
            # The import should have created a new group with a suffix
            # I check for this:
            qb = QueryBuilder().append(Group, filters={'label':{'like':grouplabel+'%'}})
            self.assertEqual(qb.count(),2)
            # Now I check for the group having one member, and whether the name is different:
            qb = QueryBuilder()
            qb.append(Group, filters={'label':{'like':grouplabel+'%'}}, tag='g', project='label')
            qb.append(StructureData, with_group='g')
            self.assertEqual(qb.count(),1)
            # I check that the group name was changed:
            self.assertTrue(qb.all()[0][0] != grouplabel)
            # I import another name, the group should not be imported again
            import_data(filename1, silent=True)
            qb = QueryBuilder()
            qb.append(Group, filters={'label':{'like':grouplabel+'%'}})
            self.assertEqual(qb.count(),2)

        finally:
            # Deleting the created temporary folder
            shutil.rmtree(temp_folder, ignore_errors=True)

    def test_calcfunction_1(self):
        import shutil, os, tempfile
        from aiida.work import calcfunction
        from aiida.orm.node.data.float import Float
        from aiida.orm import load_node
        from aiida.orm.importexport import export
        from aiida.common.exceptions import NotExistent
        # Creating a folder for the import/export files
        temp_folder = tempfile.mkdtemp()

        @calcfunction
        def add(a, b):
            """Add 2 numbers"""
            return {'res': Float(a + b)}

        def max_(**kwargs):
            """select the max value"""
            max_val = max([(v.value, v) for v in kwargs.values()])
            return {'res': max_val[1]}

        try:
            # I'm creating a bunch of nuimbers
            a, b, c, d, e = (Float(i).store() for i in range(5))
            # this adds the maximum number between bcde to a.
            res = add(a=a, b=max_(b=b, c=c, d=d, e=e)['res'])['res']
            # These are the uuids that would be exported as well (as parents) if I wanted the final result
            uuids_values = [(a.uuid, a.value), (e.uuid, e.value), (res.uuid, res.value)]
            # These are the uuids that shouldn't be exported since it's a selection.
            not_wanted_uuids = [v.uuid for v in (b, c, d)]
            # At this point we export the generated data
            filename1 = os.path.join(temp_folder, "export1.tar.gz")
            export([res], outfile=filename1, silent=True, return_reversed=True)
            self.clean_db()
            self.insert_data()
            import_data(filename1, silent=True)
            # Check that the imported nodes are correctly imported and that the value is preserved
            for uuid, value in uuids_values:
                self.assertEquals(load_node(uuid).value, value)
            for uuid in not_wanted_uuids:
                with self.assertRaises(NotExistent):
                    load_node(uuid)
        finally:
            # Deleting the created temporary folder
            shutil.rmtree(temp_folder, ignore_errors=True)

    def test_workcalculation_2(self):
        import shutil, os, tempfile

        from aiida.orm.node import WorkChainNode
        from aiida.orm.node.data.int import Int
        from aiida.orm import load_node
        from aiida.common.links import LinkType
        from aiida.orm.importexport import export

        # Creating a folder for the import/export files
        temp_folder = tempfile.mkdtemp()

        try:
            master = WorkChainNode().store()
            slave = WorkChainNode().store()

            input_1 = Int(3).store()
            input_2 = Int(5).store()
            output_1 = Int(2).store()

            master.add_incoming(input_1, LinkType.INPUT_WORK, 'input_1')
            slave.add_incoming(master, LinkType.CALL_WORK, 'CALL')
            slave.add_incoming(input_2, LinkType.INPUT_WORK, 'input_2')
            output_1.add_incoming(master, LinkType.RETURN, 'RETURN')

            uuids_values = [(v.uuid, v.value) for v in (output_1,)]
            filename1 = os.path.join(temp_folder, "export1.tar.gz")
            export([output_1], outfile=filename1, silent=True)
            self.clean_db()
            self.insert_data()
            import_data(filename1, silent=True)

            for uuid, value in uuids_values:
                self.assertEquals(load_node(uuid).value, value)

        finally:
            # Deleting the created temporary folder
            shutil.rmtree(temp_folder, ignore_errors=True)

    def test_reexport(self):
        """
        Export something, import and reexport and check if everything is valid.
        The export is rather easy::

            ___       ___          ___
           |   | INP |   | CREATE |   |
           | p | --> | c | -----> | a |
           |___|     |___|        |___|

        """
        import os, shutil, tempfile, numpy as np, string, random
        from datetime import datetime

        from aiida.orm import load_node, Group
        from aiida.orm.node.data.array import ArrayData
        from aiida.orm.node.data.parameter import ParameterData
        from aiida.orm.node import CalculationNode
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.importexport import export
        from aiida.common.hashing import make_hash
        from aiida.common.links import LinkType

        def get_hash_from_db_content(grouplabel):
            qb = QueryBuilder()
            qb.append(ParameterData, tag='p', project='*')
            qb.append(CalculationNode, tag='c', project='*', edge_tag='p2c', edge_project=('label', 'type'))
            qb.append(ArrayData, tag='a', project='*', edge_tag='c2a', edge_project=('label', 'type'))
            qb.append(Group, filters={'label': grouplabel}, project='*', tag='g', with_node='a')
            # I want the query to contain something!
            self.assertTrue(qb.count() > 0)
            # The hash is given from the preservable entries in an export-import cycle,
            # uuids, attributes, labels, descriptions, arrays, link-labels, link-types:
            hash_ = make_hash([(
                item['p']['*'].get_attrs(),
                item['p']['*'].uuid,
                item['p']['*'].label,
                item['p']['*'].description,
                item['c']['*'].uuid,
                item['c']['*'].get_attrs(),
                item['a']['*'].get_attrs(),
                [item['a']['*'].get_array(name) for name in item['a']['*'].get_arraynames()],
                item['a']['*'].uuid,
                item['g']['*'].uuid,
                item['g']['*'].label,
                item['p2c']['label'],
                item['p2c']['type'],
                item['c2a']['label'],
                item['c2a']['type'],
                item['g']['*'].label,
            ) for item in qb.dict()])
            return hash_

        # Creating a folder for the import/export files
        temp_folder = tempfile.mkdtemp()
        chars = string.ascii_uppercase + string.digits
        size = 10
        grouplabel = 'test-group'
        try:
            nparr = np.random.random((4, 3, 2))
            trial_dict = {}
            # give some integers:
            trial_dict.update({str(k): np.random.randint(100) for k in range(10)})
            # give some floats:
            trial_dict.update({str(k): np.random.random() for k in range(10, 20)})
            # give some booleans:
            trial_dict.update({str(k): bool(np.random.randint(1)) for k in range(20, 30)})
            # give some datetime:
            trial_dict.update({str(k): datetime(
                year=2017,
                month=np.random.randint(1, 12),
                day=np.random.randint(1, 28)) for k in range(30, 40)})
            # give some text:
            trial_dict.update({str(k): ''.join(random.choice(chars) for _ in range(size)) for k in range(20, 30)})

            p = ParameterData(dict=trial_dict)
            p.label = str(datetime.now())
            p.description = 'd_' + str(datetime.now())
            p.store()
            c = CalculationNode()
            # setting also trial dict as attributes, but randomizing the keys)
            (c._set_attr(str(int(k) + np.random.randint(10)), v) for k, v in trial_dict.items())
            c.store()
            a = ArrayData()
            a.set_array('array', nparr)
            a.store()
            # LINKS
            # the calculation has input the parameters-instance
            c.add_incoming(p, link_type=LinkType.INPUT_CALC, link_label='input_parameters')
            # I want the array to be an output of the calculation
            a.add_incoming(c, link_type=LinkType.CREATE, link_label='output_array')
            g = Group(label='test-group')
            g.store()
            g.add_nodes(a)

            hash_from_dbcontent = get_hash_from_db_content(grouplabel)

            # I export and reimport 3 times in a row:
            for i in range(3):
                # Always new filename:
                filename = os.path.join(temp_folder, "export-{}.zip".format(i))
                # Loading the group from the string
                g = Group.get_from_string(grouplabel)
                # exporting based on all members of the group
                # this also checks if group memberships are preserved!
                export([g] + [n for n in g.nodes], outfile=filename, silent=True)
                # cleaning the DB!
                self.clean_db()
                # reimporting the data from the file
                import_data(filename, silent=True, ignore_unknown_nodes=True)
                # creating the hash from db content
                new_hash = get_hash_from_db_content(grouplabel)
                # I check for equality against the first hash created, which implies that hashes
                # are equal in all iterations of this process
                self.assertEqual(hash_from_dbcontent, new_hash)

        finally:
            # Deleting the created temporary folder
            shutil.rmtree(temp_folder, ignore_errors=True)


class TestComplex(AiidaTestCase):
    def test_complex_graph_import_export(self):
        """
        This test checks that a small and bit complex graph can be correctly
        exported and imported.

        It will create the graph, store it to the database, export it to a file
        and import it. In the end it will check if the initial nodes are present
        at the imported graph.
        """
        import tempfile
        import shutil
        import os

        from aiida.orm.node import CalcJobNode
        from aiida.orm.node.data.folder import FolderData
        from aiida.orm.node.data.parameter import ParameterData
        from aiida.orm.node.data.remote import RemoteData
        from aiida.common.links import LinkType
        from aiida.orm.importexport import export, import_data
        from aiida.orm.utils import load_node
        from aiida.common.exceptions import NotExistent

        temp_folder = tempfile.mkdtemp()
        try:
            calc1 = CalcJobNode()
            calc1.set_computer(self.computer)
            calc1.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
            calc1.label = "calc1"
            calc1.store()

            pd1 = ParameterData()
            pd1.label = "pd1"
            pd1.store()

            pd2 = ParameterData()
            pd2.label = "pd2"
            pd2.store()

            rd1 = RemoteData()
            rd1.label = "rd1"
            rd1.set_remote_path("/x/y.py")
            rd1.set_computer(self.computer)
            rd1.store()
            rd1.add_incoming(calc1, link_type=LinkType.CREATE, link_label='link')

            calc2 = CalcJobNode()
            calc2.set_computer(self.computer)
            calc2.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
            calc2.label = "calc2"
            calc2.store()
            calc2.add_incoming(pd1, link_type=LinkType.INPUT_CALC, link_label='link1')
            calc2.add_incoming(pd2, link_type=LinkType.INPUT_CALC, link_label='link2')
            calc2.add_incoming(rd1, link_type=LinkType.INPUT_CALC, link_label='link3')

            fd1 = FolderData()
            fd1.label = "fd1"
            fd1.store()
            fd1.add_incoming(calc2, link_type=LinkType.CREATE, link_label='link')

            node_uuids_labels = {calc1.uuid: calc1.label, pd1.uuid: pd1.label,
                                 pd2.uuid: pd2.label, rd1.uuid: rd1.label,
                                 calc2.uuid: calc2.label, fd1.uuid: fd1.label}

            filename = os.path.join(temp_folder, "export.tar.gz")
            export([fd1], outfile=filename, silent=True)

            self.clean_db()

            import_data(filename, silent=True, ignore_unknown_nodes=True)

            for uuid, label in node_uuids_labels.items():
                try:
                    load_node(uuid)
                except NotExistent:
                    self.fail("Node with UUID {} and label {} was not "
                              "found.".format(uuid, label))

        finally:
            # Deleting the created temporary folder
            shutil.rmtree(temp_folder, ignore_errors=True)


class TestComputer(AiidaTestCase):

    def setUp(self):
        self.clean_db()
        self.insert_data()

    def tearDown(self):
        pass

    def test_same_computer_import(self):
        """
        Test that you can import nodes in steps without any problems. In this
        test we will import a first calculation and then a second one. The
        import should work as expected and have in the end two job
        calculations.

        Each calculation is related to the same computer. In the end we should
        have only one computer
        """
        import os
        import shutil
        import tempfile

        from aiida.orm.importexport import export
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.computers import Computer
        from aiida.orm.node import CalcJobNode

        # Creating a folder for the import/export files
        export_file_tmp_folder = tempfile.mkdtemp()
        unpack_tmp_folder = tempfile.mkdtemp()

        try:
            # Store two job calculation related to the same computer
            calc1_label = "calc1"
            calc1 = CalcJobNode()
            calc1.set_computer(self.computer)
            calc1.set_option('resources', {"num_machines": 1,
                                           "num_mpiprocs_per_machine": 1})
            calc1.label = calc1_label
            calc1.store()

            calc2_label = "calc2"
            calc2 = CalcJobNode()
            calc2.set_computer(self.computer)
            calc2.set_option('resources', {"num_machines": 2,
                                           "num_mpiprocs_per_machine": 2})
            calc2.label = calc2_label
            calc2.store()

            # Store locally the computer name
            comp_name = six.text_type(self.computer.name)
            comp_uuid = six.text_type(self.computer.uuid)

            # Export the first job calculation
            filename1 = os.path.join(export_file_tmp_folder, "export1.tar.gz")
            export([calc1], outfile=filename1, silent=True)

            # Export the second job calculation
            filename2 = os.path.join(export_file_tmp_folder, "export2.tar.gz")
            export([calc2], outfile=filename2, silent=True)

            # Clean the local database
            self.clean_db()

            # Check that there are no computers
            qb = QueryBuilder()
            qb.append(Computer, project=['*'])
            self.assertEqual(qb.count(), 0, "There should not be any computers"
                                            "in the database at this point.")

            # Check that there are no calculations
            qb = QueryBuilder()
            qb.append(CalcJobNode, project=['*'])
            self.assertEqual(qb.count(), 0, "There should not be any "
                                            "calculations in the database at "
                                            "this point.")

            # Import the first calculation
            import_data(filename1, silent=True)

            # Check that the calculation computer is imported correctly.
            qb = QueryBuilder()
            qb.append(CalcJobNode, project=['label'])
            self.assertEqual(qb.count(), 1, "Only one calculation should be "
                                            "found.")
            self.assertEqual(six.text_type(qb.first()[0]), calc1_label,
                             "The calculation label is not correct.")

            # Check that the referenced computer is imported correctly.
            qb = QueryBuilder()
            qb.append(Computer, project=['name', 'uuid', 'id'])
            self.assertEqual(qb.count(), 1, "Only one computer should be "
                                            "found.")
            self.assertEqual(six.text_type(qb.first()[0]), comp_name,
                             "The computer name is not correct.")
            self.assertEqual(six.text_type(qb.first()[1]), comp_uuid,
                             "The computer uuid is not correct.")

            # Store the id of the computer
            comp_id = qb.first()[2]

            # Import the second calculation
            import_data(filename2, silent=True)

            # Check that the number of computers remains the same and its data
            # did not change.
            qb = QueryBuilder()
            qb.append(Computer, project=['name', 'uuid', 'id'])
            self.assertEqual(qb.count(), 1, "Found {} computers"
                                            "but only one computer should be found.".format(qb.count()))
            self.assertEqual(six.text_type(qb.first()[0]), comp_name,
                             "The computer name is not correct.")
            self.assertEqual(six.text_type(qb.first()[1]), comp_uuid,
                             "The computer uuid is not correct.")
            self.assertEqual(qb.first()[2], comp_id,
                             "The computer id is not correct.")

            # Check that now you have two calculations attached to the same
            # computer.
            qb = QueryBuilder()
            qb.append(Computer, tag='comp')
            qb.append(CalcJobNode, with_computer='comp', project=['label'])
            self.assertEqual(qb.count(), 2, "Two calculations should be "
                                            "found.")
            ret_labels = set(_ for [_] in qb.all())
            self.assertEqual(ret_labels, set([calc1_label, calc2_label]),
                             "The labels of the calculations are not correct.")

        finally:
            # Deleting the created temporary folders
            shutil.rmtree(export_file_tmp_folder, ignore_errors=True)
            shutil.rmtree(unpack_tmp_folder, ignore_errors=True)

    def test_same_computer_different_name_import(self):
        """
        This test checks that if the computer is re-imported with a different
        name to the same database, then the original computer will not be
        renamed. It also checks that the names were correctly imported (without
        any change since there is no computer name collision)
        """
        import os
        import shutil
        import tempfile

        from aiida.orm.importexport import export
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.computers import Computer
        from aiida.orm.node import CalcJobNode

        # Creating a folder for the import/export files
        export_file_tmp_folder = tempfile.mkdtemp()
        unpack_tmp_folder = tempfile.mkdtemp()

        try:
            # Store a calculation
            calc1_label = "calc1"
            calc1 = CalcJobNode()
            calc1.set_computer(self.computer)
            calc1.set_option('resources', {"num_machines": 1,
                                           "num_mpiprocs_per_machine": 1})
            calc1.label = calc1_label
            calc1.store()

            # Store locally the computer name
            comp1_name = six.text_type(self.computer.name)

            # Export the first job calculation
            filename1 = os.path.join(export_file_tmp_folder, "export1.tar.gz")
            export([calc1], outfile=filename1, silent=True)

            # Rename the computer
            self.computer.set_name(comp1_name + "_updated")

            # Store a second calculation
            calc2_label = "calc2"
            calc2 = CalcJobNode()
            calc2.set_computer(self.computer)
            calc2.set_option('resources', {"num_machines": 2,
                                           "num_mpiprocs_per_machine": 2})
            calc2.label = calc2_label
            calc2.store()

            # Export the second job calculation
            filename2 = os.path.join(export_file_tmp_folder, "export2.tar.gz")
            export([calc2], outfile=filename2, silent=True)

            # Clean the local database
            self.clean_db()

            # Check that there are no computers
            qb = QueryBuilder()
            qb.append(Computer, project=['*'])
            self.assertEqual(qb.count(), 0, "There should not be any computers"
                                            "in the database at this point.")

            # Check that there are no calculations
            qb = QueryBuilder()
            qb.append(CalcJobNode, project=['*'])
            self.assertEqual(qb.count(), 0, "There should not be any "
                                            "calculations in the database at "
                                            "this point.")

            # Import the first calculation
            import_data(filename1, silent=True)

            # Check that the calculation computer is imported correctly.
            qb = QueryBuilder()
            qb.append(CalcJobNode, project=['label'])
            self.assertEqual(qb.count(), 1, "Only one calculation should be "
                                            "found.")
            self.assertEqual(six.text_type(qb.first()[0]), calc1_label,
                             "The calculation label is not correct.")

            # Check that the referenced computer is imported correctly.
            qb = QueryBuilder()
            qb.append(Computer, project=['name', 'uuid', 'id'])
            self.assertEqual(qb.count(), 1, "Only one computer should be "
                                            "found.")
            self.assertEqual(six.text_type(qb.first()[0]), comp1_name,
                             "The computer name is not correct.")

            # Import the second calculation
            import_data(filename2, silent=True)

            # Check that the number of computers remains the same and its data
            # did not change.
            qb = QueryBuilder()
            qb.append(Computer, project=['name'])
            self.assertEqual(qb.count(), 1, "Found {} computers"
                                            "but only one computer should be found.".format(qb.count()))
            self.assertEqual(six.text_type(qb.first()[0]), comp1_name,
                             "The computer name is not correct.")

        finally:
            # Deleting the created temporary folders
            shutil.rmtree(export_file_tmp_folder, ignore_errors=True)
            shutil.rmtree(unpack_tmp_folder, ignore_errors=True)

    def test_different_computer_same_name_import(self):
        """
        This test checks that if there is a name collision, the imported
        computers are renamed accordingly.
        """
        import os
        import shutil
        import tempfile

        from aiida.orm.importexport import export
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.computers import Computer
        from aiida.orm.node import CalcJobNode
        from aiida.orm.importexport import DUPL_SUFFIX

        # Creating a folder for the import/export files
        export_file_tmp_folder = tempfile.mkdtemp()
        unpack_tmp_folder = tempfile.mkdtemp()

        try:
            # Set the computer name
            comp1_name = "localhost_1"
            self.computer.set_name(comp1_name)

            # Store a calculation
            calc1_label = "calc1"
            calc1 = CalcJobNode()
            calc1.set_computer(self.computer)
            calc1.set_option('resources', {"num_machines": 1,
                                           "num_mpiprocs_per_machine": 1})
            calc1.label = calc1_label
            calc1.store()

            # Export the first job calculation
            filename1 = os.path.join(export_file_tmp_folder, "export1.tar.gz")
            export([calc1], outfile=filename1, silent=True)

            # Reset the database
            self.clean_db()
            self.insert_data()

            # Set the computer name to the same name as before
            self.computer.set_name(comp1_name)

            # Store a second calculation
            calc2_label = "calc2"
            calc2 = CalcJobNode()
            calc2.set_computer(self.computer)
            calc2.set_option('resources', {"num_machines": 2,
                                           "num_mpiprocs_per_machine": 2})
            calc2.label = calc2_label
            calc2.store()

            # Export the second job calculation
            filename2 = os.path.join(export_file_tmp_folder, "export2.tar.gz")
            export([calc2], outfile=filename2, silent=True)

            # Reset the database
            self.clean_db()
            self.insert_data()

            # Set the computer name to the same name as before
            self.computer.set_name(comp1_name)

            # Store a third calculation
            calc3_label = "calc3"
            calc3 = CalcJobNode()
            calc3.set_computer(self.computer)
            calc3.set_option('resources', {"num_machines": 2,
                                           "num_mpiprocs_per_machine": 2})
            calc3.label = calc3_label
            calc3.store()

            # Export the third job calculation
            filename3 = os.path.join(export_file_tmp_folder, "export3.tar.gz")
            export([calc3], outfile=filename3, silent=True)

            # Clean the local database
            self.clean_db()

            # Check that there are no computers
            qb = QueryBuilder()
            qb.append(Computer, project=['*'])
            self.assertEqual(qb.count(), 0, "There should not be any computers"
                                            "in the database at this point.")

            # Check that there are no calculations
            qb = QueryBuilder()
            qb.append(CalcJobNode, project=['*'])
            self.assertEqual(qb.count(), 0, "There should not be any "
                                            "calculations in the database at "
                                            "this point.")

            # Import all the calculations
            import_data(filename1, silent=True)
            import_data(filename2, silent=True)
            import_data(filename3, silent=True)

            # Retrieve the calculation-computer pairs
            qb = QueryBuilder()
            qb.append(CalcJobNode, project=['label'], tag='jcalc')
            qb.append(Computer, project=['name'],
                      with_node='jcalc')
            self.assertEqual(qb.count(), 3, "Three combinations expected.")
            res = qb.all()
            self.assertIn([calc1_label, comp1_name], res,
                          "Calc-Computer combination not found.")
            self.assertIn([calc2_label,
                           comp1_name + DUPL_SUFFIX.format(0)], res,
                          "Calc-Computer combination not found.")
            self.assertIn([calc3_label,
                           comp1_name + DUPL_SUFFIX.format(1)], res,
                          "Calc-Computer combination not found.")
        finally:
            # Deleting the created temporary folders
            shutil.rmtree(export_file_tmp_folder, ignore_errors=True)
            shutil.rmtree(unpack_tmp_folder, ignore_errors=True)

    def test_correct_import_of_computer_json_params(self):
        """
        This test checks that the metadata and transport params are
        exported and imported correctly in both backends.
        """
        import os
        import shutil
        import tempfile

        from aiida.orm.importexport import export
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.computers import Computer
        from aiida.orm.node import CalcJobNode

        # Creating a folder for the import/export files
        export_file_tmp_folder = tempfile.mkdtemp()
        unpack_tmp_folder = tempfile.mkdtemp()

        try:
            # Set the computer name
            comp1_name = "localhost_1"
            comp1_metadata = {
                u'workdir': u'/tmp/aiida'
            }
            comp1_transport_params = {
                u'key1': u'value1',
                u'key2': 2
            }
            self.computer.set_name(comp1_name)
            self.computer._set_metadata(comp1_metadata)
            self.computer.set_transport_params(comp1_transport_params)

            # Store a calculation
            calc1_label = "calc1"
            calc1 = CalcJobNode()
            calc1.set_computer(self.computer)
            calc1.set_option('resources', {"num_machines": 1,
                                           "num_mpiprocs_per_machine": 1})
            calc1.label = calc1_label
            calc1.store()

            # Export the first job calculation
            filename1 = os.path.join(export_file_tmp_folder, "export1.tar.gz")
            export([calc1], outfile=filename1, silent=True)

            # Clean the local database
            self.clean_db()
            # Import the data
            import_data(filename1, silent=True)

            qb = QueryBuilder()
            qb.append(Computer, project=['transport_params', '_metadata'],
                      tag="comp")
            self.assertEqual(qb.count(), 1, "Expected only one computer")

            res = qb.dict()[0]
            self.assertEqual(res['comp']['transport_params'],
                             comp1_transport_params,
                             "Not the expected transport parameters "
                             "were found")
            self.assertEqual(res['comp']['_metadata'],
                             comp1_metadata,
                             "Not the expected metadata were found")
        finally:
            # Deleting the created temporary folders
            shutil.rmtree(export_file_tmp_folder, ignore_errors=True)
            shutil.rmtree(unpack_tmp_folder, ignore_errors=True)

    @unittest.skip('reenable when issue #2342 is addressed')
    def test_import_of_django_sqla_export_file(self):
        """
        Check why sqla import manages to import the django export file correctly
        """
        from aiida.backends.tests.utils.fixtures import import_archive_fixture
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.computers import Computer

        for archive in ['export/compare/django.aiida', 'export/compare/sqlalchemy.aiida']:
            # Clean the database
            self.reset_database()

            # Import the needed data
            import_archive_fixture(archive)

            # The expected metadata & transport parameters
            comp1_metadata = {
                u'workdir': u'/tmp/aiida'
            }
            comp1_transport_params = {
                u'key1': u'value1',
                u'key2': 2
            }

            # Check that we got the correct metadata & transport parameters
            # Make sure to exclude the default computer
            qb = QueryBuilder()
            qb.append(Computer, project=['transport_params', '_metadata'], tag="comp",
                      filters={'name': {'!==': self.computer.name}})
            self.assertEqual(qb.count(), 1, "Expected only one computer")

            res = qb.dict()[0]

            self.assertEqual(res['comp']['transport_params'], comp1_transport_params)
            self.assertEqual(res['comp']['_metadata'], comp1_metadata)


class TestLinks(AiidaTestCase):

    def setUp(self):
        self.reset_database()

    def get_all_node_links(self):
        """
        """
        from aiida.orm import load_node, Node
        from aiida.orm.querybuilder import QueryBuilder
        qb = QueryBuilder()
        qb.append(Node, project='uuid', tag='input')
        qb.append(Node, project='uuid', tag='output',
                  edge_project=['label', 'type'], with_incoming='input')
        return qb.all()

    def test_input_and_create_links(self):
        """
        Simple test that will verify that INPUT and CREATE links are properly exported and
        correctly recreated upon import.
        """
        import os, shutil, tempfile

        from aiida.orm.node.data.int import Int
        from aiida.orm.importexport import export
        from aiida.orm.node import CalculationNode
        from aiida.common.links import LinkType

        tmp_folder = tempfile.mkdtemp()

        try:
            node_work = CalculationNode().store()
            node_input = Int(1).store()
            node_output = Int(2).store()

            node_work.add_incoming(node_input, LinkType.INPUT_CALC, 'input')
            node_output.add_incoming(node_work, LinkType.CREATE, 'output')

            export_links = self.get_all_node_links()
            export_file = os.path.join(tmp_folder, 'export.tar.gz')
            export([node_output], outfile=export_file, silent=True)

            self.reset_database()

            import_data(export_file, silent=True)
            import_links = self.get_all_node_links()

            export_set = [tuple(_) for _ in export_links]
            import_set = [tuple(_) for _ in import_links]

            self.assertEquals(set(export_set), set(import_set))
        finally:
            shutil.rmtree(tmp_folder, ignore_errors=True)

    def construct_complex_graph(self, export_combination=0):
        """
        This method creates a "complex" graph with all available link types
        (INPUT, CREATE, RETURN and CALL) and returns the nodes of the graph. It
        also returns various combinations of nodes that need to be extracted
        but also the final expected set of nodes (after adding the expected
        predecessors, desuccessors).
        """
        from aiida.orm.node.data.base import Int
        from aiida.orm.node import CalcJobNode
        from aiida.orm.node import WorkChainNode
        from aiida.common.links import LinkType

        if export_combination < 0 or export_combination > 8:
            return None

        # Node creation
        d1 = Int(1).store()
        d2 = Int(1).store()
        wc1 = WorkChainNode().store()
        wc2 = WorkChainNode().store()

        pw1 = CalcJobNode()
        pw1.set_computer(self.computer)
        pw1.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
        pw1.store()

        d3 = Int(1).store()
        d4 = Int(1).store()

        pw2 = CalcJobNode()
        pw2.set_computer(self.computer)
        pw2.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
        pw2.store()

        d5 = Int(1).store()
        d6 = Int(1).store()

        # Link creation
        wc1.add_incoming(d1, LinkType.INPUT_WORK, 'input1')
        wc1.add_incoming(d2, LinkType.INPUT_WORK, 'input2')

        wc2.add_incoming(d1, LinkType.INPUT_WORK, 'input')
        wc2.add_incoming(wc1, LinkType.CALL_WORK, 'call')

        pw1.add_incoming(d1, LinkType.INPUT_CALC, 'input')
        pw1.add_incoming(wc2, LinkType.CALL_CALC, 'call')

        d3.add_incoming(pw1, LinkType.CREATE, 'create1')
        d3.add_incoming(wc2, LinkType.RETURN, 'return1')

        d4.add_incoming(pw1, LinkType.CREATE, 'create2')
        d4.add_incoming(wc2, LinkType.RETURN, 'return2')

        pw2.add_incoming(d4, LinkType.INPUT_CALC, 'input')

        d5.add_incoming(pw2, LinkType.CREATE, 'create5')
        d6.add_incoming(pw2, LinkType.CREATE, 'create6')

        # Return the generated nodes
        graph_nodes = [d1, d2, d3, d4, d5, d6, pw1, pw2, wc1, wc2]

        # Create various combinations of nodes that should be exported
        # and the final set of nodes that are exported in each case, following
        # predecessor/successor links.
        export_list = [
            (wc1, [d1, d2, d3, d4, pw1, wc1, wc2]),
            (wc2, [d1, d3, d4, pw1, wc2]),
            (d3, [d1, d3, d4, pw1]),
            (d4, [d1, d3, d4, pw1]),
            (d5, [d1, d3, d4, d5, d6, pw1, pw2]),
            (d6, [d1, d3, d4, d5, d6, pw1, pw2]),
            (pw2, [d1, d3, d4, d5, d6, pw1, pw2]),
            (d1, [d1]),
            (d2, [d2])
        ]

        return graph_nodes, export_list[export_combination]

    def test_data_create_reversed_false(self):
        """Verify that create_reversed = False is respected when only exporting Data nodes."""
        import os
        import shutil
        import tempfile

        from aiida.orm import Data, Group
        from aiida.orm.node.data.base import Int
        from aiida.orm.node import CalcJobNode
        from aiida.orm.importexport import export
        from aiida.common.links import LinkType
        from aiida.orm.querybuilder import QueryBuilder

        tmp_folder = tempfile.mkdtemp()

        try:
            data_input = Int(1).store()
            data_output = Int(2).store()

            calc = CalcJobNode()
            calc.set_computer(self.computer)
            calc.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
            calc.store()

            calc.add_incoming(data_input, LinkType.INPUT_CALC, 'input')
            data_output.add_incoming(calc, LinkType.CREATE, 'create')

            group = orm.Group(label='test_group').store()
            group.add_nodes(data_output)

            export_file = os.path.join(tmp_folder, 'export.tar.gz')
            export([group], outfile=export_file, silent=True, create_reversed=False)

            self.reset_database()

            import_data(export_file, silent=True)

            builder = QueryBuilder()
            builder.append(Data)
            self.assertEqual(builder.count(), 1, 'Expected a single Data node but got {}'.format(builder.count()))
            self.assertEqual(builder.all()[0][0].uuid, data_output.uuid)

            builder = QueryBuilder()
            builder.append(CalcJobNode)
            self.assertEqual(builder.count(), 0, 'Expected no Calculation nodes')
        finally:
            shutil.rmtree(tmp_folder, ignore_errors=True)

    def test_complex_workflow_graph_links(self):
        """
        This test checks that all the needed links are correctly exported and
        imported. More precisely, it checks that INPUT, CREATE, RETURN and CALL
        links connecting Data nodes, CalcJobNodes and WorkCalculations are
        exported and imported correctly.
        """
        import os, shutil, tempfile

        from aiida.orm import Node
        from aiida.orm.importexport import export
        from aiida.common.links import LinkType
        from aiida.orm.querybuilder import QueryBuilder
        tmp_folder = tempfile.mkdtemp()

        try:
            graph_nodes, _ = self.construct_complex_graph()

            # Getting the input, create, return and call links
            qb = QueryBuilder()
            qb.append(Node, project='uuid')
            qb.append(Node, project='uuid',
                      edge_project=['label', 'type'],
                      edge_filters={'type': {'in': (LinkType.INPUT_CALC.value,
                                                    LinkType.INPUT_WORK.value,
                                                    LinkType.CREATE.value,
                                                    LinkType.RETURN.value,
                                                    LinkType.CALL_CALC.value,
                                                    LinkType.CALL_WORK.value)}})
            export_links = qb.all()

            export_file = os.path.join(tmp_folder, 'export.tar.gz')
            export(graph_nodes, outfile=export_file, silent=True)

            self.reset_database()

            import_data(export_file, silent=True)
            import_links = self.get_all_node_links()

            export_set = [tuple(_) for _ in export_links]
            import_set = [tuple(_) for _ in import_links]

            self.assertEquals(set(export_set), set(import_set))
        finally:
            shutil.rmtree(tmp_folder, ignore_errors=True)

    def test_complex_workflow_graph_export_set_expansion(self):
        import os, shutil, tempfile
        from aiida.orm.importexport import export
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm import Node

        for export_conf in range(0, 8):

            graph_nodes, (export_node, export_target) = (
                self.construct_complex_graph(export_conf))

            tmp_folder = tempfile.mkdtemp()
            try:
                export_file = os.path.join(tmp_folder, 'export.tar.gz')
                export([export_node], outfile=export_file, silent=True)
                export_node_str = str(export_node)

                self.reset_database()

                import_data(export_file, silent=True)

                # Get all the nodes of the database
                qb = QueryBuilder()
                qb.append(Node, project='uuid')
                imported_node_uuids = set(str(_[0]) for _ in qb.all())

                export_target_uuids = set(str(_.uuid) for _ in export_target)

                from aiida.orm.utils import load_node
                self.assertEquals(
                    export_target_uuids,
                    imported_node_uuids,
                    "Problem in comparison of export node: " +
                    str(export_node_str) + "\n" +
                    "Expected set: " + str(export_target_uuids) + "\n" +
                    "Imported set: " + str(imported_node_uuids) + "\n" +
                    "Difference: " + str([load_node(_) for _ in
                                          export_target_uuids.symmetric_difference(
                                              imported_node_uuids)])
                )

            finally:
                shutil.rmtree(tmp_folder, ignore_errors=True)

    def test_recursive_export_input_and_create_links_proper(self):
        """
        Check that CALL, INPUT, RETURN and CREATE links are followed
        recursively.
        """
        import os, shutil, tempfile
        from aiida.orm import Node
        from aiida.orm.node.data.base import Int
        from aiida.orm.importexport import export
        from aiida.orm.node import CalculationNode, WorkflowNode
        from aiida.common.links import LinkType
        from aiida.orm.querybuilder import QueryBuilder
        tmp_folder = tempfile.mkdtemp()

        try:
            wc2 = WorkflowNode().store()
            wc1 = WorkflowNode().store()
            c1 = CalculationNode().store()
            ni1 = Int(1).store()
            ni2 = Int(2).store()
            no1 = Int(1).store()
            no2 = Int(2).store()

            # Create the connections between workcalculations and calculations
            wc1.add_incoming(wc2, LinkType.CALL_WORK, 'call')
            c1.add_incoming(wc1, LinkType.CALL_CALC, 'call')

            # Connect the first data node to wc1 & c1
            wc1.add_incoming(ni1, LinkType.INPUT_WORK, 'ni1-to-wc1')
            c1.add_incoming(ni1, LinkType.INPUT_CALC, 'ni1-to-c1')

            # Connect the second data node to wc1 & c1
            wc1.add_incoming(ni2, LinkType.INPUT_WORK, 'ni2-to-wc1')
            c1.add_incoming(ni2, LinkType.INPUT_CALC, 'ni2-to-c1')

            # Connecting the first output node to wc1 & c1
            no1.add_incoming(wc1, LinkType.RETURN, 'output1')
            no1.add_incoming(c1, LinkType.CREATE, 'output1')

            # Connecting the second output node to wc1 & c1
            no2.add_incoming(wc1, LinkType.RETURN, 'output2')
            no2.add_incoming(c1, LinkType.CREATE, 'output2')

            # Getting the input, create, return and call links
            qb = QueryBuilder()
            qb.append(Node, project='uuid')
            qb.append(Node, project='uuid',
                      edge_project=['label', 'type'],
                      edge_filters={'type': {'in': (LinkType.INPUT_CALC.value,
                                                    LinkType.INPUT_WORK.value,
                                                    LinkType.CREATE.value,
                                                    LinkType.RETURN.value,
                                                    LinkType.CALL_CALC.value,
                                                    LinkType.CALL_WORK.value)}})
            export_links = qb.all()

            export_file = os.path.join(tmp_folder, 'export.tar.gz')
            export([wc2], outfile=export_file, silent=True)

            self.reset_database()

            import_data(export_file, silent=True)
            import_links = self.get_all_node_links()

            export_set = [tuple(_) for _ in export_links]
            import_set = [tuple(_) for _ in import_links]

            self.assertEquals(set(export_set), set(import_set))
        finally:
            shutil.rmtree(tmp_folder, ignore_errors=True)

    def test_links_for_workflows(self):
        """
        Check that CALL links are not followed in the export procedure, and the only creation
        is followed for data::

            ____       ____        ____
           |    | INP |    | CALL |    |
           | i1 | --> | w1 | <--- | w2 |
           |____|     |____|      |____|
                       | |
                CREATE v v RETURN
                       ____
                      |    |
                      | o1 |
                      |____|

        """
        import os, shutil, tempfile

        from aiida.orm.node.data.base import Int
        from aiida.orm.importexport import export
        from aiida.orm.node import WorkChainNode
        from aiida.common.links import LinkType
        tmp_folder = tempfile.mkdtemp()

        try:
            w1 = WorkChainNode().store()
            w2 = WorkChainNode().store()
            i1 = Int(1).store()
            o1 = Int(2).store()

            w1.add_incoming(i1, LinkType.INPUT_WORK, 'input-i1')
            w1.add_incoming(w2, LinkType.CALL_WORK, 'call')
            o1.add_incoming(w1, LinkType.RETURN, 'return')

            links_wanted = [l for l in self.get_all_node_links() if l[3] in
                            (LinkType.CREATE.value,
                             LinkType.INPUT_WORK.value,
                             LinkType.RETURN.value)]

            export_file_1 = os.path.join(tmp_folder, 'export-1.tar.gz')
            export_file_2 = os.path.join(tmp_folder, 'export-2.tar.gz')
            export([o1], outfile=export_file_1, silent=True, return_reversed=True)
            export([w1], outfile=export_file_2, silent=True, return_reversed=True)

            self.reset_database()

            import_data(export_file_1, silent=True)
            links_in_db = self.get_all_node_links()

            self.assertEquals(sorted(links_wanted), sorted(links_in_db))
            self.reset_database()

            import_data(export_file_2, silent=True)
            links_in_db = self.get_all_node_links()
            self.assertEquals(sorted(links_wanted), sorted(links_in_db))

        finally:
            shutil.rmtree(tmp_folder, ignore_errors=True)

    def test_double_return_links_for_workflows(self):
        """
        This test checks that double return links to a node can be exported
        and imported without problems,
        """
        import os, shutil, tempfile

        from aiida.orm.node.data.base import Int
        from aiida.orm.importexport import export
        from aiida.orm.node import WorkChainNode
        from aiida.common.links import LinkType
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.node import Node

        tmp_folder = tempfile.mkdtemp()

        try:
            w1 = WorkChainNode().store()
            w2 = WorkChainNode().store()
            i1 = Int(1).store()
            o1 = Int(2).store()

            w1.add_incoming(i1, LinkType.INPUT_WORK, 'input-i1')
            w1.add_incoming(w2, LinkType.CALL_WORK, 'call')
            o1.add_incoming(w1, LinkType.RETURN, 'return')
            o1.add_incoming(w2, LinkType.RETURN, 'return')

            uuids_wanted = set(_.uuid for _ in (w1, o1, i1, w2))
            links_wanted = [l for l in self.get_all_node_links() if l[3] in (
                'create', 'input_calc', 'input_work', 'return', 'call_calc', 'call_work')]

            export_file = os.path.join(tmp_folder, 'export.tar.gz')
            export([o1, w1, w2, i1],
                   outfile=export_file, silent=True)

            self.reset_database()

            import_data(export_file, silent=True)

            uuids_in_db = [str(uuid) for [uuid] in
                           QueryBuilder().append(Node, project='uuid').all()]
            self.assertEquals(sorted(uuids_wanted), sorted(uuids_in_db))

            links_in_db = self.get_all_node_links()
            self.assertEquals(sorted(links_wanted), sorted(links_in_db))

        finally:
            shutil.rmtree(tmp_folder, ignore_errors=True)

    def test_that_solo_code_is_exported_correctly(self):
        """
        This test checks that when a calculation is exported then the
        corresponding code is also exported.
        """
        import os, shutil, tempfile

        from aiida.orm.utils import load_node
        from aiida.orm.importexport import export
        from aiida.orm.code import Code

        tmp_folder = tempfile.mkdtemp()

        try:
            code_label = 'test_code1'

            code = Code()
            code.set_remote_computer_exec((self.computer, '/bin/true'))
            code.label = code_label
            code.store()

            code_uuid = code.uuid

            export_file = os.path.join(tmp_folder, 'export.tar.gz')
            export([code], outfile=export_file, silent=True)

            self.reset_database()

            import_data(export_file, silent=True)

            self.assertEquals(load_node(code_uuid).label, code_label)
        finally:
            shutil.rmtree(tmp_folder, ignore_errors=True)

    def test_that_input_code_is_exported_correctly(self):
        """
        This test checks that when a calculation is exported then the
        corresponding code is also exported. It also checks that the links
        are also in place after the import.
        """
        import os, shutil, tempfile

        from aiida.orm.utils import load_node
        from aiida.orm.importexport import export
        from aiida.common.links import LinkType
        from aiida.orm.node import CalcJobNode
        from aiida.orm.code import Code
        from aiida.orm.querybuilder import QueryBuilder

        tmp_folder = tempfile.mkdtemp()

        try:
            code_label = 'test_code1'

            code = Code()
            code.set_remote_computer_exec((self.computer, '/bin/true'))
            code.label = code_label
            code.store()

            code_uuid = code.uuid

            jc = CalcJobNode()
            jc.set_computer(self.computer)
            jc.set_option('resources',
                          {"num_machines": 1, "num_mpiprocs_per_machine": 1})
            jc.store()

            jc.add_incoming(code, LinkType.INPUT_CALC, 'code')

            export_file = os.path.join(tmp_folder, 'export.tar.gz')
            export([jc], outfile=export_file, silent=True)

            self.reset_database()

            import_data(export_file, silent=True)

            # Check that the node is there
            self.assertEquals(load_node(code_uuid).label, code_label)
            # Check that the link is in place
            qb = QueryBuilder()
            qb.append(Code, project='uuid')
            qb.append(CalcJobNode, project='uuid',
                      edge_project=['label', 'type'],
                      edge_filters={'type': {'==': LinkType.INPUT_CALC.value}})
            self.assertEquals(qb.count(), 1,
                              "Expected to find one and only one link from "
                              "code to the calculation node. {} found."
                              .format(qb.count()))
        finally:
            shutil.rmtree(tmp_folder, ignore_errors=True)

    def test_that_solo_code_is_exported_correctly(self):
        """
        This test checks that when a calculation is exported then the
        corresponding code is also exported.
        """
        import os, shutil, tempfile

        from aiida.orm.utils import load_node
        from aiida.orm.importexport import export
        from aiida.orm.code import Code

        tmp_folder = tempfile.mkdtemp()

        try:
            code_label = 'test_code1'

            code = Code()
            code.set_remote_computer_exec((self.computer, '/bin/true'))
            code.label = code_label
            code.store()

            code_uuid = code.uuid

            export_file = os.path.join(tmp_folder, 'export.tar.gz')
            export([code], outfile=export_file, silent=True)

            self.clean_db()
            self.insert_data()

            import_data(export_file, silent=True)

            self.assertEquals(load_node(code_uuid).label, code_label)
        finally:
            shutil.rmtree(tmp_folder, ignore_errors=True)


class TestLogs(AiidaTestCase):
    """ Tests for export/import of nodes with logs """

    def tearDown(self):
        """
        Delete all the created log entries
        """
        from aiida.orm import Log
        super(TestLogs, self).tearDown()
        Log.objects.delete_many({})

    def test_export_import_of_critical_log_msg(self):
        """ Testing logging of critical message """
        import os, shutil, tempfile
        from aiida.orm import Log, CalculationNode
        from aiida.orm.importexport import export

        tmp_folder = tempfile.mkdtemp()

        try:
            message = 'Testing logging of critical failure'
            calc = CalculationNode()

            # Firing a log for an unstored node should not end up in the database
            calc.logger.critical(message)
            # There should be no log messages for the unstored object
            self.assertEquals(len(Log.objects.all()), 0)

            # After storing the node, logs above log level should be stored
            calc.store()
            calc.logger.critical(message)

            export_file = os.path.join(tmp_folder, 'export.tar.gz')
            export([calc], outfile=export_file, silent=True)

            self.reset_database()

            import_data(export_file, silent=True)

            # Finding all the log messages
            logs = Log.objects.all()

            self.assertEquals(len(logs), 1)
            self.assertEquals(logs[0].message, message)

        finally:
            shutil.rmtree(tmp_folder, ignore_errors=True)

    def test_exclude_logs_flag(self):
        """Test that the `include_logs` argument for `export` works."""
        import os, shutil, tempfile
        from aiida.orm import Log, CalculationNode, QueryBuilder
        from aiida.orm.importexport import export

        tmp_folder = tempfile.mkdtemp()

        log_msg = 'Testing logging of critical failure'

        try:
            # Create node
            calc = CalculationNode()
            calc.store()

            # Create log message
            calc.logger.critical(log_msg)

            # Save uuids prior to export
            calc_uuid = calc.uuid

            # Export, excluding logs
            export_file = os.path.join(tmp_folder, 'export.tar.gz')
            export([calc], outfile=export_file, silent=True, include_logs=False)

            # Clean database and reimport exported data
            self.reset_database()
            import_data(export_file, silent=True)

            # Finding all the log messages
            import_calcs = QueryBuilder().append(CalculationNode, project=['uuid']).all()
            import_logs = QueryBuilder().append(Log, project=['uuid']).all()

            # There should be exactly: 1 CalculationNode, 0 Logs
            self.assertEqual(len(import_calcs), 1)
            self.assertEqual(len(import_logs), 0)

            # Check it's the correct node
            self.assertEqual(str(import_calcs[0][0]), calc_uuid)

        finally:
            shutil.rmtree(tmp_folder, ignore_errors=True)


class TestComments(AiidaTestCase):
    """ Tests for export/import of nodes with comments """

    def setUp(self):
        super(TestComments, self).setUp()
        self.comments = [
            "We're no strangers to love",
            "You know the rules and so do I",
            "A full commitment's what I'm thinking of",
            "You wouldn't get this from any other guy"
        ]

    def tearDown(self):
        super(TestComments, self).tearDown()
        from aiida.orm import Comment
        comments = Comment.objects.all()
        for comment in comments:
            Comment.objects.delete(comment.id)

    def test_exclude_comments_flag(self):
        """Test comments and associated commenting users are not exported when using `include_comments=False`."""
        import os, shutil, tempfile
        from aiida.orm import Comment, User, Data, QueryBuilder, Node
        from aiida.orm.importexport import export

        tmp_folder = tempfile.mkdtemp()

        try:
            # Create users, node, and comments
            user_one = User.objects.get_default()
            user_two = User(email="commenting@user.s").store()

            node = Data().store()

            comment_one = Comment(node, user_one, self.comments[0]).store()
            comment_two = Comment(node, user_one, self.comments[1]).store()

            comment_three = Comment(node, user_two, self.comments[2]).store()
            comment_four = Comment(node, user_two, self.comments[3]).store()

            # Get values prior to export
            users_email = [u.email for u in [user_one, user_two]]
            node_uuid = node.uuid
            user_one_comments_uuid = [c.uuid for c in [comment_one, comment_two]]
            user_two_comments_uuid = [c.uuid for c in [comment_three, comment_four]]

            # Check that node belongs to user_one
            self.assertEqual(node.get_user().email, users_email[0])

            # Export nodes, excluding comments
            export_file = os.path.join(tmp_folder, 'export.tar.gz')
            export([node], outfile=export_file, silent=True, include_comments=False)

            # Clean database and reimport exported file
            self.reset_database()
            import_data(export_file, silent=True)

            # Get node, users, and comments
            import_nodes = QueryBuilder().append(Node, project=['uuid']).all()
            import_comments = QueryBuilder().append(Comment, project=['uuid']).all()
            import_users = QueryBuilder().append(User, project=['email']).all()

            # There should be exactly: 1 Node, 0 Comments, 1 User
            self.assertEqual(len(import_nodes), 1)
            self.assertEqual(len(import_comments), 0)
            self.assertEqual(len(import_users), 1)

            # Check it's the correct user (and node)
            self.assertEqual(str(import_nodes[0][0]), node_uuid)
            self.assertEqual(str(import_users[0][0]), users_email[0])

        finally:
            shutil.rmtree(tmp_folder, ignore_errors=True)

    def test_calc_and_data_nodes_with_comments(self):
        """ Test comments for CalculatioNode and Data node are correctly ex-/imported """
        import os, shutil, tempfile
        from aiida.orm import CalculationNode, Comment, User, Data, QueryBuilder, Node
        from aiida.orm.importexport import export

        tmp_folder = tempfile.mkdtemp()

        try:
            # Create user, nodes, and comments
            user = User.objects.get_default()

            calc_node = CalculationNode().store()
            data_node = Data().store()

            comment_one = Comment(calc_node, user, self.comments[0]).store()
            comment_two = Comment(calc_node, user, self.comments[1]).store()

            comment_three = Comment(data_node, user, self.comments[2]).store()
            comment_four = Comment(data_node, user, self.comments[3]).store()

            # Get values prior to export
            user_email = user.email
            calc_uuid = calc_node.uuid
            data_uuid = data_node.uuid
            calc_comments_uuid = [c.uuid for c in [comment_one, comment_two]]
            data_comments_uuid = [c.uuid for c in [comment_three, comment_four]]

            # Export nodes
            export_file = os.path.join(tmp_folder, 'export.tar.gz')
            export([calc_node, data_node], outfile=export_file, silent=True)

            # Clean database and reimport exported file
            self.reset_database()
            import_data(export_file, silent=True)

            # Get nodes and comments
            builder = QueryBuilder()
            builder.append(Node, tag='node', project=['uuid'])
            builder.append(Comment, with_node='node', project=['uuid'])
            nodes_and_comments = builder.all()

            self.assertEqual(len(nodes_and_comments), len(self.comments))
            for entry in nodes_and_comments:
                self.assertEqual(len(entry), 2)  # 1 Node + 1 Comment

                import_node_uuid = str(entry[0])
                import_comment_uuid = str(entry[1])

                self.assertIn(import_node_uuid, [calc_uuid, data_uuid])
                if import_node_uuid == calc_uuid:
                    # Calc node comments
                    self.assertIn(import_comment_uuid, calc_comments_uuid)
                else:
                    # Data node comments
                    self.assertIn(import_comment_uuid, data_comments_uuid)

        finally:
            shutil.rmtree(tmp_folder, ignore_errors=True)

    def test_multiple_user_comments_for_single_node(self):
        """ Test multiple users commenting on a single CalculationNode """
        import os, shutil, tempfile
        from aiida.orm import CalculationNode, Comment, User, Node, QueryBuilder
        from aiida.orm.importexport import export

        tmp_folder = tempfile.mkdtemp()

        try:
            # Create users, node, and comments
            user_one = User.objects.get_default()
            user_two = User(email="commenting@user.s").store()

            node = CalculationNode().store()

            comment_one = Comment(node, user_one, self.comments[0]).store()
            comment_two = Comment(node, user_one, self.comments[1]).store()

            comment_three = Comment(node, user_two, self.comments[2]).store()
            comment_four = Comment(node, user_two, self.comments[3]).store()

            # Get values prior to export
            users_email = [u.email for u in [user_one, user_two]]
            node_uuid = str(node.uuid)
            user_one_comments_uuid = [str(c.uuid) for c in [comment_one, comment_two]]
            user_two_comments_uuid = [str(c.uuid) for c in [comment_three, comment_four]]

            # Export node, along with comments and users recursively
            export_file = os.path.join(tmp_folder, 'export.tar.gz')
            export([node], outfile=export_file, silent=True)

            # Clean database and reimport exported file
            self.reset_database()
            import_data(export_file, silent=True)

            # Get node, users, and comments
            builder = QueryBuilder()
            builder.append(Node, tag='node', project=['uuid'])
            builder.append(Comment, tag='comment', with_node='node', project=['uuid'])
            builder.append(User, with_comment='comment', project=['email'])
            entries = builder.all()

            # Check that all 4 comments are retrieved, along with their respective node and user
            self.assertEqual(len(entries), len(self.comments))

            # Go through [Node.uuid, Comment.uuid, User.email]-entries
            imported_node_uuids = set()
            imported_user_one_comment_uuids = set()
            imported_user_two_comment_uuids = set()
            imported_user_emails = set()
            for entry in entries:
                self.assertEqual(len(entry), 3)  # 1 Node + 1 Comment + 1 User

                # Add node to set of imported nodes
                imported_node_uuids.add(str(entry[0]))

                # Add user to set of imported users
                import_user_email = entry[2]
                imported_user_emails.add(str(import_user_email))

                # Add comment to set of imported comments pertaining to correct user
                if import_user_email == users_email[0]:
                    # User_one comments
                    imported_user_one_comment_uuids.add(str(entry[1]))
                else:
                    # User_two comments
                    imported_user_two_comment_uuids.add(str(entry[1]))

            # Check same number of nodes (1) and users (2) were ex- and imported
            self.assertEqual(len(imported_node_uuids), 1)
            self.assertEqual(len(imported_user_emails), len(users_email))

            # Check imported node equals exported node
            self.assertSetEqual(imported_node_uuids, {node_uuid})

            # Check imported user is part of exported users
            self.assertSetEqual(imported_user_emails, set(users_email))

            # Check same number of comments (2) pertaining to each user were ex- and imported
            self.assertEqual(len(imported_user_one_comment_uuids), len(user_one_comments_uuid))
            self.assertEqual(len(imported_user_two_comment_uuids), len(user_two_comments_uuid))

            # Check imported comments equal exported comments pertaining to specific user
            self.assertSetEqual(imported_user_one_comment_uuids, set(user_one_comments_uuid))
            self.assertSetEqual(imported_user_two_comment_uuids, set(user_two_comments_uuid))

        finally:
            shutil.rmtree(tmp_folder, ignore_errors=True)

class TestExtras(AiidaTestCase):
    """Test extras import"""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """Only run to prepare an export file"""
        import os 
        import tempfile
        from aiida.orm.data import Data
        from aiida.orm.importexport import export
        super(TestExtras, cls).setUpClass()
        d = Data()
        d.label = 'my_test_data_node'
        d.store()
        d.set_extras({'b': 2, 'c': 3})
        tmp_folder = tempfile.mkdtemp()
        cls.export_file = os.path.join(tmp_folder, 'export.aiida')
        export([d], outfile=cls.export_file, silent=True)

    def setUp(self):
        """This function runs before every test execution"""
        from aiida.orm.importexport import import_data
        self.clean_db()
        self.insert_data()

    def import_extras(self, mode_new='import'):
        """Import an aiida database"""
        from aiida.orm.data import Data
        from aiida.orm.querybuilder import QueryBuilder
        import_data(self.export_file, silent=True, extras_mode_new=mode_new)
        q = QueryBuilder().append(Data, filters={'label': 'my_test_data_node'})
        self.assertEquals(q.count(), 1)
        self.imported_node = q.all()[0][0]

    def modify_extras(self, mode_existing):
        """Import the same aiida database again"""
        from aiida.orm.data import Data
        from aiida.orm.querybuilder import QueryBuilder
        self.imported_node.set_extra('a', 1)
        self.imported_node.set_extra('b', 1000)
        self.imported_node.del_extra('c')

        import_data(self.export_file, silent=True, extras_mode_existing=mode_existing)

        # Query again the database
        q = QueryBuilder().append(Data, filters={'label': 'my_test_data_node'})
        self.assertEquals(q.count(), 1)
        return q.all()[0][0]

    def tearDown(self):
        pass


    def test_import_of_extras(self):
        """Check if extras are properly imported"""
        self.import_extras()
        self.assertEquals(self.imported_node.get_extra('b'), 2)
        self.assertEquals(self.imported_node.get_extra('c'), 3)

    def test_absence_of_extras(self):
        """Check whether extras are not imported if the mode is set to 'none'"""
        self.import_extras(mode_new='none')
        with self.assertRaises(AttributeError):
            # the extra 'b' should not exist
            self.imported_node.get_extra('b')
        with self.assertRaises(AttributeError):
            # the extra 'c' should not exist
            self.imported_node.get_extra('c')
        
    def test_extras_import_mode_keep_existing(self):
        """Check if old extras are not modified in case of name collision"""
        self.import_extras()
        imported_node = self.modify_extras(mode_existing='kcl')

        # Check that extras are imported correctly
        self.assertEquals(imported_node.get_extra('a'), 1)
        self.assertEquals(imported_node.get_extra('b'), 1000)
        self.assertEquals(imported_node.get_extra('c'), 3)

    def test_extras_import_mode_update_existing(self):
        """Check if old extras are modified in case of name collision"""
        self.import_extras()
        imported_node = self.modify_extras(mode_existing='kcu')

        # Check that extras are imported correctly
        self.assertEquals(imported_node.get_extra('a'), 1)
        self.assertEquals(imported_node.get_extra('b'), 2)
        self.assertEquals(imported_node.get_extra('c'), 3)
    
    def test_extras_import_mode_mirror(self):
        """Check if old extras are fully overwritten by the imported ones"""
        self.import_extras()
        imported_node = self.modify_extras(mode_existing='ncu')

        # Check that extras are imported correctly
        with self.assertRaises(AttributeError): # the extra 
            # 'a' should not exist, as the extras were fully mirrored with respect to
            # the imported node
            imported_node.get_extra('a')
        self.assertEquals(imported_node.get_extra('b'), 2)
        self.assertEquals(imported_node.get_extra('c'), 3)
    
    def test_extras_import_mode_none(self):
        """Check if old extras are fully overwritten by the imported ones"""
        self.import_extras()
        imported_node = self.modify_extras(mode_existing='knl')

        # Check if extras are imported correctly
        self.assertEquals(imported_node.get_extra('b'), 1000)
        self.assertEquals(imported_node.get_extra('a'), 1)
        with self.assertRaises(AttributeError): # the extra
            # 'c' should not exist, as the extras were keept untached
            imported_node.get_extra('c')
    
    def test_extras_import_mode_strange(self):
        """Check a mode that is probably does not make much sense but is still available"""
        self.import_extras()
        imported_node = self.modify_extras(mode_existing='kcd')

        # Check if extras are imported correctly
        self.assertEquals(imported_node.get_extra('a'), 1)
        self.assertEquals(imported_node.get_extra('c'), 3)
        with self.assertRaises(AttributeError): # the extra
            # 'b' should not exist, as the collided extras are deleted
            imported_node.get_extra('b')
