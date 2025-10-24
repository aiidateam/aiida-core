###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test data-related verdi commands."""

import asyncio
import io
import os
import subprocess as sp
import tempfile

import numpy as np
import pytest

from aiida import orm
from aiida.cmdline.commands import cmd_group
from aiida.cmdline.commands.cmd_data import (
    cmd_array,
    cmd_bands,
    cmd_cif,
    cmd_dict,
    cmd_remote,
    cmd_show,
    cmd_singlefile,
    cmd_structure,
    cmd_trajectory,
    cmd_upf,
)
from aiida.engine import calcfunction
from aiida.orm import ArrayData, BandsData, CifData, Dict, Group, KpointsData, RemoteData, StructureData, TrajectoryData
from aiida.orm.nodes.data.cif import has_pycifrw
from tests.static import STATIC_DIR


def has_mayavi() -> bool:
    """Return whether the ``mayavi`` module can be imported."""
    try:
        import mayavi  # noqa: F401
    except ImportError:
        return False
    return True


class DummyVerdiDataExportable:
    """Test exportable data objects."""

    NODE_ID_STR = 'node_id'
    EMPTY_GROUP_ID_STR = 'empty_group_id'
    EMPTY_GROUP_NAME_STR = 'empty_group'
    NON_EMPTY_GROUP_ID_STR = 'non_empty_group_id'
    NON_EMPTY_GROUP_NAME_STR = 'non_empty_group'

    @pytest.mark.skipif(not has_pycifrw(), reason='Unable to import PyCifRW')
    def data_export_test(self, datatype, ids, supported_formats, output_flag, tmp_path):
        """This method tests that the data listing works as expected with all
        possible flags and arguments for different datatypes.
        """
        datatype_mapping = {
            CifData: cmd_cif.cif_export,
            StructureData: cmd_structure.structure_export,
            TrajectoryData: cmd_trajectory.trajectory_export,
        }

        if datatype is None or datatype not in datatype_mapping:
            raise RuntimeError(f'The listing of the objects {datatype} is not supported')

        export_cmd = datatype_mapping[datatype]

        # Check that the simple command works as expected
        options = [str(ids[self.NODE_ID_STR])]
        res = self.cli_runner(export_cmd, options)
        assert res.exit_code == 0, 'The command did not finish correctly'

        for flag in ['-F', '--format']:
            for frmt in supported_formats:
                options = [flag, frmt, str(ids[self.NODE_ID_STR])]
                res = self.cli_runner(export_cmd, options)
                assert res.exit_code == 0, f'The command did not finish correctly. Output:\n{res.output}'

        filepath = tmp_path / 'output_file.txt'
        options = [output_flag, str(filepath), str(ids[self.NODE_ID_STR])]
        res = self.cli_runner(export_cmd, options)
        assert res.exit_code == 0, f'The command should finish correctly.Output:\n{res.output}'

        # Try to export it again. It should fail because the
        # file exists
        res = self.cli_runner(export_cmd, options, raises=True)
        assert res.exit_code != 0, 'The command should fail because the file already exists'

        # Now we force the export of the file and it should overwrite
        # existing files
        options = [output_flag, str(filepath), '-f', str(ids[self.NODE_ID_STR])]
        res = self.cli_runner(export_cmd, options)
        assert res.exit_code == 0, f'The command should finish correctly.Output: {res.output}'


