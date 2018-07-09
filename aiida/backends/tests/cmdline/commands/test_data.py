import sys
import os
import shutil
import unittest
import tempfile
import numpy as np
import subprocess as sp

from click.testing import CliRunner


from aiida.orm import Computer
from aiida.cmdline.utils import echo
from aiida.orm.group import Group
from aiida.orm.data.array import ArrayData
from aiida.orm.data.array.bands import BandsData
from aiida.orm.data.array.kpoints import KpointsData
from aiida.orm.data.cif import CifData
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.remote import RemoteData
from aiida.orm.data.structure import StructureData
from aiida.orm.data.array.trajectory import TrajectoryData

from aiida.orm.backend import construct_backend
from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.data import array
from aiida.cmdline.commands.data import bands 
from aiida.cmdline.commands.data import cif
from aiida.cmdline.commands.data import parameter
from aiida.cmdline.commands.data import remote
from aiida.cmdline.commands.data import structure
from aiida.cmdline.commands.data import trajectory
from aiida.cmdline.commands.data import upf

from aiida.backends.utils import get_backend_type

if get_backend_type() == 'sqlalchemy':
    from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo
else:
    from aiida.backends.djsite.db.models import DbAuthInfo


from unittest import skip

from aiida.work.workfunctions import workfunction as wf


