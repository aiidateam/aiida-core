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
from __future__ import with_statement

import io
import unittest
import os
import shutil
import tempfile
import six
from six.moves import range, zip

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common.utils import get_new_uuid
from aiida.orm.importexport import import_data, export
from aiida.backends.tests.utils.configuration import with_temp_dir


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
        parameters = orm.Dict(dict={
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
            self.assertEqual(orm.QueryBuilder().append(orm.Node).count(), len(nodes))

            # Clean the database and verify there are no nodes left
            self.clean_db()
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
        child_calculation.store()
        remote_folder = orm.RemoteData(computer=self.computer, remote_path='/').store()

        remote_folder.add_incoming(parent_process, link_type=LinkType.CREATE, link_label='link')
        child_calculation.add_incoming(remote_folder, link_type=LinkType.INPUT_CALC, link_label='link')
        structure.add_incoming(child_calculation, link_type=LinkType.CREATE, link_label='link')

        with tempfile.NamedTemporaryFile() as handle:

            nodes = [structure, child_calculation, parent_process, remote_folder]
            export(nodes, outfile=handle.name, overwrite=True, silent=True)

            # Check that we have the expected number of nodes in the database
            self.assertEqual(orm.QueryBuilder().append(orm.Node).count(), len(nodes))

            # Clean the database and verify there are no nodes left
            self.clean_db()
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
                self.assertEqual(structure.cell, test_cell)

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
        values = ("Hello", 6, -1.2399834e12, False)  # , ["Bla", 1, 1e-10])
        filename = os.path.join(temp_dir, "export.tar.gz")

        # producing nodes:
        nodes = [cls(val).store() for val, cls in zip(values, (orm.Str, orm.Int, orm.Float, orm.Bool))]
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
            self.assertEqual(orm.load_node(uuid).value, refval)

    @with_temp_dir
    def test_calc_of_structuredata(self, temp_dir):
        """Simple ex-/import of CalcJobNode with input StructureData"""
        from aiida.common.links import LinkType
        from aiida.plugins import DataFactory

        StructureData = DataFactory('structure')
        struct = StructureData()
        struct.store()

        calc = orm.CalcJobNode()
        calc.computer = self.computer
        calc.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
        calc.store()

        calc.add_incoming(struct, link_type=LinkType.INPUT_CALC, link_label='link')

        pks = [struct.pk, calc.pk]

        attrs = {}
        for pk in pks:
            node = orm.load_node(pk)
            attrs[node.uuid] = dict()
            for k in node.attributes.keys():
                attrs[node.uuid][k] = node.get_attribute(k)

        filename = os.path.join(temp_dir, "export.tar.gz")

        export([calc], outfile=filename, silent=True)

        self.clean_db()

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
        import tarfile

        from aiida.common import exceptions
        from aiida.plugins import DataFactory
        from aiida.common import json

        # Creating a folder for the import/export files
        export_file_tmp_folder = tempfile.mkdtemp()
        unpack_tmp_folder = tempfile.mkdtemp()
        try:
            StructureData = DataFactory('structure')
            struct = StructureData()
            struct.store()

            filename = os.path.join(export_file_tmp_folder, "export.tar.gz")
            export([struct], outfile=filename, silent=True)

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

    def test_control_of_licenses(self):
        """Test control of licenses."""
        from aiida.common.exceptions import LicensingException
        from aiida.common.folders import SandboxFolder
        from aiida.orm.importexport import export_tree

        from aiida.plugins import DataFactory

        StructureData = DataFactory('structure')
        struct = StructureData()
        struct.source = {'license': 'GPL'}
        struct.store()

        folder = SandboxFolder()
        export_tree([struct], folder=folder, silent=True,
                    allowed_licenses=['GPL'])
        # Folder should contain two files of metadata + nodes/
        self.assertEqual(len(folder.get_content_list()), 3)

        folder = SandboxFolder()
        export_tree([struct], folder=folder, silent=True,
                    forbidden_licenses=['Academic'])
        # Folder should contain two files of metadata + nodes/
        self.assertEqual(len(folder.get_content_list()), 3)

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([struct], folder=folder, silent=True,
                        allowed_licenses=['CC0'])

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([struct], folder=folder, silent=True,
                        forbidden_licenses=['GPL'])

        def cc_filter(license_):
            return license_.startswith('CC')

        def gpl_filter(license_):
            return license_ == 'GPL'

        def crashing_filter():
            raise NotImplementedError("not implemented yet")

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([struct], folder=folder, silent=True,
                        allowed_licenses=cc_filter)

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([struct], folder=folder, silent=True,
                        forbidden_licenses=gpl_filter)

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([struct], folder=folder, silent=True,
                        allowed_licenses=crashing_filter)

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([struct], folder=folder, silent=True,
                        forbidden_licenses=crashing_filter)


class TestUsers(AiidaTestCase):
    """Test ex-/import cases related to Users"""

    def setUp(self):
        self.reset_database()

    def tearDown(self):
        self.reset_database()

    @with_temp_dir
    def test_nodes_belonging_to_different_users(self, temp_dir):
        """
        This test checks that nodes belonging to different users are correctly
        exported & imported.
        """
        from aiida.common.links import LinkType
        from aiida.manage.manager import get_manager

        manager = get_manager()

        # Create another user
        new_email = "newuser@new.n"
        user = orm.User(email=new_email).store()

        # Create a structure data node that has a calculation as output
        sd1 = orm.StructureData()
        sd1.user = user
        sd1.label = 'sd1'
        sd1.store()

        jc1 = orm.CalcJobNode()
        jc1.computer = self.computer
        jc1.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
        jc1.user = user
        jc1.label = 'jc1'
        jc1.store()
        jc1.add_incoming(sd1, link_type=LinkType.INPUT_CALC, link_label='link')

        # Create some nodes from a different user
        sd2 = orm.StructureData()
        sd2.user = user
        sd2.label = 'sd2'
        sd2.store()
        sd2.add_incoming(jc1, link_type=LinkType.CREATE, link_label='l1')  # I assume jc1 CREATED sd2

        jc2 = orm.CalcJobNode()
        jc2.computer = self.computer
        jc2.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
        jc2.label = 'jc2'
        jc2.store()
        jc2.add_incoming(sd2, link_type=LinkType.INPUT_CALC, link_label='l2')

        sd3 = orm.StructureData()
        sd3.label = 'sd3'
        sd3.store()
        sd3.add_incoming(jc2, link_type=LinkType.CREATE, link_label='l3')

        uuids_u1 = [sd1.uuid, jc1.uuid, sd2.uuid]
        uuids_u2 = [jc2.uuid, sd3.uuid]

        filename = os.path.join(temp_dir, "export.tar.gz")

        export([sd3], outfile=filename, silent=True)
        self.clean_db()
        import_data(filename, silent=True)

        # Check that the imported nodes are correctly imported and that
        # the user assigned to the nodes is the right one
        for uuid in uuids_u1:
            node = orm.load_node(uuid=uuid)
            self.assertEqual(node.user.email, new_email)
        for uuid in uuids_u2:
            self.assertEqual(orm.load_node(uuid).user.email, manager.get_profile().default_user_email)

    @with_temp_dir
    def test_non_default_user_nodes(self, temp_dir):
        """
        This test checks that nodes belonging to user A (which is not the
        default user) can be correctly exported, imported, enriched with nodes
        from the default user, re-exported & re-imported and that in the end
        all the nodes that have been finally imported belonging to the right
        users.
        """
        from aiida.common.links import LinkType
        from aiida.manage.manager import get_manager

        manager = get_manager()

        # Create another user
        new_email = "newuser@new.n"
        user = orm.User(email=new_email).store()

        # Create a structure data node that has a calculation as output
        sd1 = orm.StructureData()
        sd1.user = user
        sd1.label = 'sd1'
        sd1.store()

        jc1 = orm.CalcJobNode()
        jc1.computer = self.computer
        jc1.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
        jc1.user = user
        jc1.label = 'jc1'
        jc1.store()
        jc1.add_incoming(sd1, link_type=LinkType.INPUT_CALC, link_label='link')

        # Create some nodes from a different user
        sd2 = orm.StructureData()
        sd2.user = user
        sd2.label = 'sd2'
        sd2.store()
        sd2.add_incoming(jc1, link_type=LinkType.CREATE, link_label='l1')
        sd2_uuid = sd2.uuid

        # At this point we export the generated data
        filename1 = os.path.join(temp_dir, "export1.tar.gz")
        export([sd2], outfile=filename1, silent=True)
        uuids1 = [sd1.uuid, jc1.uuid, sd2.uuid]
        self.clean_db()
        self.insert_data()
        import_data(filename1, silent=True)

        # Check that the imported nodes are correctly imported and that
        # the user assigned to the nodes is the right one
        for uuid in uuids1:
            self.assertEqual(orm.load_node(uuid).user.email, new_email)

        # Now we continue to generate more data based on the imported
        # data
        sd2_imp = orm.load_node(sd2_uuid)

        jc2 = orm.CalcJobNode()
        jc2.computer = self.computer
        jc2.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
        jc2.label = 'jc2'
        jc2.store()
        jc2.add_incoming(sd2_imp, link_type=LinkType.INPUT_CALC, link_label='l2')

        sd3 = orm.StructureData()
        sd3.label = 'sd3'
        sd3.store()
        sd3.add_incoming(jc2, link_type=LinkType.CREATE, link_label='l3')

        # Store the UUIDs of the nodes that should be checked
        # if they can be imported correctly.
        uuids2 = [jc2.uuid, sd3.uuid]

        filename2 = os.path.join(temp_dir, "export2.tar.gz")
        export([sd3], outfile=filename2, silent=True)
        self.clean_db()
        self.insert_data()
        import_data(filename2, silent=True)

        # Check that the imported nodes are correctly imported and that
        # the user assigned to the nodes is the right one
        for uuid in uuids1:
            self.assertEqual(orm.load_node(uuid).user.email, new_email)
        for uuid in uuids2:
            self.assertEqual(orm.load_node(uuid).user.email, manager.get_profile().default_user_email)


class TestGroups(AiidaTestCase):
    """Test ex-/import cases related to Groups"""

    def setUp(self):
        self.reset_database()

    def tearDown(self):
        self.reset_database()

    @with_temp_dir
    def test_nodes_in_group(self, temp_dir):
        """
        This test checks that nodes that belong to a specific group are
        correctly imported and exported.
        """
        from aiida.common.links import LinkType

        # Create another user
        new_email = "newuser@new.n"
        user = orm.User(email=new_email)
        user.store()

        # Create a structure data node that has a calculation as output
        sd1 = orm.StructureData()
        sd1.user = user
        sd1.label = 'sd1'
        sd1.store()

        jc1 = orm.CalcJobNode()
        jc1.computer = self.computer
        jc1.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
        jc1.user = user
        jc1.label = 'jc1'
        jc1.store()
        jc1.add_incoming(sd1, link_type=LinkType.INPUT_CALC, link_label='link')

        # Create a group and add the data inside
        gr1 = orm.Group(label="node_group")
        gr1.store()
        gr1.add_nodes([sd1, jc1])
        gr1_uuid = gr1.uuid

        # At this point we export the generated data
        filename1 = os.path.join(temp_dir, "export1.tar.gz")
        export([sd1, jc1, gr1], outfile=filename1,
                silent=True)
        n_uuids = [sd1.uuid, jc1.uuid]
        self.clean_db()
        self.insert_data()
        import_data(filename1, silent=True)

        # Check that the imported nodes are correctly imported and that
        # the user assigned to the nodes is the right one
        for uuid in n_uuids:
            self.assertEqual(orm.load_node(uuid).user.email, new_email)

        # Check that the exported group is imported correctly
        builder = orm.QueryBuilder()
        builder.append(orm.Group, filters={'uuid': {'==': gr1_uuid}})
        self.assertEqual(builder.count(), 1, "The group was not found.")

    @with_temp_dir
    def test_group_export(self, temp_dir):
        """Test that when exporting just a group, its nodes are also exported"""
        # Create another user
        new_email = "newuser@new.n"
        user = orm.User(email=new_email)
        user.store()

        # Create a structure data node
        sd1 = orm.StructureData()
        sd1.user = user
        sd1.label = 'sd1'
        sd1.store()

        # Create a group and add the data inside
        g1 = orm.Group(label="node_group")
        g1.store()
        g1.add_nodes([sd1])
        g1_uuid = g1.uuid

        # At this point we export the generated data
        filename1 = os.path.join(temp_dir, "export1.tar.gz")
        export([g1], outfile=filename1, silent=True)
        n_uuids = [sd1.uuid]
        self.clean_db()
        self.insert_data()
        import_data(filename1, silent=True)

        # Check that the imported nodes are correctly imported and that
        # the user assigned to the nodes is the right one
        for uuid in n_uuids:
            self.assertEqual(orm.load_node(uuid).user.email, new_email)

        # Check that the exported group is imported correctly
        builder = orm.QueryBuilder()
        builder.append(orm.Group, filters={'uuid': {'==': g1_uuid}})
        self.assertEqual(builder.count(), 1, "The group was not found.")

    @with_temp_dir
    def test_group_import_existing(self, temp_dir):
        """
        Testing what happens when I try to import a group that already exists in the
        database. This should raise an appropriate exception
        """
        grouplabel = "node_group_existing"

        # Create another user
        new_email = "newuser@new.n"
        user = orm.User(email=new_email)
        user.store()

        # Create a structure data node
        sd1 = orm.StructureData()
        sd1.user = user
        sd1.label = 'sd'
        sd1.store()

        # Create a group and add the data inside
        g1 = orm.Group(label=grouplabel)
        g1.store()
        g1.add_nodes([sd1])

        # At this point we export the generated data
        filename1 = os.path.join(temp_dir, "export1.tar.gz")
        export([g1], outfile=filename1, silent=True)
        self.clean_db()
        self.insert_data()

        # Creating a group of the same name
        g1 = orm.Group(label="node_group_existing")
        g1.store()
        import_data(filename1, silent=True)
        # The import should have created a new group with a suffix
        # I check for this:
        builder = orm.QueryBuilder().append(orm.Group, filters={'label': {'like': grouplabel + '%'}})
        self.assertEqual(builder.count(), 2)
        # Now I check for the group having one member, and whether the name is different:
        builder = orm.QueryBuilder()
        builder.append(orm.Group, filters={'label': {'like': grouplabel + '%'}}, tag='g', project='label')
        builder.append(orm.StructureData, with_group='g')
        self.assertEqual(builder.count(), 1)
        # I check that the group name was changed:
        self.assertTrue(builder.all()[0][0] != grouplabel)
        # I import another name, the group should not be imported again
        import_data(filename1, silent=True)
        builder = orm.QueryBuilder()
        builder.append(orm.Group, filters={'label': {'like': grouplabel + '%'}})
        self.assertEqual(builder.count(), 2)


class TestCalculations(AiidaTestCase):
    """Test ex-/import cases related to Calculations"""

    def setUp(self):
        self.reset_database()

    def tearDown(self):
        self.reset_database()

    @with_temp_dir
    def test_calcfunction(self, temp_dir):
        """Test @calcfunction"""
        from aiida.engine import calcfunction
        from aiida.common.exceptions import NotExistent

        @calcfunction
        def add(a, b):
            """Add 2 numbers"""
            return {'res': orm.Float(a + b)}

        def max_(**kwargs):
            """select the max value"""
            max_val = max([(v.value, v) for v in kwargs.values()])
            return {'res': max_val[1]}

        # I'm creating a bunch of numbers
        a, b, c, d, e = (orm.Float(i).store() for i in range(5))
        # this adds the maximum number between bcde to a.
        res = add(a=a, b=max_(b=b, c=c, d=d, e=e)['res'])['res']
        # These are the uuids that would be exported as well (as parents) if I wanted the final result
        uuids_values = [(a.uuid, a.value), (e.uuid, e.value), (res.uuid, res.value)]
        # These are the uuids that shouldn't be exported since it's a selection.
        not_wanted_uuids = [v.uuid for v in (b, c, d)]
        # At this point we export the generated data
        filename1 = os.path.join(temp_dir, "export1.tar.gz")
        export([res], outfile=filename1, silent=True, return_reversed=True)
        self.clean_db()
        self.insert_data()
        import_data(filename1, silent=True)
        # Check that the imported nodes are correctly imported and that the value is preserved
        for uuid, value in uuids_values:
            self.assertEqual(orm.load_node(uuid).value, value)
        for uuid in not_wanted_uuids:
            with self.assertRaises(NotExistent):
                orm.load_node(uuid)

    @with_temp_dir
    def test_workcalculation(self, temp_dir):
        """Test simple master/slave WorkChainNodes"""
        from aiida.common.links import LinkType

        master = orm.WorkChainNode().store()
        slave = orm.WorkChainNode().store()

        input_1 = orm.Int(3).store()
        input_2 = orm.Int(5).store()
        output_1 = orm.Int(2).store()

        master.add_incoming(input_1, LinkType.INPUT_WORK, 'input_1')
        slave.add_incoming(master, LinkType.CALL_WORK, 'CALL')
        slave.add_incoming(input_2, LinkType.INPUT_WORK, 'input_2')
        output_1.add_incoming(master, LinkType.RETURN, 'RETURN')

        uuids_values = [(v.uuid, v.value) for v in (output_1,)]
        filename1 = os.path.join(temp_dir, "export1.tar.gz")
        export([output_1], outfile=filename1, silent=True)
        self.clean_db()
        self.insert_data()
        import_data(filename1, silent=True)

        for uuid, value in uuids_values:
            self.assertEqual(orm.load_node(uuid).value, value)


class TestComplex(AiidaTestCase):
    """Test complex ex-/import cases"""

    def setUp(self):
        self.reset_database()

    def tearDown(self):
        self.reset_database()

    @with_temp_dir
    def test_complex_graph_import_export(self, temp_dir):
        """
        This test checks that a small and bit complex graph can be correctly
        exported and imported.

        It will create the graph, store it to the database, export it to a file
        and import it. In the end it will check if the initial nodes are present
        at the imported graph.
        """
        from aiida.common.links import LinkType
        from aiida.common.exceptions import NotExistent

        calc1 = orm.CalcJobNode()
        calc1.computer = self.computer
        calc1.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
        calc1.label = "calc1"
        calc1.store()

        pd1 = orm.Dict()
        pd1.label = "pd1"
        pd1.store()

        pd2 = orm.Dict()
        pd2.label = "pd2"
        pd2.store()

        rd1 = orm.RemoteData()
        rd1.label = "rd1"
        rd1.set_remote_path("/x/y.py")
        rd1.computer = self.computer
        rd1.store()
        rd1.add_incoming(calc1, link_type=LinkType.CREATE, link_label='link')

        calc2 = orm.CalcJobNode()
        calc2.computer = self.computer
        calc2.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
        calc2.label = "calc2"
        calc2.store()
        calc2.add_incoming(pd1, link_type=LinkType.INPUT_CALC, link_label='link1')
        calc2.add_incoming(pd2, link_type=LinkType.INPUT_CALC, link_label='link2')
        calc2.add_incoming(rd1, link_type=LinkType.INPUT_CALC, link_label='link3')

        fd1 = orm.FolderData()
        fd1.label = "fd1"
        fd1.store()
        fd1.add_incoming(calc2, link_type=LinkType.CREATE, link_label='link')

        node_uuids_labels = {calc1.uuid: calc1.label, pd1.uuid: pd1.label,
                                pd2.uuid: pd2.label, rd1.uuid: rd1.label,
                                calc2.uuid: calc2.label, fd1.uuid: fd1.label}

        filename = os.path.join(temp_dir, "export.tar.gz")
        export([fd1], outfile=filename, silent=True)

        self.clean_db()

        import_data(filename, silent=True, ignore_unknown_nodes=True)

        for uuid, label in node_uuids_labels.items():
            try:
                orm.load_node(uuid)
            except NotExistent:
                self.fail("Node with UUID {} and label {} was not "
                            "found.".format(uuid, label))

    @with_temp_dir
    def test_reexport(self, temp_dir):
        """
        Export something, import and reexport and check if everything is valid.
        The export is rather easy::

            ___       ___          ___
           |   | INP |   | CREATE |   |
           | p | --> | c | -----> | a |
           |___|     |___|        |___|

        """
        import numpy as np
        import string
        import random
        from datetime import datetime

        from aiida.common.hashing import make_hash
        from aiida.common.links import LinkType

        def get_hash_from_db_content(grouplabel):
            builder = orm.QueryBuilder()
            builder.append(orm.Dict, tag='p', project='*')
            builder.append(orm.CalculationNode, tag='c', project='*', edge_tag='p2c', edge_project=('label', 'type'))
            builder.append(orm.ArrayData, tag='a', project='*', edge_tag='c2a', edge_project=('label', 'type'))
            builder.append(orm.Group, filters={'label': grouplabel}, project='*', tag='g', with_node='a')
            # I want the query to contain something!
            self.assertTrue(builder.count() > 0)
            # The hash is given from the preservable entries in an export-import cycle,
            # uuids, attributes, labels, descriptions, arrays, link-labels, link-types:
            hash_ = make_hash([(
                item['p']['*'].attributes,
                item['p']['*'].uuid,
                item['p']['*'].label,
                item['p']['*'].description,
                item['c']['*'].uuid,
                item['c']['*'].attributes,
                item['a']['*'].attributes,
                [item['a']['*'].get_array(name) for name in item['a']['*'].get_arraynames()],
                item['a']['*'].uuid,
                item['g']['*'].uuid,
                item['g']['*'].label,
                item['p2c']['label'],
                item['p2c']['type'],
                item['c2a']['label'],
                item['c2a']['type'],
                item['g']['*'].label,
            ) for item in builder.dict()])
            return hash_

        # Creating a folder for the import/export files
        chars = string.ascii_uppercase + string.digits
        size = 10
        grouplabel = 'test-group'

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

        p = orm.Dict(dict=trial_dict)
        p.label = str(datetime.now())
        p.description = 'd_' + str(datetime.now())
        p.store()
        c = orm.CalculationNode()
        # setting also trial dict as attributes, but randomizing the keys)
        (c.set_attribute(str(int(k) + np.random.randint(10)), v) for k, v in trial_dict.items())
        c.store()
        a = orm.ArrayData()
        a.set_array('array', nparr)
        a.store()
        # LINKS
        # the calculation has input the parameters-instance
        c.add_incoming(p, link_type=LinkType.INPUT_CALC, link_label='input_parameters')
        # I want the array to be an output of the calculation
        a.add_incoming(c, link_type=LinkType.CREATE, link_label='output_array')
        g = orm.Group(label='test-group')
        g.store()
        g.add_nodes(a)

        hash_from_dbcontent = get_hash_from_db_content(grouplabel)

        # I export and reimport 3 times in a row:
        for i in range(3):
            # Always new filename:
            filename = os.path.join(temp_dir, "export-{}.zip".format(i))
            # Loading the group from the string
            g = orm.Group.get(label=grouplabel)
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


class TestComputer(AiidaTestCase):
    """Test ex-/import cases related to Computers"""

    def setUp(self):
        self.reset_database()

    def tearDown(self):
        self.reset_database()

    @with_temp_dir
    def test_same_computer_import(self, temp_dir):
        """
        Test that you can import nodes in steps without any problems. In this
        test we will import a first calculation and then a second one. The
        import should work as expected and have in the end two job
        calculations.

        Each calculation is related to the same computer. In the end we should
        have only one computer
        """
        # Use local computer
        comp = self.computer

        # Store two job calculation related to the same computer
        calc1_label = "calc1"
        calc1 = orm.CalcJobNode()
        calc1.computer = comp
        calc1.set_option('resources', {"num_machines": 1,
                                        "num_mpiprocs_per_machine": 1})
        calc1.label = calc1_label
        calc1.store()

        calc2_label = "calc2"
        calc2 = orm.CalcJobNode()
        calc2.computer = comp
        calc2.set_option('resources', {"num_machines": 2,
                                        "num_mpiprocs_per_machine": 2})
        calc2.label = calc2_label
        calc2.store()

        # Store locally the computer name
        comp_name = six.text_type(comp.name)
        comp_uuid = six.text_type(comp.uuid)

        # Export the first job calculation
        filename1 = os.path.join(temp_dir, "export1.tar.gz")
        export([calc1], outfile=filename1, silent=True)

        # Export the second job calculation
        filename2 = os.path.join(temp_dir, "export2.tar.gz")
        export([calc2], outfile=filename2, silent=True)

        # Clean the local database
        self.clean_db()

        # Check that there are no computers
        builder = orm.QueryBuilder()
        builder.append(orm.Computer, project=['*'])
        self.assertEqual(builder.count(), 0, "There should not be any computers in the database at this point.")

        # Check that there are no calculations
        builder = orm.QueryBuilder()
        builder.append(orm.CalcJobNode, project=['*'])
        self.assertEqual(builder.count(), 0, "There should not be any calculations in the database at this point.")

        # Import the first calculation
        import_data(filename1, silent=True)

        # Check that the calculation computer is imported correctly.
        builder = orm.QueryBuilder()
        builder.append(orm.CalcJobNode, project=['label'])
        self.assertEqual(builder.count(), 1, "Only one calculation should be found.")
        self.assertEqual(six.text_type(builder.first()[0]), calc1_label, "The calculation label is not correct.")

        # Check that the referenced computer is imported correctly.
        builder = orm.QueryBuilder()
        builder.append(orm.Computer, project=['name', 'uuid', 'id'])
        self.assertEqual(builder.count(), 1, "Only one computer should be found.")
        self.assertEqual(six.text_type(builder.first()[0]), comp_name, "The computer name is not correct.")
        self.assertEqual(six.text_type(builder.first()[1]), comp_uuid, "The computer uuid is not correct.")

        # Store the id of the computer
        comp_id = builder.first()[2]

        # Import the second calculation
        import_data(filename2, silent=True)

        # Check that the number of computers remains the same and its data
        # did not change.
        builder = orm.QueryBuilder()
        builder.append(orm.Computer, project=['name', 'uuid', 'id'])
        self.assertEqual(builder.count(), 1, "Found {} computers"
                            "but only one computer should be found.".format(builder.count()))
        self.assertEqual(six.text_type(builder.first()[0]), comp_name,
                            "The computer name is not correct.")
        self.assertEqual(six.text_type(builder.first()[1]), comp_uuid,
                            "The computer uuid is not correct.")
        self.assertEqual(builder.first()[2], comp_id,
                            "The computer id is not correct.")

        # Check that now you have two calculations attached to the same
        # computer.
        builder = orm.QueryBuilder()
        builder.append(orm.Computer, tag='comp')
        builder.append(orm.CalcJobNode, with_computer='comp', project=['label'])
        self.assertEqual(builder.count(), 2, "Two calculations should be found.")
        ret_labels = set(_ for [_] in builder.all())
        self.assertEqual(ret_labels, set([calc1_label, calc2_label]),
                            "The labels of the calculations are not correct.")

    @with_temp_dir
    def test_same_computer_different_name_import(self, temp_dir):
        """
        This test checks that if the computer is re-imported with a different
        name to the same database, then the original computer will not be
        renamed. It also checks that the names were correctly imported (without
        any change since there is no computer name collision)
        """
        # Get computer
        comp1 = self.computer

        # Store a calculation
        calc1_label = "calc1"
        calc1 = orm.CalcJobNode()
        calc1.computer = self.computer
        calc1.set_option('resources', {"num_machines": 1,
                                        "num_mpiprocs_per_machine": 1})
        calc1.label = calc1_label
        calc1.store()

        # Store locally the computer name
        comp1_name = six.text_type(comp1.name)

        # Export the first job calculation
        filename1 = os.path.join(temp_dir, "export1.tar.gz")
        export([calc1], outfile=filename1, silent=True)

        # Rename the computer
        comp1.set_name(comp1_name + "_updated")

        # Store a second calculation
        calc2_label = "calc2"
        calc2 = orm.CalcJobNode()
        calc2.computer = self.computer
        calc2.set_option('resources', {"num_machines": 2,
                                        "num_mpiprocs_per_machine": 2})
        calc2.label = calc2_label
        calc2.store()

        # Export the second job calculation
        filename2 = os.path.join(temp_dir, "export2.tar.gz")
        export([calc2], outfile=filename2, silent=True)

        # Clean the local database
        self.clean_db()

        # Check that there are no computers
        builder = orm.QueryBuilder()
        builder.append(orm.Computer, project=['*'])
        self.assertEqual(builder.count(), 0, "There should not be any computers in the database at this point.")

        # Check that there are no calculations
        builder = orm.QueryBuilder()
        builder.append(orm.CalcJobNode, project=['*'])
        self.assertEqual(builder.count(), 0, "There should not be any calculations in the database at this point.")

        # Import the first calculation
        import_data(filename1, silent=True)

        # Check that the calculation computer is imported correctly.
        builder = orm.QueryBuilder()
        builder.append(orm.CalcJobNode, project=['label'])
        self.assertEqual(builder.count(), 1, "Only one calculation should be found.")
        self.assertEqual(six.text_type(builder.first()[0]), calc1_label, "The calculation label is not correct.")

        # Check that the referenced computer is imported correctly.
        builder = orm.QueryBuilder()
        builder.append(orm.Computer, project=['name', 'uuid', 'id'])
        self.assertEqual(builder.count(), 1, "Only one computer should be found.")
        self.assertEqual(six.text_type(builder.first()[0]), comp1_name, "The computer name is not correct.")

        # Import the second calculation
        import_data(filename2, silent=True)

        # Check that the number of computers remains the same and its data
        # did not change.
        builder = orm.QueryBuilder()
        builder.append(orm.Computer, project=['name'])
        self.assertEqual(builder.count(), 1, "Found {} computers"
                            "but only one computer should be found.".format(builder.count()))
        self.assertEqual(six.text_type(builder.first()[0]), comp1_name,
                            "The computer name is not correct.")

    @with_temp_dir
    def test_different_computer_same_name_import(self, temp_dir):
        """
        This test checks that if there is a name collision, the imported
        computers are renamed accordingly.
        """
        from aiida.orm.importexport import DUPL_SUFFIX

        # Set the computer name
        comp1_name = "localhost_1"
        self.computer.set_name(comp1_name)

        # Store a calculation
        calc1_label = "calc1"
        calc1 = orm.CalcJobNode()
        calc1.computer = self.computer
        calc1.set_option('resources', {"num_machines": 1,
                                        "num_mpiprocs_per_machine": 1})
        calc1.label = calc1_label
        calc1.store()

        # Export the first job calculation
        filename1 = os.path.join(temp_dir, "export1.tar.gz")
        export([calc1], outfile=filename1, silent=True)

        # Reset the database
        self.clean_db()
        self.insert_data()

        # Set the computer name to the same name as before
        self.computer.set_name(comp1_name)

        # Store a second calculation
        calc2_label = "calc2"
        calc2 = orm.CalcJobNode()
        calc2.computer = self.computer
        calc2.set_option('resources', {"num_machines": 2,
                                        "num_mpiprocs_per_machine": 2})
        calc2.label = calc2_label
        calc2.store()

        # Export the second job calculation
        filename2 = os.path.join(temp_dir, "export2.tar.gz")
        export([calc2], outfile=filename2, silent=True)

        # Reset the database
        self.clean_db()
        self.insert_data()

        # Set the computer name to the same name as before
        self.computer.set_name(comp1_name)

        # Store a third calculation
        calc3_label = "calc3"
        calc3 = orm.CalcJobNode()
        calc3.computer = self.computer
        calc3.set_option('resources', {"num_machines": 2,
                                        "num_mpiprocs_per_machine": 2})
        calc3.label = calc3_label
        calc3.store()

        # Export the third job calculation
        filename3 = os.path.join(temp_dir, "export3.tar.gz")
        export([calc3], outfile=filename3, silent=True)

        # Clean the local database
        self.clean_db()

        # Check that there are no computers
        builder = orm.QueryBuilder()
        builder.append(orm.Computer, project=['*'])
        self.assertEqual(builder.count(), 0, "There should not be any computers"
                                                "in the database at this point.")

        # Check that there are no calculations
        builder = orm.QueryBuilder()
        builder.append(orm.CalcJobNode, project=['*'])
        self.assertEqual(builder.count(), 0, "There should not be any "
                                                "calculations in the database at "
                                                "this point.")

        # Import all the calculations
        import_data(filename1, silent=True)
        import_data(filename2, silent=True)
        import_data(filename3, silent=True)

        # Retrieve the calculation-computer pairs
        builder = orm.QueryBuilder()
        builder.append(orm.CalcJobNode, project=['label'], tag='jcalc')
        builder.append(orm.Computer, project=['name'],
                    with_node='jcalc')
        self.assertEqual(builder.count(), 3, "Three combinations expected.")
        res = builder.all()
        self.assertIn([calc1_label, comp1_name], res,
                        "Calc-Computer combination not found.")
        self.assertIn([calc2_label,
                        comp1_name + DUPL_SUFFIX.format(0)], res,
                        "Calc-Computer combination not found.")
        self.assertIn([calc3_label,
                        comp1_name + DUPL_SUFFIX.format(1)], res,
                        "Calc-Computer combination not found.")

    @with_temp_dir
    def test_correct_import_of_computer_json_params(self, temp_dir):
        """
        This test checks that the metadata and transport params are
        exported and imported correctly in both backends.
        """
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
        self.computer.set_metadata(comp1_metadata)
        self.computer.set_transport_params(comp1_transport_params)

        # Store a calculation
        calc1_label = "calc1"
        calc1 = orm.CalcJobNode()
        calc1.computer = self.computer
        calc1.set_option('resources', {"num_machines": 1,
                                        "num_mpiprocs_per_machine": 1})
        calc1.label = calc1_label
        calc1.store()

        # Export the first job calculation
        filename1 = os.path.join(temp_dir, "export1.tar.gz")
        export([calc1], outfile=filename1, silent=True)

        # Clean the local database
        self.clean_db()
        # Import the data
        import_data(filename1, silent=True)

        builder = orm.QueryBuilder()
        builder.append(orm.Computer, project=['transport_params', '_metadata'],
                    tag="comp")
        self.assertEqual(builder.count(), 1, "Expected only one computer")

        res = builder.dict()[0]
        self.assertEqual(res['comp']['transport_params'],
                            comp1_transport_params,
                            "Not the expected transport parameters "
                            "were found")
        self.assertEqual(res['comp']['_metadata'],
                            comp1_metadata,
                            "Not the expected metadata were found")

    @unittest.skip("Reenable when issue #2426 has been solved (migrate exported files from 0.3 to 0.4)")
    def test_import_of_django_sqla_export_file(self):
        """Check that sqla import manages to import the django export file correctly"""
        from aiida.backends.tests.utils.fixtures import import_archive_fixture

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
            builder = orm.QueryBuilder()
            builder.append(orm.Computer, project=['transport_params', '_metadata'], tag="comp",
                      filters={'name': {'!==': self.computer.name}})
            self.assertEqual(builder.count(), 1, "Expected only one computer")

            res = builder.dict()[0]

            self.assertEqual(res['comp']['transport_params'], comp1_transport_params)
            self.assertEqual(res['comp']['_metadata'], comp1_metadata)


class TestLinks(AiidaTestCase):
    """Test ex-/import cases related to Links"""

    def setUp(self):
        self.reset_database()

    def tearDown(self):
        self.reset_database()

    def get_all_node_links(self):
        """ Get all Node links currently in the DB """
        builder = orm.QueryBuilder()
        builder.append(orm.Node, project='uuid', tag='input')
        builder.append(orm.Node, project='uuid', tag='output', edge_project=['label', 'type'], with_incoming='input')
        return builder.all()

    @with_temp_dir
    def test_links_to_unknown_nodes(self, temp_dir):
        """
        Test importing of nodes, that have links to unknown nodes.
        """
        import tarfile

        from aiida.common.folders import SandboxFolder
        from aiida.common import json

        node_label = "Test structure data"
        sd = orm.StructureData()
        sd.label = str(node_label)
        sd.store()
        sd_uuid = sd.uuid

        filename = os.path.join(temp_dir, "export.tar.gz")
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
        self.assertEqual(orm.load_node(sd_uuid).label, node_label)

    @with_temp_dir
    def test_input_and_create_links(self, temp_dir):
        """
        Simple test that will verify that INPUT and CREATE links are properly exported and
        correctly recreated upon import.
        """
        from aiida.common.links import LinkType

        node_work = orm.CalculationNode().store()
        node_input = orm.Int(1).store()
        node_output = orm.Int(2).store()

        node_work.add_incoming(node_input, LinkType.INPUT_CALC, 'input')
        node_output.add_incoming(node_work, LinkType.CREATE, 'output')

        export_links = self.get_all_node_links()
        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([node_output], outfile=export_file, silent=True)

        self.reset_database()

        import_data(export_file, silent=True)
        import_links = self.get_all_node_links()

        export_set = [tuple(_) for _ in export_links]
        import_set = [tuple(_) for _ in import_links]

        self.assertSetEqual(set(export_set), set(import_set))

    def construct_complex_graph(self, export_combination=0,
            work_nodes=None, calc_nodes=None):
        """
        This method creates a "complex" graph with all available link types:
        INPUT_WORK, INPUT_CALC, CALL_WORK, CALL_CALC, CREATE, and RETURN
        and returns the nodes of the graph. It also returns various combinations
        of nodes that need to be extracted but also the final expected set of nodes
        (after adding the expected predecessors, desuccessors).
        """
        from aiida.common.links import LinkType

        if export_combination < 0 or export_combination > 9:
            return None

        if work_nodes is None:
            work_nodes = ["WorkflowNode", "WorkflowNode"]

        if calc_nodes is None:
            calc_nodes = ["orm.CalculationNode", "orm.CalculationNode"]

        # Class mapping
        # "CalcJobNode" is left out, since it is special.
        string_to_class = {
            "WorkflowNode": orm.WorkflowNode,
            "WorkChainNode": orm.WorkChainNode,
            "WorkFunctionNode": orm.WorkFunctionNode,
            "orm.CalculationNode": orm.CalculationNode,
            "CalcFunctionNode": orm.CalcFunctionNode
        }

        # Node creation
        data1 = orm.Int(1).store()
        data2 = orm.Int(1).store()
        work1 = string_to_class[work_nodes[0]]().store()
        work2 = string_to_class[work_nodes[1]]().store()

        if calc_nodes[0] == "CalcJobNode":
            calc1 = orm.CalcJobNode()
            calc1.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        else:
            calc1 = string_to_class[calc_nodes[0]]()
        calc1.computer = self.computer
        calc1.store()

        # Waiting to store Data nodes until they have been "created" with the links below,
        # because @calcfunctions cannot return data, i.e. return stored Data nodes
        data3 = orm.Int(1)
        data4 = orm.Int(1)

        if calc_nodes[1] == "CalcJobNode":
            calc2 = orm.CalcJobNode()
            calc2.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        else:
            calc2 = string_to_class[calc_nodes[1]]()
        calc2.computer = self.computer
        calc2.store()

        # Waiting to store Data nodes until they have been "created" with the links below,
        # because @calcfunctions cannot return data, i.e. return stored Data nodes
        data5 = orm.Int(1)
        data6 = orm.Int(1)

        # Link creation
        work1.add_incoming(data1, LinkType.INPUT_WORK, 'input1')
        work1.add_incoming(data2, LinkType.INPUT_WORK, 'input2')

        work2.add_incoming(data1, LinkType.INPUT_WORK, 'input1')
        work2.add_incoming(work1, LinkType.CALL_WORK, 'call2')

        calc1.add_incoming(data1, LinkType.INPUT_CALC, 'input1')
        calc1.add_incoming(work2, LinkType.CALL_CALC, 'call1')

        data3.add_incoming(calc1, LinkType.CREATE, 'create3')
        # data3 is stored now, because a @workfunction cannot return unstored Data,
        # i.e. create data.
        data3.store()
        data3.add_incoming(work2, LinkType.RETURN, 'return3')

        data4.add_incoming(calc1, LinkType.CREATE, 'create4')
        # data3 is stored now, because a @workfunction cannot return unstored Data,
        # i.e. create data.
        data4.store()
        data4.add_incoming(work2, LinkType.RETURN, 'return4')

        calc2.add_incoming(data4, LinkType.INPUT_CALC, 'input4')

        data5.add_incoming(calc2, LinkType.CREATE, 'create5')
        data6.add_incoming(calc2, LinkType.CREATE, 'create6')

        data5.store()
        data6.store()

        graph_nodes = [data1, data2, data3, data4, data5, data6, calc1, calc2, work1, work2]

        # Create various combinations of nodes that should be exported
        # and the final set of nodes that are exported in each case, following
        # predecessor(INPUT, CREATE)/successor(CALL, RETURN, CREATE) links.
        export_list = [
            (work1, [data1, data2, data3, data4, calc1, work1, work2]),
            (work2, [data1, data3, data4, calc1, work2]),
            (data3, [data1, data3, data4, calc1]),
            (data4, [data1, data3, data4, calc1]),
            (data5, [data1, data3, data4, data5, data6, calc1, calc2]),
            (data6, [data1, data3, data4, data5, data6, calc1, calc2]),
            (calc1, [data1, data3, data4, calc1]),
            (calc2, [data1, data3, data4, data5, data6, calc1, calc2]),
            (data1, [data1]),
            (data2, [data2])
        ]

        return graph_nodes, export_list[export_combination]

    @with_temp_dir
    def test_data_create_reversed_false(self, temp_dir):
        """Verify that create_reversed = False is respected when only exporting Data nodes."""
        from aiida.common.links import LinkType

        data_input = orm.Int(1).store()
        data_output = orm.Int(2).store()

        calc = orm.CalcJobNode()
        calc.computer = self.computer
        calc.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})
        calc.store()

        calc.add_incoming(data_input, LinkType.INPUT_CALC, 'input')
        data_output.add_incoming(calc, LinkType.CREATE, 'create')
        data_output_uuid = data_output.uuid

        group = orm.Group(label='test_group').store()
        group.add_nodes(data_output)

        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([group], outfile=export_file, silent=True, create_reversed=False)

        self.reset_database()

        import_data(export_file, silent=True)

        builder = orm.QueryBuilder()
        builder.append(orm.Data)
        self.assertEqual(builder.count(), 1, 'Expected a single Data node but got {}'.format(builder.count()))
        self.assertEqual(builder.all()[0][0].uuid, data_output_uuid)

        builder = orm.QueryBuilder()
        builder.append(orm.CalcJobNode)
        self.assertEqual(builder.count(), 0, 'Expected no Calculation nodes')

    @with_temp_dir
    def test_complex_workflow_graph_links(self, temp_dir):
        """
        This test checks that all the needed links are correctly exported and
        imported. More precisely, it checks that INPUT, CREATE, RETURN and CALL
        links connecting Data nodes, CalcJobNodes and WorkCalculations are
        exported and imported correctly.
        """
        from aiida.common.links import LinkType

        graph_nodes, _ = self.construct_complex_graph()

        # Getting the input, create, return and call links
        builder = orm.QueryBuilder()
        builder.append(orm.Node, project='uuid')
        builder.append(orm.Node, project='uuid',
                    edge_project=['label', 'type'],
                    edge_filters={'type': {'in': (LinkType.INPUT_CALC.value,
                                                LinkType.INPUT_WORK.value,
                                                LinkType.CREATE.value,
                                                LinkType.RETURN.value,
                                                LinkType.CALL_CALC.value,
                                                LinkType.CALL_WORK.value)}})
        export_links = builder.all()

        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export(graph_nodes, outfile=export_file, silent=True)

        self.reset_database()

        import_data(export_file, silent=True)
        import_links = self.get_all_node_links()

        export_set = [tuple(_) for _ in export_links]
        import_set = [tuple(_) for _ in import_links]

        self.assertSetEqual(set(export_set), set(import_set))

    @with_temp_dir
    def test_complex_workflow_graph_export_sets(self, temp_dir):
        """Test ex-/import of individual nodes in complex graph"""
        for export_conf in range(0, 9):

            _, (export_node, export_target) = self.construct_complex_graph(export_conf)
            export_target_uuids = set(str(_.uuid) for _ in export_target)

            export_file = os.path.join(temp_dir, 'export.tar.gz')
            export([export_node], outfile=export_file, silent=True, overwrite=True)
            export_node_str = str(export_node)

            self.reset_database()

            import_data(export_file, silent=True)

            # Get all the nodes of the database
            builder = orm.QueryBuilder()
            builder.append(orm.Node, project='uuid')
            imported_node_uuids = set(str(_[0]) for _ in builder.all())

            self.assertSetEqual(
                export_target_uuids,
                imported_node_uuids,
                "Problem in comparison of export node: " +
                str(export_node_str) + "\n" +
                "Expected set: " + str(export_target_uuids) + "\n" +
                "Imported set: " + str(imported_node_uuids) + "\n" +
                "Difference: " + str([_ for _ in
                                        export_target_uuids.symmetric_difference(
                                            imported_node_uuids)])
            )

    @with_temp_dir
    def test_high_level_workflow_links(self, temp_dir):
        """
        This test checks that all the needed links are correctly exported and imported.
        INPUT_CALC, INPUT_WORK, CALL_CALC, CALL_WORK, CREATE, and RETURN
        links connecting Data nodes and high-level Calculation and Workflow nodes:
        CalcJobNode, CalcFunctionNode, WorkChainNode, WorkFunctionNode
        """
        from aiida.common.links import LinkType

        high_level_calc_nodes = [
            ["CalcJobNode", "CalcJobNode"],
            ["CalcJobNode", "CalcFunctionNode"],
            ["CalcFunctionNode", "CalcJobNode"],
            ["CalcFunctionNode", "CalcFunctionNode"]
        ]

        high_level_work_nodes = [
            ["WorkChainNode", "WorkChainNode"],
            ["WorkChainNode", "WorkFunctionNode"],
            ["WorkFunctionNode", "WorkChainNode"],
            ["WorkFunctionNode", "WorkFunctionNode"]
        ]

        for calcs in high_level_calc_nodes:
            for works in high_level_work_nodes:
                self.reset_database()

                graph_nodes, _ = self.construct_complex_graph(calc_nodes=calcs, work_nodes=works)

                # Getting the input, create, return and call links
                builder = orm.QueryBuilder()
                builder.append(orm.Node, project='uuid')
                builder.append(orm.Node, project='uuid',
                        edge_project=['label', 'type'],
                        edge_filters={'type': {'in': (LinkType.INPUT_CALC.value,
                                                        LinkType.INPUT_WORK.value,
                                                        LinkType.CREATE.value,
                                                        LinkType.RETURN.value,
                                                        LinkType.CALL_CALC.value,
                                                        LinkType.CALL_WORK.value)}})

                self.assertEqual(builder.count(), 13, msg=
                "Failed with c1={}, c2={}, w1={}, w2={}".format(calcs[0], calcs[1], works[0], works[1]))

                export_links = builder.all()

                export_file = os.path.join(temp_dir, 'export.tar.gz')
                export(graph_nodes, outfile=export_file, silent=True, overwrite=True)

                self.reset_database()

                import_data(export_file, silent=True)
                import_links = self.get_all_node_links()

                export_set = [tuple(_) for _ in export_links]
                import_set = [tuple(_) for _ in import_links]

                self.assertSetEqual(set(export_set), set(import_set), msg=
                "Failed with c1={}, c2={}, w1={}, w2={}".format(calcs[0], calcs[1], works[0], works[1]))

    @with_temp_dir
    def test_links_for_workflows(self, temp_dir):
        """
        Check export flag `return_reversed=True`.
        Check that CALL links are not followed in the export procedure,
        and the only creation is followed for data::

            ____       ____        ____
           |    | INP |    | CALL |    |
           | i1 | --> | w1 | <--- | w2 |
           |____|     |____|      |____|
                        |
                        v RETURN
                       ____
                      |    |
                      | o1 |
                      |____|

        """
        from aiida.common.links import LinkType

        w1 = orm.WorkflowNode().store()
        w2 = orm.WorkflowNode().store()
        i1 = orm.Int(1).store()
        o1 = orm.Int(2).store()

        w1.add_incoming(i1, LinkType.INPUT_WORK, 'input-i1')
        w1.add_incoming(w2, LinkType.CALL_WORK, 'call')
        o1.add_incoming(w1, LinkType.RETURN, 'return')

        links_count_wanted = 2  # All 3 links, except CALL links (the CALL_WORK)
        links_wanted = [l for l in self.get_all_node_links() if l[3] not in
                        (LinkType.CALL_WORK.value,
                        LinkType.CALL_CALC.value)]
        # Check all links except CALL links are retrieved
        self.assertEqual(links_count_wanted, len(links_wanted))

        export_file_1 = os.path.join(temp_dir, 'export-1.tar.gz')
        export_file_2 = os.path.join(temp_dir, 'export-2.tar.gz')
        export([o1], outfile=export_file_1, silent=True, return_reversed=True)
        export([w1], outfile=export_file_2, silent=True, return_reversed=True)

        self.reset_database()

        import_data(export_file_1, silent=True)
        import_links = self.get_all_node_links()

        self.assertListEqual(sorted(links_wanted), sorted(import_links))
        self.assertEqual(links_count_wanted, len(import_links))
        self.reset_database()

        import_data(export_file_2, silent=True)
        import_links = self.get_all_node_links()
        self.assertListEqual(sorted(links_wanted), sorted(import_links))
        self.assertEqual(links_count_wanted, len(import_links))

    @with_temp_dir
    def test_double_return_links_for_workflows(self, temp_dir):
        """
        This test checks that double return links to a node can be exported
        and imported without problems,
        """
        from aiida.common.links import LinkType

        w1 = orm.WorkflowNode().store()
        w2 = orm.WorkflowNode().store()
        i1 = orm.Int(1).store()
        o1 = orm.Int(2).store()

        w1.add_incoming(i1, LinkType.INPUT_WORK, 'input-i1')
        w1.add_incoming(w2, LinkType.CALL_WORK, 'call')
        o1.add_incoming(w1, LinkType.RETURN, 'return1')
        o1.add_incoming(w2, LinkType.RETURN, 'return2')
        links_count = 4

        uuids_wanted = set(_.uuid for _ in (w1, o1, i1, w2))
        links_wanted = self.get_all_node_links()

        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([o1, w1, w2, i1], outfile=export_file, silent=True)

        self.reset_database()

        import_data(export_file, silent=True)

        uuids_in_db = [str(uuid) for [uuid] in
            orm.QueryBuilder().append(orm.Node, project='uuid').all()]
        self.assertListEqual(sorted(uuids_wanted), sorted(uuids_in_db))

        links_in_db = self.get_all_node_links()
        self.assertListEqual(sorted(links_wanted), sorted(links_in_db))

        # Assert number of links, checking both RETURN links are included
        self.assertEqual(len(links_wanted), links_count)  # Before export
        self.assertEqual(len(links_in_db), links_count)   # After import


