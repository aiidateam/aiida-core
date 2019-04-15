# -*- coding: utf-8 -*-
"""
Tests for the export and import routines.
"""
import aiida
import os

from aiida.backends.djsite.db.testbase import AiidaTestCase
from aiida.common.folders import SandboxFolder
from aiida.orm import DataFactory
from aiida.orm.calculation.job import JobCalculation
from aiida.orm.importexport import export, import_data
from aiida.orm import load_node

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0.1"
__authors__ = "The AiiDA team."


class TestPort(AiidaTestCase):
    def test_1(self):
        from aiida.orm import delete_computer, Node

        StructureData = DataFactory('structure')
        sd = StructureData()
        sd.store()

        calc = JobCalculation()
        calc.set_computer(self.computer)
        calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})
        calc.store()

        calc._add_link_from(sd)

        pks = [sd.pk, calc.pk]

        attrs = {}
        for pk in pks:
            node = load_node(pk)
            attrs[node.uuid] = dict()
            for k in node.attrs():
                attrs[node.uuid][k] = node.get_attr(k)

        s = SandboxFolder()
        filename = os.path.join(s.abspath, "export.tar.gz")
        export([calc.dbnode], outfile=filename, silent=True)

        self.tearDownClass()
        self.setUpClass()
        delete_computer(self.computer)

        # NOTE: it is better to load new nodes by uuid, rather than assuming
        # that they will have the first 3 pks. In fact, a recommended policy in
        # databases is that pk always increment, even if you've deleted elements
        import_data(filename, silent=True)
        for uuid in attrs.keys():
            node = load_node(uuid)
            for k in node.attrs():
                self.assertEquals(attrs[uuid][k], node.get_attr(k))

    def test_2(self):
        """
        Test the check for the export format version.
        """
        import json
        import tarfile

        StructureData = DataFactory('structure')
        sd = StructureData()
        sd.store()

        s = SandboxFolder()
        filename = os.path.join(s.abspath, "export.tar.gz")
        export([sd.dbnode], outfile=filename, silent=True)

        unpack = SandboxFolder()
        with tarfile.open(filename, "r:gz", format=tarfile.PAX_FORMAT) as tar:
            tar.extractall(unpack.abspath)

        with open(unpack.get_abs_path('metadata.json'), 'r') as f:
            metadata = json.load(f)
        metadata['export_version'] = 0.0
        with open(unpack.get_abs_path('metadata.json'), 'w') as f:
            json.dump(metadata, f)

        with tarfile.open(filename, "w:gz", format=tarfile.PAX_FORMAT) as tar:
            tar.add(unpack.abspath, arcname="")

        self.tearDownClass()
        self.setUpClass()

        with self.assertRaises(ValueError):
            import_data(filename, silent=True)

    def test_3(self):
        """
        Test importing of nodes, that have links to unknown nodes.
        """
        import json
        import tarfile

        StructureData = DataFactory('structure')
        sd = StructureData()
        sd.store()

        s = SandboxFolder()
        filename = os.path.join(s.abspath, "export.tar.gz")
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

        self.tearDownClass()
        self.setUpClass()

        with self.assertRaises(ValueError):
            import_data(filename, silent=True)

        import_data(filename, ignore_unknown_nodes=True, silent=True)

    def test_4(self):
        """
        Test control of licenses.
        """
        from aiida.common.exceptions import LicensingException
        from aiida.common.folders import SandboxFolder
        from aiida.orm.importexport import export_tree

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
