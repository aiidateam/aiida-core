# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=no-member
"""Test data-related verdi commands."""

import io
import os
import shutil
import unittest
import tempfile
import subprocess as sp
import numpy as np

from click.testing import CliRunner

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.cmd_data import cmd_array, cmd_bands, cmd_cif, cmd_dict, cmd_remote
from aiida.cmdline.commands.cmd_data import cmd_structure, cmd_trajectory, cmd_upf, cmd_singlefile
from aiida.engine import calcfunction
from aiida.orm.nodes.data.cif import has_pycifrw
from aiida.orm import Group, ArrayData, BandsData, KpointsData, CifData, Dict, RemoteData, StructureData, TrajectoryData


class DummyVerdiDataExportable:
    """Test exportable data objects."""

    NODE_ID_STR = 'node_id'
    EMPTY_GROUP_ID_STR = 'empty_group_id'
    EMPTY_GROUP_NAME_STR = 'empty_group'
    NON_EMPTY_GROUP_ID_STR = 'non_empty_group_id'
    NON_EMPTY_GROUP_NAME_STR = 'non_empty_group'

    @unittest.skipUnless(has_pycifrw(), 'Unable to import PyCifRW')
    def data_export_test(self, datatype, ids, supported_formats):
        """This method tests that the data listing works as expected with all
        possible flags and arguments for different datatypes."""
        datatype_mapping = {
            CifData: cmd_cif.cif_export,
            StructureData: cmd_structure.structure_export,
            TrajectoryData: cmd_trajectory.trajectory_export,
        }

        if datatype is None or datatype not in datatype_mapping.keys():
            raise Exception('The listing of the objects {} is not supported'.format(datatype))

        export_cmd = datatype_mapping[datatype]

        # Check that the simple command works as expected
        options = [str(ids[self.NODE_ID_STR])]
        res = self.cli_runner.invoke(export_cmd, options, catch_exceptions=False)
        self.assertEqual(res.exit_code, 0, 'The command did not finish correctly')

        for flag in ['-F', '--format']:
            for frmt in supported_formats:
                options = [flag, frmt, str(ids[self.NODE_ID_STR])]
                res = self.cli_runner.invoke(export_cmd, options, catch_exceptions=False)
                self.assertEqual(
                    res.exit_code, 0, 'The command did not finish '
                    'correctly. Output:\n{}'.format(res.output)
                )

        # Check that the output to file flags work correctly:
        # -o, --output
        output_flags = ['-o', '--output']
        for flag in output_flags:
            try:
                tmpd = tempfile.mkdtemp()
                filepath = os.path.join(tmpd, 'output_file.txt')
                options = [flag, filepath, str(ids[self.NODE_ID_STR])]
                res = self.cli_runner.invoke(export_cmd, options, catch_exceptions=False)
                self.assertEqual(
                    res.exit_code, 0, 'The command should finish correctly.'
                    'Output:\n{}'.format(res.output)
                )

                # Try to export it again. It should fail because the
                # file exists
                res = self.cli_runner.invoke(export_cmd, options, catch_exceptions=False)
                self.assertNotEqual(res.exit_code, 0, 'The command should fail because the file already exists')

                # Now we force the export of the file and it should overwrite
                # existing files
                options = [flag, filepath, '-f', str(ids[self.NODE_ID_STR])]
                res = self.cli_runner.invoke(export_cmd, options, catch_exceptions=False)
                self.assertEqual(
                    res.exit_code, 0, 'The command should finish correctly.'
                    'Output: {}'.format(res.output)
                )
            finally:
                shutil.rmtree(tmpd)


