import os
import subprocess as sp
import click
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.code import setup_code


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
        from aiida.orm import Computer
        self.comp = Computer.get('comp')
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
        os.environ['VISUAL'] = 'sleep 1; vim -cwq'
        os.environ['EDITOR'] = 'sleep 1; vim -cwq'
        label = 'interactive_remote'
        user_input = '\n'.join([
            label, 'description', 'yes', 'simpleplugins.arithmetic.add', self.comp.name,
            '/remote/abs/path'])
        result = self.runner.invoke(setup_code, input=user_input)
        self.assertIsNone(result.exception, msg="There was an unexpected exception. Output: {}".format(result.output))
        self.assertIsInstance(Code.get_from_string('{}@{}'.format(label, self.comp.name)), Code)

    def test_interactive_upload(self):
        from aiida.orm import Code
        os.environ['VISUAL'] = 'sleep 1; vim -cwq'
        os.environ['EDITOR'] = 'sleep 1; vim -cwq'
        label = 'interactive_upload'
        user_input = '\n'.join([
            label, 'description', 'no', 'simpleplugins.arithmetic.add', self.comp.name, self.this_folder, self.this_file])
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
