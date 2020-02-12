# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi config`."""

from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_verdi
from aiida.manage.configuration import get_config

from tests.utils.configuration import with_temporary_config_instance


class TestVerdiConfig(AiidaTestCase):
    """Tests for `verdi config`."""

    def setUp(self):
        self.cli_runner = CliRunner()

    @with_temporary_config_instance
    def test_config_set_option(self):
        """Test the `verdi config` command when setting an option."""
        config = get_config()

        option_name = 'daemon.timeout'
        option_values = [str(10), str(20)]

        for option_value in option_values:
            options = ['config', option_name, str(option_value)]
            result = self.cli_runner.invoke(cmd_verdi.verdi, options)

            self.assertClickSuccess(result)
            self.assertEqual(str(config.get_option(option_name, scope=config.current_profile.name)), option_value)

    @with_temporary_config_instance
    def test_config_get_option(self):
        """Test the `verdi config` command when getting an option."""
        option_name = 'daemon.timeout'
        option_value = str(30)

        options = ['config', option_name, option_value]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)
        self.assertClickResultNoException(result)

        options = ['config', option_name]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)
        self.assertIn(option_value, result.output.strip())

    @with_temporary_config_instance
    def test_config_unset_option(self):
        """Test the `verdi config` command when unsetting an option."""
        option_name = 'daemon.timeout'
        option_value = str(30)

        options = ['config', option_name, str(option_value)]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)

        options = ['config', option_name]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)
        self.assertIn(option_value, result.output.strip())

        options = ['config', option_name, '--unset']
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)
        self.assertIn('{} unset'.format(option_name), result.output.strip())

        options = ['config', option_name]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)
        self.assertEqual(result.output, '')

    @with_temporary_config_instance
    def test_config_set_option_global_only(self):
        """Test that `global_only` options are only set globally even if the `--global` flag is not set."""
        config = get_config()
        option_name = 'user.email'
        option_value = 'some@email.com'

        options = ['config', option_name, str(option_value)]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)

        options = ['config', option_name]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)

        # Check that the current profile name is not in the output
        self.assertClickSuccess(result)
        self.assertIn(option_value, result.output.strip())
        self.assertNotIn(config.current_profile.name, result.output.strip())
