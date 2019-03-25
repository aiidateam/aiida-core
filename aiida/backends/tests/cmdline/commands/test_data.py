# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
import sys
import io
import os
import shutil
import unittest
import tempfile
import numpy as np
import subprocess as sp

from six.moves import cStringIO as StringIO

from contextlib import contextmanager
from click.testing import CliRunner

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.cmd_data import cmd_array
from aiida.cmdline.commands.cmd_data import cmd_bands
from aiida.cmdline.commands.cmd_data import cmd_cif
from aiida.cmdline.commands.cmd_data import cmd_parameter
from aiida.cmdline.commands.cmd_data import cmd_remote
from aiida.cmdline.commands.cmd_data import cmd_structure
from aiida.cmdline.commands.cmd_data import cmd_trajectory
from aiida.cmdline.commands.cmd_data import cmd_upf
from aiida.engine import calcfunction
from aiida.orm.nodes.data.cif import has_pycifrw
from aiida.orm import Group, ArrayData, BandsData, KpointsData, CifData, Dict, RemoteData, StructureData, TrajectoryData


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class TestVerdiDataExportable:

    def __init__(self):
        pass

    NODE_ID_STR = "node_id"
    EMPTY_GROUP_ID_STR = 'empty_group_id'
    EMPTY_GROUP_NAME_STR = 'empty_group'
    NON_EMPTY_GROUP_ID_STR = 'non_empty_group_id'
    NON_EMPTY_GROUP_NAME_STR = 'non_empty_group'

    @unittest.skipUnless(has_pycifrw(), "Unable to import PyCifRW")
    def data_export_test(self, datatype, ids, supported_formats):
        """
        This method tests that the data listing works as expected with all
        possible flags and arguments for different datatypes.
        """

        from aiida.cmdline.commands.cmd_data.cmd_cif import cif_export
        from aiida.cmdline.commands.cmd_data.cmd_structure import structure_export
        from aiida.cmdline.commands.cmd_data.cmd_trajectory import trajectory_export

        datatype_mapping = {
            CifData: cif_export,
            StructureData: structure_export,
            TrajectoryData: trajectory_export,
        }

        if datatype is None or datatype not in datatype_mapping.keys():
            raise Exception("The listing of the objects {} is not supported".format(datatype))

        export_cmd = datatype_mapping[datatype]

        # Check that the simple command works as expected
        options = [str(ids[self.NODE_ID_STR])]
        res = self.cli_runner.invoke(export_cmd, options, catch_exceptions=False)
        self.assertEqual(res.exit_code, 0, "The command did not finish correctly")

        dump_flags = ['-F', '--format']
        for flag in dump_flags:
            for format in supported_formats:
                # with captured_output() as (out, err):
                options = [flag, format, str(ids[self.NODE_ID_STR])]
                res = self.cli_runner.invoke(export_cmd, options,
                                             catch_exceptions=False)
                self.assertEqual(res.exit_code, 0,
                                  "The command did not finish "
                                  "correctly. Output:\n{}".format(res.output))

        # Check that the output to file flags work correctly:
        # -o, --output
        output_flags = ['-o', '--output']
        for flag in output_flags:
            try:
                tmpd = tempfile.mkdtemp()
                filepath = os.path.join(tmpd, 'output_file.txt')
                options = [flag, filepath, str(ids[self.NODE_ID_STR])]
                res = self.cli_runner.invoke(export_cmd, options,
                                             catch_exceptions=False)
                self.assertEqual(res.exit_code, 0,
                                  "The command should finish correctly."
                                  "Output:\n{}".format(res.output))

                # Try to export it again. It should fail because the
                # file exists
                res = self.cli_runner.invoke(export_cmd, options, catch_exceptions=False)
                self.assertNotEquals(res.exit_code, 0, "The command should fail because the file already exists")

                # Now we force the export of the file and it should overwrite
                # existing files
                options = [flag, filepath, '-f', str(ids[self.NODE_ID_STR])]
                res = self.cli_runner.invoke(export_cmd, options,
                                             catch_exceptions=False)
                self.assertEqual(res.exit_code, 0,
                                  "The command should finish correctly."
                                  "Output: {}".format(res.output))
            finally:
                shutil.rmtree(tmpd)