class DummyVerdiDataListable:
    """Test listable data objects."""

    NODE_ID_STR = 'node_id'
    EMPTY_GROUP_ID_STR = 'empty_group_id'
    EMPTY_GROUP_NAME_STR = 'empty_group'
    NON_EMPTY_GROUP_ID_STR = 'non_empty_group_id'
    NON_EMPTY_GROUP_NAME_STR = 'non_empty_group'

    def data_listing_test(self, datatype, search_string, ids):
        """This method tests that the data listing works as expected with all
        possible flags and arguments for different datatypes."""

        headers_mapping = {
            CifData: cmd_cif.LIST_PROJECT_HEADERS,
            StructureData: cmd_structure.LIST_PROJECT_HEADERS,
            TrajectoryData: cmd_trajectory.LIST_PROJECT_HEADERS,
            BandsData: cmd_bands.LIST_PROJECT_HEADERS
        }

        datatype_mapping = {
            CifData: cmd_cif.cif_list,
            StructureData: cmd_structure.structure_list,
            TrajectoryData: cmd_trajectory.trajectory_list,
            BandsData: cmd_bands.bands_list
        }

        if datatype is None or datatype not in datatype_mapping.keys():
            raise Exception('The listing of the objects {} is not supported'.format(datatype))

        listing_cmd = datatype_mapping[datatype]

        # the output we are comparing to is un-decoded bytes, convert search strings:
        search_string_bytes = search_string.encode('utf-8')

        # Check that the normal listing works as expected
        res = self.cli_runner.invoke(listing_cmd, [], catch_exceptions=False)
        self.assertIn(
            search_string_bytes, res.stdout_bytes, 'The string {} was not found in the listing'.format(search_string)
        )

        # Check that the past days filter works as expected
        past_days_flags = ['-p', '--past-days']
        # past_days_flags = ['-p']
        for flag in past_days_flags:
            options = [flag, '1']
            res = self.cli_runner.invoke(listing_cmd, options, catch_exceptions=False)
            self.assertIn(
                search_string_bytes, res.stdout_bytes,
                'The string {} was not found in the listing'.format(search_string)
            )

            options = [flag, '0']
            res = self.cli_runner.invoke(listing_cmd, options, catch_exceptions=False)
            self.assertNotIn(
                search_string_bytes, res.stdout_bytes,
                'A not expected string {} was found in the listing'.format(search_string)
            )

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
                self.assertNotIn(
                    search_string_bytes, res.stdout_bytes, 'A not expected string {} was found in the listing'
                )

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
            for header in headers_mapping[datatype]:
                self.assertNotIn(header.encode('utf-8'), res.stdout_bytes)


class TestVerdiData(AiidaTestCase):
    """Testing reachability of the verdi data subcommands."""

    @classmethod
    def setUpClass(cls):  # pylint: disable=arguments-differ
        super().setUpClass()

    def setUp(self):
        pass

    def test_reachable(self):
        """Testing reachability of the following commands:
        verdi data array
        verdi data bands
        verdi data cif
        verdi data dict
        verdi data remote
        verdi data structure
        verdi data trajectory
        verdi data upf"""
        subcommands = ['array', 'bands', 'cif', 'dict', 'remote', 'structure', 'trajectory', 'upf']
        for sub_cmd in subcommands:
            output = sp.check_output(['verdi', 'data', sub_cmd, '--help'])
            self.assertIn(b'Usage:', output, 'Sub-command verdi data {} --help failed.'.format(sub_cmd))


class TestVerdiDataArray(AiidaTestCase):
    """Testing verdi data array."""

    @classmethod
    def setUpClass(cls):  # pylint: disable=arguments-differ
        super().setUpClass()

    def setUp(self):
        self.arr = ArrayData()
        self.arr.set_array('test_array', np.array([0, 1, 3]))
        self.arr.store()

        self.cli_runner = CliRunner()

    def test_arrayshowhelp(self):
        output = sp.check_output(['verdi', 'data', 'array', 'show', '--help'])
        self.assertIn(b'Usage:', output, 'Sub-command verdi data array show --help failed.')

    def test_arrayshow(self):
        options = [str(self.arr.id)]
        res = self.cli_runner.invoke(cmd_array.array_show, options, catch_exceptions=False)
        self.assertEqual(res.exit_code, 0, 'The command did not finish correctly')