from contextlib import contextmanager
from StringIO import StringIO

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

    def data_export_test(self, datatype, ids, supported_formats):
        """
        This method tests that the data listing works as expected with all
        possible flags and arguments for different datatypes.
        """

        from aiida.cmdline.commands.data.cif import export as export_cif
        from aiida.cmdline.commands.data.structure import export as export_str
        from aiida.cmdline.commands.data.trajectory import export as export_tr
        # from aiida.cmdline.commands.data.bands import bands_list

        datatype_mapping = {
            CifData: export_cif,
            StructureData: export_str,
            TrajectoryData: export_tr,
            # BandsData: bands_list
        }

        if datatype is None or datatype not in datatype_mapping.keys():
            raise Exception("The listing of the objects {} is not supported"
                            .format(datatype))

        export_cmd = datatype_mapping[datatype]

        # Check that the simple command works as expected
        options = [str(ids[self.NODE_ID_STR])]
        res = self.cli_runner.invoke(export_cmd, options,
                                     catch_exceptions=False)
        self.assertEquals(res.exit_code, 0, "The command did not finish "
                                            "correctly")

        # Check that you can export the various formats
        # TODO: Why do we also have tcod_parameters as export format?
        dump_flags = ['-y', '--format']
        for flag in dump_flags:
            for format in supported_formats:
                # with captured_output() as (out, err):
                options = [flag, format, str(ids[self.NODE_ID_STR])]
                res = self.cli_runner.invoke(export_cmd, options,
                                             catch_exceptions=False)
                self.assertEquals(res.exit_code, 0,
                                  "The command did not finish "
                                  "correctly")


        # The --parameter-data flag is not implemented and it should fail
        options = ['--parameter-data', '0', str(ids[self.NODE_ID_STR])]
        res = self.cli_runner.invoke(export_cmd, options,
                                     catch_exceptions=False)
        self.assertNotEquals(res.exit_code, 0,
                          "The command should not finish correctly and"
                          "return normal termination exit status.")

        # The following flags fail.
        # We have to see why. The --reduce-symmetry seems to work in
        # the original code. The other one not.
        symmetry_flags = ['--reduce-symmetry', '--no-reduce-symmetry']
        for flag in symmetry_flags:
            options = [flag, str(ids[self.NODE_ID_STR])]
            res = self.cli_runner.invoke(export_cmd, options,
                                         catch_exceptions=False)
            self.assertNotEquals(res.exit_code, 0,
                              "The command should not finish correctly and"
                              "return normal termination exit status.")


        # The following two flags are not implemented and should return
        # an error:
        # --dump-aiida-database / --no-dump-aiida-database
        dump_flags = ['--dump-aiida-database' , '--no-dump-aiida-database']
        for flag in dump_flags:
            options = [flag, str(ids[self.NODE_ID_STR])]
            res = self.cli_runner.invoke(export_cmd, options,
                                         catch_exceptions=False)
            self.assertNotEquals(res.exit_code, 0,
                              "The command should not finish correctly and"
                              "return normal termination exit status.")


        # The following two flags are not implemented and should return
        # an error:
        # --exclude-external-contents / --no-exclude-external-contents
        external_cont_flags = ['--exclude-external-contents' ,
                               '--no-exclude-external-contents']
        for flag in external_cont_flags:
            options = [flag, str(ids[self.NODE_ID_STR])]
            res = self.cli_runner.invoke(export_cmd, options,
                                         catch_exceptions=False)
            self.assertNotEquals(res.exit_code, 0,
                              "The command should not finish correctly and"
                              "return normal termination exit status.")


        # The following two flags are not implemented and should return
        # an error:
        # --gzip / --no-gzip
        gzip_flags = ['--gzip' , '--no-gzip']
        for flag in gzip_flags:
            options = [flag, str(ids[self.NODE_ID_STR])]
            res = self.cli_runner.invoke(export_cmd, options,
                                         catch_exceptions=False)

            self.assertNotEquals(res.exit_code, 0,
                              "The command should not finish correctly and"
                              "return normal termination exit status.")

        # The --gzip-threshold flag is not implemented and it should fail
        options = ['--gzip-threshold', '1', str(ids[self.NODE_ID_STR])]
        res = self.cli_runner.invoke(export_cmd, options,
                                     catch_exceptions=False)
        self.assertNotEquals(res.exit_code, 0,
                          "The command should not finish correctly and"
                          "return normal termination exit status.")

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
                self.assertEquals(res.exit_code, 0,
                                     "The command should finish correctly."
                                     "Output: {}".format(res.output_bytes))

                # Try to export it again. It should fail because the
                # file exists
                res = self.cli_runner.invoke(export_cmd, options,
                                             catch_exceptions=False)
                self.assertNotEquals(res.exit_code, 0,
                                     "The command should fail because the "
                                     "file already exists")

                # Now we force the export of the file and it should overwrite
                # existing files
                options = [flag, filepath, '-f', str(ids[self.NODE_ID_STR])]
                res = self.cli_runner.invoke(export_cmd, options,
                                             catch_exceptions=False)
                self.assertEquals(res.exit_code, 0,
                                     "The command should finish correctly."
                                     "Output: {}".format(res.output_bytes))
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

        from aiida.cmdline.commands.data.cif import cif_list
        from aiida.cmdline.commands.data.structure import list_structures
        from aiida.cmdline.commands.data.trajectory import list_trajections
        from aiida.cmdline.commands.data.bands import bands_list

        from aiida.cmdline.commands.data.structure import project_headers as p_str
        from aiida.cmdline.commands.data.cif import project_headers as p_cif
        from aiida.cmdline.commands.data.trajectory import project_headers as p_tr
        from aiida.cmdline.commands.data.bands import project_headers as p_bands

        headers_mapping = {
            CifData: p_cif,
            StructureData: p_str,
            TrajectoryData: p_tr,
            BandsData: p_bands
        }

        datatype_mapping = {
            CifData: cif_list,
            StructureData: list_structures,
            TrajectoryData: list_trajections,
            BandsData: bands_list
        }

        if datatype is None or datatype not in datatype_mapping.keys():
            raise Exception("The listing of the objects {} is not supported"
                            .format(datatype))

        listing_cmd = datatype_mapping[datatype]
        project_headers = headers_mapping[datatype]

        # Check that the normal listing works as expected
        res = self.cli_runner.invoke(listing_cmd, [],
                                     catch_exceptions=False)
        self.assertIn(search_string, res.output_bytes,
                      'The string {} was not found in the listing'
                      .format(search_string))

        # Check that the past days filter works as expected
        past_days_flags = ['-p', '--past-days']
        # past_days_flags = ['-p']
        for flag in past_days_flags:
            options = [flag, '1']
            res = self.cli_runner.invoke(listing_cmd, options,
                                         catch_exceptions=False)
            self.assertIn(search_string, res.output_bytes,
                          'The string {} was not found in the listing'
                          .format(search_string))

            options = [flag, '0']
            res = self.cli_runner.invoke(listing_cmd, options,
                                         catch_exceptions=False)
            self.assertNotIn(search_string, res.output_bytes,
                          'A not expected string {} was found in the listing'
                          .format(search_string))

        # Check that the group filter works as expected
        group_flags = ['-G', '--groups']
        for flag in group_flags:
            # Non empty group
            for non_empty in [self.NON_EMPTY_GROUP_NAME_STR,
                              str(ids[self.NON_EMPTY_GROUP_ID_STR])]:
                options = [flag, non_empty]
                res = self.cli_runner.invoke(listing_cmd, options,
                                             catch_exceptions=False)
                self.assertIn(search_string, res.output_bytes,
                              'The string {} was not found in the listing')

            # Empty group
            for empty in [self.EMPTY_GROUP_NAME_STR,
                          str(ids[self.EMPTY_GROUP_ID_STR])]:
                options = [flag, empty]
                res = self.cli_runner.invoke(listing_cmd, options,
                                             catch_exceptions=False)
                self.assertNotIn(
                    search_string, res.output_bytes,
                    'A not expected string {} was found in the listing')

            # Group combination
            for non_empty in [self.NON_EMPTY_GROUP_NAME_STR,
                              str(ids[self.NON_EMPTY_GROUP_ID_STR])]:
                for empty in [self.EMPTY_GROUP_NAME_STR,
                          str(ids[self.EMPTY_GROUP_ID_STR])]:
                    options = [flag, non_empty, empty]
                    res = self.cli_runner.invoke(listing_cmd, options,
                                                 catch_exceptions=False)
                    self.assertIn(search_string, res.output_bytes,
                                  'The string {} was not found in the listing')

        # Check raw flag
        raw_flags = ['-r', '--raw']
        for flag in raw_flags:
            options = [flag]
            res = self.cli_runner.invoke(listing_cmd, options,
                                         catch_exceptions=False)
            for header in project_headers:
                self.assertNotIn(header, res.output_bytes)

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
        subcommands = ['array', 'bands', 'cif', 'parameter', 'remote',
                'structure', 'trajectory', 'upf']
        for sub_cmd in subcommands:
            output = sp.check_output(['verdi', 'data', sub_cmd, '--help'])
            self.assertIn(
                'Usage:', output,
                "Sub-command verdi data {} --help failed.". format(sub_cmd))

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
        self.assertIn(
            'Usage:', output,
            "Sub-command verdi data array show --help failed.")

    def test_arrayshow(self):
        dump_flags = ['-f', '--format']
        supported_formats = ['json_date']
        for flag in dump_flags:
            for format in supported_formats:
                # with captured_output() as (out, err):
                options = [flag, format, str(self.a.id)]
                res = self.cli_runner.invoke(array.show, options,
                                             catch_exceptions=False)
                self.assertEquals(res.exit_code, 0,
                                  "The command did not finish "
                                  "correctly")