class TestCode(AiidaTestCase):
    """Test ex-/import cases related to Codes"""

    def setUp(self):
        self.reset_database()

    def tearDown(self):
        self.reset_database()

    def get_all_node_links(self):
        """ Get all Node links currently in the DB """
        builder = orm.QueryBuilder()
        builder.append(orm.Node, project='uuid', tag='input')
        builder.append(orm.Node, project='uuid', tag='output', edge_project=['label', 'type'], with_incoming='input')
        return builder.all()

    @with_temp_dir
    def test_that_solo_code_is_exported_correctly(self, temp_dir):
        """
        This test checks that when a calculation is exported then the
        corresponding code is also exported.
        """
        code_label = 'test_code1'

        code = orm.Code()
        code.set_remote_computer_exec((self.computer, '/bin/true'))
        code.label = code_label
        code.store()

        code_uuid = code.uuid

        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([code], outfile=export_file, silent=True)

        self.reset_database()

        import_data(export_file, silent=True)

        self.assertEqual(orm.load_node(code_uuid).label, code_label)

    @with_temp_dir
    def test_input_code(self, temp_dir):
        """
        This test checks that when a calculation is exported then the
        corresponding code is also exported. It also checks that the links
        are also in place after the import.
        """
        from aiida.common.links import LinkType

        code_label = 'test_code1'

        code = orm.Code()
        code.set_remote_computer_exec((self.computer, '/bin/true'))
        code.label = code_label
        code.store()

        code_uuid = code.uuid

        jc = orm.CalcJobNode()
        jc.computer = self.computer
        jc.set_option('resources',
                     {"num_machines": 1, "num_mpiprocs_per_machine": 1})
        jc.store()

        jc.add_incoming(code, LinkType.INPUT_CALC, 'code')
        links_count = 1

        export_links = self.get_all_node_links()

        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([jc], outfile=export_file, silent=True)

        self.reset_database()

        import_data(export_file, silent=True)

        # Check that the code node is there
        self.assertEqual(orm.load_node(code_uuid).label, code_label)

        # Check that the link is in place
        import_links = self.get_all_node_links()
        self.assertListEqual(sorted(export_links), sorted(import_links))
        self.assertEqual(len(export_links), links_count,
                         "Expected to find only one link from code to "
                         "the calculation node before export. {} found."
                         .format(len(export_links)))
        self.assertEqual(len(import_links), links_count,
                         "Expected to find only one link from code to "
                         "the calculation node after import. {} found."
                         .format(len(import_links)))

    @with_temp_dir
    def test_solo_code(self, temp_dir):
        """
        This test checks that when a calculation is exported then the
        corresponding code is also exported.
        """
        code_label = 'test_code1'

        code = orm.Code()
        code.set_remote_computer_exec((self.computer, '/bin/true'))
        code.label = code_label
        code.store()

        code_uuid = code.uuid

        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([code], outfile=export_file, silent=True)

        self.clean_db()
        self.insert_data()

        import_data(export_file, silent=True)

        self.assertEqual(orm.load_node(code_uuid).label, code_label)


