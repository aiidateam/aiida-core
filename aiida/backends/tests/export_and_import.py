# -*- coding: utf-8 -*-
"""
Tests for the export and import routines.
"""

from aiida.orm.importexport import import_data
from aiida.backends.testbase import AiidaTestCase

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1"
__authors__ = "The AiiDA team."


class TestSpecificImport(AiidaTestCase):
    def test_import(self):
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.node import Node
        from aiida.orm.calculation import Calculation
        from aiida.orm.data.structure import StructureData
        import inspect
        import os

        curr_path = inspect.getfile(inspect.currentframe())
        folder_path = os.path.dirname(curr_path)
        relative_folder_path = ("export_import_test_files/"
                                "parents_of_6537645.aiida")
        test_file_path = os.path.join(folder_path, relative_folder_path)

        # Clean the database
        self.clean_db()

        # Import the needed data
        import_data(test_file_path, silent=True)

        # Check that the number of nodes if correct
        qb = QueryBuilder()
        qb.append(Node, project=["id"])
        self.assertEquals(qb.count(), 83, "The number of Nodes is not the "
                                          "expected one.")

        # Check the number of calculations and that the attributes were
        # imported correctly
        qb = QueryBuilder()
        qb.append(Calculation, project=["*"])
        self.assertEquals(qb.count(), 19, "The number of Calculations is not "
                                          "the expected one.")
        for [calc] in qb.all():
            attr = calc.get_attrs()
            self.assertIsInstance(attr, dict, "A dictionary should be "
                                              "returned")
            self.assertNotEquals(len(attr), 0, "The attributes should not be "
                                               "empty.")

        # Check the number of the structure data and that the label is the
        # expected one
        qb = QueryBuilder()
        qb.append(StructureData, project=["*"])
        self.assertEquals(qb.count(), 7, "The number of StructureData is not "
                                          "the expected one.")
        for [struct] in qb.all():
            self.assertEquals(struct.label, "3D_with_2D_substructure",
                              "A label is not correct")


        # TO BE SEEN WITH MOUNET
        # print "<================= ParameterData attributes.energy ====================>"
        #
        # from aiida.orm.data.parameter import ParameterData
        # qb = QueryBuilder()
        # # qb.append(Calculation, filters={
        # #     'id': {"==": 6525492}}, project=["id"], tag="res")
        # qb.append(ParameterData, project=["attributes"], tag="res")
        # print qb.all()
        # for [struct] in qb.all():
        #     print struct
        #     # print struct.get_attrs()
        #     # print struct.uuid
        #     # print struct.label
        #     print "=============="
        # TO BE SEEN WITH MOUNET

        # Check that the cell attributes of the structure data is not empty.
        qb = QueryBuilder()
        qb.append(StructureData, project=["attributes.cell"])
        for [cell] in qb.all():
            self.assertNotEquals(len(cell), 0, "There should be cells.")

        # Check that the cell of specific structure data is the expected one
        qb = QueryBuilder()
        qb.append(StructureData, project=["attributes.cell"], filters={
            'uuid': {"==": "45670237-dc1e-4300-8e0b-4d3639dc77cf"}})
        for [cell] in qb.all():
            #print cell
            self.assertEquals(cell,
                              [[8.34, 0.0, 0.0], [0.298041701839357,
                                                  8.53479766274308, 0.0],
                               [0.842650688117053, 0.47118495164127,
                                10.6965192730702]],
                              "The cell is not the expected one.")

        # Check that the kind attributes are the correct ones.
        qb = QueryBuilder()
        qb.append(StructureData, project=["attributes.kinds"], tag="res")
        for [kinds] in qb.all():
            self.assertEqual(len(kinds), 2, "Attributes kinds should be of "
                                            "length 2")
            self.assertIn(
                {u'symbols': [u'Fe'], u'weights': [1.0], u'mass': 55.847,
                 u'name': u'Fe'}, kinds)
            self.assertIn(
                {u'symbols': [u'S'], u'weights': [1.0], u'mass': 32.066,
                 u'name': u'S'}, kinds)

        # Check that there are StructureData that are outputs of Calculations
        qb = QueryBuilder()
        qb.append(Calculation, project=["uuid"], tag="res")
        qb.append(StructureData, output_of="res")
        self.assertGreater(len(qb.all()), 0, "There should be results for the"
                                             "query.")

        # Check that there are RemoteData that are children and
        # parents of Calculations
        from aiida.orm.data.remote import RemoteData
        qb = QueryBuilder()
        qb.append(Calculation, tag="c1")
        qb.append(RemoteData, project=["uuid"], output_of="c1", tag='r1')
        qb.append(Calculation, output_of="r1", tag="c2")

        self.assertGreater(len(qb.all()), 0, "There should be results for the"
                                             "query.")

        # TO BE SEEN WITH MOUNET
        # from aiida.orm.data.array.trajectory import TrajectoryData
        # qb = QueryBuilder()
        # qb.append(TrajectoryData, project=["*"], tag="res")
        # print qb.all()
        # for [struct] in qb.all():
        #     print struct
        #     print struct.get_attrs()
        #     # print struct.uuid
        #     # print struct.label
        #     print "=============="
        # TO BE SEEN WITH MOUNET

        # Check that a specific UUID exists
        qb = QueryBuilder()
        qb.append(Node, filters={
            'uuid': {"==": "45670237-dc1e-4300-8e0b-4d3639dc77cf"}},
                  project=["*"], tag="res")
        self.assertGreater(len(qb.all()), 0, "There should be results for the"
                                             "query.")