class TestVerdiDataBands(AiidaTestCase, TestVerdiDataListable):
    """
    Testing verdi data bands 
    """

    @staticmethod
    def create_structure_bands():
        alat = 4.  # angstrom
        cell = [[alat, 0., 0., ],
                [0., alat, 0., ],
                [0., 0., alat, ],
                ]
        s = StructureData(cell=cell)
        s.append_atom(position=(0., 0., 0.), symbols='Fe')
        s.append_atom(position=(alat / 2., alat / 2., alat / 2.), symbols='O')
        s.store()

        @wf
        def connect_structure_bands(structure):
            alat = 4.
            cell = np.array([[alat, 0., 0.],
                             [0., alat, 0.],
                             [0., 0., alat],
                             ])

            k = KpointsData()
            k.set_cell(cell)
            k.set_kpoints_path([('G', 'M', 2)])

            b = BandsData()
            b.set_kpointsdata(k)
            b.set_bands([[1.0, 2.0], [3.0, 4.0]])

            k.store()
            b.store()

            return b

        b = connect_structure_bands(s)

        # Create 2 groups and add the data to one of them
        g_ne = Group(name='non_empty_group')
        g_ne.store()
        g_ne.add_nodes(b)

        g_e = Group(name='empty_group')
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
        self.assertIn(
            'Usage:', output,
            "Sub-command verdi data bands show --help failed.")
    
    def test_bandlistshelp(self):
        output = sp.check_output(['verdi', 'data', 'bands', 'list', '--help'])
        self.assertIn(
            'Usage:', output,
            "Sub-command verdi data bands show --help failed.")

    def test_bandslist(self):
        from aiida.orm.data.array.bands import BandsData

        self.data_listing_test(BandsData, 'FeO', self.ids)


    def test_bandexporthelp(self):
        output = sp.check_output(['verdi', 'data', 'bands', 'export', '--help'])
        self.assertIn(
            'Usage:', output,
            "Sub-command verdi data bands export --help failed.")

    def test_bandsexport(self):
        options = [str(self.ids[TestVerdiDataListable.NODE_ID_STR])]
        res = self.cli_runner.invoke(bands.export, options, 
                                     catch_exceptions=False)
        self.assertEquals(res.exit_code, 0,
                          "The command did not finish "
                          "correctly")
        self.assertIn("[1.0, 3.0]", res.output_bytes,
                      'The string [1.0, 3.0] was not found in the bands'
                      'export')

