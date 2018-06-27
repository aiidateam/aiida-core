import os
import subprocess as sp
import click
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.data.cif import cif


class TestVerdiData(AiidaTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestVerdiData, cls).setUpClass()
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

    def test_help(self):
        result = self.runner.invoke(cif, ['--help'])

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

    def test_data_cif_list(self):
        import os
        import tempfile

        from aiida.orm.data.cif import CifData

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

        with tempfile.NamedTemporaryFile() as f:
            filename = f.name
            f.write(valid_sample_cif_str)
            f.flush()
            a = CifData(file=filename,
                        source={'version': '1234',
                                'db_name': 'COD',
                                'id': '0000001'})
            a.store()

        # Check that the normal listing works as expected
        output = sp.check_output(['verdi', 'data', 'cif', 'list'])
        self.assertIn('C O2', output, 'The Cif formula was not found in '
                                      'the listing')

        # Check that the past days filter works as expected
        past_days_flags = ['-p', '--past-days']
        for flag in past_days_flags:
            output = sp.check_output(['verdi', 'data', 'cif', 'list', '-p', '1'])
            self.assertIn('C O2', output, 'The Cif formula was not found in '
                                          'the listing')

            # Check that the normal listing works as expected
            output = sp.check_output(['verdi', 'data', 'cif', 'list', '-p', '0'])
            self.assertNotIn('C O2', output, 'A not expected Cif formula was '
                                             'found in the listing')





    # def test_interactive_remote(self):
    #     from aiida.orm import Code
    #     os.environ['VISUAL'] = 'vim -cwq'
    #     os.environ['EDITOR'] = 'vim -cwq'
    #     label = 'interactive_remote'
    #     user_input = '\n'.join([
    #         label, 'description', 'yes', 'simpleplugins.arithmetic.add', self.comp.name,
    #         '/remote/abs/path'])
    #     result = self.runner.invoke(setup_code, input=user_input)
    #     self.assertIsNone(result.exception)
    #     self.assertIsInstance(Code.get_from_string('{}@{}'.format(label, self.comp.name)), Code)
    #
    # def test_interactive_upload(self):
    #     from aiida.orm import Code
    #     os.environ['VISUAL'] = 'vim -cwq'
    #     os.environ['EDITOR'] = 'vim -cwq'
    #     label = 'interactive_upload'
    #     user_input = '\n'.join([
    #         label, 'description', 'no', 'simpleplugins.arithmetic.add', self.this_folder, self.this_file])
    #     result = self.runner.invoke(setup_code, input=user_input)
    #     self.assertIsNone(result.exception, result.output)
    #     self.assertIsInstance(Code.get_from_string('{}'.format(label)), Code)
    #
    # def test_noninteractive_remote(self):
    #     from aiida.orm import Code
    #     label = 'noninteractive_remote'
    #     options = ['--non-interactive', '--label={}'.format(label), '--description=description',
    #                '--on-computer', '--input-plugin=simpleplugins.arithmetic.add',
    #                '--computer={}'.format(self.comp.name), '--remote-abs-path=/remote/abs/path']
    #     result = self.runner.invoke(setup_code, options)
    #     self.assertIsNone(result.exception, result.output[-1000:])
    #     self.assertIsInstance(Code.get_from_string('{}@{}'.format(label, self.comp.name)), Code)
    #
    # def test_noninteractive_upload(self):
    #     from aiida.orm import Code
    #     label = 'noninteractive_upload'
    #     options = ['--non-interactive', '--label={}'.format(label), '--description=description',
    #                '--store-upload', '--input-plugin=simpleplugins.arithmetic.add',
    #                '--code-folder={}'.format(self.this_folder), '--code-rel-path={}'.format(self.this_file)]
    #     result = self.runner.invoke(setup_code, options)
    #     self.assertIsNone(result.exception, result.output[-1000:])
    #     self.assertIsInstance(Code.get_from_string('{}'.format(label)), Code)
    #
    # def test_mixed(self):
    #     from aiida.orm import Code
    #     label = 'mixed_remote'
    #     options = ['--description=description', '--on-computer', '--remote-abs-path=/remote/abs/path']
    #     user_input = '\n'.join([label, 'simpleplugins.arithmetic.add', self.comp.name])
    #     result = self.runner.invoke(setup_code, options, input=user_input)
    #     self.assertIsNone(result.exception, result.output[-1000:])
    #     self.assertIsInstance(Code.get_from_string('{}@{}'.format(label, self.comp.name)), Code)
