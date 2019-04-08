# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=cyclic-import
"""
.. py:module::config
    :synopsis: Convenience class for configuration file option
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import yaml
import click_config_file

from .overridable import OverridableOption


def yaml_config_file_provider(file_path, cmd_name):  # pylint: disable=unused-argument
    """Read yaml config file."""
    try:
        with open(file_path, 'r') as handle:
            return yaml.load(handle)
    except IOError:
        return {}


class ConfigFileOption(OverridableOption):
    """
    Wrapper around click_config_file.configuration_option that increases reusability

    Example::

        CONFIG_FILE = ConfigFileOption('--config', help='A configuration file')

        @click.command()
        @click.option('my_option')
        @CONFIG_FILE(help='Configuration file for this cmd')
        def ls_or_create(my_option):
            click.echo(os.listdir(folder))

        ls_or_create --config myconfig.yml

    """

    def __init__(self, *args, **kwargs):  # pylint: disable=super-init-not-called
        """
        Store the default args and kwargs.

        :param args: default arguments to be used for the option
        :param kwargs: default keyword arguments to be used that can be overridden in the call
        """
        self.args = args
        self.kwargs = {'provider': yaml_config_file_provider}
        self.kwargs.update(kwargs)

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
