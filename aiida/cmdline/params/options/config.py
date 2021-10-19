# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=cyclic-import
"""
.. py:module::config
    :synopsis: Convenience class for configuration file option
"""
import click_config_file
import yaml

from .overridable import OverridableOption

__all__ = ('ConfigFileOption',)


def yaml_config_file_provider(handle, cmd_name):  # pylint: disable=unused-argument
    """Read yaml config file from file handle."""
    return yaml.safe_load(handle)


class ConfigFileOption(OverridableOption):
    """
    Wrapper around click_config_file.configuration_option that increases reusability.

    Example::

        CONFIG_FILE = ConfigFileOption('--config', help='A configuration file')

        @click.command()
        @click.option('computer_name')
        @CONFIG_FILE(help='Configuration file for computer_setup')
        def computer_setup(computer_name):
            click.echo(f"Setting up computer {computername}")

        computer_setup --config config.yml

    with config.yml::

        ---
        computer_name: computer1

    """

    def __init__(self, *args, **kwargs):
        """
        Store the default args and kwargs.

        :param args: default arguments to be used for the option
        :param kwargs: default keyword arguments to be used that can be overridden in the call
        """
        kwargs.update({'provider': yaml_config_file_provider, 'implicit': False})
        super().__init__(*args, **kwargs)

    def __call__(self, **kwargs):
        """
        Override the stored kwargs, (ignoring args as we do not allow option name changes) and return the option.

        :param kwargs: keyword arguments that will override those set in the construction
        :return: click_config_file.configuration_option constructed with args and kwargs defined during construction
            and call of this instance
        """
        kw_copy = self.kwargs.copy()
        kw_copy.update(kwargs)

        return click_config_file.configuration_option(*self.args, **kw_copy)