class TestVerdiDataListable:

    def __init__(self):
        pass

    NODE_ID_STR = "node_id"
    EMPTY_GROUP_ID_STR = 'empty_group_id'
    EMPTY_GROUP_NAME_STR = 'empty_group'
    NON_EMPTY_GROUP_ID_STR = 'non_empty_group_id'
    NON_EMPTY_GROUP_NAME_STR = 'non_empty_group'

    def data_listing_test(self, datatype, search_string, ids):
        """
        This method tests that the data listing works as expected with all
        possible flags and arguments for different datatypes.
        """

        from aiida.cmdline.commands.cmd_data.cmd_cif import cif_list
        from aiida.cmdline.commands.cmd_data.cmd_structure import structure_list
        from aiida.cmdline.commands.cmd_data.cmd_trajectory import trajectory_list
        from aiida.cmdline.commands.cmd_data.cmd_bands import bands_list

        from aiida.cmdline.commands.cmd_data.cmd_structure import LIST_PROJECT_HEADERS as p_str
        from aiida.cmdline.commands.cmd_data.cmd_cif import LIST_PROJECT_HEADERS as p_cif
        from aiida.cmdline.commands.cmd_data.cmd_trajectory import LIST_PROJECT_HEADERS as p_tr
        from aiida.cmdline.commands.cmd_data.cmd_bands import LIST_PROJECT_HEADERS as p_bands

        headers_mapping = {CifData: p_cif, StructureData: p_str, TrajectoryData: p_tr, BandsData: p_bands}

        datatype_mapping = {
            CifData: cif_list,
            StructureData: structure_list,
            TrajectoryData: trajectory_list,
            BandsData: bands_list
        }

        if datatype is None or datatype not in datatype_mapping.keys():
            raise Exception("The listing of the objects {} is not supported".format(datatype))

        listing_cmd = datatype_mapping[datatype]
        project_headers = headers_mapping[datatype]

        # the output we are comparing to is un-decoded bytes, convert search strings:
        search_string_bytes = search_string.encode('utf-8')

        # Check that the normal listing works as expected
        res = self.cli_runner.invoke(listing_cmd, [], catch_exceptions=False)
        self.assertIn(search_string_bytes, res.stdout_bytes, 'The string {} was not found in the listing'
                      .format(search_string))

        # Check that the past days filter works as expected
        past_days_flags = ['-p', '--past-days']
        # past_days_flags = ['-p']
        for flag in past_days_flags:
            options = [flag, '1']
            res = self.cli_runner.invoke(listing_cmd, options, catch_exceptions=False)
            self.assertIn(search_string_bytes, res.stdout_bytes, 'The string {} was not found in the listing'
                          .format(search_string))

            options = [flag, '0']
            res = self.cli_runner.invoke(listing_cmd, options, catch_exceptions=False)
            self.assertNotIn(search_string_bytes, res.stdout_bytes, 'A not expected string {} was found in the listing'
                             .format(search_string))

        # Check that the group filter works as expected
        group_flags = ['-G', '--groups']
        for flag in group_flags:
            # Non empty group
            for non_empty in [self.NON_EMPTY_GROUP_NAME_STR, str(ids[self.NON_EMPTY_GROUP_ID_STR])]:
                options = [flag, non_empty]
                res = self.cli_runner.invoke(listing_cmd, options, catch_exceptions=False)
                self.assertIn(search_string_bytes, res.stdout_bytes, 'The string {} was not found in the listing')

            # Empty group
            for empty in [self.EMPTY_GROUP_NAME_STR, str(ids[self.EMPTY_GROUP_ID_STR])]:
                options = [flag, empty]
                res = self.cli_runner.invoke(listing_cmd, options, catch_exceptions=False)
                self.assertNotIn(search_string_bytes, res.stdout_bytes,
                                 'A not expected string {} was found in the listing')

            # Group combination
            for non_empty in [self.NON_EMPTY_GROUP_NAME_STR, str(ids[self.NON_EMPTY_GROUP_ID_STR])]:
                for empty in [self.EMPTY_GROUP_NAME_STR, str(ids[self.EMPTY_GROUP_ID_STR])]:
                    options = [flag, non_empty, empty]
                    res = self.cli_runner.invoke(listing_cmd, options, catch_exceptions=False)
                    self.assertIn(search_string_bytes, res.stdout_bytes, 'The string {} was not found in the listing')

        # Check raw flag
        raw_flags = ['-r', '--raw']
        for flag in raw_flags:
            options = [flag]
            res = self.cli_runner.invoke(listing_cmd, options, catch_exceptions=False)
            for header in project_headers:
                self.assertNotIn(header.encode('utf-8'), res.stdout_bytes)


