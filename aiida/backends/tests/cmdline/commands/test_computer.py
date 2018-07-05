"""Tests for the 'verdi computer' command."""
import os
import subprocess as sp
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.computer import (disable_computer, enable_computer)
from aiida.common.exceptions import NotExistent


# pylint: disable=missing-docstring
class TestVerdiComputerCommands(AiidaTestCase):
    """Testing verdi computer commands.

    Testing everything besides `computer setup`.
    """

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestVerdiComputerCommands, cls).setUpClass(*args, **kwargs)
        from aiida.orm import Computer
        new_comp = Computer(
            name='comp', hostname='localhost', transport_type='local', scheduler_type='direct', workdir='/tmp/aiida')
        new_comp.store()

    def setUp(self):
        from aiida.cmdline.commands.computer import Computer as ComputerCmd
        from aiida.utils.capturing import Capturing

        from aiida.orm import Computer
        self.comp = Computer.get('comp')

        self.user = self.backend.users.get_automatic_user()

        # I need to configure the computer here; being 'local',
        # there should not be any options asked here
        with Capturing():
            ComputerCmd().run('configure', self.comp.name)

        assert self.comp.is_user_configured(
            self.user), "There was a problem configuring the test computer"

        self.runner = CliRunner()

    def test_enable_disable_globally(self):
        """
        Test if enabling and disabling a computer has the intended effect.
        Note I have to do it three times, because if because of a bug 
        'enable' is a no-op and the computer was already enabled, the 
        test would pass.
        """
        def enable_disable_globally_loop(self, user=None, user_enabled_state=True):
            result = self.runner.invoke(enable_computer, [str(self.comp.label)])
            self.assertIsNone(result.exception)
            self.assertTrue(self.comp.is_enabled())

            # Check that the change of global state did not affect the
            # per-user state
            if user is not None:
                if user_enabled_state:
                    self.assertTrue(self.comp.is_user_enabled(user))
                else:
                    self.assertFalse(self.comp.is_user_enabled(user))

            result = self.runner.invoke(disable_computer, [str(self.comp.label)])
            self.assertIsNone(result.exception)
            self.assertFalse(self.comp.is_enabled())
            
            # Check that the change of global state did not affect the
            # per-user state
            if user is not None:
                if user_enabled_state:
                    self.assertTrue(self.comp.is_user_enabled(user))
                else:
                    self.assertFalse(self.comp.is_user_enabled(user))            

            result = self.runner.invoke(enable_computer, [str(self.comp.label)])
            self.assertIsNone(result.exception)
            self.assertTrue(self.comp.is_enabled())

            # Check that the change of global state did not affect the
            # per-user state
            if user is not None:
                if user_enabled_state:
                    self.assertTrue(self.comp.is_user_enabled(user))
                else:
                    self.assertFalse(self.comp.is_user_enabled(user))

        ## Start of actual tests
        result = self.runner.invoke(enable_computer, ['--only-for-user={}'.format(self.user_email), str(self.comp.label)])
        self.assertIsNone(result.exception, msg="Error, output: {}".format(result.output))    #.stdout, result.stderr))
        self.assertTrue(self.comp.is_user_enabled(self.user))
        # enable and disable the computer globally as well
        enable_disable_globally_loop(self, self.user, user_enabled_state=True)

        result = self.runner.invoke(disable_computer, ['--only-for-user={}'.format(self.user_email), str(self.comp.label)])
        self.assertIsNone(result.exception, msg="Error, output: {}".format(result.output))    #.stdout, result.stderr))
        self.assertFalse(self.comp.is_user_enabled(self.user))
        # enable and disable the computer globally as well
        enable_disable_globally_loop(self, self.user, user_enabled_state=False)

        result = self.runner.invoke(enable_computer, ['--only-for-user={}'.format(self.user_email), str(self.comp.label)])
        self.assertIsNone(result.exception, msg="Error, output: {}".format(result.output))    #.stdout, result.stderr))
        self.assertTrue(self.comp.is_user_enabled(self.user))
        # enable and disable the computer globally as well
        enable_disable_globally_loop(self, self.user, user_enabled_state=True)