class TestVerdiDataParameter(AiidaTestCase):
    """
    Testing verdi data parameter 
    """
    @classmethod
    def setUpClass(cls):
        super(TestVerdiDataParameter, cls).setUpClass()

    def setUp(self):
        self.p = ParameterData()
        self.p.set_dict({'a':1, 'b':2})
        self.p.store()

        self.cli_runner = CliRunner()

    def test_parametershowhelp(self):
        output = sp.check_output(['verdi', 'data', 'parameter', 'show', '--help'])
        self.assertIn(
            'Usage:', output,
            "Sub-command verdi data parameter show --help failed.")

    def test_parametershow(self):
        supported_formats = ['json_date']
        for format in supported_formats:
            options = ['--format', format, str(self.p.id)]
            res = self.cli_runner.invoke(parameter.show, options,
                                         catch_exceptions=False)
            self.assertEquals(res.exit_code, 0,
                              "The command verdi data parameter show did not"
                              " finish correctly")
        self.assertIn('"a": 1', res.output_bytes,
                      'The string "a": 1 was not found in the output'
                      ' of verdi data parameter show')

class TestVerdiDataRemote(AiidaTestCase):
    """
    Testing verdi data remote 
    """
    @classmethod
    def setUpClass(cls):
        super(TestVerdiDataRemote, cls).setUpClass()
        new_comp = Computer(name='comp',
                            hostname='localhost',
                            transport_type='local',
                            scheduler_type='direct',
                            workdir=tempfile.mkdtemp())
        new_comp.store()
        b = construct_backend()
        aiidauser = b.users.get_automatic_user()
        authinfo = DbAuthInfo(dbcomputer=new_comp.dbcomputer,
                aiidauser=aiidauser.dbuser)
        authinfo.save()

    def setUp(self):
        comp = Computer.get('comp')
        self.r = RemoteData()
        p = tempfile.mkdtemp()
        self.r.set_remote_path(p)
        with open(p+'/file.txt', 'w') as f:
            f.write("test string")
        self.r.set_computer(comp)
        self.r.store()

        self.cli_runner = CliRunner()

    def test_remoteshowhelp(self):
        output = sp.check_output(['verdi', 'data', 'remote', 'show', '--help'])
        self.assertIn(
            'Usage:', output,
            "Sub-command verdi data remote show --help failed.")

    def test_remoteshow(self):
        options = [str(self.r.id)]
        res = self.cli_runner.invoke(remote.show, options,
                                     catch_exceptions=False)
        self.assertEquals(res.exit_code, 0,
                          "The command verdi data remote show did not"
                          " finish correctly")
        self.assertIn('Remote computer name:', res.output_bytes,
                      'The string "Remote computer name:" was not found in the'
                      ' output of verdi data remote show')
        self.assertIn('Remote folder full path:', res.output_bytes,
                      'The string "Remote folder full path:" was not found in the'
                      ' output of verdi data remote show')
    
    def test_remotelshelp(self):
        output = sp.check_output(['verdi', 'data', 'remote', 'ls', '--help'])
        self.assertIn(
            'Usage:', output,
            "Sub-command verdi data remote ls --help failed.")

    def test_remotels(self):
        options = ['--long', str(self.r.id)]
        res = self.cli_runner.invoke(remote.ls, options,
                                     catch_exceptions=False)
        self.assertEquals(res.exit_code, 0,
                          "The command verdi data remote ls did not"
                          " finish correctly")
        self.assertIn('file.txt', res.output_bytes,
                      'The file "file.txt" was not found in the output'
                      ' of verdi data remote ls')

    def test_remotecathelp(self):
        output = sp.check_output(['verdi', 'data', 'remote', 'cat', '--help'])
        self.assertIn(
            'Usage:', output,
            "Sub-command verdi data remote cat --help failed.")

    def test_remotecat(self):
        options = [str(self.r.id), 'file.txt']
        res = self.cli_runner.invoke(remote.cat, options,
                                     catch_exceptions=False)
        self.assertEquals(res.exit_code, 0,
                          "The command verdi data parameter cat did not"
                          " finish correctly")
        self.assertIn('test string', res.output_bytes,
                      'The string "test string" was not found in the output'
                      ' of verdi data remote cat file.txt')