class TestVerdiData(AiidaTestCase):
    """
    Testing reachability of the verdi data subcommands
    """

    @classmethod
    def setUpClass(cls):
        super(TestVerdiData, cls).setUpClass()

    def setUp(self):
        pass

    def test_reachable(self):
        """
        Testing reachability of the following commands:
        verdi data array
        verdi data bands
        verdi data cif
        verdi data parameter
        verdi data remote
        verdi data structure
        verdi data trajectory
        verdi data upf
        """
        subcommands = ['array', 'bands', 'cif', 'parameter', 'remote', 'structure', 'trajectory', 'upf']
        for sub_cmd in subcommands:
            output = sp.check_output(['verdi', 'data', sub_cmd, '--help'])
            self.assertIn(b'Usage:', output, "Sub-command verdi data {} --help failed.".format(sub_cmd))


class TestVerdiDataArray(AiidaTestCase):
    """
    Testing verdi data array
    """

    @classmethod
    def setUpClass(cls):
        super(TestVerdiDataArray, cls).setUpClass()

    def setUp(self):
        self.a = ArrayData()
        self.a.set_array('test_array', np.array([0, 1, 3]))
        self.a.store()

        self.cli_runner = CliRunner()

    def test_arrayshowhelp(self):
        output = sp.check_output(['verdi', 'data', 'array', 'show', '--help'])
        self.assertIn(b'Usage:', output, "Sub-command verdi data array show --help failed.")

    def test_arrayshow(self):
        # with captured_output() as (out, err):
        options = [str(self.a.id)]
        res = self.cli_runner.invoke(cmd_array.array_show, options, catch_exceptions=False)
        self.assertEqual(res.exit_code, 0, "The command did not finish correctly")


