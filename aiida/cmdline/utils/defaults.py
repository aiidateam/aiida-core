# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Default values and lazy default get methods for command line options."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.cmdline.utils import echo
from aiida.common import exceptions
from aiida.manage.configuration import get_config


def get_default_profile(ctx, param, value):  # pylint: disable=unused-argument
    """Try to get the default profile.

    This should be used if the default profile should be returned lazily, at a point for example when the config
    is not created at import time. Otherwise, the preference should go to calling `get_config` to load the actual
    config and using `config.default_profile_name` to get the default profile name

    :raises click.UsageError: if the config could not be loaded or no default profile exists
    :return: the default profile
    """
    if value:
        return value

    try:
        config = get_config()
    except exceptions.ConfigurationError as exception:
        echo.echo_critical(str(exception))

    try:
        default_profile = config.get_profile(config.default_profile_name)
    except exceptions.ProfileConfigurationError:
        default_profile = None

    return default_profile