class TestVerdiDataTrajectory(AiidaTestCase, TestVerdiDataListable,
                              TestVerdiDataExportable):

    @staticmethod
    def create_trajectory_data():
        from aiida.orm.data.array.trajectory import TrajectoryData
        from aiida.orm.group import Group
        import numpy

        # Create a node with two arrays
        n = TrajectoryData()

        # I create sample data
        stepids = numpy.array([60, 70])
        times = stepids * 0.01
        cells = numpy.array([
            [[2., 0., 0., ],
             [0., 2., 0., ],
             [0., 0., 2., ]],
            [[3., 0., 0., ],
             [0., 3., 0., ],
             [0., 0., 3., ]]])
        symbols = numpy.array(['H', 'O', 'C'])
        positions = numpy.array([
            [[0., 0., 0.],
             [0.5, 0.5, 0.5],
             [1.5, 1.5, 1.5]],
            [[0., 0., 0.],
             [0.5, 0.5, 0.5],
             [1.5, 1.5, 1.5]]])
        velocities = numpy.array([
            [[0., 0., 0.],
             [0., 0., 0.],
             [0., 0., 0.]],
            [[0.5, 0.5, 0.5],
             [0.5, 0.5, 0.5],
             [-0.5, -0.5, -0.5]]])

        # I set the node
        n.set_trajectory(stepids=stepids, cells=cells, symbols=symbols,
                         positions=positions, times=times,
                         velocities=velocities)

        n.store()

        # Create 2 groups and add the data to one of them
        g_ne = Group(name='non_empty_group')
        g_ne.store()
        g_ne.add_nodes(n)

        g_e = Group(name='empty_group')
        g_e.store()

        return {
            TestVerdiDataListable.NODE_ID_STR: n.id,
            TestVerdiDataListable.NON_EMPTY_GROUP_ID_STR: g_ne.id,
            TestVerdiDataListable.EMPTY_GROUP_ID_STR: g_e.id
        }

    @classmethod
    def setUpClass(cls):
        super(TestVerdiDataTrajectory, cls).setUpClass()
        new_comp = Computer(name='comp',
                                hostname='localhost',
                                transport_type='local',
                                scheduler_type='direct',
                                workdir='/tmp/aiida')
        new_comp.store()
        cls.ids = cls.create_trajectory_data()

    def setUp(self):
        self.comp = Computer.get('comp')
        self.runner = CliRunner()
        self.this_folder = os.path.dirname(__file__)
        self.this_file = os.path.basename(__file__)

        self.cli_runner = CliRunner()

    def test_help(self):
        self.runner.invoke(trajectory, ['--help'])

    def test_data_trajectory_list(self):
        self.data_listing_test(
            TrajectoryData, str(self.ids[TestVerdiDataListable.NODE_ID_STR]),
            self.ids)

    def test_data_trajectory_export(self):
        from aiida.cmdline.commands.data.trajectory import supported_formats
        new_supported_formats = list(supported_formats)
        # TCOD export needs special arguments
        new_supported_formats.remove('tcod')
        self.data_export_test(TrajectoryData, self.ids, new_supported_formats)