class TestVerdiDataBands(AiidaTestCase, TestVerdiDataListable):
    """
    Testing verdi data bands 
    """

    @staticmethod
    def create_structure_bands():
        alat = 4.  # angstrom
        cell = [
            [
                alat,
                0.,
                0.,
            ],
            [
                0.,
                alat,
                0.,
            ],
            [
                0.,
                0.,
                alat,
            ],
        ]
        s = StructureData(cell=cell)
        s.append_atom(position=(0., 0., 0.), symbols='Fe')
        s.append_atom(position=(alat / 2., alat / 2., alat / 2.), symbols='O')
        s.store()

        @calcfunction
        def connect_structure_bands(structure):
            alat = 4.
            cell = np.array([
                [alat, 0., 0.],
                [0., alat, 0.],
                [0., 0., alat],
            ])

            k = KpointsData()
            k.set_cell(cell)
            k.set_kpoints_path([('G', 'M', 2)])

            b = BandsData()
            b.set_kpointsdata(k)
            b.set_bands([[1.0, 2.0], [3.0, 4.0]])

            return b

        b = connect_structure_bands(s)

        # Create 2 groups and add the data to one of them
        g_ne = Group(label='non_empty_group')
        g_ne.store()
        g_ne.add_nodes(b)

        g_e = Group(label='empty_group')
        g_e.store()

        return {
            TestVerdiDataListable.NODE_ID_STR: b.id,
            TestVerdiDataListable.NON_EMPTY_GROUP_ID_STR: g_ne.id,
            TestVerdiDataListable.EMPTY_GROUP_ID_STR: g_e.id
        }

    @classmethod
    def setUpClass(cls):
        super(TestVerdiDataBands, cls).setUpClass()
        cls.ids = cls.create_structure_bands()

    def setUp(self):
        self.cli_runner = CliRunner()

    def test_bandsshowhelp(self):
        output = sp.check_output(['verdi', 'data', 'bands', 'show', '--help'])
        self.assertIn(b'Usage:', output, "Sub-command verdi data bands show --help failed.")

    def test_bandlistshelp(self):
        output = sp.check_output(['verdi', 'data', 'bands', 'list', '--help'])
        self.assertIn(b'Usage:', output, "Sub-command verdi data bands show --help failed.")

    def test_bandslist(self):
        from aiida.orm import BandsData

        self.data_listing_test(BandsData, 'FeO', self.ids)

    def test_bandexporthelp(self):
        output = sp.check_output(['verdi', 'data', 'bands', 'export', '--help'])
        self.assertIn(b'Usage:', output, "Sub-command verdi data bands export --help failed.")

    def test_bandsexport(self):
        options = [str(self.ids[TestVerdiDataListable.NODE_ID_STR])]
        res = self.cli_runner.invoke(cmd_bands.bands_export, options, catch_exceptions=False)
        self.assertEqual(res.exit_code, 0, 'The command did not finish correctly')
        self.assertIn(b"[1.0, 3.0]", res.stdout_bytes, 'The string [1.0, 3.0] was not found in the bands' 'export')


class TestVerdiDataParameter(AiidaTestCase):
    """
    Testing verdi data parameter 
    """

    @classmethod
    def setUpClass(cls):
        super(TestVerdiDataParameter, cls).setUpClass()

    def setUp(self):
        self.p = Dict()
        self.p.set_dict({'a': 1, 'b': 2})
        self.p.store()

        self.cli_runner = CliRunner()

    def test_parametershowhelp(self):
        output = sp.check_output(['verdi', 'data', 'parameter', 'show', '--help'])
        self.assertIn(b'Usage:', output, "Sub-command verdi data parameter show --help failed.")

    def test_parametershow(self):
        supported_formats = ['json_date']
        for format in supported_formats:
            options = [str(self.p.id)]
            res = self.cli_runner.invoke(cmd_parameter.parameter_show, options, catch_exceptions=False)
            self.assertEqual(res.exit_code, 0, "The command verdi data parameter show did not" " finish correctly")
        self.assertIn(b'"a": 1', res.stdout_bytes, 'The string "a": 1 was not found in the output'
                                                   ' of verdi data parameter show')


