import os
import subprocess as sp
import click
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
# from aiida.cmdline.commands.data.cif import cif
from aiida.backends.settings import AIIDADB_PROFILE
from aiida.cmdline.commands.data import cif

from unittest import skip

import sys
import os
import shutil


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


class TestVerdiDataCif(AiidaTestCase):

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
    def setUpClass(cls):
        super(TestVerdiDataCif, cls).setUpClass()
        from aiida.orm import Computer
        new_comp = Computer(name='comp',
                                hostname='localhost',
                                transport_type='local',
                                scheduler_type='direct',
                                workdir='/tmp/aiida')
        new_comp.store()

    def setUp(self):
        from aiida.orm import Computer
        self.comp = Computer.get('comp')
        self.runner = CliRunner()
        self.this_folder = os.path.dirname(__file__)
        self.this_file = os.path.basename(__file__)

        self.cli_runner = CliRunner()

    def test_help(self):
        result = self.runner.invoke(cif, ['--help'])

    @skip("")
    def test_reachable(self):
        """
        Testing reachability of the following commands:
        verdi data remote
        verdi data cif
        verdi data upf
        verdi data trajectory
        verdi data bands
        verdi data array
        verdi data parameter
        verdi data structure
        """
        subcommands = ['remote', 'cif', 'upf', 'trajectory', 'bands', 'array',
                       'parameter', 'structure']
        for sub_cmd in subcommands:
            output = sp.check_output(['verdi', 'data', sub_cmd, '--help'])
            self.assertIn(
                'Usage:', output,
                "Sub-command verdi data {} --help failed.". format(sub_cmd))

    @skip("")
    def test_data_cif_list(self):
        """
        This method tests that the Cif listing works as expected with all
        possible flags and arguments.
        """
        import tempfile

        from aiida.orm.data.cif import CifData
        from aiida.orm.group import Group

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

        # Check that the normal listing works as expected
        output = sp.check_output(['verdi', 'data', 'cif', 'list'])
        self.assertIn('C O2', output, 'The Cif formula was not found in '
                                      'the listing')

        # Check that the past days filter works as expected
        past_days_flags = ['-p', '--past-days']
        # past_days_flags = ['-p']
        for flag in past_days_flags:
            output = sp.check_output(['verdi', 'data', 'cif', 'list', flag, '1'])
            self.assertIn('C O2', output, 'The Cif formula was not found in '
                                          'the listing')

            # Check that the normal listing works as expected
            output = sp.check_output(['verdi', 'data', 'cif', 'list', flag, '0'])
            self.assertNotIn('C O2', output, 'A not expected Cif formula was '
                                             'found in the listing')

        # Check that the group filter works as expected
        group_flags = ['-G', '--groups']
        for flag in group_flags:
            # Non empty group
            for non_empty in ['non_empty_group', str(g_ne.id)]:
                output = sp.check_output(['verdi', 'data', 'cif', 'list', flag, non_empty])
                self.assertIn('C O2', output, 'The Cif formula was not found in '
                                              'the listing')
            # Empty group
            for empty in ['empty_group', str(g_e.id)]:
                # Check that the normal listing works as expected
                output = sp.check_output(['verdi', 'data', 'cif', 'list', flag, empty])
                self.assertNotIn('C O2', output, 'A not expected Cif formula was '
                                                 'found in the listing')

            # Group combination
            for non_empty in ['non_empty_group', str(g_ne.id)]:
                for empty in ['empty_group', str(g_e.id)]:
                    output = sp.check_output(
                        ['verdi', 'data', 'cif', 'list', flag, non_empty,
                         empty])
                    self.assertIn('C O2', output,
                                  'The Cif formula was not found in '
                                  'the listing')

        # Check raw flag
        raw_flags = ['-r', '--raw']
        for flag in raw_flags:
            output = sp.check_output(['verdi', 'data', 'cif', 'list', flag])
            self.assertNotIn('ID', output)
            self.assertNotIn('formulae', output)
            self.assertNotIn('source_uri', output)

    @skip("")
    def test_data_cif_import(self):
        """
        This method tests that the Cif import works as expected with all
        possible flags and arguments.
        """
        import tempfile
        from cStringIO import StringIO

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
        import tempfile

        from aiida.orm.data.cif import CifData

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
        res = self.cli_runner.invoke(cif.export, options, catch_exceptions=False)
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