class TestVerdiDataStructure(AiidaTestCase, TestVerdiDataListable,
                             TestVerdiDataExportable):

    @staticmethod
    def create_structure_data():
        from aiida.orm.data.structure import StructureData, Site, Kind
        from aiida.orm.group import Group

        alat = 4.  # angstrom
        cell = [[alat, 0., 0., ],
                [0., alat, 0., ],
                [0., 0., alat, ],
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
        g_ne = Group(name='non_empty_group')
        g_ne.store()
        g_ne.add_nodes(struc)

        g_e = Group(name='empty_group')
        g_e.store()

        return {
            TestVerdiDataListable.NODE_ID_STR: struc.id,
            TestVerdiDataListable.NON_EMPTY_GROUP_ID_STR: g_ne.id,
            TestVerdiDataListable.EMPTY_GROUP_ID_STR: g_e.id
        }

    @classmethod
    def setUpClass(cls):
        super(TestVerdiDataStructure, cls).setUpClass()
        from aiida.orm import Computer
        new_comp = Computer(name='comp',
                                hostname='localhost',
                                transport_type='local',
                                scheduler_type='direct',
                                workdir='/tmp/aiida')
        new_comp.store()
        cls.ids = cls.create_structure_data()

    def setUp(self):
        from aiida.orm import Computer
        self.comp = Computer.get('comp')
        self.runner = CliRunner()
        self.this_folder = os.path.dirname(__file__)
        self.this_file = os.path.basename(__file__)

        self.cli_runner = CliRunner()

    def test_help(self):
        self.runner.invoke(cif, ['--help'])

    def test_data_structure_list(self):
        self.data_listing_test(StructureData, 'BaO3Ti', self.ids)

    def test_data_structure_export(self):
        from aiida.cmdline.commands.data.structure import supported_formats
        self.data_export_test(StructureData, self.ids, supported_formats)


class TestVerdiDataCif(AiidaTestCase, TestVerdiDataListable):

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

    def create_cif_data(self):
        with tempfile.NamedTemporaryFile() as f:
            filename = f.name
            f.write(self.valid_sample_cif_str)
            f.flush()
            a = CifData(file=filename,
                        source={'version': '1234',
                                'db_name': 'COD',
                                'id': '0000001'})
            a.store()

            g_ne = Group(name='non_empty_group')
            g_ne.store()
            g_ne.add_nodes(a)

            g_e = Group(name='empty_group')
            g_e.store()

        return {
            TestVerdiDataListable.NODE_ID_STR: a.id,
            TestVerdiDataListable.NON_EMPTY_GROUP_ID_STR: g_ne.id,
            TestVerdiDataListable.EMPTY_GROUP_ID_STR: g_e.id
        }


    @classmethod
    def setUpClass(cls):
        super(TestVerdiDataCif, cls).setUpClass()
        new_comp = Computer(name='comp',
                                hostname='localhost',
                                transport_type='local',
                                scheduler_type='direct',
                                workdir='/tmp/aiida')
        new_comp.store()

    def setUp(self):
        self.comp = Computer.get('comp')
        self.runner = CliRunner()
        self.this_folder = os.path.dirname(__file__)
        self.this_file = os.path.basename(__file__)

        self.cli_runner = CliRunner()

    @skip("")
    def test_help(self):
        self.runner.invoke(cif, ['--help'])

    def test_data_cif_list(self):
        """
        This method tests that the Cif listing works as expected with all
        possible flags and arguments.
        """
        from aiida.orm.data.cif import CifData

        ids = self.create_cif_data()
        self.data_listing_test(CifData, 'C O2', ids)

    @skip("")
    def test_data_cif_import(self):
        """
        This method tests that the Cif import works as expected with all
        possible flags and arguments.
        """
        # Check format flag
        format_flags = ['-f', '--format']
        for flag in format_flags:
            #  Check invalid format
            self.assertRaises(
                Exception, sp.check_output,
                ['verdi', 'data', 'cif', 'import', flag, 'not_supported'],
                stderr=sp.STDOUT)

        # Check that a file is parsed correctly if passed as an argument
        format_flags = ['-f', '--format']
        for flag in format_flags:
            file_content = "data_test _cell_length_a 10(1)"

            # Check that you can load a Cif from a file.
            # with captured_output() as (out, err):
            with tempfile.NamedTemporaryFile() as f:
                f.write(file_content)
                f.flush()
                sp.check_call(
                    ['verdi', 'data', 'cif', 'import', flag,
                     'cif', '--file', f.name])

                # Check that you can load a Cif from STDIN
                sp.check_call(
                    ['verdi', 'data', 'cif', 'import', flag,
                     'cif', '--file', f.name], stdin=f)

    def test_data_cif_export(self):
        """
        This method checks if the Cif export works as expected with all
        possible flags and arguments.
        """

        # Create a valid CifNode
        with tempfile.NamedTemporaryFile() as f:
            filename = f.name
            f.write(self.valid_sample_cif_str)
            f.flush()
            a = CifData(file=filename,
                        source={'version': '1234',
                                'db_name': 'COD',
                                'id': '0000001'})
            a.store()

        # Check that the simple command works as expected
        options = [str(a.id)]
        res = self.cli_runner.invoke(cif.export, options,
                                     catch_exceptions=False)
        self.assertEquals(res.exit_code, 0, "The command did not finish "
                                            "correctly")

        # Check that you can export the various formats
        # TODO: Why do we also have tcod_parameters as export format?
        dump_flags = ['-y', '--format']
        supported_formats = ['cif', 'tcod']
        for flag in dump_flags:
            for format in supported_formats:
                # with captured_output() as (out, err):
                options = [flag, format, str(a.id)]
                res = self.cli_runner.invoke(cif.export, options,
                                             catch_exceptions=False)
                self.assertEquals(res.exit_code, 0,
                                  "The command did not finish "
                                  "correctly")


        # The --parameter-data flag is not implemented and it should fail
        options = ['--parameter-data', '0', str(a.id)]
        res = self.cli_runner.invoke(cif.export, options,
                                     catch_exceptions=False)
        self.assertNotEquals(res.exit_code, 0,
                          "The command should not finish correctly and"
                          "return normal termination exit status.")

        # The following flags fail.
        # We have to see why. The --reduce-symmetry seems to work in
        # the original code. The other one not.
        symmetry_flags = ['--reduce-symmetry', '--no-reduce-symmetry']
        for flag in symmetry_flags:
            options = [flag, str(a.id)]
            res = self.cli_runner.invoke(cif.export, options,
                                         catch_exceptions=False)
            self.assertNotEquals(res.exit_code, 0,
                              "The command should not finish correctly and"
                              "return normal termination exit status.")


        # The following two flags are not implemented and should return
        # an error:
        # --dump-aiida-database / --no-dump-aiida-database
        dump_flags = ['--dump-aiida-database' , '--no-dump-aiida-database']
        for flag in dump_flags:
            options = [flag, str(a.id)]
            res = self.cli_runner.invoke(cif.export, options,
                                         catch_exceptions=False)
            self.assertNotEquals(res.exit_code, 0,
                              "The command should not finish correctly and"
                              "return normal termination exit status.")


        # The following two flags are not implemented and should return
        # an error:
        # --exclude-external-contents / --no-exclude-external-contents
        external_cont_flags = ['--exclude-external-contents' ,
                               '--no-exclude-external-contents']
        for flag in external_cont_flags:
            options = [flag, str(a.id)]
            res = self.cli_runner.invoke(cif.export, options,
                                         catch_exceptions=False)
            self.assertNotEquals(res.exit_code, 0,
                              "The command should not finish correctly and"
                              "return normal termination exit status.")


        # The following two flags are not implemented and should return
        # an error:
        # --gzip / --no-gzip
        gzip_flags = ['--gzip' , '--no-gzip']
        for flag in gzip_flags:
            options = [flag, str(a.id)]
            res = self.cli_runner.invoke(cif.export, options,
                                         catch_exceptions=False)

            self.assertNotEquals(res.exit_code, 0,
                              "The command should not finish correctly and"
                              "return normal termination exit status.")

        # The --gzip-threshold flag is not implemented and it should fail
        options = ['--gzip-threshold', '1', str(a.id)]
        res = self.cli_runner.invoke(cif.export, options,
                                     catch_exceptions=False)
        self.assertNotEquals(res.exit_code, 0,
                          "The command should not finish correctly and"
                          "return normal termination exit status.")

        # Check that the output to file flags work correctly:
        # -o, --output
        output_flags = ['-o', '--output']
        for flag in output_flags:
            try:
                tmpd = tempfile.mkdtemp()
                filepath = os.path.join(tmpd, 'output_file.txt')
                options = [flag, filepath, str(a.id)]
                res = self.cli_runner.invoke(cif.export, options,
                                             catch_exceptions=False)
                self.assertEquals(res.exit_code, 0,
                                     "The command should finish correctly."
                                     "Output: {}".format(res.output_bytes))

                # Check that the file contents are correct
                with file(filepath) as f:
                    s = f.read()
                    self.assertEquals(s, self.valid_sample_cif_str,
                                      "The stored data are not the expected.")

                # Try to export it again. It should fail because the
                # file exists
                res = self.cli_runner.invoke(cif.export, options,
                                             catch_exceptions=False)
                self.assertNotEquals(res.exit_code, 0,
                                     "The command should fail because the "
                                     "file already exists")

                # Now we force the export of the file and it should overwrite
                # existing files
                options = [flag, filepath, '-f', str(a.id)]
                res = self.cli_runner.invoke(cif.export, options,
                                             catch_exceptions=False)
                self.assertEquals(res.exit_code, 0,
                                     "The command should finish correctly."
                                     "Output: {}".format(res.output_bytes))

                # Check that the file contents are correct
                with file(filepath) as f:
                    s = f.read()
                    self.assertEquals(s, self.valid_sample_cif_str,
                                      "The stored data are not the expected.")


            finally:
                shutil.rmtree(tmpd)

class TestVerdiDataUpf(AiidaTestCase):
    """
    Testing verdi data upf
    """
    @classmethod
    def setUpClass(cls):
        super(TestVerdiDataUpf, cls).setUpClass()

    def setUp(self):
        self.this_folder = os.path.dirname(__file__)
        self.this_file = os.path.basename(__file__)
        self.pseudos_dir = "../../../../../examples/testdata/qepseudos/"

        self.cli_runner = CliRunner()

    def upload_family(self):
        options = [self.this_folder+'/'+self.pseudos_dir,
                "test_group",
                "test description"]
        res = self.cli_runner.invoke(upf.uploadfamily, options,
                                     catch_exceptions=False)
        self.assertIn('UPF files found: 3', res.output_bytes,
                      'The string "UPF files found: 3" was not found in the'
                      ' output of verdi data upf uploadfamily')

    
    def test_uploadfamilyhelp(self):
        output = sp.check_output(['verdi', 'data', 'upf', 'uploadfamily', '--help'])
        self.assertIn(
            'Usage:', output,
            "Sub-command verdi data upf uploadfamily --help failed.")

    def test_uploadfamily(self):
        self.upload_family()
        options = [self.this_folder+'/'+self.pseudos_dir,
                "test_group",
                "test description",
                "--stop-if-existing"]
        with self.assertRaises(ValueError):
            res = self.cli_runner.invoke(upf.uploadfamily, options,
                                         catch_exceptions=False)


    def test_exportfamilyhelp(self):
        output = sp.check_output(['verdi', 'data', 'upf', 'exportfamily', '--help'])
        self.assertIn(
            'Usage:', output,
            "Sub-command verdi data upf exportfamily --help failed.")


    def test_exportfamily(self):
        self.upload_family()
        
        p = tempfile.mkdtemp()
        options = [p, 'test_group']
        res = self.cli_runner.invoke(upf.exportfamily, options,
                                     catch_exceptions=False)
        output = sp.check_output(['ls', p ])
        self.assertIn(
            'Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF', output,
            "Sub-command verdi data upf exportfamily --help failed.")
        self.assertIn(
            'O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF', output,
            "Sub-command verdi data upf exportfamily --help failed.")
        self.assertIn(
            'Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF', output,
            "Sub-command verdi data upf exportfamily --help failed.")


    def test_listfamilieshelp(self):
        output = sp.check_output(['verdi', 'data', 'upf', 'listfamilies', '--help'])
        self.assertIn(
            'Usage:', output,
            "Sub-command verdi data upf listfamilies --help failed.")

    def test_listfamilies(self):
        self.upload_family()

        options = ['-d', '-e', 'Ba']
        res = self.cli_runner.invoke(upf.listfamilies, options,
                                     catch_exceptions=False)
        
        self.assertIn('test_group', res.output_bytes,
                      'The string "test_group" was not found in the'
                      ' output of verdi data upf listfamilies')

        self.assertIn('test description', res.output_bytes,
                      'The string "test_group" was not found in the'
                      ' output of verdi data upf listfamilies')
        
        
        options = ['-d', '-e', 'Fe']
        res = self.cli_runner.invoke(upf.listfamilies, options,
                                     catch_exceptions=False)
        self.assertIn('No valid UPF pseudopotential', res.output_bytes,
                      'The string "No valid UPF pseudopotential" was not'
                      ' found in the output of verdi data upf listfamilies')
    def test_importhelp(self):
        output = sp.check_output(['verdi', 'data', 'upf', 'import', '--help'])
        self.assertIn(
            'Usage:', output,
            "Sub-command verdi data upf listfamilies --help failed.")
    def test_import(self):
        options = [self.this_folder + '/'+self.pseudos_dir + '/' +
                'Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF',
                '--format',
                'upf']
        res = self.cli_runner.invoke(upf.import_upf, options,
                                     catch_exceptions=False)

        self.assertIn('Imported', res.output_bytes,
                      'The string "Imported" was not'
                      ' found in the output of verdi data import' )
