# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=undefined-variable,wildcard-import,global-statement
"""Modules related to the configuration of an AiiDA instance."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from .config import *
from .options import *
from .profile import *
from .utils import *

CONFIG = None

__all__ = (config.__all__ + options.__all__ + profile.__all__ + utils.__all__ + ('get_config', 'get_config_option'))


def get_config():
    """Return the current configuration.

    If the configuration has not been loaded yet, it will be loaded first and then returned.

    Note: this function should only be called by parts of the code that expect that a complete AiiDA instance exists,
    i.e. an AiiDA folder exists and contains a valid configuration file.

    :return: the config
    :rtype: :class:`~aiida.manage.configuration.config.Config`
    :raises aiida.common.ConfigurationError: if the configuration file could not be found, read or deserialized
    """
    global CONFIG

    if not CONFIG:
        CONFIG = load_config()

    return CONFIG


def get_config_option(option_name):
    """Return the value for the given configuration option.

    This function will attempt to load the value of the option as defined for the current profile or otherwise as
    defined configuration wide. If no configuration is yet loaded, this function will fall back on the default that may
    be defined for the option itself. This is useful for options that need to be defined at loading time of AiiDA when
    no configuration is yet loaded or may not even yet exist. In cases where one expects a profile to be loaded,
    preference should be given to retrieving the option through the Config instance and its `option_get` method.

    :param option_name: the name of the configuration option
    :return: option value as specified for the profile/configuration if loaded, otherwise option default
    """
    from aiida.common import exceptions

    option = options.get_option(option_name)

    try:
        config = get_config()
    except exceptions.ConfigurationError:
        value = option.default
    else:
        if config.current_profile:
            # Try to get the option for the profile, but do not return the option default
            value_profile = config.option_get(option_name, scope=config.current_profile.name, default=False)
        else:
            value_profile = None

        # Value is the profile value if defined or otherwise the global value, which will be None if not set
        value = value_profile if value_profile else config.option_get(option_name)

    return value