class TestLogs(AiidaTestCase):
    """Test ex-/import cases related to Logs"""

    def setUp(self):
        """Reset database prior to all tests"""
        super(TestLogs, self).setUp()
        self.reset_database()

    def tearDown(self):
        """
        Delete all the created log entries
        """
        super(TestLogs, self).tearDown()
        orm.Log.objects.delete_many({})

    @with_temp_dir
    def test_export_import_of_critical_log_msg_and_metadata(self, temp_dir):
        """ Testing logging of critical message """
        message = 'Testing logging of critical failure'
        calc = orm.CalculationNode()

        # Firing a log for an unstored node should not end up in the database
        calc.logger.critical(message)
        # There should be no log messages for the unstored object
        self.assertEqual(len(orm.Log.objects.all()), 0)

        # After storing the node, logs above log level should be stored
        calc.store()
        calc.logger.critical(message)

        # Store Log metadata
        log_metadata = orm.Log.objects.get(dbnode_id=calc.id).metadata

        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([calc], outfile=export_file, silent=True)

        self.reset_database()

        import_data(export_file, silent=True)

        # Finding all the log messages
        logs = orm.Log.objects.all()

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].message, message)
        self.assertEqual(logs[0].metadata, log_metadata)

    @with_temp_dir
    def test_exclude_logs_flag(self, temp_dir):
        """Test that the `include_logs` argument for `export` works."""
        log_msg = 'Testing logging of critical failure'

        # Create node
        calc = orm.CalculationNode()
        calc.store()

        # Create log message
        calc.logger.critical(log_msg)

        # Save uuids prior to export
        calc_uuid = calc.uuid

        # Export, excluding logs
        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([calc], outfile=export_file, silent=True, include_logs=False)

        # Clean database and reimport exported data
        self.reset_database()
        import_data(export_file, silent=True)

        # Finding all the log messages
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid']).all()
        import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid']).all()

        # There should be exactly: 1 orm.CalculationNode, 0 Logs
        self.assertEqual(len(import_calcs), 1)
        self.assertEqual(len(import_logs), 0)

        # Check it's the correct node
        self.assertEqual(str(import_calcs[0][0]), calc_uuid)

    @with_temp_dir
    def test_export_of_imported_logs(self, temp_dir):
        """Test export of imported Log"""
        log_msg = 'Testing export of imported log'

        # Create node
        calc = orm.CalculationNode()
        calc.store()

        # Create log message
        calc.logger.critical(log_msg)

        # Save uuids prior to export
        calc_uuid = calc.uuid
        log_uuid = orm.QueryBuilder().append(orm.Log, project=['uuid']).all()
        log_uuid = str(log_uuid[0][0])

        # Export
        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([calc], outfile=export_file, silent=True)

        # Clean database and reimport exported data
        self.reset_database()
        import_data(export_file, silent=True)

        # Finding all the log messages
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid']).all()
        import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid']).all()

        # There should be exactly: 1 CalculationNode, 1 Log
        self.assertEqual(len(import_calcs), 1)
        self.assertEqual(len(import_logs), 1)

        # Check the UUIDs are the same
        self.assertEqual(str(import_calcs[0][0]), calc_uuid)
        self.assertEqual(str(import_logs[0][0]), log_uuid)

        # Re-export
        calc = orm.load_node(import_calcs[0][0])
        re_export_file = os.path.join(temp_dir, 're_export.tar.gz')
        export([calc], outfile=re_export_file, silent=True)

        # Clean database and reimport exported data
        self.reset_database()
        import_data(re_export_file, silent=True)

        # Finding all the log messages
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid']).all()
        import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid']).all()

        # There should be exactly: 1 CalculationNode, 1 Log
        self.assertEqual(len(import_calcs), 1)
        self.assertEqual(len(import_logs), 1)

        # Check the UUIDs are the same
        self.assertEqual(str(import_calcs[0][0]), calc_uuid)
        self.assertEqual(str(import_logs[0][0]), log_uuid)

    @with_temp_dir
    def test_multiple_imports_for_single_node(self, temp_dir):
        """Test multiple imports for single node with different logs are imported correctly"""
        log_msgs = [
            "Life is like riding a bicycle.",
            "To keep your balance,",
            "you must keep moving."
        ]

        # Create Node and initial log message and save UUIDs prior to export
        node = orm.CalculationNode().store()
        node.logger.critical(log_msgs[0])
        node_uuid = node.uuid
        log_uuid_existing = orm.QueryBuilder().append(orm.Log, project=['uuid']).all()
        log_uuid_existing = str(log_uuid_existing[0][0])

        # Export as "EXISTING" DB
        export_file_existing = os.path.join(temp_dir, 'export_EXISTING.tar.gz')
        export([node], outfile=export_file_existing, silent=True)

        # Add 2 more Logs and save UUIDs for all three Logs prior to export
        node.logger.critical(log_msgs[1])
        node.logger.critical(log_msgs[2])
        log_uuids_full = orm.QueryBuilder().append(orm.Log, project=['uuid']).all()
        log_uuids_full = [str(log[0]) for log in log_uuids_full]

        # Export as "FULL" DB
        export_file_full = os.path.join(temp_dir, 'export_FULL.tar.gz')
        export([node], outfile=export_file_full, silent=True)

        # Clean database and reimport "EXISTING" DB
        self.reset_database()
        import_data(export_file_existing, silent=True)

        # Check correct import
        builder = orm.QueryBuilder().append(orm.Node, tag='node', project=['uuid'])
        builder.append(orm.Log, with_node='node', project=['uuid', 'message'])
        builder = builder.all()

        self.assertEqual(len(builder), 1) # There is 1 Log in "EXISTING" DB

        imported_node_uuid = builder[0][0]
        self.assertEqual(imported_node_uuid, node_uuid)

        imported_log_uuid = builder[0][1]
        imported_log_message = builder[0][2]
        self.assertEqual(imported_log_uuid, log_uuid_existing)
        self.assertEqual(imported_log_message, log_msgs[0])

        # Import "FULL" DB
        import_data(export_file_full, silent=True)

        # Since the UUID of the node is identical with the node already in the DB,
        # the Logs should be added to the existing node, avoiding the addition of
        # the single Log already present.
        # Check this by retrieving all Logs for the node.
        builder = orm.QueryBuilder().append(orm.Node, tag='node', project=['uuid'])
        builder.append(orm.Log, with_node='node', project=['uuid', 'message'])
        builder = builder.all()

        self.assertEqual(len(builder), len(log_msgs)) # There should now be 3 Logs

        imported_node_uuid = builder[0][0]
        self.assertEqual(imported_node_uuid, node_uuid)
        for log in builder:
            imported_log_uuid = log[1]
            imported_log_content = log[2]

            self.assertIn(imported_log_uuid, log_uuids_full)
            self.assertIn(imported_log_content, log_msgs)

    @with_temp_dir
    def test_reimport_of_logs_for_single_node(self, temp_dir):
        """
        When a node with logs already exist in the DB, and more logs are imported
        for the same node (same UUID), test that only new log-entries are added.

        Part I:
        Create CalculationNode and 1 Log for it.
        Export CalculationNode with its 1 Log to export file #1 "EXISTING database".
        Add 2 Logs to CalculationNode.
        Export CalculationNode with its 3 Logs to export file #2 "FULL database".
        Reset database.

        Part II:
        Reimport export file #1 "EXISTING database".
        Add 2 Logs to CalculationNode (different UUID than for "FULL database").
        Export CalculationNode with its 3 Logs to export file #3 "NEW database".
        Reset database.

        Part III:
        Reimport export file #1 "EXISTING database" (1 CalculationNode, 1 Log).
        Import export file #2 "FULL database" (1 CalculationNode, 3 Logs).
        Check the database EXACTLY contains 1 CalculationNode and 3 Logs,
        with matching UUIDS all the way through all previous Parts.

        Part IV:
        Import export file #3 "NEW database" (1 CalculationNode, 3 Logs).
        Check the database EXACTLY contains 1 CalculationNode and 5 Logs,
        with matching UUIDS all the way through all previous Parts.
        NB! There should now be 5 Logs in the database. 4 of which are identical
        in pairs, except for their UUID.
        """
        export_filenames = {
            "EXISTING": "export_EXISTING_db.tar.gz",
            "FULL": "export_FULL_db.tar.gz",
            "NEW": "export_NEW_db.tar.gz"
        }

        log_msgs = [
            "Life is like riding a bicycle.",
            "To keep your balance,",
            "you must keep moving."
        ]

        ## Part I
        # Create node and save UUID
        calc = orm.CalculationNode()
        calc.store()
        calc_uuid = calc.uuid

        # Create first log message
        calc.logger.critical(log_msgs[0])

        # There should be exactly: 1 CalculationNode, 1 Log
        export_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        export_logs = orm.QueryBuilder().append(orm.Log, project=['uuid'])
        self.assertEqual(export_calcs.count(), 1)
        self.assertEqual(export_logs.count(), 1)

        # Save Log UUID before export
        existing_log_uuids = [str(export_logs.all()[0][0])]

        # Export "EXISTING" DB
        export_file_existing = os.path.join(temp_dir, export_filenames["EXISTING"])
        export([calc], outfile=export_file_existing, silent=True)

        # Add remaining Log messages
        for log_msg in log_msgs[1:]:
            calc.logger.critical(log_msg)

        # There should be exactly: 1 CalculationNode, 3 Logs (len(log_msgs))
        export_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        export_logs = orm.QueryBuilder().append(orm.Log, project=['uuid'])
        self.assertEqual(export_calcs.count(), 1)
        self.assertEqual(export_logs.count(), len(log_msgs))

        # Save Log UUIDs before export, there should be 3 UUIDs in total (len(log_msgs))
        full_log_uuids = set(existing_log_uuids)
        for log_uuid in export_logs.all():
            full_log_uuids.add(str(log_uuid[0]))
        self.assertEqual(len(full_log_uuids), len(log_msgs))

        # Export "FULL" DB
        export_file_full = os.path.join(temp_dir, export_filenames["FULL"])
        export([calc], outfile=export_file_full, silent=True)

        # Clean database
        self.reset_database()

        ## Part II
        # Reimport "EXISTING" DB
        import_data(export_file_existing, silent=True)

        # Check the database is correctly imported.
        # There should be exactly: 1 CalculationNode, 1 Log
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid'])
        self.assertEqual(import_calcs.count(), 1)
        self.assertEqual(import_logs.count(), 1)
        # Furthermore, the UUIDs should be the same
        self.assertEqual(str(import_calcs.all()[0][0]), calc_uuid)
        self.assertIn(str(import_logs.all()[0][0]), existing_log_uuids)

        # Add remaining Log messages (again)
        calc = orm.load_node(import_calcs.all()[0][0])
        for log_msg in log_msgs[1:]:
            calc.logger.critical(log_msg)

        # There should be exactly: 1 CalculationNode, 3 Logs (len(log_msgs))
        export_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        export_logs = orm.QueryBuilder().append(orm.Log, project=['uuid'])
        self.assertEqual(export_calcs.count(), 1)
        self.assertEqual(export_logs.count(), len(log_msgs))

        # Save Log UUIDs before export, there should be 3 UUIDs in total (len(log_msgs))
        new_log_uuids = set(existing_log_uuids)
        for log_uuid in export_logs.all():
            new_log_uuids.add(str(log_uuid[0]))
        self.assertEqual(len(new_log_uuids), len(log_msgs))

        # Export "NEW" DB
        export_file_new = os.path.join(temp_dir, export_filenames["NEW"])
        export([calc], outfile=export_file_new, silent=True)

        # Clean database
        self.reset_database()

        ## Part III
        # Reimport "EXISTING" DB
        import_data(export_file_existing, silent=True)

        # Check the database is correctly imported.
        # There should be exactly: 1 CalculationNode, 1 Log
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid'])
        self.assertEqual(import_calcs.count(), 1)
        self.assertEqual(import_logs.count(), 1)
        # Furthermore, the UUIDs should be the same
        self.assertEqual(str(import_calcs.all()[0][0]), calc_uuid)
        self.assertIn(str(import_logs.all()[0][0]), existing_log_uuids)

        # Import "FULL" DB
        import_data(export_file_full, silent=True)

        # Check the database is correctly imported.
        # There should be exactly: 1 CalculationNode, 3 Logs (len(log_msgs))
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid'])
        self.assertEqual(import_calcs.count(), 1)
        self.assertEqual(import_logs.count(), len(log_msgs))
        # Furthermore, the UUIDs should be the same
        self.assertEqual(str(import_calcs.all()[0][0]), calc_uuid)
        for log in import_logs.all():
            log_uuid = str(log[0])
            self.assertIn(log_uuid, full_log_uuids)

        ## Part IV
        # Import "NEW" DB
        import_data(export_file_new, silent=True)

        # Check the database is correctly imported.
        # There should be exactly: 1 CalculationNode, 5 Logs (len(log_msgs))
        # 4 of the logs are identical in pairs, except for the UUID.
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        import_logs = orm.QueryBuilder().append(orm.Log, project=['uuid', 'message'])
        self.assertEqual(import_calcs.count(), 1)
        self.assertEqual(import_logs.count(), 5)
        # Furthermore, the UUIDs should be the same
        self.assertEqual(str(import_calcs.all()[0][0]), calc_uuid)
        total_log_uuids = full_log_uuids.copy()
        total_log_uuids.update(new_log_uuids)
        for log in import_logs.all():
            log_uuid = str(log[0])
            log_message = str(log[1])
            self.assertIn(log_uuid, total_log_uuids)
            self.assertIn(log_message, log_msgs)


