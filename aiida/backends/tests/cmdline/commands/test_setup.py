# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi setup`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import tempfile

from click.testing import CliRunner

from aiida.backends import settings
from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_setup
from aiida.common import setup as aiida_cfg


class TestVerdiSetup(AiidaTestCase):
    """Tests for `verdi setup`."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """Create a dummy profile."""
        super(TestVerdiSetup, cls).setUpClass()
        from aiida import settings as profile_settings

        cls._old_aiida_config_folder = None
        cls._new_aiida_config_folder = tempfile.mkdtemp()

        cls._old_aiida_config_folder = aiida_cfg.AIIDA_CONFIG_FOLDER
        aiida_cfg.AIIDA_CONFIG_FOLDER = cls._new_aiida_config_folder
        aiida_cfg.create_base_dirs()

        profile_name = 'verdi_setup'

        profile = {}
        profile['db_name'] = profile_name
        profile['db_user'] = 'dummy_user'
        profile['db_pass'] = 'dummy_pass'
        profile['db_host'] = 'localhost'
        profile['db_port'] = '5432'
        profile['backend'] = profile_settings.BACKEND
        profile['email'] = 'dummy@localhost'
        profile['first'] = 'dumb'
        profile['last'] = 'one'
        profile['institution'] = 'DumbInc.'
        profile['repo'] = aiida_cfg.AIIDA_CONFIG_FOLDER + '/repository_' + profile_name

        aiida_cfg.create_config_noninteractive(profile=profile_name, **profile)

        cls.default_profile = settings.AIIDADB_PROFILE
        cls.profile = profile
        cls.profile_name = profile_name

        settings.AIIDADB_PROFILE = None

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        """Delete the temporary config folder setup in the setUpClass."""
        import os
        import shutil

        settings.AIIDADB_PROFILE = cls.default_profile
        aiida_cfg.AIIDA_CONFIG_FOLDER = cls._old_aiida_config_folder

        if os.path.isdir(cls._new_aiida_config_folder):
            shutil.rmtree(cls._new_aiida_config_folder)

    def setUp(self):
        """Create runner object to run tests."""
        self.cli_runner = CliRunner()

    def test_non_interactive_override(self):
        """Tests that existing profile can be overridden in non-interactive mode with the `--force` option."""
        option_string = '--backend={backend} --email={email} --repository={repo} --db-host={db_host} ' \
                        '--db-port={db_port} --db-name={db_name} --db-username={db_user} --db-password={db_pass} ' \
                        '--first-name={first} --last-name={last} --institution={institution}'

        options = ['--non-interactive'] + option_string.format(**self.profile).split()

        # Without profile name should raise exception
        result = self.cli_runner.invoke(cmd_setup.setup, options)
        self.assertIsNotNone(result.exception)
        self.assertIn('Missing argument', result.output)
        self.assertIn('profile_name', result.output)

        # With existing profile name should raise exception
        options.append(self.profile_name)
        result = self.cli_runner.invoke(cmd_setup.setup, options)
        self.assertIsNotNone(result.exception, result.output)

        # Need to set the current profile to None again, otherwise it will complain that `verdi` is using `-p` flag
        settings.AIIDADB_PROFILE = None

        # Adding the `--force` option should allow it
        options.append('--force')
        result = self.cli_runner.invoke(cmd_setup.setup, options)
        self.assertIsNone(result.exception, result.output)
