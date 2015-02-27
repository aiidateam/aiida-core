# -*- coding: utf-8 -*-
"""
Tests for the export and import routines.
"""
import os
import tempfile

from aiida.djsite.db.testbase import AiidaTestCase
from aiida.common.folders import SandboxFolder
from aiida.orm import DataFactory
from aiida.orm.calculation.job import JobCalculation
import aiida

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.0"

class TestPort(AiidaTestCase):

    def test_1(self):
        from aiida.cmdline.commands.exportfile import export
        from aiida.cmdline.commands.importfile import import_file
        from aiida.orm.computer import delete_computer
        from aiida.orm.node import Node

        StructureData = DataFactory('structure')
        sd = StructureData()
        sd.store()

        calc = JobCalculation()
        calc.set_computer(self.computer)
        calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})
        calc.store()

        calc._add_link_from(sd)

        attrs = dict()
        for i in range(1,3):
            node = Node.get_subclass_from_pk(i)
            attrs[i] = dict()
            for k in node.attrs():
                attrs[i][k] = node.get_attr(k)

        s = SandboxFolder()
        filename = os.path.join(s.abspath,"export.tar.gz")
        export([calc.dbnode],outfile=filename,silent=True)

        self.tearDownClass()
        self.setUpClass()
        delete_computer(self.computer)

        import_file(filename,silent=True)
        for i in range(1,3):
            node = Node.get_subclass_from_pk(i)
            for k in node.attrs():
                self.assertEquals(attrs[i][k],node.get_attr(k))

    def test_2(self):
        from aiida.cmdline.commands.exportfile import export
        from aiida.cmdline.commands.importfile import import_file
        import json
        import tarfile
        from tarfile import TarInfo

        StructureData = DataFactory('structure')
        sd = StructureData()
        sd.store()

        s = SandboxFolder()
        filename = os.path.join(s.abspath,"export.tar.gz")
        export([sd.dbnode],outfile=filename,silent=True)

        unpack = SandboxFolder()
        with tarfile.open(filename, "r:gz", format=tarfile.PAX_FORMAT) as tar:
            tar.extractall(unpack.abspath)

        with open(unpack.get_abs_path('metadata.json'),'r') as f:
            metadata = json.load(f)
        metadata['export_version'] = 0.0
        with open(unpack.get_abs_path('metadata.json'),'w') as f:
            json.dump(metadata,f)

        with tarfile.open(filename, "w:gz", format=tarfile.PAX_FORMAT) as tar:
            tar.add(unpack.abspath,arcname="")

        self.tearDownClass()
        self.setUpClass()

        with self.assertRaises(ValueError):
            import_file(filename,silent=True)