class TestVerdiDataRemote(AiidaTestCase):
    """
    Testing verdi data remote 
    """

    @classmethod
    def setUpClass(cls):
        super(TestVerdiDataRemote, cls).setUpClass()
        user = orm.User.objects.get_default()
        orm.AuthInfo(cls.computer, user).store()

    def setUp(self):
        comp = self.computer
        self.r = RemoteData()
        p = tempfile.mkdtemp()
        self.r.set_remote_path(p)
        with io.open(p + '/file.txt', 'w', encoding='utf8') as fhandle:
            fhandle.write(u"test string")
        self.r.computer = comp
        self.r.store()

        self.cli_runner = CliRunner()

    def test_remoteshowhelp(self):
        output = sp.check_output(['verdi', 'data', 'remote', 'show', '--help'])
        self.assertIn(b'Usage:', output, "Sub-command verdi data remote show --help failed.")

    def test_remoteshow(self):
        options = [str(self.r.id)]
        res = self.cli_runner.invoke(cmd_remote.remote_show, options, catch_exceptions=False)
        self.assertEqual(res.exit_code, 0, "The command verdi data remote show did not" " finish correctly")
        self.assertIn(b'Remote computer name:', res.stdout_bytes,
                      'The string "Remote computer name:" was not found in the'
                      ' output of verdi data remote show')
        self.assertIn(b'Remote folder full path:', res.stdout_bytes,
                      'The string "Remote folder full path:" was not found in the'
                      ' output of verdi data remote show')

    def test_remotelshelp(self):
        output = sp.check_output(['verdi', 'data', 'remote', 'ls', '--help'])
        self.assertIn(b'Usage:', output, "Sub-command verdi data remote ls --help failed.")

    def test_remotels(self):
        options = ['--long', str(self.r.id)]
        res = self.cli_runner.invoke(cmd_remote.remote_ls, options, catch_exceptions=False)
        self.assertEqual(res.exit_code, 0, "The command verdi data remote ls did not" " finish correctly")
        self.assertIn(b'file.txt', res.stdout_bytes, 'The file "file.txt" was not found in the output'
                                                     ' of verdi data remote ls')

    def test_remotecathelp(self):
        output = sp.check_output(['verdi', 'data', 'remote', 'cat', '--help'])
        self.assertIn(b'Usage:', output, "Sub-command verdi data remote cat --help failed.")

    def test_remotecat(self):
        options = [str(self.r.id), 'file.txt']
        res = self.cli_runner.invoke(cmd_remote.remote_cat, options, catch_exceptions=False)
        self.assertEqual(res.exit_code, 0, "The command verdi data parameter cat did not" " finish correctly")
        self.assertIn(b'test string', res.stdout_bytes, 'The string "test string" was not found in the output'
                                                        ' of verdi data remote cat file.txt')


class TestVerdiDataTrajectory(AiidaTestCase, TestVerdiDataListable, TestVerdiDataExportable):

    @staticmethod
    def create_trajectory_data():
        import numpy

        # Create a node with two arrays
        n = TrajectoryData()

        # I create sample data
        stepids = numpy.array([60, 70])
        times = stepids * 0.01
        cells = numpy.array([[[
            2.,
            0.,
            0.,
        ], [
            0.,
            2.,
            0.,
        ], [
            0.,
            0.,
            2.,
        ]], [[
            3.,
            0.,
            0.,
        ], [
            0.,
            3.,
            0.,
        ], [
            0.,
            0.,
            3.,
        ]]])
        symbols = ['H', 'O', 'C']
        positions = numpy.array([[[0., 0., 0.], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]], [[0., 0., 0.], [0.5, 0.5, 0.5],
                                                                                    [1.5, 1.5, 1.5]]])
        velocities = numpy.array([[[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]], [[0.5, 0.5, 0.5], [0.5, 0.5, 0.5],
                                                                               [-0.5, -0.5, -0.5]]])

        # I set the node
        n.set_trajectory(
            stepids=stepids, cells=cells, symbols=symbols, positions=positions, times=times, velocities=velocities)

        n.store()

        # Create 2 groups and add the data to one of them
        g_ne = Group(label='non_empty_group')
        g_ne.store()
        g_ne.add_nodes(n)

        g_e = Group(label='empty_group')
        g_e.store()

        return {
            TestVerdiDataListable.NODE_ID_STR: n.id,
            TestVerdiDataListable.NON_EMPTY_GROUP_ID_STR: g_ne.id,
            TestVerdiDataListable.EMPTY_GROUP_ID_STR: g_e.id
        }

    @classmethod
    def setUpClass(cls):
        super(TestVerdiDataTrajectory, cls).setUpClass()
        orm.Computer(
            name='comp',
            hostname='localhost',
            transport_type='local',
            scheduler_type='direct',
            workdir='/tmp/aiida').store()
        cls.ids = cls.create_trajectory_data()

    def setUp(self):
        self.comp = self.computer
        self.runner = CliRunner()
        self.this_folder = os.path.dirname(__file__)
        self.this_file = os.path.basename(__file__)

        self.cli_runner = CliRunner()

    def test_showhelp(self):
        res = self.runner.invoke(cmd_trajectory.trajectory_show, ['--help'])
        self.assertIn(b'Usage:', res.stdout_bytes, 'The string "Usage: " was not found in the output'
                                                   ' of verdi data trajecotry show --help')

    def test_list(self):
        self.data_listing_test(TrajectoryData, str(self.ids[TestVerdiDataListable.NODE_ID_STR]), self.ids)

    @unittest.skipUnless(has_pycifrw(), "Unable to import PyCifRW")
    def test_export(self):
        from aiida.cmdline.commands.cmd_data.cmd_trajectory import EXPORT_FORMATS, trajectory_export

        new_supported_formats = list(EXPORT_FORMATS)
        self.data_export_test(TrajectoryData, self.ids, new_supported_formats)