class DummyVerdiDataListable:
    """Test listable data objects."""

    NODE_ID_STR = 'node_id'
    EMPTY_GROUP_ID_STR = 'empty_group_id'
    EMPTY_GROUP_NAME_STR = 'empty_group'
    NON_EMPTY_GROUP_ID_STR = 'non_empty_group_id'
    NON_EMPTY_GROUP_NAME_STR = 'non_empty_group'

    def data_listing_test(self, datatype, search_string, ids):
        """This method tests that the data listing works as expected with all
        possible flags and arguments for different datatypes.
        """
        headers_mapping = {
            CifData: cmd_cif.LIST_PROJECT_HEADERS,
            StructureData: cmd_structure.LIST_PROJECT_HEADERS,
            TrajectoryData: cmd_trajectory.LIST_PROJECT_HEADERS,
            BandsData: cmd_bands.LIST_PROJECT_HEADERS,
        }

        datatype_mapping = {
            CifData: cmd_cif.cif_list,
            StructureData: cmd_structure.structure_list,
            TrajectoryData: cmd_trajectory.trajectory_list,
            BandsData: cmd_bands.bands_list,
        }

        if datatype is None or datatype not in datatype_mapping:
            raise RuntimeError(f'The listing of the objects {datatype} is not supported')

        listing_cmd = datatype_mapping[datatype]

        # the output we are comparing to is un-decoded bytes, convert search strings:
        search_string_bytes = search_string.encode('utf-8')

        # Check that the normal listing works as expected
        res = self.cli_runner(listing_cmd, [])
        assert search_string_bytes in res.stdout_bytes, f'The string {search_string} was not found in the listing'

        # Check that the past days filter works as expected
        past_days_flags = ['-p', '--past-days']
        for flag in past_days_flags:
            options = [flag, '1']
            res = self.cli_runner(listing_cmd, options)
            assert search_string_bytes in res.stdout_bytes, f'The string {search_string} was not found in the listing'

            options = [flag, '0']
            res = self.cli_runner(listing_cmd, options)
            assert (
                search_string_bytes not in res.stdout_bytes
            ), f'A not expected string {search_string} was found in the listing'

        # Check that the group filter works as expected
        # if ids is not None:
        group_flags = ['-G', '--groups']
        for flag in group_flags:
            # Non empty group
            for non_empty in [self.NON_EMPTY_GROUP_NAME_STR, str(ids[self.NON_EMPTY_GROUP_ID_STR])]:
                options = [flag, non_empty]
                res = self.cli_runner(listing_cmd, options)
                assert search_string_bytes in res.stdout_bytes, 'The string {} was not found in the listing'

            # Empty group
            for empty in [self.EMPTY_GROUP_NAME_STR, str(ids[self.EMPTY_GROUP_ID_STR])]:
                options = [flag, empty]
                res = self.cli_runner(listing_cmd, options)
                assert search_string_bytes not in res.stdout_bytes, 'A not expected string {} was found in the listing'

            # Group combination
            for non_empty in [self.NON_EMPTY_GROUP_NAME_STR, str(ids[self.NON_EMPTY_GROUP_ID_STR])]:
                for empty in [self.EMPTY_GROUP_NAME_STR, str(ids[self.EMPTY_GROUP_ID_STR])]:
                    options = [flag, non_empty, empty]
                    res = self.cli_runner(listing_cmd, options)
                    assert search_string_bytes in res.stdout_bytes, 'The string {} was not found in the listing'

        # Check raw flag
        raw_flags = ['-r', '--raw']
        for flag in raw_flags:
            options = [flag]
            res = self.cli_runner(listing_cmd, options)
            for header in headers_mapping[datatype]:
                assert header.encode('utf-8') not in res.stdout_bytes


class TestVerdiData:
    """Testing reachability of the verdi data subcommands."""

    def test_reachable(self):
        """Testing reachability of the following commands:
        verdi data core.array
        verdi data core.bands
        verdi data core.cif
        verdi data core.dict
        verdi data core.upf
        verdi data core.structure
        verdi data core.trajectory
        verdi data core.upf
        """
        subcommands = [
            'core.array',
            'core.bands',
            'core.cif',
            'core.dict',
            'core.remote',
            'core.structure',
            'core.trajectory',
            'core.upf',
        ]
        for sub_cmd in subcommands:
            output = sp.check_output(['verdi', 'data', sub_cmd, '--help'])
            assert b'Usage:' in output, f'Sub-command verdi data {sub_cmd} --help failed.'


