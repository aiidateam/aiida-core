"""
Test suite to test verdi profile command
"""

from click.testing import CliRunner
from aiida.backends.testbase import AiidaTestCase
from aiida.common import setup as aiida_cfg


class TestVerdiProfileSetup(AiidaTestCase):
    """
    Test suite to test verdi profile command
    """

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """
        Create dummy 5 profiles and set first profile as default profile.
        All tests will run on these dummy profiles.

        :param args: list of arguments
        :param kwargs: list of keyword arguments
        """
        import tempfile

        super(TestVerdiProfileSetup, cls).setUpClass()

        cls._old_aiida_config_folder = None
        cls._new_aiida_config_folder = tempfile.mkstemp()
        print ":", cls._new_aiida_config_folder

        cls._old_aiida_config_folder = aiida_cfg.AIIDA_CONFIG_FOLDER
        aiida_cfg.AIIDA_CONFIG_FOLDER = cls._new_aiida_config_folder
        aiida_cfg.create_base_dirs()

        for profile in ['dummy_profile1', 'dummy_profile2', 'dummy_profile3', 'dummy_profile4', 'dummy_profile5']:
            dummy_profile = {}
            dummy_profile['backend'] = 'django'
            dummy_profile['db_host'] = 'localhost'
            dummy_profile['db_port'] = '5432'
            dummy_profile['email'] = 'dummy@localhost'
            dummy_profile['db_name'] = profile
            dummy_profile['db_user'] = 'dummy_user'
            dummy_profile['db_pass'] = 'dummy_pass'
            dummy_profile['repo'] = aiida_cfg.AIIDA_CONFIG_FOLDER + '/repository_' + profile
            aiida_cfg.create_config_noninteractive(profile=profile, **dummy_profile)

        aiida_cfg.set_default_profile('dummy_profile1', force_rewrite=True)

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        """
        Remove dummy profiles created in setUpClass.

        :param args: list of arguments
        :param kwargs: list of keyword arguments
        """

        aiida_cfg.AIIDA_CONFIG_FOLDER = cls._old_aiida_config_folder

        import os
        import shutil
        if os.path.isdir(cls._new_aiida_config_folder):
            shutil.rmtree(cls._new_aiida_config_folder)

    def setUp(self):
        """
        Create runner object to run tests
        """
        self.runner = CliRunner()

    def test_help(self):
        """
        Tests help text for all profile sub commands
        """
        options = ["--help"]
        from aiida.cmdline.commands.profile import (profile_list, profile_setdefault, profile_delete)

        result = self.runner.invoke(profile_list, options)
        self.assertIsNone(result.exception)
        self.assertIn('Usage', result.output)

        result = self.runner.invoke(profile_setdefault, options)
        self.assertIsNone(result.exception)
        self.assertIn('Usage', result.output)

        result = self.runner.invoke(profile_delete, options)
        self.assertIsNone(result.exception)
        self.assertIn('Usage', result.output)

    def test_list(self):
        """
        Test for verdi profile list command
        """
        from aiida.cmdline.commands.profile import profile_list
        result = self.runner.invoke(profile_list)
        self.assertIsNone(result.exception)
        self.assertIn('Configuration folder: ' + self._new_aiida_config_folder, result.output)
        self.assertIn('* dummy_profile1', result.output)
        self.assertIn('dummy_profile2', result.output)

    def test_setdefault(self):
        """
        Test for verdi profile setdefault command
        """
        from aiida.cmdline.commands.profile import profile_setdefault
        result = self.runner.invoke(profile_setdefault, ["dummy_profile2"])
        self.assertIsNone(result.exception)

        from aiida.cmdline.commands.profile import profile_list
        result = self.runner.invoke(profile_list)

        self.assertIsNone(result.exception)
        self.assertIn('Configuration folder: ' + self._new_aiida_config_folder, result.output)
        self.assertIn('* dummy_profile2', result.output)
        self.assertIsNone(result.exception)

    def test_delete(self):
        """
        Test for verdi profile delete command
        """
        from aiida.cmdline.commands.profile import profile_delete, profile_list

        ### delete single profile
        result = self.runner.invoke(profile_delete, ["--force", "dummy_profile3"])
        self.assertIsNone(result.exception)
        print "delete output: ", result.output

        result = self.runner.invoke(profile_list)
        self.assertIsNone(result.exception)
        print "list output: ", result.output

        self.assertNotIn('dummy_profile3', result.output)
        self.assertIsNone(result.exception)

        ### delete multiple profile
        result = self.runner.invoke(profile_delete, ["--force", "dummy_profile4", "dummy_profile5"])
        self.assertIsNone(result.exception)

        result = self.runner.invoke(profile_list)
        self.assertIsNone(result.exception)
        self.assertNotIn('dummy_profile4', result.output)
        self.assertNotIn('dummy_profile5', result.output)
        self.assertIsNone(result.exception)