class TestVerdiDataStructure(AiidaTestCase, TestVerdiDataListable, TestVerdiDataExportable):

    @staticmethod
    def create_structure_data():
        alat = 4.  # angstrom
        cell = [
            [
                alat,
                0.,
                0.,
            ],
            [
                0.,
                alat,
                0.,
            ],
            [
                0.,
                0.,
                alat,
            ],
        ]

        # BaTiO3 cubic structure
        struc = StructureData(cell=cell)
        struc.append_atom(position=(0., 0., 0.), symbols='Ba')
        struc.append_atom(position=(alat / 2., alat / 2., alat / 2.), symbols='Ti')
        struc.append_atom(position=(alat / 2., alat / 2., 0.), symbols='O')
        struc.append_atom(position=(alat / 2., 0., alat / 2.), symbols='O')
        struc.append_atom(position=(0., alat / 2., alat / 2.), symbols='O')
        struc.store()

        # Create 2 groups and add the data to one of them
        g_ne = Group(label='non_empty_group')
        g_ne.store()
        g_ne.add_nodes(struc)

        g_e = Group(label='empty_group')
        g_e.store()

        return {
            TestVerdiDataListable.NODE_ID_STR: struc.id,
            TestVerdiDataListable.NON_EMPTY_GROUP_ID_STR: g_ne.id,
            TestVerdiDataListable.EMPTY_GROUP_ID_STR: g_e.id
        }

    @classmethod
    def setUpClass(cls):
        super(TestVerdiDataStructure, cls).setUpClass()
        orm.Computer(name='comp',
                     hostname='localhost',
                     transport_type='local',
                     scheduler_type='direct',
                     workdir='/tmp/aiida').store()
        cls.ids = cls.create_structure_data()

    def setUp(self):
        self.comp = self.computer
        self.runner = CliRunner()
        self.this_folder = os.path.dirname(__file__)
        self.this_file = os.path.basename(__file__)

        self.cli_runner = CliRunner()

    def test_importhelp(self):
        res = self.runner.invoke(cmd_structure.structure_import, ['--help'])
        self.assertIn(b'Usage:', res.stdout_bytes, 'The string "Usage: " was not found in the output'
                                                   ' of verdi data import --help')

    def test_import(self):
        xyzcontent = '''
        2

        Fe     0.0 0.0 0.0
        O      2.0 2.0 2.0
        '''
        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            fhandle.write(xyzcontent)
            fhandle.flush()
            options = [
                fhandle.name,
                '--format',
                'xyz',
                '--vacuum-factor',
                '1.0',
                '--vacuum-addition',
                '10.0',
                '--pbc',
                '1',
                '1',
                '1',
            ]
            res = self.cli_runner.invoke(cmd_structure.structure_import, options, catch_exceptions=False)
            self.assertIn(b'PK = None', res.stdout_bytes, 'The string "PK = None" was not found in the output'
                                                          ' of verdi data structure import with --store option.')
            options.append('--store')
            res = self.cli_runner.invoke(cmd_structure.structure_import, options, catch_exceptions=False)
            self.assertIn(b'Succesfully imported', res.stdout_bytes,
                          'The string "Succesfully imported" was not found in the output'
                          ' of verdi data structure import.')

    def test_showhelp(self):
        res = self.runner.invoke(cmd_structure.structure_import, ['--help'])
        self.assertIn(b'Usage:', res.stdout_bytes, 'The string "Usage: " was not found in the output'
                                                   ' of verdi data show --help')

    def test_list(self):
        self.data_listing_test(StructureData, 'BaO3Ti', self.ids)

    def test_export(self):
        from aiida.cmdline.commands.cmd_data.cmd_structure import EXPORT_FORMATS
        self.data_export_test(StructureData, self.ids, EXPORT_FORMATS)