class TestVerdiDataArray:
    """Testing verdi data core.array."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_profile_clean, run_cli_command):
        """Initialize the profile."""
        self.arr = ArrayData()
        self.arr.set_array('test_array', np.array([0, 1, 3]))
        self.arr.store()
        self.cli_runner = run_cli_command

    def test_arrayshowhelp(self):
        output = sp.check_output(['verdi', 'data', 'core.array', 'show', '--help'])
        assert b'Usage:' in output, 'Sub-command verdi data core.array show --help failed.'

    def test_arrayshow(self):
        options = [str(self.arr.pk)]
        res = self.cli_runner(cmd_array.array_show, options)
        assert res.exit_code == 0, 'The command did not finish correctly'


class TestVerdiDataBands(DummyVerdiDataListable):
    """Testing verdi data core.bands."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_profile_clean, run_cli_command):
        """Initialize the profile."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.pks = self.create_structure_bands()
        self.cli_runner = run_cli_command
        yield
        self.loop.close()

    @staticmethod
    def create_structure_bands():
        """Create bands structure object."""
        alat = 4.0  # angstrom
        cell = [
            [
                alat,
                0.0,
                0.0,
            ],
            [
                0.0,
                alat,
                0.0,
            ],
            [
                0.0,
                0.0,
                alat,
            ],
        ]
        strct = StructureData(cell=cell)
        strct.append_atom(position=(0.0, 0.0, 0.0), symbols='Fe')
        strct.append_atom(position=(alat / 2.0, alat / 2.0, alat / 2.0), symbols='O')
        strct.store()

        @calcfunction
        def connect_structure_bands(strct):
            alat = 4.0
            cell = np.array(
                [
                    [alat, 0.0, 0.0],
                    [0.0, alat, 0.0],
                    [0.0, 0.0, alat],
                ]
            )

            kpnts = KpointsData()
            kpnts.set_cell(cell)
            kpnts.set_kpoints([[0.0, 0.0, 0.0], [0.1, 0.1, 0.1]])

            bands = BandsData()
            bands.set_kpointsdata(kpnts)
            bands.set_bands([[1.0, 2.0], [3.0, 4.0]])
            return bands

        bands = connect_structure_bands(strct)

        bands_isolated = BandsData()
        bands_isolated.store()

        # Create 2 groups and add the data to one of them
        g_ne = Group(label='non_empty_group')
        g_ne.store()
        g_ne.add_nodes(bands)
        g_ne.add_nodes(bands_isolated)

        g_e = Group(label='empty_group')
        g_e.store()

        return {
            DummyVerdiDataListable.NODE_ID_STR: bands.pk,
            DummyVerdiDataListable.NON_EMPTY_GROUP_ID_STR: g_ne.pk,
            DummyVerdiDataListable.EMPTY_GROUP_ID_STR: g_e.pk,
        }

    def test_bandsshowhelp(self):
        output = sp.check_output(['verdi', 'data', 'core.bands', 'show', '--help'])
        assert b'Usage:' in output, 'Sub-command verdi data core.bands show --help failed.'

    def test_bandlistshelp(self):
        output = sp.check_output(['verdi', 'data', 'core.bands', 'list', '--help'])
        assert b'Usage:' in output, 'Sub-command verdi data core.bands show --help failed.'

    def test_bandslist(self):
        self.data_listing_test(BandsData, 'FeO', self.pks)
        self.data_listing_test(BandsData, '<<NOT FOUND>>', self.pks)

    def test_bandslist_with_elements(self):
        options = ['-e', 'Fe']
        res = self.cli_runner(cmd_bands.bands_list, options)
        assert b'FeO' in res.stdout_bytes, 'The string "FeO" was not found in the listing'
        assert b'<<NOT FOUND>>' not in res.stdout_bytes, 'The string "<<NOT FOUND>>" should not in the listing'

    def test_bandexporthelp(self):
        output = sp.check_output(['verdi', 'data', 'core.bands', 'export', '--help'])
        assert b'Usage:' in output, 'Sub-command verdi data core.bands export --help failed.'

    def test_bandsexport(self):
        options = [str(self.pks[DummyVerdiDataListable.NODE_ID_STR])]
        res = self.cli_runner(cmd_bands.bands_export, options)
        assert res.exit_code == 0, 'The command did not finish correctly'
        assert b'[1.0, 3.0]' in res.stdout_bytes, 'The string [1.0, 3.0] was not found in the bands export'

    def test_bandsexport_single_kp(self):
        """Plot band for single k-point (issue #2462)."""
        kpnts = KpointsData()
        kpnts.set_kpoints([[0.0, 0.0, 0.0]])

        bands = BandsData()
        bands.set_kpointsdata(kpnts)
        bands.set_bands([[1.0, 2.0]])
        bands.store()

        # matplotlib
        options = [str(bands.pk), '--format', 'mpl_singlefile']
        res = self.cli_runner(cmd_bands.bands_export, options)
        assert b'p.scatter' in res.stdout_bytes, 'The string p.scatter was not found in the bands mpl export'

        # gnuplot
        from click.testing import CliRunner

        with CliRunner().isolated_filesystem():
            options = [str(bands.pk), '--format', 'gnuplot', '-o', 'bands.gnu']
            self.cli_runner(cmd_bands.bands_export, options)
            with open('bands.gnu', 'r', encoding='utf8') as gnu_file:
                res = gnu_file.read()
                assert 'vectors nohead' in res, 'The string "vectors nohead" was not found in the gnuplot script'


class TestVerdiDataDict:
    """Testing verdi data core.dict."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_profile_clean, run_cli_command):
        """Initialize the profile."""
        self.dct = Dict()
        self.dct.set_dict({'a': 1, 'b': 2})
        self.dct.store()
        self.cli_runner = run_cli_command

    def test_dictshowhelp(self):
        output = sp.check_output(['verdi', 'data', 'core.dict', 'show', '--help'])
        assert b'Usage:' in output, 'Sub-command verdi data core.dict show --help failed.'

    def test_dictshow(self):
        """Test verdi data core.dict show."""
        options = [str(self.dct.pk)]
        res = self.cli_runner(cmd_dict.dictionary_show, options)
        assert res.exit_code == 0, 'The command verdi data core.dict show did not finish correctly'
        assert b'"a": 1' in res.stdout_bytes, (
            'The string "a": 1 was not found in the output' ' of verdi data core.dict show'
        )


class TestVerdiDataRemote:
    """Testing verdi data core.upf."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_profile_clean, aiida_localhost, run_cli_command, tmp_path):
        """Initialize the profile."""
        tmp_path.joinpath('file.txt').write_text('test string', encoding='utf8')
        self.rmt = RemoteData()
        self.rmt.set_remote_path(str(tmp_path.absolute()))
        self.rmt.computer = aiida_localhost
        self.rmt.store()
        self.cli_runner = run_cli_command

    def test_remoteshowhelp(self):
        output = sp.check_output(['verdi', 'data', 'core.remote', 'show', '--help'])
        assert b'Usage:' in output, 'Sub-command verdi data core.upf show --help failed.'

    def test_remoteshow(self):
        """Test verdi data core.upf show."""
        options = [str(self.rmt.pk)]
        res = self.cli_runner(cmd_remote.remote_show, options)
        assert res.exit_code == 0, 'The command verdi data core.upf show did not finish correctly'
        assert (
            b'Remote computer name:' in res.stdout_bytes
        ), 'The string "Remote computer name:" was not found in the output of verdi data core.upf show'
        assert (
            b'Remote folder full path:' in res.stdout_bytes
        ), 'The string "Remote folder full path:" was not found in the output of verdi data core.upf show'

    def test_remotelshelp(self):
        output = sp.check_output(['verdi', 'data', 'core.remote', 'ls', '--help'])
        assert b'Usage:' in output, 'Sub-command verdi data core.upf ls --help failed.'

    def test_remotels(self):
        options = ['--long', str(self.rmt.pk)]
        res = self.cli_runner(cmd_remote.remote_ls, options)
        assert res.exit_code == 0, 'The command verdi data core.upf ls did not finish correctly'
        assert b'file.txt' in res.stdout_bytes, (
            'The file "file.txt" was not found in the output' ' of verdi data core.upf ls'
        )

    def test_remotecathelp(self):
        output = sp.check_output(['verdi', 'data', 'core.remote', 'cat', '--help'])
        assert b'Usage:' in output, 'Sub-command verdi data core.upf cat --help failed.'

    def test_remotecat(self):
        options = [str(self.rmt.pk), 'file.txt']
        res = self.cli_runner(cmd_remote.remote_cat, options)
        assert res.exit_code == 0, 'The command verdi data core.upf cat did not finish correctly'
        assert b'test string' in res.stdout_bytes, (
            'The string "test string" was not found in the output' ' of verdi data core.upf cat file.txt'
        )


class TestVerdiDataTrajectory(DummyVerdiDataListable, DummyVerdiDataExportable):
    """Test verdi data core.trajectory."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_profile_clean, aiida_localhost, run_cli_command):
        """Initialize the profile."""
        self.comp = aiida_localhost
        self.this_folder = os.path.dirname(__file__)
        self.this_file = os.path.basename(__file__)
        self.pks = self.create_trajectory_data()
        self.cli_runner = run_cli_command

    @staticmethod
    def create_trajectory_data():
        """Create TrajectoryData object with two arrays."""
        traj = TrajectoryData()

        # I create sample data
        stepids = np.array([60, 70])
        times = stepids * 0.01
        cells = np.array(
            [
                [
                    [
                        2.0,
                        0.0,
                        0.0,
                    ],
                    [
                        0.0,
                        2.0,
                        0.0,
                    ],
                    [
                        0.0,
                        0.0,
                        2.0,
                    ],
                ],
                [
                    [
                        3.0,
                        0.0,
                        0.0,
                    ],
                    [
                        0.0,
                        3.0,
                        0.0,
                    ],
                    [
                        0.0,
                        0.0,
                        3.0,
                    ],
                ],
            ]
        )
        symbols = ['H', 'O', 'C']
        positions = np.array(
            [[[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]], [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]]]
        )
        velocities = np.array(
            [
                [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
                [[0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, -0.5, -0.5]],
            ]
        )

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
            DummyVerdiDataListable.NODE_ID_STR: traj.pk,
            DummyVerdiDataListable.NON_EMPTY_GROUP_ID_STR: g_ne.pk,
            DummyVerdiDataListable.EMPTY_GROUP_ID_STR: g_e.pk,
        }

    def test_showhelp(self):
        res = self.cli_runner(cmd_trajectory.trajectory_show, ['--help'])
        assert b'Usage:' in res.stdout_bytes, (
            'The string "Usage: " was not found in the output' ' of verdi data trajecotry show --help'
        )

    def test_list(self):
        self.data_listing_test(TrajectoryData, str(self.pks[DummyVerdiDataListable.NODE_ID_STR]), self.pks)

    @pytest.mark.skipif(not has_pycifrw(), reason='Unable to import PyCifRW')
    @pytest.mark.parametrize('output_flag', ['-o', '--output'])
    def test_export(self, output_flag, tmp_path):
        new_supported_formats = list(cmd_trajectory.EXPORT_FORMATS)
        self.data_export_test(TrajectoryData, self.pks, new_supported_formats, output_flag, tmp_path)

    @pytest.mark.parametrize(
        'fmt',
        (
            pytest.param(
                'jmol', marks=pytest.mark.skipif(not cmd_show.has_executable('jmol'), reason='No jmol executable.')
            ),
            pytest.param(
                'xcrysden',
                marks=pytest.mark.skipif(not cmd_show.has_executable('xcrysden'), reason='No xcrysden executable.'),
            ),
            pytest.param(
                'mpl_heatmap', marks=pytest.mark.skipif(not has_mayavi(), reason='Package `mayavi` not installed.')
            ),
            pytest.param('mpl_pos'),
        ),
    )
    def test_trajectoryshow(self, fmt, monkeypatch, run_cli_command):
        """Test showing the trajectory data in different formats"""
        trajectory_pk = self.pks[DummyVerdiDataListable.NODE_ID_STR]
        options = ['--format', fmt, str(trajectory_pk), '--dont-block']

        def mock_check_output(options):
            assert isinstance(options, list)
            assert options[0] == fmt

        if fmt in ['jmol', 'xcrysden']:
            # This is called by the ``_show_jmol`` and ``_show_xcrysden`` implementations. We want to test just the
            # function but not the actual commands through a sub process. Note that this mock needs to happen only for
            # these specific formats, because ``matplotlib`` used in the others _also_ calls ``subprocess.check_output``
            monkeypatch.setattr(sp, 'check_output', mock_check_output)

        if fmt in ['mpl_pos']:
            # This has to be mocked because ``plot_positions_xyz`` imports ``matplotlib.pyplot`` and for some completely
            # unknown reason, causes ``tests/storage/psql_dos/test_backend.py::test_unload_profile`` to fail. For some
            # reason, merely importing ``matplotlib`` (even here directly in the test) will cause that test to claim
            # that there still is something holding on to a reference of an sqlalchemy session that it keeps track of
            # in the ``sqlalchemy.orm.session._sessions`` weak ref dictionary. Since it is impossible to figure out why
            # the hell importing matplotlib would interact with sqlalchemy sessions, the function that does the import
            # is simply mocked out for now.
            from aiida.orm.nodes.data.array import trajectory

            monkeypatch.setattr(trajectory, 'plot_positions_XYZ', lambda *args, **kwargs: None)

        run_cli_command(cmd_trajectory.trajectory_show, options, use_subprocess=False)


class TestVerdiDataStructure(DummyVerdiDataListable, DummyVerdiDataExportable):
    """Test verdi data core.structure."""

    from aiida.orm.nodes.data.structure import has_ase  # type: ignore[misc]

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_profile_clean, aiida_localhost, run_cli_command):
        """Initialize the profile."""
        self.comp = aiida_localhost
        self.this_folder = os.path.dirname(__file__)
        self.this_file = os.path.basename(__file__)
        self.pks = self.create_structure_data()
        for group_label in ['xyz structure group', 'ase structure group']:
            Group(label=group_label).store()
        self.cli_runner = run_cli_command

    @staticmethod
    def create_structure_data():
        """Create StructureData object."""
        alat = 4.0  # angstrom
        cell = [
            [
                alat,
                0.0,
                0.0,
            ],
            [
                0.0,
                alat,
                0.0,
            ],
            [
                0.0,
                0.0,
                alat,
            ],
        ]

        # BaTiO3 cubic structure
        struc = StructureData(cell=cell)
        struc.append_atom(position=(0.0, 0.0, 0.0), symbols='Ba')
        struc.append_atom(position=(alat / 2.0, alat / 2.0, alat / 2.0), symbols='Ti')
        struc.append_atom(position=(alat / 2.0, alat / 2.0, 0.0), symbols='O')
        struc.append_atom(position=(alat / 2.0, 0.0, alat / 2.0), symbols='O')
        struc.append_atom(position=(0.0, alat / 2.0, alat / 2.0), symbols='O')
        struc.store()

        # Create 2 groups and add the data to one of them
        g_ne = Group(label='non_empty_group')
        g_ne.store()
        g_ne.add_nodes(struc)

        g_e = Group(label='empty_group')
        g_e.store()

        return {
            DummyVerdiDataListable.NODE_ID_STR: struc.pk,
            DummyVerdiDataListable.NON_EMPTY_GROUP_ID_STR: g_ne.pk,
            DummyVerdiDataListable.EMPTY_GROUP_ID_STR: g_e.pk,
        }

    def test_importhelp(self):
        res = self.cli_runner(cmd_structure.structure_import, ['--help'])
        assert b'Usage:' in res.stdout_bytes, (
            'The string "Usage: " was not found in the output' ' of verdi core.data structure import --help'
        )

    def test_importhelp_ase(self):
        res = self.cli_runner(cmd_structure.import_ase, ['--help'])
        assert b'Usage:' in res.stdout_bytes, (
            'The string "Usage: " was not found in the output' ' of verdi data core.structure import ase --help'
        )

    def test_importhelp_aiida_xyz(self):
        res = self.cli_runner(cmd_structure.import_aiida_xyz, ['--help'])
        assert b'Usage:' in res.stdout_bytes, (
            'The string "Usage: " was not found in the output' ' of verdi data core.structure import aiida-xyz --help'
        )

    def test_import_aiida_xyz(self):
        """Test import xyz file."""
        xyzcontent = """
        2

        Fe     0.0 0.0 0.0
        O      2.0 2.0 2.0
        """
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
            res = self.cli_runner(cmd_structure.import_aiida_xyz, options)
            assert b'Successfully imported' in res.stdout_bytes, (
                'The string "Successfully imported" was not found in the output' ' of verdi data core.structure import.'
            )
            assert b'PK' in res.stdout_bytes, (
                'The string "PK" was not found in the output' ' of verdi data core.structure import.'
            )

    def test_import_aiida_xyz_2(self):
        """Test import xyz file."""
        xyzcontent = """
        2

        Fe     0.0 0.0 0.0
        O      2.0 2.0 2.0
        """
        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            fhandle.write(xyzcontent)
            fhandle.flush()
            options = [
                fhandle.name,
                '-n',  # dry-run
            ]
            res = self.cli_runner(cmd_structure.import_aiida_xyz, options)
            assert b'Successfully imported' in res.stdout_bytes, (
                'The string "Successfully imported" was not found in the output' ' of verdi data core.structure import.'
            )
            assert b'dry-run' in res.stdout_bytes, (
                'The string "dry-run" was not found in the output' ' of verdi data core.structure import.'
            )

    def test_import_aiida_xyz_w_group_label(self):
        """Test import xyz file including setting label and group."""
        xyzcontent = """
        2

        Fe     0.0 0.0 0.0
        O      2.0 2.0 2.0
        """
        group_label = 'xyz structure group'
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
                '--label',
                'a  structure',
                '--group',
                group_label,
            ]
            res = self.cli_runner(cmd_structure.import_aiida_xyz, options)
            assert b'Successfully imported' in res.stdout_bytes, (
                'The string "Successfully imported" was not found in the output' ' of verdi data core.structure import.'
            )
            assert b'PK' in res.stdout_bytes, (
                'The string "PK" was not found in the output' ' of verdi data core.structure import.'
            )
            res = self.cli_runner(cmd_group.group_show, [group_label])
            for grpline in [group_label, 'StructureData']:
                assert grpline in res.output

    @pytest.mark.skipif(not has_ase(), reason='Unable to import ase')
    def test_import_ase(self):
        """Trying to import an xsf file through ase."""
        xsfcontent = """CRYSTAL
PRIMVEC
    2.7100000000    2.7100000000    0.0000000000
    2.7100000000    0.0000000000    2.7100000000
    0.0000000000    2.7100000000    2.7100000000
 PRIMCOORD
           2           1
 16      0.0000000000     0.0000000000     0.0000000000
 30      1.3550000000    -1.3550000000    -1.3550000000
        """
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.xsf') as fhandle:
            fhandle.write(xsfcontent)
            fhandle.flush()
            options = [
                fhandle.name,
            ]
            res = self.cli_runner(cmd_structure.import_ase, options)
            assert b'Successfully imported' in res.stdout_bytes, (
                'The string "Successfully imported" was not found in the output' ' of verdi data core.structure import.'
            )
            assert b'PK' in res.stdout_bytes, (
                'The string "PK" was not found in the output' ' of verdi data core.structure import.'
            )

    @pytest.mark.skipif(not has_ase(), reason='Unable to import ase')
    def test_import_ase_w_group_label(self):
        """Trying to import an xsf file through ase including setting label and group."""
        xsfcontent = """CRYSTAL
PRIMVEC
    2.7100000000    2.7100000000    0.0000000000
    2.7100000000    0.0000000000    2.7100000000
    0.0000000000    2.7100000000    2.7100000000
 PRIMCOORD
           2           1
 16      0.0000000000     0.0000000000     0.0000000000
 30      1.3550000000    -1.3550000000    -1.3550000000
        """
        group_label = 'ase structure group'
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.xsf') as fhandle:
            fhandle.write(xsfcontent)
            fhandle.flush()
            options = [fhandle.name, '--label', 'another  structure', '--group', group_label]
            res = self.cli_runner(cmd_structure.import_ase, options)
            assert b'Successfully imported' in res.stdout_bytes, (
                'The string "Successfully imported" was not found in the output' ' of verdi data core.structure import.'
            )
            assert b'PK' in res.stdout_bytes, (
                'The string "PK" was not found in the output' ' of verdi data core.structure import.'
            )
            res = self.cli_runner(cmd_group.group_show, [group_label])
            for grpline in [group_label, 'StructureData']:
                assert grpline in res.output

    def test_list(self):
        self.data_listing_test(StructureData, 'BaO3Ti', self.pks)

    @pytest.mark.parametrize('output_flag', ['-o', '--output'])
    def test_export(self, output_flag, tmp_path):
        self.data_export_test(StructureData, self.pks, cmd_structure.EXPORT_FORMATS, output_flag, tmp_path)


@pytest.mark.skipif(not has_pycifrw(), reason='Unable to import PyCifRW')
class TestVerdiDataCif(DummyVerdiDataListable, DummyVerdiDataExportable):
    """Test verdi data core.cif."""

    valid_sample_cif_str = """
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
    """

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_profile_clean, aiida_localhost, run_cli_command):
        """Initialize the profile."""
        self.comp = aiida_localhost
        self.this_folder = os.path.dirname(__file__)
        self.this_file = os.path.basename(__file__)
        self.pks = self.create_cif_data()
        self.cli_runner = run_cli_command

    def create_cif_data(self):
        """Create CifData object."""
        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            filename = fhandle.name
            fhandle.write(self.valid_sample_cif_str)
            fhandle.flush()
            a_cif = CifData(file=filename, source={'version': '1234', 'db_name': 'COD', 'id': '0000001'})
            a_cif.store()

            g_ne = Group(label='non_empty_group')
            g_ne.store()
            g_ne.add_nodes(a_cif)

            g_e = Group(label='empty_group')
            g_e.store()

        self.cif = a_cif

        return {
            DummyVerdiDataListable.NODE_ID_STR: a_cif.pk,
            DummyVerdiDataListable.NON_EMPTY_GROUP_ID_STR: g_ne.pk,
            DummyVerdiDataListable.EMPTY_GROUP_ID_STR: g_e.pk,
        }

    def test_list(self):
        """This method tests that the Cif listing works as expected with all
        possible flags and arguments.
        """
        self.data_listing_test(CifData, 'C O2', self.pks)

    def test_showhelp(self):
        options = ['--help']
        res = self.cli_runner(cmd_cif.cif_show, options)
        assert b'Usage:' in res.stdout_bytes, (
            'The string "Usage: " was not found in the output' ' of verdi data show help'
        )

    def test_importhelp(self):
        options = ['--help']
        res = self.cli_runner(cmd_cif.cif_import, options)
        assert b'Usage:' in res.stdout_bytes, (
            'The string "Usage: " was not found in the output' ' of verdi data import help'
        )

    def test_import(self):
        """Test verdi data core.cif import."""
        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            fhandle.write(self.valid_sample_cif_str)
            fhandle.flush()
            options = [fhandle.name]
            res = self.cli_runner(cmd_cif.cif_import, options)
            assert b'imported uuid' in res.stdout_bytes, (
                'The string "imported uuid" was not found in the output' ' of verdi data import.'
            )

    def test_content(self):
        """Test that `verdi data core.cif content` returns the content of the file."""
        options = [str(self.cif.uuid)]
        result = self.cli_runner(cmd_cif.cif_content, options, suppress_warnings=True)

        for line in result.output.split('\n'):
            assert line in self.valid_sample_cif_str

    @pytest.mark.parametrize('output_flag', ['-o', '--output'])
    def test_export(self, output_flag, tmp_path):
        """This method checks if the Cif export works as expected with all
        possible flags and arguments.
        """
        self.data_export_test(CifData, self.pks, cmd_cif.EXPORT_FORMATS, output_flag, tmp_path)


class TestVerdiDataSinglefile(DummyVerdiDataListable, DummyVerdiDataExportable):
    """Test verdi data singlefile."""

    sample_str = """
        data_test
    """

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_profile_clean, aiida_localhost, run_cli_command):
        """Initialize the profile."""
        self.comp = aiida_localhost
        self.this_folder = os.path.dirname(__file__)
        self.this_file = os.path.basename(__file__)
        self.cli_runner = run_cli_command

    def test_content(self):
        """Test that `verdi data singlefile content` returns the content of the file."""
        content = 'abc\ncde'
        singlefile = orm.SinglefileData(file=io.BytesIO(content.encode('utf8'))).store()

        options = [str(singlefile.uuid)]
        result = self.cli_runner(cmd_singlefile.singlefile_content, options, suppress_warnings=True)

        for line in result.output.split('\n'):
            assert line in content


class TestVerdiDataUpf:
    """Testing verdi data core.upf."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_profile_clean, run_cli_command):
        """Initialize the profile."""
        self.filepath_pseudos = os.path.join(STATIC_DIR, 'pseudos')
        self.cli_runner = run_cli_command

    def upload_family(self):
        options = [self.filepath_pseudos, 'test_group', 'test description']
        res = self.cli_runner(cmd_upf.upf_uploadfamily, options)
        assert b'UPF files found: 4' in res.stdout_bytes, (
            'The string "UPF files found: 4" was not found in the' ' output of verdi data core.upf uploadfamily'
        )

    def test_uploadfamilyhelp(self):
        output = sp.check_output(['verdi', 'data', 'core.upf', 'uploadfamily', '--help'])
        assert b'Usage:' in output, f'Sub-command verdi data core.upf uploadfamily --help failed: {output}'

    def test_uploadfamily(self):
        self.upload_family()
        options = [self.filepath_pseudos, 'test_group', 'test description', '--stop-if-existing']
        self.cli_runner(cmd_upf.upf_uploadfamily, options, raises=True)

    def test_exportfamilyhelp(self):
        output = sp.check_output(['verdi', 'data', 'core.upf', 'exportfamily', '--help'])
        assert b'Usage:' in output, 'Sub-command verdi data core.upf exportfamily --help failed.'

    def test_exportfamily(self, tmp_path):
        """Test verdi data core.upf exportfamily."""
        self.upload_family()

        options = [tmp_path, 'test_group']
        self.cli_runner(cmd_upf.upf_exportfamily, options)
        output = sp.check_output(['ls', tmp_path])
        assert (
            b'Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF' in output
        ), f'Sub-command verdi data core.upf exportfamily --help failed: {output}'
        assert (
            b'O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF' in output
        ), 'Sub-command verdi data core.upf exportfamily --help failed.'
        assert (
            b'Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF' in output
        ), 'Sub-command verdi data core.upf exportfamily --help failed.'
        assert b'C_pbe_v1.2.uspp.F.UPF' in output, 'Sub-command verdi data core.upf exportfamily --help failed.'

    def test_listfamilieshelp(self):
        output = sp.check_output(['verdi', 'data', 'core.upf', 'listfamilies', '--help'])
        assert b'Usage:' in output, 'Sub-command verdi data core.upf listfamilies --help failed.'

    def test_listfamilies(self):
        """Test verdi data core.upf listfamilies"""
        self.upload_family()

        options = ['-d', '-e', 'Ba']
        res = self.cli_runner(cmd_upf.upf_listfamilies, options)

        assert (
            b'test_group' in res.stdout_bytes
        ), f'The string "test_group" was not found in the output of verdi data core.upf listfamilies: {res.output}'

        assert b'test description' in res.stdout_bytes, (
            'The string "test_group" was not found in the' ' output of verdi data core.upf listfamilies'
        )

        options = ['-d', '-e', 'Fe']
        res = self.cli_runner(cmd_upf.upf_listfamilies, options)
        assert (
            b'No valid UPF pseudopotential' in res.stdout_bytes
        ), 'The string "No valid UPF pseudopotential" was not found in the output of verdi data core.upf listfamilies'

    def test_importhelp(self):
        output = sp.check_output(['verdi', 'data', 'core.upf', 'import', '--help'])
        assert b'Usage:' in output, 'Sub-command verdi data core.upf listfamilies --help failed.'

    def test_import(self):
        options = [os.path.join(self.filepath_pseudos, 'Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF')]
        res = self.cli_runner(cmd_upf.upf_import, options)

        assert (
            b'Imported' in res.stdout_bytes
        ), f'The string "Imported" was not found in the output of verdi data import: {res.output}'
