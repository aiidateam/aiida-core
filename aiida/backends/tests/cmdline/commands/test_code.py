import click
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.code import setup_code


class TestVerdiCode(AiidaTestCase):

    def setUpClass(cls):
        super(TestVerdiCode, cls).setUpClass()
        from aiida.orm import Computer
        new_comp = Computer(name='bbb',
                                hostname='localhost',
                                transport_type='local',
                                scheduler_type='direct',
                                workdir='/tmp/aiida')
        new_comp.store()

    def setUp(self):
        self.comp = Computer.get(name='bbb')
        self.runner = CliRunner()

    def test_code_help(self):
        result = self.runner.invoke(setup_code)
