# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test suite to test the `verdi profile` commands."""
from __future__ import absolute_import

from click.testing import CliRunner
from six.moves import range

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
        super(TestVerdiProfileSetup, cls).setUpClass()

        import tempfile

        cls._old_aiida_config_folder = None
        cls._new_aiida_config_folder = tempfile.mkdtemp()

        cls._old_aiida_config_folder = aiida_cfg.AIIDA_CONFIG_FOLDER
        aiida_cfg.AIIDA_CONFIG_FOLDER = cls._new_aiida_config_folder
        aiida_cfg.create_base_dirs()

        dummy_profile_list = ['dummy_profile1', 'dummy_profile2', 'dummy_profile3', 'dummy_profile4', 'dummy_profile5']
        dummy_profile_list = ["{}_{}".format(profile_name, get_random_string(4)) for profile_name in dummy_profile_list]

        for profile_name in dummy_profile_list:
            dummy_profile = {}
            dummy_profile['backend'] = 'django'
            dummy_profile['db_host'] = 'localhost'
            dummy_profile['db_port'] = '5432'
            dummy_profile['email'] = 'dummy@localhost'
            dummy_profile['db_name'] = profile_name
            dummy_profile['db_user'] = 'dummy_user'
            dummy_profile['db_pass'] = 'dummy_pass'
            dummy_profile['repo'] = aiida_cfg.AIIDA_CONFIG_FOLDER + '/repository_' + profile_name
            aiida_cfg.create_config_noninteractive(profile=profile_name, **dummy_profile)

        aiida_cfg.set_default_profile(dummy_profile_list[0], force_rewrite=True)
        cls.dummy_profile_list = dummy_profile_list

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        """
        Remove dummy profiles created in setUpClass.

        :param args: list of arguments
        :param kwargs: list of keyword arguments
        """
        import os
        import shutil

        aiida_cfg.AIIDA_CONFIG_FOLDER = cls._old_aiida_config_folder

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
        from aiida.cmdline.commands.cmd_profile import (profile_list, profile_setdefault, profile_delete)

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
        from aiida.cmdline.commands.cmd_profile import profile_list
        result = self.runner.invoke(profile_list)
        self.assertIsNone(result.exception)
        self.assertIn('configuration folder: ' + self._new_aiida_config_folder, result.output)
        self.assertIn('* {}'.format(self.dummy_profile_list[0]), result.output)
        self.assertIn(self.dummy_profile_list[1], result.output)

    def test_setdefault(self):
        """
        Test for verdi profile setdefault command
        """
        from aiida.cmdline.commands.cmd_profile import profile_setdefault
        result = self.runner.invoke(profile_setdefault, [self.dummy_profile_list[1]])
        self.assertIsNone(result.exception)

        from aiida.cmdline.commands.cmd_profile import profile_list
        result = self.runner.invoke(profile_list)

        self.assertIsNone(result.exception)
        self.assertIn('configuration folder: ' + self._new_aiida_config_folder, result.output)
        self.assertIn('* {}'.format(self.dummy_profile_list[1]), result.output)
        self.assertIsNone(result.exception)

    def test_show(self):
        """
        Test for verdi profile show command
        """
        from aiida.cmdline.commands.cmd_profile import profile_show
        from aiida.common.setup import get_config

        config = get_config()
        profiles = config['profiles']
        profile_name = self.dummy_profile_list[0]
        profile = profiles[profile_name]

        result = self.runner.invoke(profile_show, [profile_name])
        self.assertIsNone(result.exception, result.output)
        for key, value in profile.items():
            self.assertIn(key.lower(), result.output)
            self.assertIn(value, result.output)

    def test_delete(self):
        """
        Test for verdi profile delete command
        """
        from aiida.cmdline.commands.cmd_profile import profile_delete, profile_list

        # delete single profile
        result = self.runner.invoke(profile_delete, ["--force", self.dummy_profile_list[2]])
        self.assertIsNone(result.exception)

        result = self.runner.invoke(profile_list)
        self.assertIsNone(result.exception)

        self.assertNotIn(self.dummy_profile_list[2], result.output)
        self.assertIsNone(result.exception)

        # delete multiple profile
        result = self.runner.invoke(profile_delete, ["--force", self.dummy_profile_list[3], self.dummy_profile_list[4]])
        self.assertIsNone(result.exception)

        result = self.runner.invoke(profile_list)
        self.assertIsNone(result.exception)
        self.assertNotIn(self.dummy_profile_list[3], result.output)
        self.assertNotIn(self.dummy_profile_list[4], result.output)
        self.assertIsNone(result.exception)


def get_random_string(length):
    import string
    import random

    return ''.join(random.choice(string.ascii_letters) for m in range(length))