class TestComments(AiidaTestCase):
    """Test ex-/import cases related to Comments"""

    def setUp(self):
        super(TestComments, self).setUp()
        self.reset_database()
        self.comments = [
            "We're no strangers to love",
            "You know the rules and so do I",
            "A full commitment's what I'm thinking of",
            "You wouldn't get this from any other guy"
        ]

    def tearDown(self):
        super(TestComments, self).tearDown()
        self.reset_database()

    @with_temp_dir
    def test_multiple_imports_for_single_node(self, temp_dir):
        """Test multiple imports for single node with different comments are imported correctly"""
        user = orm.User.objects.get_default()

        # Create Node and initial comments and save UUIDs prior to export
        node = orm.CalculationNode().store()
        comment_one = orm.Comment(node, user, self.comments[0]).store()
        comment_two = orm.Comment(node, user, self.comments[1]).store()
        node_uuid = node.uuid
        comment_uuids = [c.uuid for c in [comment_one, comment_two]]

        # Export as "EXISTING" DB
        export_file_existing = os.path.join(temp_dir, 'export_EXISTING.tar.gz')
        export([node], outfile=export_file_existing, silent=True)

        # Add 2 more Comments and save UUIDs prior to export
        comment_three = orm.Comment(node, user, self.comments[2]).store()
        comment_four = orm.Comment(node, user, self.comments[3]).store()
        comment_uuids += [c.uuid for c in [comment_three, comment_four]]

        # Export as "FULL" DB
        export_file_full = os.path.join(temp_dir, 'export_FULL.tar.gz')
        export([node], outfile=export_file_full, silent=True)

        # Clean database and reimport "EXISTING" DB
        self.reset_database()
        import_data(export_file_existing, silent=True)

        # Check correct import
        builder = orm.QueryBuilder().append(orm.Node, tag='node', project=['uuid'])
        builder.append(orm.Comment, with_node='node', project=['uuid', 'content'])
        builder = builder.all()

        self.assertEqual(len(builder), 2) # There are 2 Comments in "EXISTING" DB

        imported_node_uuid = builder[0][0]
        self.assertEqual(imported_node_uuid, node_uuid)
        for comment in builder:
            imported_comment_uuid = comment[1]
            imported_comment_content = comment[2]

            self.assertIn(imported_comment_uuid, comment_uuids[0:2])
            self.assertIn(imported_comment_content, self.comments[0:2])

        # Import "FULL" DB
        import_data(export_file_full, silent=True)

        # Since the UUID of the node is identical with the node already in the DB,
        # the Comments should be added to the existing node, avoiding the addition
        # of the two Comments already present.
        # Check this by retrieving all Comments for the node.
        builder = orm.QueryBuilder().append(orm.Node, tag='node', project=['uuid'])
        builder.append(orm.Comment, with_node='node', project=['uuid', 'content'])
        builder = builder.all()

        self.assertEqual(len(builder), len(self.comments)) # There should now be 4 Comments

        imported_node_uuid = builder[0][0]
        self.assertEqual(imported_node_uuid, node_uuid)
        for comment in builder:
            imported_comment_uuid = comment[1]
            imported_comment_content = comment[2]

            self.assertIn(imported_comment_uuid, comment_uuids)
            self.assertIn(imported_comment_content, self.comments)

    @with_temp_dir
    def test_exclude_comments_flag(self, temp_dir):
        """Test comments and associated commenting users are not exported when using `include_comments=False`."""
        # Create users, node, and comments
        user_one = orm.User.objects.get_default()
        user_two = orm.User(email="commenting@user.s").store()

        node = orm.Data().store()

        comment_one = orm.Comment(node, user_one, self.comments[0]).store()
        comment_two = orm.Comment(node, user_one, self.comments[1]).store()

        comment_three = orm.Comment(node, user_two, self.comments[2]).store()
        comment_four = orm.Comment(node, user_two, self.comments[3]).store()

        # Get values prior to export
        users_email = [u.email for u in [user_one, user_two]]
        node_uuid = node.uuid

        # Check that node belongs to user_one
        self.assertEqual(node.user.email, users_email[0])

        # Export nodes, excluding comments
        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([node], outfile=export_file, silent=True, include_comments=False)

        # Clean database and reimport exported file
        self.reset_database()
        import_data(export_file, silent=True)

        # Get node, users, and comments
        import_nodes = orm.QueryBuilder().append(orm.Node, project=['uuid']).all()
        import_comments = orm.QueryBuilder().append(orm.Comment, project=['uuid']).all()
        import_users = orm.QueryBuilder().append(orm.User, project=['email']).all()

        # There should be exactly: 1 Node, 0 Comments, 1 User
        self.assertEqual(len(import_nodes), 1)
        self.assertEqual(len(import_comments), 0)
        self.assertEqual(len(import_users), 1)

        # Check it's the correct user (and node)
        self.assertEqual(str(import_nodes[0][0]), node_uuid)
        self.assertEqual(str(import_users[0][0]), users_email[0])

    @with_temp_dir
    def test_calc_and_data_nodes_with_comments(self, temp_dir):
        """ Test comments for CalculatioNode and Data node are correctly ex-/imported """
        # Create user, nodes, and comments
        user = orm.User.objects.get_default()

        calc_node = orm.CalculationNode().store()
        data_node = orm.Data().store()

        comment_one = orm.Comment(calc_node, user, self.comments[0]).store()
        comment_two = orm.Comment(calc_node, user, self.comments[1]).store()

        comment_three = orm.Comment(data_node, user, self.comments[2]).store()
        comment_four = orm.Comment(data_node, user, self.comments[3]).store()

        # Get values prior to export
        calc_uuid = calc_node.uuid
        data_uuid = data_node.uuid
        calc_comments_uuid = [c.uuid for c in [comment_one, comment_two]]
        data_comments_uuid = [c.uuid for c in [comment_three, comment_four]]

        # Export nodes
        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([calc_node, data_node], outfile=export_file, silent=True)

        # Clean database and reimport exported file
        self.reset_database()
        import_data(export_file, silent=True)

        # Get nodes and comments
        builder = orm.QueryBuilder()
        builder.append(orm.Node, tag='node', project=['uuid'])
        builder.append(orm.Comment, with_node='node', project=['uuid'])
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

    @with_temp_dir
    def test_multiple_user_comments_for_single_node(self, temp_dir):
        """ Test multiple users commenting on a single orm.CalculationNode """
        # Create users, node, and comments
        user_one = orm.User.objects.get_default()
        user_two = orm.User(email="commenting@user.s").store()

        node = orm.CalculationNode().store()

        comment_one = orm.Comment(node, user_one, self.comments[0]).store()
        comment_two = orm.Comment(node, user_one, self.comments[1]).store()

        comment_three = orm.Comment(node, user_two, self.comments[2]).store()
        comment_four = orm.Comment(node, user_two, self.comments[3]).store()

        # Get values prior to export
        users_email = [u.email for u in [user_one, user_two]]
        node_uuid = str(node.uuid)
        user_one_comments_uuid = [str(c.uuid) for c in [comment_one, comment_two]]
        user_two_comments_uuid = [str(c.uuid) for c in [comment_three, comment_four]]

        # Export node, along with comments and users recursively
        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([node], outfile=export_file, silent=True)

        # Clean database and reimport exported file
        self.reset_database()
        import_data(export_file, silent=True)

        # Get node, users, and comments
        builder = orm.QueryBuilder()
        builder.append(orm.Node, tag='node', project=['uuid'])
        builder.append(orm.Comment, tag='comment', with_node='node', project=['uuid'])
        builder.append(orm.User, with_comment='comment', project=['email'])
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

    @with_temp_dir
    def test_mtime_of_imported_comments(self, temp_dir):
        """
        Test mtime does not change for imported comments
        This is related to correct usage of `comment_mode` when importing.
        """
        # Get user
        user = orm.User.objects.get_default()

        comment_content = "You get what you give"

        # Create node
        calc = orm.CalculationNode().store()

        # Create comment
        comment = orm.Comment(calc, user, comment_content).store()
        calc.store()

        # Save UUIDs and mtime
        calc_uuid = calc.uuid
        builder = orm.QueryBuilder().append(orm.Comment, project=['uuid', 'mtime']).all()
        comment_uuid = str(builder[0][0])
        comment_mtime = builder[0][1]

        builder = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid', 'mtime']).all()
        calc_uuid = str(builder[0][0])
        calc_mtime = builder[0][1]

        # Export, reset database and reimport
        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([calc], outfile=export_file, silent=True)
        self.reset_database()
        import_data(export_file, silent=True)

        # Retrieve node and comment
        builder = orm.QueryBuilder().append(orm.CalculationNode, tag='calc', project=['uuid', 'mtime'])
        builder.append(orm.Comment, with_node='calc', project=['uuid', 'mtime'])

        import_entities = builder.all()[0]

        self.assertEqual(len(import_entities), 4) # Check we have the correct amount of returned values

        import_calc_uuid = str(import_entities[0])
        import_calc_mtime = import_entities[1]
        import_comment_uuid = str(import_entities[2])
        import_comment_mtime = import_entities[3]

        # Check we have the correct UUIDs
        self.assertEqual(import_calc_uuid, calc_uuid)
        self.assertEqual(import_comment_uuid, comment_uuid)

        # Make sure the mtime is the same after import as it was before export
        self.assertEqual(import_comment_mtime, comment_mtime)
        self.assertEqual(import_calc_mtime, calc_mtime)

    @with_temp_dir
    def test_import_arg_comment_mode(self, temp_dir):
        """
        Test the import keyword `comment_mode`.
        It may be `'newest'` or `'overwrite'`.
        Test import of 'old' comment that has since been changed in DB.
        """
        # Get user
        # Will have to do this again after resetting the DB
        user = orm.User.objects.get_default()

        ## Test comment_mode='newest'
        # Create node
        calc = orm.CalculationNode().store()
        calc_uuid = calc.uuid

        # Creates comment
        cmt = orm.Comment(calc, user, self.comments[0]).store()
        cmt_uuid = cmt.uuid

        # Export calc and comment
        export_file = os.path.join(temp_dir, "export_file.tar.gz")
        export([calc], outfile=export_file, silent=True)

        # Update comment
        cmt.set_content(self.comments[1])

        # Check that Comment has been updated, and that there is only 1
        export_comments = orm.QueryBuilder().append(orm.Comment, project=['uuid', 'content'])
        self.assertEqual(export_comments.count(), 1)
        self.assertEqual(export_comments.all()[0][0], cmt_uuid)
        self.assertEqual(export_comments.all()[0][1], self.comments[1])

        # Export calc and UPDATED comment
        export_file_updated = os.path.join(temp_dir, "export_file_updated.tar.gz")
        export([calc], outfile=export_file_updated, silent=True)

        # Reimport exported 'old' calc and comment
        import_data(export_file, silent=True, comment_mode='newest')

        # Check there are exactly 1 CalculationNode and 1 Comment
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, tag='calc', project=['uuid'])
        self.assertEqual(import_calcs.count(), 1)
        import_comments = import_calcs.append(orm.Comment, with_node='calc', project=['uuid', 'content'])
        self.assertEqual(import_comments.count(), 1)

        # Check the uuids have not changed
        self.assertEqual(import_calcs.all()[0][0], calc_uuid)
        self.assertEqual(import_comments.all()[0][1], cmt_uuid)

        # Check the content of the comment has NOT been rewritten ('newest' mode)
        self.assertEqual(import_comments.all()[0][2], self.comments[1])

        ## Test comment_mode='overwrite'
        # Reimport exported 'old' calc and comment
        import_data(export_file, silent=True, comment_mode='overwrite')

        # Check there are exactly 1 CalculationNode and 1 Comment
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, tag='calc', project=['uuid'])
        import_comments = import_calcs.append(orm.Comment, with_node='calc', project=['uuid', 'content'])
        self.assertEqual(import_calcs.count(), 1)
        self.assertEqual(import_comments.count(), 1)

        # Check the uuids have not changed
        self.assertEqual(import_calcs.all()[0][0], calc_uuid)
        self.assertEqual(import_comments.all()[0][1], cmt_uuid)

        # Check the content of the comment HAS been rewritten ('overwrite' mode)
        self.assertEqual(import_comments.all()[0][2], self.comments[0])

        ## Test ValueError is raised when using a wrong comment_mode:
        with self.assertRaises(ValueError):
            import_data(export_file, silent=True, comment_mode='invalid')

    @with_temp_dir
    def test_reimport_of_comments_for_single_node(self, temp_dir):
        """
        When a node with comments already exist in the DB, and more comments are
        imported for the same node (same UUID), test that only new comment-entries
        are added.

        Part I:
        Create CalculationNode and 1 Comment for it.
        Export CalculationNode with its 1 Comment to export file #1 "EXISTING database".
        Add 3 Comments to CalculationNode.
        Export CalculationNode with its 4 Comments to export file #2 "FULL database".
        Reset database.

        Part II:
        Reimport export file #1 "EXISTING database".
        Add 3 Comments to CalculationNode.
        Export CalculationNode with its 4 Comments to export file #3 "NEW database".
        Reset database.

        Part III:
        Reimport export file #1 "EXISTING database" (1 CalculationNode, 1 Comment).
        Import export file #2 "FULL database" (1 CalculationNode, 4 Comments).
        Check the database EXACTLY contains 1 CalculationNode and 4 Comments,
        with matching UUIDS all the way through all previous Parts.

        Part IV:
        Import export file #3 "NEW database" (1 CalculationNode, 4 Comments).
        Check the database EXACTLY contains 1 CalculationNode and 7 Comments,
        with matching UUIDS all the way through all previous Parts.
        NB! There should now be 7 Comments in the database. 6 of which are identical
        in pairs, except for their UUID.
        """
        export_filenames = {
            "EXISTING": "export_EXISTING_db.tar.gz",
            "FULL": "export_FULL_db.tar.gz",
            "NEW": "export_NEW_db.tar.gz"
        }

        # Get user
        # Will have to do this again after resetting the DB
        user = orm.User.objects.get_default()

        ## Part I
        # Create node and save UUID
        calc = orm.CalculationNode()
        calc.store()
        calc_uuid = calc.uuid

        # Create first comment
        orm.Comment(calc, user, self.comments[0]).store()

        # There should be exactly: 1 CalculationNode, 1 Comment
        export_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        export_comments = orm.QueryBuilder().append(orm.Comment, project=['uuid'])
        self.assertEqual(export_calcs.count(), 1)
        self.assertEqual(export_comments.count(), 1)

        # Save Comment UUID before export
        existing_comment_uuids = [str(export_comments.all()[0][0])]

        # Export "EXISTING" DB
        export_file_existing = os.path.join(temp_dir, export_filenames["EXISTING"])
        export([calc], outfile=export_file_existing, silent=True)

        # Add remaining Comments
        for comment in self.comments[1:]:
            orm.Comment(calc, user, comment).store()

        # There should be exactly: 1 CalculationNode, 3 Comments (len(self.comments))
        export_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        export_comments = orm.QueryBuilder().append(orm.Comment, project=['uuid'])
        self.assertEqual(export_calcs.count(), 1)
        self.assertEqual(export_comments.count(), len(self.comments))

        # Save Comment UUIDs before export, there should be 4 UUIDs in total (len(self.comments))
        full_comment_uuids = set(existing_comment_uuids)
        for comment_uuid in export_comments.all():
            full_comment_uuids.add(str(comment_uuid[0]))
        self.assertEqual(len(full_comment_uuids), len(self.comments))

        # Export "FULL" DB
        export_file_full = os.path.join(temp_dir, export_filenames["FULL"])
        export([calc], outfile=export_file_full, silent=True)

        # Clean database
        self.reset_database()

        ## Part II
        # Reimport "EXISTING" DB
        import_data(export_file_existing, silent=True)

        # Check the database is correctly imported.
        # There should be exactly: 1 CalculationNode, 1 Comment
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        import_comments = orm.QueryBuilder().append(orm.Comment, project=['uuid'])
        self.assertEqual(import_calcs.count(), 1)
        self.assertEqual(import_comments.count(), 1)
        # Furthermore, the UUIDs should be the same
        self.assertEqual(str(import_calcs.all()[0][0]), calc_uuid)
        self.assertIn(str(import_comments.all()[0][0]), existing_comment_uuids)

        # Add remaining Comments (again)
        calc = orm.load_node(import_calcs.all()[0][0])  # Reload CalculationNode
        user = orm.User.objects.get_default()           # Get user - again
        for comment in self.comments[1:]:
            orm.Comment(calc, user, comment).store()

        # There should be exactly: 1 CalculationNode, 4 Comments (len(self.comments))
        export_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        export_comments = orm.QueryBuilder().append(orm.Comment, project=['uuid'])
        self.assertEqual(export_calcs.count(), 1)
        self.assertEqual(export_comments.count(), len(self.comments))

        # Save Comment UUIDs before export, there should be 4 UUIDs in total (len(self.comments))
        new_comment_uuids = set(existing_comment_uuids)
        for comment_uuid in export_comments.all():
            new_comment_uuids.add(str(comment_uuid[0]))
        self.assertEqual(len(new_comment_uuids), len(self.comments))

        # Export "NEW" DB
        export_file_new = os.path.join(temp_dir, export_filenames["NEW"])
        export([calc], outfile=export_file_new, silent=True)

        # Clean database
        self.reset_database()

        ## Part III
        # Reimport "EXISTING" DB
        import_data(export_file_existing, silent=True)

        # Check the database is correctly imported.
        # There should be exactly: 1 CalculationNode, 1 Comment
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        import_comments = orm.QueryBuilder().append(orm.Comment, project=['uuid'])
        self.assertEqual(import_calcs.count(), 1)
        self.assertEqual(import_comments.count(), 1)
        # Furthermore, the UUIDs should be the same
        self.assertEqual(str(import_calcs.all()[0][0]), calc_uuid)
        self.assertIn(str(import_comments.all()[0][0]), existing_comment_uuids)

        # Import "FULL" DB
        import_data(export_file_full, silent=True)

        # Check the database is correctly imported.
        # There should be exactly: 1 CalculationNode, 4 Comments (len(self.comments))
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        import_comments = orm.QueryBuilder().append(orm.Comment, project=['uuid'])
        self.assertEqual(import_calcs.count(), 1)
        self.assertEqual(import_comments.count(), len(self.comments))
        # Furthermore, the UUIDs should be the same
        self.assertEqual(str(import_calcs.all()[0][0]), calc_uuid)
        for comment in import_comments.all():
            comment_uuid = str(comment[0])
            self.assertIn(comment_uuid, full_comment_uuids)

        ## Part IV
        # Import "NEW" DB
        import_data(export_file_new, silent=True)

        # Check the database is correctly imported.
        # There should be exactly: 1 CalculationNode, 7 Comments (org. (1) + 2 x added (3) Comments)
        # 4 of the comments are identical in pairs, except for the UUID.
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        import_comments = orm.QueryBuilder().append(orm.Comment, project=['uuid', 'content'])
        self.assertEqual(import_calcs.count(), 1)
        self.assertEqual(import_comments.count(), 7)
        # Furthermore, the UUIDs should be the same
        self.assertEqual(str(import_calcs.all()[0][0]), calc_uuid)
        total_comment_uuids = full_comment_uuids.copy()
        total_comment_uuids.update(new_comment_uuids)
        for comment in import_comments.all():
            comment_uuid = str(comment[0])
            comment_content = str(comment[1])
            self.assertIn(comment_uuid, total_comment_uuids)
            self.assertIn(comment_content, self.comments)