class TestVerdiDataBands(AiidaTestCase, DummyVerdiDataListable):
    """Testing verdi data bands."""

    @staticmethod
    def create_structure_bands():
        """Create bands structure object."""
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
        strct = StructureData(cell=cell)
        strct.append_atom(position=(0., 0., 0.), symbols='Fe')
        strct.append_atom(position=(alat / 2., alat / 2., alat / 2.), symbols='O')
        strct.store()

        @calcfunction
        def connect_structure_bands(strct):  # pylint: disable=unused-argument
            alat = 4.
            cell = np.array([
                [alat, 0., 0.],
                [0., alat, 0.],
                [0., 0., alat],
            ])

            kpnts = KpointsData()
            kpnts.set_cell(cell)
            kpnts.set_kpoints([[0., 0., 0.], [0.1, 0.1, 0.1]])

            bands = BandsData()
            bands.set_kpointsdata(kpnts)
            bands.set_bands([[1.0, 2.0], [3.0, 4.0]])
            return bands

        bands = connect_structure_bands(strct)

        # Create 2 groups and add the data to one of them
        g_ne = Group(label='non_empty_group')
        g_ne.store()
        g_ne.add_nodes(bands)

        g_e = Group(label='empty_group')
        g_e.store()

        return {
            DummyVerdiDataListable.NODE_ID_STR: bands.id,
            DummyVerdiDataListable.NON_EMPTY_GROUP_ID_STR: g_ne.id,
            DummyVerdiDataListable.EMPTY_GROUP_ID_STR: g_e.id
        }

    @classmethod
    def setUpClass(cls):  # pylint: disable=arguments-differ
        super().setUpClass()
        cls.ids = cls.create_structure_bands()

    def setUp(self):
        self.cli_runner = CliRunner()

    def test_bandsshowhelp(self):
        output = sp.check_output(['verdi', 'data', 'bands', 'show', '--help'])
        self.assertIn(b'Usage:', output, 'Sub-command verdi data bands show --help failed.')

    def test_bandlistshelp(self):
        output = sp.check_output(['verdi', 'data', 'bands', 'list', '--help'])
        self.assertIn(b'Usage:', output, 'Sub-command verdi data bands show --help failed.')

    def test_bandslist(self):
        self.data_listing_test(BandsData, 'FeO', self.ids)

    def test_bandexporthelp(self):
        output = sp.check_output(['verdi', 'data', 'bands', 'export', '--help'])
        self.assertIn(b'Usage:', output, 'Sub-command verdi data bands export --help failed.')

    def test_bandsexport(self):
        options = [str(self.ids[DummyVerdiDataListable.NODE_ID_STR])]
        res = self.cli_runner.invoke(cmd_bands.bands_export, options, catch_exceptions=False)
        self.assertEqual(res.exit_code, 0, 'The command did not finish correctly')
        self.assertIn(b'[1.0, 3.0]', res.stdout_bytes, 'The string [1.0, 3.0] was not found in the bands' 'export')


class TestVerdiDataDict(AiidaTestCase):
    """Testing verdi data dict."""

    @classmethod
    def setUpClass(cls):  # pylint: disable=arguments-differ
        super().setUpClass()

    def setUp(self):
        self.dct = Dict()
        self.dct.set_dict({'a': 1, 'b': 2})
        self.dct.store()

        self.cli_runner = CliRunner()

    def test_dictshowhelp(self):
        output = sp.check_output(['verdi', 'data', 'dict', 'show', '--help'])
        self.assertIn(b'Usage:', output, 'Sub-command verdi data dict show --help failed.')

    def test_dictshow(self):
        """Test verdi data dict show."""
        options = [str(self.dct.id)]
        res = self.cli_runner.invoke(cmd_dict.dictionary_show, options, catch_exceptions=False)
        self.assertEqual(res.exit_code, 0, 'The command verdi data dict show did not finish correctly')
        self.assertIn(
            b'"a": 1', res.stdout_bytes, 'The string "a": 1 was not found in the output'
            ' of verdi data dict show'
        )