@unittest.skipUnless(has_pycifrw(), "Unable to import PyCifRW")
class TestVerdiDataCif(AiidaTestCase, TestVerdiDataListable, TestVerdiDataExportable):
    valid_sample_cif_str = u'''
        data_test
        _cell_length_a    10
        _cell_length_b    10
        _cell_length_c    10
        _cell_angle_alpha 90
        _cell_angle_beta  90
        _cell_angle_gamma 90
        _chemical_formula_sum 'C O2'
        loop_
        _atom_site_label
        _atom_site_fract_x
        _atom_site_fract_y
        _atom_site_fract_z
        _atom_site_attached_hydrogens
        C 0 0 0 0
        O 0.5 0.5 0.5 .
        H 0.75 0.75 0.75 0
    '''

    @classmethod
    def create_cif_data(cls):
        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            filename = fhandle.name
            fhandle.write(cls.valid_sample_cif_str)
            fhandle.flush()
            a = CifData(file=filename, source={'version': '1234', 'db_name': 'COD', 'id': '0000001'})
            a.store()

            g_ne = Group(label='non_empty_group')
            g_ne.store()
            g_ne.add_nodes(a)

            g_e = Group(label='empty_group')
            g_e.store()

        cls.cif = a

        return {
            TestVerdiDataListable.NODE_ID_STR: a.id,
            TestVerdiDataListable.NON_EMPTY_GROUP_ID_STR: g_ne.id,
            TestVerdiDataListable.EMPTY_GROUP_ID_STR: g_e.id
        }

    @classmethod
    def setUpClass(cls):
        super(TestVerdiDataCif, cls).setUpClass()
        orm.Computer(
            name='comp',
            hostname='localhost',
            transport_type='local',
            scheduler_type='direct',
            workdir='/tmp/aiida').store()

        cls.ids = cls.create_cif_data()

    def setUp(self):
        super(TestVerdiDataCif, self).setUp()
        self.comp = self.computer
        self.runner = CliRunner()
        self.this_folder = os.path.dirname(__file__)
        self.this_file = os.path.basename(__file__)

        self.cli_runner = CliRunner()

    def test_list(self):
        """
        This method tests that the Cif listing works as expected with all
        possible flags and arguments.
        """
        self.data_listing_test(CifData, 'C O2', self.ids)

    def test_showhelp(self):
        options = ['--help']
        res = self.cli_runner.invoke(cmd_cif.cif_show, options, catch_exceptions=False)
        self.assertIn(b'Usage:', res.stdout_bytes, 'The string "Usage: " was not found in the output'
                                                   ' of verdi data show help')

    def test_importhelp(self):
        options = ['--help']
        res = self.cli_runner.invoke(cmd_cif.cif_import, options, catch_exceptions=False)
        self.assertIn(b'Usage:', res.stdout_bytes, 'The string "Usage: " was not found in the output'
                                                   ' of verdi data import help')

    def test_import(self):
        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            fhandle.write(self.valid_sample_cif_str)
            fhandle.flush()
            options = [fhandle.name]
            res = self.cli_runner.invoke(cmd_cif.cif_import, options, catch_exceptions=False)
            self.assertIn(b'imported uuid', res.stdout_bytes, 'The string "imported uuid" was not found in the output'
                                                              ' of verdi data import.')

    def test_content(self):
        """Test that `verdi data cif content` returns the content of the file."""
        options = [str(self.cif.uuid)]
        result = self.cli_runner.invoke(cmd_cif.cif_content, options, catch_exceptions=False)

        for line in result.output.split('\n'):
            self.assertIn(line, self.valid_sample_cif_str)

    def test_export(self):
        """
        This method checks if the Cif export works as expected with all
        possible flags and arguments.
        """
        from aiida.cmdline.commands.cmd_data.cmd_cif import EXPORT_FORMATS
        self.data_export_test(CifData, self.ids, EXPORT_FORMATS)