class TestExtras(AiidaTestCase):
    """Test ex-/import cases related to Extras"""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """Only run to prepare an export file"""
        super(TestExtras, cls).setUpClass()

        data = orm.Data()
        data.label = 'my_test_data_node'
        data.store()
        data.set_extras({'b': 2, 'c': 3})
        cls.tmp_folder = tempfile.mkdtemp()
        cls.export_file = os.path.join(cls.tmp_folder, 'export.aiida')
        export([data], outfile=cls.export_file, silent=True)

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        """Remove tmp_folder"""
        super(TestExtras, cls).tearDownClass()

        shutil.rmtree(cls.tmp_folder, ignore_errors=True)

    def setUp(self):
        """This function runs before every test execution"""
        self.clean_db()
        self.insert_data()

    def import_extras(self, mode_new='import'):
        """Import an aiida database"""
        import_data(self.export_file, silent=True, extras_mode_new=mode_new)

        builder = orm.QueryBuilder().append(orm.Data, filters={'label': 'my_test_data_node'})

        self.assertEqual(builder.count(), 1)
        self.imported_node = builder.all()[0][0]

    def modify_extras(self, mode_existing):
        """Import the same aiida database again"""
        self.imported_node.set_extra('a', 1)
        self.imported_node.set_extra('b', 1000)
        self.imported_node.delete_extra('c')

        import_data(self.export_file, silent=True, extras_mode_existing=mode_existing)

        # Query again the database
        builder = orm.QueryBuilder().append(orm.Data, filters={'label': 'my_test_data_node'})
        self.assertEqual(builder.count(), 1)
        return builder.all()[0][0]

    def tearDown(self):
        pass

    def test_import_of_extras(self):
        """Check if extras are properly imported"""
        self.import_extras()
        self.assertEqual(self.imported_node.get_extra('b'), 2)
        self.assertEqual(self.imported_node.get_extra('c'), 3)

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
        self.assertEqual(imported_node.get_extra('a'), 1)
        self.assertEqual(imported_node.get_extra('b'), 1000)
        self.assertEqual(imported_node.get_extra('c'), 3)

    def test_extras_import_mode_update_existing(self):
        """Check if old extras are modified in case of name collision"""
        self.import_extras()
        imported_node = self.modify_extras(mode_existing='kcu')

        # Check that extras are imported correctly
        self.assertEqual(imported_node.get_extra('a'), 1)
        self.assertEqual(imported_node.get_extra('b'), 2)
        self.assertEqual(imported_node.get_extra('c'), 3)

    def test_extras_import_mode_mirror(self):
        """Check if old extras are fully overwritten by the imported ones"""
        self.import_extras()
        imported_node = self.modify_extras(mode_existing='ncu')

        # Check that extras are imported correctly
        with self.assertRaises(AttributeError):  # the extra
            # 'a' should not exist, as the extras were fully mirrored with respect to
            # the imported node
            imported_node.get_extra('a')
        self.assertEqual(imported_node.get_extra('b'), 2)
        self.assertEqual(imported_node.get_extra('c'), 3)

    def test_extras_import_mode_none(self):
        """Check if old extras are fully overwritten by the imported ones"""
        self.import_extras()
        imported_node = self.modify_extras(mode_existing='knl')

        # Check if extras are imported correctly
        self.assertEqual(imported_node.get_extra('b'), 1000)
        self.assertEqual(imported_node.get_extra('a'), 1)
        with self.assertRaises(AttributeError):  # the extra
            # 'c' should not exist, as the extras were keept untached
            imported_node.get_extra('c')

    def test_extras_import_mode_strange(self):
        """Check a mode that is probably does not make much sense but is still available"""
        self.import_extras()
        imported_node = self.modify_extras(mode_existing='kcd')

        # Check if extras are imported correctly
        self.assertEqual(imported_node.get_extra('a'), 1)
        self.assertEqual(imported_node.get_extra('c'), 3)
        with self.assertRaises(AttributeError):  # the extra
            # 'b' should not exist, as the collided extras are deleted
            imported_node.get_extra('b')

    def test_extras_import_mode_correct(self):
        """Test all possible import modes except 'ask' """
        self.import_extras()
        for l1 in ['k', 'n']:  # keep or not keep old extras
            for l2 in ['n', 'c']:  # create or not create new extras
                for l3 in ['l', 'u', 'd']:  # leave old, update or delete collided extras
                    mode = l1 + l2 + l3
                    import_data(self.export_file, silent=True, extras_mode_existing=mode)

    def test_extras_import_mode_wrong(self):
        """Check a mode that is wrong"""
        self.import_extras()
        with self.assertRaises(ValueError):
            import_data(self.export_file, silent=True, extras_mode_existing='xnd')  # first letter is wrong
        with self.assertRaises(ValueError):
            import_data(self.export_file, silent=True, extras_mode_existing='nxd')  # second letter is wrong
        with self.assertRaises(ValueError):
            import_data(self.export_file, silent=True, extras_mode_existing='nnx')  # third letter is wrong
        with self.assertRaises(ValueError):
            import_data(self.export_file, silent=True, extras_mode_existing='n')  # too short
        with self.assertRaises(ValueError):
            import_data(self.export_file, silent=True, extras_mode_existing='nndnn')  # too long
        with self.assertRaises(TypeError):
            import_data(self.export_file, silent=True, extras_mode_existing=5)  # wrong type