class TestVerdiDataRemote(AiidaTestCase):
    """Testing verdi data remote."""

    @classmethod
    def setUpClass(cls):  # pylint: disable=arguments-differ
        super().setUpClass()
        user = orm.User.objects.get_default()
        orm.AuthInfo(cls.computer, user).store()

    def setUp(self):
        comp = self.computer
        self.rmt = RemoteData()
        path = tempfile.mkdtemp()
        self.rmt.set_remote_path(path)
        with open(os.path.join(path, 'file.txt'), 'w', encoding='utf8') as fhandle:
            fhandle.write('test string')
        self.rmt.computer = comp
        self.rmt.store()

        self.cli_runner = CliRunner()

    def test_remoteshowhelp(self):
        output = sp.check_output(['verdi', 'data', 'remote', 'show', '--help'])
        self.assertIn(b'Usage:', output, 'Sub-command verdi data remote show --help failed.')

    def test_remoteshow(self):
        """Test verdi data remote show."""
        options = [str(self.rmt.id)]
        res = self.cli_runner.invoke(cmd_remote.remote_show, options, catch_exceptions=False)
        self.assertEqual(res.exit_code, 0, 'The command verdi data remote show did not finish correctly')
        self.assertIn(
            b'Remote computer name:', res.stdout_bytes, 'The string "Remote computer name:" was not found in the'
            ' output of verdi data remote show'
        )
        self.assertIn(
            b'Remote folder full path:', res.stdout_bytes, 'The string "Remote folder full path:" was not found in the'
            ' output of verdi data remote show'
        )

    def test_remotelshelp(self):
        output = sp.check_output(['verdi', 'data', 'remote', 'ls', '--help'])
        self.assertIn(b'Usage:', output, 'Sub-command verdi data remote ls --help failed.')

    def test_remotels(self):
        options = ['--long', str(self.rmt.id)]
        res = self.cli_runner.invoke(cmd_remote.remote_ls, options, catch_exceptions=False)
        self.assertEqual(res.exit_code, 0, 'The command verdi data remote ls did not finish correctly')
        self.assertIn(
            b'file.txt', res.stdout_bytes, 'The file "file.txt" was not found in the output'
            ' of verdi data remote ls'
        )

    def test_remotecathelp(self):
        output = sp.check_output(['verdi', 'data', 'remote', 'cat', '--help'])
        self.assertIn(b'Usage:', output, 'Sub-command verdi data remote cat --help failed.')

    def test_remotecat(self):
        options = [str(self.rmt.id), 'file.txt']
        res = self.cli_runner.invoke(cmd_remote.remote_cat, options, catch_exceptions=False)
        self.assertEqual(res.exit_code, 0, 'The command verdi data remote cat did not finish correctly')
        self.assertIn(
            b'test string', res.stdout_bytes, 'The string "test string" was not found in the output'
            ' of verdi data remote cat file.txt'
        )