class TestVerdiDataUpf(AiidaTestCase):
    """
    Testing verdi data upf
    """

    @classmethod
    def setUpClass(cls):
        super(TestVerdiDataUpf, cls).setUpClass()

    def setUp(self):
        self.filepath_pseudos = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'fixtures', 'pseudos')
        self.cli_runner = CliRunner()

    def upload_family(self):
        options = [self.filepath_pseudos, "test_group", "test description"]
        res = self.cli_runner.invoke(cmd_upf.upf_uploadfamily, options, catch_exceptions=False)
        self.assertIn(b'UPF files found: 3', res.stdout_bytes, 'The string "UPF files found: 3" was not found in the'
                                                               ' output of verdi data upf uploadfamily')

    def test_uploadfamilyhelp(self):
        output = sp.check_output(['verdi', 'data', 'upf', 'uploadfamily', '--help'])
        self.assertIn(b'Usage:', output, "Sub-command verdi data upf uploadfamily --help failed: {}".format(output))

    def test_uploadfamily(self):
        self.upload_family()
        options = [self.filepath_pseudos, "test_group", "test description", "--stop-if-existing"]
        with self.assertRaises(ValueError):
            self.cli_runner.invoke(cmd_upf.upf_uploadfamily, options, catch_exceptions=False)

    def test_exportfamilyhelp(self):
        output = sp.check_output(['verdi', 'data', 'upf', 'exportfamily', '--help'])
        self.assertIn(b'Usage:', output, "Sub-command verdi data upf exportfamily --help failed.")

    def test_exportfamily(self):
        self.upload_family()

        p = tempfile.mkdtemp()
        options = [p, 'test_group']
        res = self.cli_runner.invoke(cmd_upf.upf_exportfamily, options, catch_exceptions=False)
        self.assertClickResultNoException(res)
        output = sp.check_output(['ls', p])
        self.assertIn(b'Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF', output,
                      "Sub-command verdi data upf exportfamily --help failed: {}".format(output))
        self.assertIn(b'O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF', output,
                      "Sub-command verdi data upf exportfamily --help failed.")
        self.assertIn(b'Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF', output,
                      "Sub-command verdi data upf exportfamily --help failed.")

    def test_listfamilieshelp(self):
        output = sp.check_output(['verdi', 'data', 'upf', 'listfamilies', '--help'])
        self.assertIn(b'Usage:', output, "Sub-command verdi data upf listfamilies --help failed.")

    def test_listfamilies(self):
        self.upload_family()

        options = ['-d', '-e', 'Ba']
        res = self.cli_runner.invoke(cmd_upf.upf_listfamilies, options, catch_exceptions=False)

        self.assertIn(b'test_group', res.stdout_bytes, 'The string "test_group" was not found in the'
                                                       ' output of verdi data upf listfamilies: {}'.format(res.output))

        self.assertIn(b'test description', res.stdout_bytes, 'The string "test_group" was not found in the'
                                                             ' output of verdi data upf listfamilies')

        options = ['-d', '-e', 'Fe']
        res = self.cli_runner.invoke(cmd_upf.upf_listfamilies, options, catch_exceptions=False)
        self.assertIn(b'No valid UPF pseudopotential', res.stdout_bytes,
                      'The string "No valid UPF pseudopotential" was not'
                      ' found in the output of verdi data upf listfamilies')

    def test_importhelp(self):
        output = sp.check_output(['verdi', 'data', 'upf', 'import', '--help'])
        self.assertIn(b'Usage:', output, "Sub-command verdi data upf listfamilies --help failed.")

    def test_import(self):
        options = [os.path.join(self.filepath_pseudos, 'Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF')]
        res = self.cli_runner.invoke(cmd_upf.upf_import, options, catch_exceptions=False)

        self.assertIn(b'Imported', res.stdout_bytes, 'The string "Imported" was not'
                                                     ' found in the output of verdi data import: {}'.format(res.output))
