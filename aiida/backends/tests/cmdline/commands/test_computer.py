"""Tests for the 'verdi computer' command."""
import os
import subprocess as sp
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.computer import (disable_computer, enable_computer)
from aiida.common.exceptions import NotExistent
from aiida.utils.capturing import Capturing

class TestVerdiComputerCommands(AiidaTestCase):
    """Testing verdi computer commands.

    Testing everything besides `computer setup`.
    """

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """Create a new computer> I create a new one because I want to configure it and I don't want to 
        interfere with other tests"""
        from aiida.orm.backend import construct_backend

        super(TestVerdiComputerCommands, cls).setUpClass(*args, **kwargs)
        from aiida.orm import Computer
        backend = construct_backend()
        cls.computer_name = "comp_cli_test_computer"
        cls.comp = Computer(
            name=cls.computer_name,
            hostname='localhost',
            transport_type='local',
            scheduler_type='direct',
            workdir='/tmp/aiida')
        cls.comp.store()

    def setUp(self):
        """
        Prepare the computer and user
        """
        from aiida.cmdline.commands.computer import Computer as ComputerCmd

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

    def test_computer_test(self):
        """
        Test if the 'verdi computer test' command works

        It should work as it is a local connection
        """
        from aiida.cmdline.commands.computer import Computer as ComputerCmd

        # Check that indeed, if there is a problem, we detect it as such
        with self.assertRaises(SystemExit):
            with Capturing(capture_stderr=True):
                ComputerCmd().run('test', "not_existent_computer_name")

        # Test the computer
        with Capturing():
            ComputerCmd().run('test', self.computer_name)