class TestVerdiDataTrajectory(AiidaTestCase, DummyVerdiDataListable, DummyVerdiDataExportable):
    """Test verdi data trajectory."""

    @staticmethod
    def create_trajectory_data():
        """Create TrajectoryData object with two arrays."""

        traj = TrajectoryData()

        # I create sample data
        stepids = np.array([60, 70])
        times = stepids * 0.01
        cells = np.array([[[
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
        positions = np.array([[[0., 0., 0.], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]],
                              [[0., 0., 0.], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]]])
        velocities = np.array([[[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]],
                               [[0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, -0.5, -0.5]]])

        # I set the node
        traj.set_trajectory(
            stepids=stepids, cells=cells, symbols=symbols, positions=positions, times=times, velocities=velocities
        )

        traj.store()

        # Create 2 groups and add the data to one of them
        g_ne = Group(label='non_empty_group')
        g_ne.store()
        g_ne.add_nodes(traj)

        g_e = Group(label='empty_group')
        g_e.store()

        return {
            DummyVerdiDataListable.NODE_ID_STR: traj.id,
            DummyVerdiDataListable.NON_EMPTY_GROUP_ID_STR: g_ne.id,
            DummyVerdiDataListable.EMPTY_GROUP_ID_STR: g_e.id
        }

    @classmethod
    def setUpClass(cls):  # pylint: disable=arguments-differ
        super().setUpClass()
        orm.Computer(
            name='comp', hostname='localhost', transport_type='local', scheduler_type='direct', workdir='/tmp/aiida'
        ).store()
        cls.ids = cls.create_trajectory_data()

    def setUp(self):
        self.comp = self.computer
        self.runner = CliRunner()
        self.this_folder = os.path.dirname(__file__)
        self.this_file = os.path.basename(__file__)

        self.cli_runner = CliRunner()

    def test_showhelp(self):
        res = self.runner.invoke(cmd_trajectory.trajectory_show, ['--help'])
        self.assertIn(
            b'Usage:', res.stdout_bytes, 'The string "Usage: " was not found in the output'
            ' of verdi data trajecotry show --help'
        )

    def test_list(self):
        self.data_listing_test(TrajectoryData, str(self.ids[DummyVerdiDataListable.NODE_ID_STR]), self.ids)

    @unittest.skipUnless(has_pycifrw(), 'Unable to import PyCifRW')
    def test_export(self):
        new_supported_formats = list(cmd_trajectory.EXPORT_FORMATS)
        self.data_export_test(TrajectoryData, self.ids, new_supported_formats)


class TestVerdiDataStructure(AiidaTestCase, DummyVerdiDataListable, DummyVerdiDataExportable):
    """Test verdi data structure."""
    from aiida.orm.nodes.data.structure import has_ase

    @staticmethod
    def create_structure_data():
        """Create StructureData object."""
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
            DummyVerdiDataListable.NODE_ID_STR: struc.id,
            DummyVerdiDataListable.NON_EMPTY_GROUP_ID_STR: g_ne.id,
            DummyVerdiDataListable.EMPTY_GROUP_ID_STR: g_e.id
        }

    @classmethod
    def setUpClass(cls):  # pylint: disable=arguments-differ
        super().setUpClass()
        orm.Computer(
            name='comp', hostname='localhost', transport_type='local', scheduler_type='direct', workdir='/tmp/aiida'
        ).store()
        cls.ids = cls.create_structure_data()

    def setUp(self):
        self.comp = self.computer
        self.runner = CliRunner()
        self.this_folder = os.path.dirname(__file__)
        self.this_file = os.path.basename(__file__)

        self.cli_runner = CliRunner()

    def test_importhelp(self):
        res = self.runner.invoke(cmd_structure.structure_import, ['--help'])
        self.assertIn(
            b'Usage:', res.stdout_bytes, 'The string "Usage: " was not found in the output'
            ' of verdi data structure import --help'
        )

    def test_importhelp_ase(self):
        res = self.runner.invoke(cmd_structure.import_ase, ['--help'])
        self.assertIn(
            b'Usage:', res.stdout_bytes, 'The string "Usage: " was not found in the output'
            ' of verdi data structure import ase --help'
        )

    def test_importhelp_aiida_xyz(self):
        res = self.runner.invoke(cmd_structure.import_aiida_xyz, ['--help'])
        self.assertIn(
            b'Usage:', res.stdout_bytes, 'The string "Usage: " was not found in the output'
            ' of verdi data structure import aiida-xyz --help'
        )

    def test_import_aiida_xyz(self):
        """Test import xyz file."""
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
                '--vacuum-factor',
                '1.0',
                '--vacuum-addition',
                '10.0',
                '--pbc',
                '1',
                '1',
                '1',
            ]
            res = self.cli_runner.invoke(cmd_structure.import_aiida_xyz, options, catch_exceptions=False)
            self.assertIn(
                b'Successfully imported', res.stdout_bytes,
                'The string "Successfully imported" was not found in the output'
                ' of verdi data structure import.'
            )
            self.assertIn(
                b'PK', res.stdout_bytes, 'The string "PK" was not found in the output'
                ' of verdi data structure import.'
            )

    def test_import_aiida_xyz_2(self):
        """Test import xyz file."""
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
                '-n'  # dry-run
            ]
            res = self.cli_runner.invoke(cmd_structure.import_aiida_xyz, options, catch_exceptions=False)
            self.assertIn(
                b'Successfully imported', res.stdout_bytes,
                'The string "Successfully imported" was not found in the output'
                ' of verdi data structure import.'
            )
            self.assertIn(
                b'dry-run', res.stdout_bytes, 'The string "dry-run" was not found in the output'
                ' of verdi data structure import.'
            )

    @unittest.skipIf(not has_ase(), 'Unable to import ase')
    def test_import_ase(self):
        """Trying to import an xsf file through ase."""
        xsfcontent = '''CRYSTAL
PRIMVEC
    2.7100000000    2.7100000000    0.0000000000
    2.7100000000    0.0000000000    2.7100000000
    0.0000000000    2.7100000000    2.7100000000
 PRIMCOORD
           2           1
 16      0.0000000000     0.0000000000     0.0000000000
 30      1.3550000000    -1.3550000000    -1.3550000000
        '''
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.xsf') as fhandle:
            fhandle.write(xsfcontent)
            fhandle.flush()
            options = [
                fhandle.name,
            ]
            res = self.cli_runner.invoke(cmd_structure.import_ase, options, catch_exceptions=False)
            self.assertIn(
                b'Successfully imported', res.stdout_bytes,
                'The string "Successfully imported" was not found in the output'
                ' of verdi data structure import.'
            )
            self.assertIn(
                b'PK', res.stdout_bytes, 'The string "PK" was not found in the output'
                ' of verdi data structure import.'
            )

    def test_list(self):
        self.data_listing_test(StructureData, 'BaO3Ti', self.ids)

    def test_export(self):
        self.data_export_test(StructureData, self.ids, cmd_structure.EXPORT_FORMATS)