class TestProvenanceRedesign(AiidaTestCase):
    """ Check changes in database schema after upgrading to v0.4 (Provenance Redesign)
    This includes all migrations from "base_data_plugin_type_string" (django: 0008)
    until "dbgroup_type_string_change_content" (django: 0022), both included.

    The effects of the large db migration "provenance_redesign" (django: 0020)
    is tested in `TestLinks`, since the greatest change concerns links.
    """

    def setUp(self):
        super(TestProvenanceRedesign, self).setUp()

    def tearDown(self):
        super(TestProvenanceRedesign, self).tearDown()

    @with_temp_dir
    def test_base_data_type_change(self, temp_dir):
        """ Base Data types type string changed
        Example: Bool: “data.base.Bool.” → “data.bool.Bool.”
        """
        # Test content
        test_content = ("Hello", 6, -1.2399834e12, False)
        test_types = ()
        for node_type in ["str", "int", "float", "bool"]:
            add_type = ('data.{}.{}.'.format(node_type, node_type.capitalize()),)
            test_types = test_types.__add__(add_type)

        # List of nodes to be exported
        export_nodes = []

        # Create list of base type nodes
        nodes = [cls(val).store() for val, cls in zip(test_content, (orm.Str, orm.Int, orm.Float, orm.Bool))]
        export_nodes.extend(nodes)

        # Collect uuids for created nodes
        uuids = [n.uuid for n in nodes]

        # Create List() and insert already created nodes into it
        list_node = orm.List()
        list_node.set_list(nodes)
        list_node.store()
        list_node_uuid = list_node.uuid
        export_nodes.append(list_node)

        # Export nodes
        filename = os.path.join(temp_dir, "export.tar.gz")
        export(export_nodes, outfile=filename, silent=True)

        # Clean the database
        self.reset_database()

        # Import nodes again
        import_data(filename, silent=True)

        # Check whether types are correctly imported
        nlist = orm.load_node(list_node_uuid)  # List
        for uuid, list_value, refval, reftype in zip(uuids, nlist.get_list(), test_content, test_types):
            # Str, Int, Float, Bool
            n = orm.load_node(uuid)
            # Check value/content
            self.assertEqual(n.value, refval)
            # Check type
            msg = "type of node ('{}') is not updated according to db schema v0.4".format(n.node_type)
            self.assertEqual(n.node_type, reftype, msg=msg)

            # List
            # Check value
            self.assertEqual(list_value, refval)

        # Check List type
        msg = "type of node ('{}') is not updated according to db schema v0.4".format(nlist.node_type)
        self.assertEqual(nlist.node_type, 'data.list.List.', msg=msg)

    @with_temp_dir
    def test_node_process_type(self, temp_dir):
        """ Column `process_type` added to `Node` entity DB table """
        from aiida.backends.tests.utils.processes import AddProcess
        from aiida.engine import run_get_node

        # Create temporary folder for the import/export files
        tmp_folder = tempfile.mkdtemp()

        # Node types
        node_type = "process.workflow.WorkflowNode."
        node_process_type = "aiida.backends.tests.utils.processes.AddProcess"

        # Run workflow
        inputs = {'a': orm.Int(2), 'b': orm.Int(3)}
        result, node = run_get_node(AddProcess, **inputs)

        # Save node uuid
        node_uuid = str(node.uuid)

        # Assert correct type and process_type strings
        self.assertEqual(node.node_type, node_type)
        self.assertEqual(node.process_type, node_process_type)

        # Export nodes
        filename = os.path.join(temp_dir, "export.tar.gz")
        export([node], outfile=filename, silent=True)

        # Clean the database and reimport data
        self.reset_database()
        import_data(filename, silent=True)

        # Retrieve node and check exactly one node is imported
        builder = orm.QueryBuilder()
        builder.append(orm.ProcessNode, project=['uuid'])

        self.assertEqual(builder.count(), 1)

        # Get node uuid and check it is the same as the one exported
        nodes = builder.all()
        imported_node_uuid = str(nodes[0][0])

        self.assertEqual(imported_node_uuid, node_uuid)

        # Check imported node type and process type
        node = orm.load_node(imported_node_uuid)

        self.assertEqual(node.node_type, node_type)
        self.assertEqual(node.process_type, node_process_type)

    @with_temp_dir
    def test_code_type_change(self, temp_dir):
        """ Code type string changed
        Change: “code.Bool.” → “data.code.Code.”
        """
        # Create Code instance
        code = orm.Code()
        code.set_remote_computer_exec((self.computer, '/bin/true'))
        code.store()

        # Save uuid and type
        code_uuid = str(code.uuid)
        code_type = code.node_type

        # Assert correct type exists prior to export
        self.assertEqual(code_type, "data.code.Code.")

        # Export node
        filename = os.path.join(temp_dir, "export.tar.gz")
        export([code], outfile=filename, silent=True)

        # Clean the database and reimport
        self.reset_database()
        import_data(filename, silent=True)

        # Retrieve Code node and make sure exactly 1 is retrieved
        builder = orm.QueryBuilder()
        builder.append(orm.Code, project=['uuid'])
        imported_code = builder.all()

        self.assertEqual(builder.count(), 1)

        # Check uuid is the same after import
        imported_code_uuid = str(imported_code[0][0])

        self.assertEqual(imported_code_uuid, code_uuid)

        # Check whether types are correctly imported
        imported_code_type = orm.load_node(imported_code_uuid).node_type

        self.assertEqual(imported_code_type, code_type)

    def test_group_name_and_type_change(self):
        """ Group's name and type columns have changed
        Change for columns:
        “name”            --> “label”
        "type"            --> "type_string"
        Furthermore, type_strings have been updated to:
        ""                --> "user"
        "data.upf.family" --> "data.upf"
        "aiida.import"    --> "auto.import"
        "autogroup.run"   --> "auto.run"

        The new columns are called on group instances, and will fail if not present.
        A user created Group is validated to have the "user" value as a type_string.
        A UPF file is created and imported/uploaded as a UPF family,
        in order to create a Group with type_string="data.upf".
        Any import will create a Group with type_string "auto.import", which is checked.
        The type_string="auto.run" is not directly checked, but if the three checks
        above succeed, it is understood that "auto.run" is also correctly ex-/imported
        as the type_string content for the relevant Groups.
        """
        from aiida.orm.nodes.data.upf import upload_upf_family

        # Create temporary folders for the import/export files
        export_tmp_folder = tempfile.mkdtemp()
        upf_tmp_folder = tempfile.mkdtemp()

        # To be saved
        groups_label = ["Users", "UpfData"]
        upf_filename = "Al.test_file.UPF"
        # regular upf file version 2 header
        upf_contents = u"\n".join([
            "<UPF version=\"2.0.1\">",
            "Human readable section is completely irrelevant for parsing!",
            "<PP_HEADER",
            "contents before element tag",
            "element=\"Al\"",
            "contents following element tag",
            ">",
        ])
        path_to_upf = os.path.join(upf_tmp_folder, upf_filename)
        with open(path_to_upf, 'w') as upf_file:
            upf_file.write(upf_contents)

        try:
            # Create Groups
            node1 = orm.CalculationNode().store()
            node2 = orm.CalculationNode().store()
            group_user = orm.Group(label=groups_label[0]).store()
            group_user.add_nodes([node1, node2])

            nfiles, nuploads = upload_upf_family(upf_tmp_folder, groups_label[1], "")
            group_upf = orm.load_group(groups_label[1])

            # Save uuids and type
            users_uuid         = [str(u.uuid)   for u in group_user.nodes]
            upfs_uuid          = [str(u.uuid)   for u in group_upf.nodes]
            groups_uuid        = [str(g.uuid)   for g in [group_user, group_upf]]
            groups_type_string = [g.type_string for g in [group_user, group_upf]]

            # Assert correct type strings exists prior to export
            self.assertListEqual(groups_type_string, ["user", "data.upf"])

            # Export node
            filename = os.path.join(export_tmp_folder, "export.tar.gz")
            export([group_user, group_upf], outfile=filename, silent=True)

            # Clean the database and reimport
            self.reset_database()
            import_data(filename, silent=True)

            # Retrieve Groups and make sure exactly 3 are retrieved (including the "import group")
            builder = orm.QueryBuilder()
            builder.append(orm.Group, project=['uuid'])
            imported_groups = builder.all()

            self.assertEqual(builder.count(), 3)

            # Check uuids are the same after import
            imported_groups_uuid = [str(g[0]) for g in imported_groups]

            # We do not know the "import group"'s uuid, so go through known uuids
            for group_uuid in groups_uuid:
                self.assertIn(group_uuid, imported_groups_uuid)

                # Pop known uuid from imported_groups_uuid, eventually leaving
                # only the "import group"
                imported_groups_uuid.remove(group_uuid)

                # Load group
                imported_group = orm.load_group(group_uuid)

                # Check whether types are correctly imported
                self.assertIn(imported_group.type_string, groups_type_string)

                # Assert labels are imported correctly
                self.assertIn(imported_group.label, groups_label)

            # Check type_string content of "import group"
            import_group = orm.load_group(imported_groups_uuid[0])
            self.assertEqual(import_group.type_string, "auto.import")

        finally:
            # Deleting the created temporary folders
            shutil.rmtree(export_tmp_folder, ignore_errors=True)
            shutil.rmtree(upf_tmp_folder, ignore_errors=True)