class TestSimple(AiidaTestCase):

    def test_1(self):
        import os
        import shutil
        import tempfile

        from aiida.orm import DataFactory
        from aiida.orm import load_node
        from aiida.orm.calculation.job import JobCalculation
        from aiida.orm.importexport import export

        # Creating a folder for the import/export files
        temp_folder = tempfile.mkdtemp()
        try:
            StructureData = DataFactory('structure')
            sd = StructureData()
            sd.store()

            calc = JobCalculation()
            calc.set_computer(self.computer)
            calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})
            calc.store()

            calc.add_link_from(sd)

            pks = [sd.pk, calc.pk]

            attrs = {}
            for pk in pks:
                node = load_node(pk)
                attrs[node.uuid] = dict()
                for k in node.attrs():
                    attrs[node.uuid][k] = node.get_attr(k)

            filename = os.path.join(temp_folder, "export.tar.gz")

            export([calc.dbnode], outfile=filename, silent=True)

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
        import json
        import tarfile
        import os
        import shutil
        import tempfile

        from aiida.orm import DataFactory
        from aiida.orm.importexport import export

        # Creating a folder for the import/export files
        export_file_tmp_folder = tempfile.mkdtemp()
        unpack_tmp_folder = tempfile.mkdtemp()
        try:
            StructureData = DataFactory('structure')
            sd = StructureData()
            sd.store()

            filename = os.path.join(export_file_tmp_folder, "export.tar.gz")
            export([sd.dbnode], outfile=filename, silent=True)

            with tarfile.open(filename, "r:gz", format=tarfile.PAX_FORMAT) as tar:
                tar.extractall(unpack_tmp_folder)

            with open(os.path.join(unpack_tmp_folder,
                                   'metadata.json'), 'r') as f:
                metadata = json.load(f)
            metadata['export_version'] = 0.0
            with open(os.path.join(unpack_tmp_folder,
                                   'metadata.json'), 'w') as f:
                json.dump(metadata, f)

            with tarfile.open(filename, "w:gz", format=tarfile.PAX_FORMAT) as tar:
                tar.add(unpack_tmp_folder, arcname="")

            self.tearDownClass()
            self.setUpClass()

            with self.assertRaises(ValueError):
                import_data(filename, silent=True)
        finally:
            # Deleting the created temporary folders
            shutil.rmtree(export_file_tmp_folder, ignore_errors=True)
            shutil.rmtree(unpack_tmp_folder, ignore_errors=True)

    def test_3(self):
        """
        Test importing of nodes, that have links to unknown nodes.
        """
        import json
        import tarfile
        import os
        import shutil
        import tempfile

        from aiida.orm import DataFactory
        from aiida.orm.importexport import export
        from aiida.common.folders import SandboxFolder

        # Creating a folder for the import/export files
        temp_folder = tempfile.mkdtemp()
        try:
            StructureData = DataFactory('structure')
            sd = StructureData()
            sd.store()

            filename = os.path.join(temp_folder, "export.tar.gz")
            export([sd.dbnode], outfile=filename, silent=True)

            unpack = SandboxFolder()
            with tarfile.open(filename, "r:gz", format=tarfile.PAX_FORMAT) as tar:
                tar.extractall(unpack.abspath)

            with open(unpack.get_abs_path('data.json'), 'r') as f:
                metadata = json.load(f)
            metadata['links_uuid'].append({
                'output': sd.uuid,
                'input': 'non-existing-uuid',
                'label': 'parent'
            })
            with open(unpack.get_abs_path('data.json'), 'w') as f:
                json.dump(metadata, f)

            with tarfile.open(filename, "w:gz", format=tarfile.PAX_FORMAT) as tar:
                tar.add(unpack.abspath, arcname="")

            self.clean_db()

            with self.assertRaises(ValueError):
                import_data(filename, silent=True)

            import_data(filename, ignore_unknown_nodes=True, silent=True)
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
        export_tree([sd.dbnode], folder=folder, silent=True,
                    allowed_licenses=['GPL'])
        # Folder should contain two files of metadata + nodes/
        self.assertEquals(len(folder.get_content_list()), 3)

        folder = SandboxFolder()
        export_tree([sd.dbnode], folder=folder, silent=True,
                    forbidden_licenses=['Academic'])
        # Folder should contain two files of metadata + nodes/
        self.assertEquals(len(folder.get_content_list()), 3)

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([sd.dbnode], folder=folder, silent=True,
                        allowed_licenses=['CC0'])

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([sd.dbnode], folder=folder, silent=True,
                        forbidden_licenses=['GPL'])

        def cc_filter(license):
            return license.startswith('CC')

        def gpl_filter(license):
            return license == 'GPL'

        def crashing_filter(license):
            raise NotImplementedError("not implemented yet")

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([sd.dbnode], folder=folder, silent=True,
                        allowed_licenses=cc_filter)

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([sd.dbnode], folder=folder, silent=True,
                        forbidden_licenses=gpl_filter)

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([sd.dbnode], folder=folder, silent=True,
                        allowed_licenses=crashing_filter)

        folder = SandboxFolder()
        with self.assertRaises(LicensingException):
            export_tree([sd.dbnode], folder=folder, silent=True,
                        forbidden_licenses=crashing_filter)


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

        from aiida.orm.calculation.job import JobCalculation
        from aiida.orm.data.folder import FolderData
        from aiida.orm.data.parameter import ParameterData
        from aiida.orm.data.remote import RemoteData
        from aiida.common.links import LinkType
        from aiida.orm.importexport import export, import_data
        from aiida.orm.utils import load_node
        from aiida.common.exceptions import NotExistent

        temp_folder = tempfile.mkdtemp()
        try:
            calc1 = JobCalculation()
            calc1.set_computer(self.computer)
            calc1.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})
            calc1.label = "calc1"
            calc1.store()
            calc1._set_state('RETRIEVING')

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
            rd1.add_link_from(calc1, link_type=LinkType.CREATE)

            calc2 = JobCalculation()
            calc2.set_computer(self.computer)
            calc2.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})
            calc2.label = "calc2"
            calc2.store()
            calc2.add_link_from(pd1, link_type=LinkType.INPUT)
            calc2.add_link_from(pd2, link_type=LinkType.INPUT)
            calc2.add_link_from(rd1, link_type=LinkType.INPUT)
            calc2._set_state('SUBMITTING')

            fd1 = FolderData()
            fd1.label = "fd1"
            fd1.store()
            fd1.add_link_from(calc2, link_type=LinkType.CREATE)

            node_uuids_labels = {calc1.uuid: calc1.label, pd1.uuid: pd1.label,
                                 pd2.uuid: pd2.label, rd1.uuid: rd1.label,
                                 calc2.uuid: calc2.label, fd1.uuid: fd1.label}

            filename = os.path.join(temp_folder, "export.tar.gz")
            export([fd1.dbnode], outfile=filename, silent=True)

            self.clean_db()

            import_data(filename, silent=True, ignore_unknown_nodes=True)

            for uuid, label in node_uuids_labels.iteritems():
                try:
                    load_node(uuid)
                except NotExistent:
                    self.fail("Node with UUID {} and label {} was not "
                              "found.".format(uuid, label))

        finally:
            # Deleting the created temporary folder
            shutil.rmtree(temp_folder, ignore_errors=True)

    def dis_test_graph_generation(self):
        # Get the graph of the following - Its the blue node
        from aiida.cmdline.commands.graph import Graph
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.node import Node

        qb = QueryBuilder()
        qb.append(Node, filters={
            'uuid': {"==": "99d516d5-fafe-40d3-979f-12726e626648"}},
                  project=["*"], tag="res")
        #for [node] in qb.all():
        #    print node.get_attrs()
        #    print node.uuid
        #    print node.id
        #    print "=============="

        g = Graph()
        g.graph_generate((str(node.id)))