@unittest.skipUnless(has_pycifrw(), 'Unable to import PyCifRW')
class TestVerdiDataCif(AiidaTestCase, DummyVerdiDataListable, DummyVerdiDataExportable):
    """Test verdi data cif."""
    valid_sample_cif_str = '''
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
        """Create CifData object."""
        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            filename = fhandle.name
            fhandle.write(cls.valid_sample_cif_str)
            fhandle.flush()
            a_cif = CifData(file=filename, source={'version': '1234', 'db_name': 'COD', 'id': '0000001'})
            a_cif.store()

            g_ne = Group(label='non_empty_group')
            g_ne.store()
            g_ne.add_nodes(a_cif)

            g_e = Group(label='empty_group')
            g_e.store()

        cls.cif = a_cif

        return {
            DummyVerdiDataListable.NODE_ID_STR: a_cif.id,
            DummyVerdiDataListable.NON_EMPTY_GROUP_ID_STR: g_ne.id,
            DummyVerdiDataListable.EMPTY_GROUP_ID_STR: g_e.id
        }

    @classmethod
    def setUpClass(cls):  # pylint: disable=arguments-differ
        """Setup class to test CifData."""
        super().setUpClass()
        orm.Computer(
            name='comp', hostname='localhost', transport_type='local', scheduler_type='direct', workdir='/tmp/aiida'
        ).store()

        cls.ids = cls.create_cif_data()

    def setUp(self):
        super().setUp()
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
        self.assertIn(
            b'Usage:', res.stdout_bytes, 'The string "Usage: " was not found in the output'
            ' of verdi data show help'
        )

    def test_importhelp(self):
        options = ['--help']
        res = self.cli_runner.invoke(cmd_cif.cif_import, options, catch_exceptions=False)
        self.assertIn(
            b'Usage:', res.stdout_bytes, 'The string "Usage: " was not found in the output'
            ' of verdi data import help'
        )

    def test_import(self):
        """Test verdi data cif import."""
        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            fhandle.write(self.valid_sample_cif_str)
            fhandle.flush()
            options = [fhandle.name]
            res = self.cli_runner.invoke(cmd_cif.cif_import, options, catch_exceptions=False)
            self.assertIn(
                b'imported uuid', res.stdout_bytes, 'The string "imported uuid" was not found in the output'
                ' of verdi data import.'
            )

    def test_content(self):
        """Test that `verdi data cif content` returns the content of the file."""
        options = [str(self.cif.uuid)]
        result = self.cli_runner.invoke(cmd_cif.cif_content, options, catch_exceptions=False)

        for line in result.output.split('\n'):
            self.assertIn(line, self.valid_sample_cif_str)

    def test_export(self):
        """This method checks if the Cif export works as expected with all
        possible flags and arguments."""
        self.data_export_test(CifData, self.ids, cmd_cif.EXPORT_FORMATS)


class TestVerdiDataSinglefile(AiidaTestCase, DummyVerdiDataListable, DummyVerdiDataExportable):
    """Test verdi data singlefile."""
    sample_str = '''
        data_test
    '''

    @classmethod
    def setUpClass(cls):  # pylint: disable=arguments-differ
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.comp = self.computer
        self.runner = CliRunner()
        self.this_folder = os.path.dirname(__file__)
        self.this_file = os.path.basename(__file__)

        self.cli_runner = CliRunner()

    def test_content(self):
        """Test that `verdi data singlefile content` returns the content of the file."""
        content = 'abc\ncde'
        singlefile = orm.SinglefileData(file=io.BytesIO(content.encode('utf8'))).store()

        options = [str(singlefile.uuid)]
        result = self.cli_runner.invoke(cmd_singlefile.singlefile_content, options, catch_exceptions=False)

        for line in result.output.split('\n'):
            self.assertIn(line, content)


class TestVerdiDataUpf(AiidaTestCase):
    """Testing verdi data upf."""

    @classmethod
    def setUpClass(cls):  # pylint: disable=arguments-differ
        super().setUpClass()

    def setUp(self):
        self.filepath_pseudos = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'fixtures', 'pseudos')
        self.cli_runner = CliRunner()

    def upload_family(self):
        options = [self.filepath_pseudos, 'test_group', 'test description']
        res = self.cli_runner.invoke(cmd_upf.upf_uploadfamily, options, catch_exceptions=False)
        self.assertIn(
            b'UPF files found: 4', res.stdout_bytes, 'The string "UPF files found: 4" was not found in the'
            ' output of verdi data upf uploadfamily'
        )

    def test_uploadfamilyhelp(self):
        output = sp.check_output(['verdi', 'data', 'upf', 'uploadfamily', '--help'])
        self.assertIn(b'Usage:', output, 'Sub-command verdi data upf uploadfamily --help failed: {}'.format(output))

    def test_uploadfamily(self):
        self.upload_family()
        options = [self.filepath_pseudos, 'test_group', 'test description', '--stop-if-existing']
        with self.assertRaises(ValueError):
            self.cli_runner.invoke(cmd_upf.upf_uploadfamily, options, catch_exceptions=False)

    def test_exportfamilyhelp(self):
        output = sp.check_output(['verdi', 'data', 'upf', 'exportfamily', '--help'])
        self.assertIn(b'Usage:', output, 'Sub-command verdi data upf exportfamily --help failed.')

    def test_exportfamily(self):
        """Test verdi data upf exportfamily."""
        self.upload_family()

        path = tempfile.mkdtemp()
        options = [path, 'test_group']
        res = self.cli_runner.invoke(cmd_upf.upf_exportfamily, options, catch_exceptions=False)
        self.assertClickResultNoException(res)
        output = sp.check_output(['ls', path])
        self.assertIn(
            b'Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF', output,
            'Sub-command verdi data upf exportfamily --help failed: {}'.format(output)
        )
        self.assertIn(
            b'O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF', output,
            'Sub-command verdi data upf exportfamily --help failed.'
        )
        self.assertIn(
            b'Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF', output,
            'Sub-command verdi data upf exportfamily --help failed.'
        )
        self.assertIn(b'C_pbe_v1.2.uspp.F.UPF', output, 'Sub-command verdi data upf exportfamily --help failed.')

    def test_listfamilieshelp(self):
        output = sp.check_output(['verdi', 'data', 'upf', 'listfamilies', '--help'])
        self.assertIn(b'Usage:', output, 'Sub-command verdi data upf listfamilies --help failed.')

    def test_listfamilies(self):
        """Test verdi data upf listfamilies"""
        self.upload_family()

        options = ['-d', '-e', 'Ba']
        res = self.cli_runner.invoke(cmd_upf.upf_listfamilies, options, catch_exceptions=False)

        self.assertIn(
            b'test_group', res.stdout_bytes, 'The string "test_group" was not found in the'
            ' output of verdi data upf listfamilies: {}'.format(res.output)
        )

        self.assertIn(
            b'test description', res.stdout_bytes, 'The string "test_group" was not found in the'
            ' output of verdi data upf listfamilies'
        )

        options = ['-d', '-e', 'Fe']
        res = self.cli_runner.invoke(cmd_upf.upf_listfamilies, options, catch_exceptions=False)
        self.assertIn(
            b'No valid UPF pseudopotential', res.stdout_bytes, 'The string "No valid UPF pseudopotential" was not'
            ' found in the output of verdi data upf listfamilies'
        )

    def test_importhelp(self):
        output = sp.check_output(['verdi', 'data', 'upf', 'import', '--help'])
        self.assertIn(b'Usage:', output, 'Sub-command verdi data upf listfamilies --help failed.')

    def test_import(self):
        options = [os.path.join(self.filepath_pseudos, 'Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF')]
        res = self.cli_runner.invoke(cmd_upf.upf_import, options, catch_exceptions=False)

        self.assertIn(
            b'Imported', res.stdout_bytes, 'The string "Imported" was not'
            ' found in the output of verdi data import: {}'.format(res.output)
        )
