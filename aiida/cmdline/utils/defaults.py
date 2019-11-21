# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Default values and lazy default get methods for command line options."""

from aiida.cmdline.utils import echo
from aiida.common import exceptions
from aiida.manage.configuration import get_config


def get_default_profile():  # pylint: disable=unused-argument
    """Try to get the name of the default profile.

    This utility function should only be used for defaults or callbacks in command line interface parameters.
    Otherwise, the preference should go to calling `get_config` to load the actual config and using
    `config.default_profile_name` to get the default profile name.

    :raises click.UsageError: if the config could not be loaded or no default profile exists
    :return: the default profile name or None if no default is defined in the configuration
    """
    try:
        config = get_config(create=True)
    except exceptions.ConfigurationError as exception:
        echo.echo_critical(str(exception))

    try:
        default_profile = config.get_profile(config.default_profile_name).name
    except exceptions.ProfileConfigurationError:
        default_profile = None

    return default_profile
