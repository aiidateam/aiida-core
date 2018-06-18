import os
import subprocess as sp
import click
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.code import setup_code, delete, hide, reveal, relabel


class TestVerdiCodeSetup(AiidaTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestVerdiCodeSetup, cls).setUpClass()
        from aiida.orm import Computer
        new_comp = Computer(name='comp',
                                hostname='localhost',
                                transport_type='local',
                                scheduler_type='direct',
                                workdir='/tmp/aiida')
        new_comp.store()


    def setUp(self):
        from aiida.orm import Computer, Code
        self.comp = Computer.get('comp')

        from aiida.orm import Code
        from aiida.common.exceptions import NotExistent
        try:
            code = Code.get_from_string('code')
        except NotExistent:
            code = Code(
                input_plugin_name='simpleplugins.arithmetic.add',
                remote_computer_exec=[self.comp, '/remote/abs/path'],
            )
            code.label = 'code'
            code.store()
        self.code = code

        self.runner = CliRunner()
        self.this_folder = os.path.dirname(__file__)
        self.this_file = os.path.basename(__file__)

    def test_help(self):
        result = self.runner.invoke(setup_code, ['--help'])

    def test_reachable(self):
        output = sp.check_output(['verdi', 'code', 'setup', '--help'])
        self.assertIn('Usage:', output)

    def test_interactive_remote(self):
        from aiida.orm import Code
        os.environ['VISUAL'] = 'vim -cwq'
        os.environ['EDITOR'] = 'vim -cwq'
        label = 'interactive_remote'
        user_input = '\n'.join([
            label, 'description', 'yes', 'simpleplugins.arithmetic.add', self.comp.name,
            '/remote/abs/path'])
        result = self.runner.invoke(setup_code, input=user_input)
        self.assertIsNone(result.exception)
        self.assertIsInstance(Code.get_from_string('{}@{}'.format(label, self.comp.name)), Code)

    def test_interactive_upload(self):
        from aiida.orm import Code
        os.environ['VISUAL'] = 'vim -cwq'
        os.environ['EDITOR'] = 'vim -cwq'
        label = 'interactive_upload'
        user_input = '\n'.join([
            label, 'description', 'no', 'simpleplugins.arithmetic.add', self.this_folder, self.this_file])
        result = self.runner.invoke(setup_code, input=user_input)
        self.assertIsNone(result.exception, result.output)
        self.assertIsInstance(Code.get_from_string('{}'.format(label)), Code)

    def test_noninteractive_remote(self):
        from aiida.orm import Code
        label = 'noninteractive_remote'
        options = ['--non-interactive', '--label={}'.format(label), '--description=description',
                   '--on-computer', '--input-plugin=simpleplugins.arithmetic.add',
                   '--computer={}'.format(self.comp.name), '--remote-abs-path=/remote/abs/path']
        result = self.runner.invoke(setup_code, options)
        self.assertIsNone(result.exception, result.output[-1000:])
        self.assertIsInstance(Code.get_from_string('{}@{}'.format(label, self.comp.name)), Code)

    def test_noninteractive_upload(self):
        from aiida.orm import Code
        label = 'noninteractive_upload'
        options = ['--non-interactive', '--label={}'.format(label), '--description=description',
                   '--store-upload', '--input-plugin=simpleplugins.arithmetic.add',
                   '--code-folder={}'.format(self.this_folder), '--code-rel-path={}'.format(self.this_file)]
        result = self.runner.invoke(setup_code, options)
        self.assertIsNone(result.exception, result.output[-1000:])
        self.assertIsInstance(Code.get_from_string('{}'.format(label)), Code)

    def test_mixed(self):
        from aiida.orm import Code
        label = 'mixed_remote'
        options = ['--description=description', '--on-computer', '--remote-abs-path=/remote/abs/path']
        user_input = '\n'.join([label, 'simpleplugins.arithmetic.add', self.comp.name])
        result = self.runner.invoke(setup_code, options, input=user_input)
        self.assertIsNone(result.exception, result.output[-1000:])
        self.assertIsInstance(Code.get_from_string('{}@{}'.format(label, self.comp.name)), Code)

    def test_hide_one(self):
        result = self.runner.invoke(hide, [str(self.code.pk)])
        self.assertIsNone(result.exception)

    def test_reveal_one(self):
        result = self.runner.invoke(reveal, [str(self.code.pk)])
        self.assertIsNone(result.exception)

    def test_relabel_code(self):
        result = self.runner.invoke(relabel, [str(self.code.pk), 'new_code'])
        self.assertIsNone(result.exception)

    def test_relabel_code_2(self):
        result = self.runner.invoke(relabel, [str(self.code.pk), 'new_code@comp'])
        self.assertIsNone(result.exception)

    def test_relabel_code_3(self):
        result = self.runner.invoke(relabel, [str(self.code.pk), 'new_code@otherstuff'])
        self.assertIsNotNone(result.exception)

    def test_delete_one(self):
        result = self.runner.invoke(delete, [str(self.code.pk)])
        self.assertIsNone(result.exception)


