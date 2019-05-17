# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=undefined-variable,wildcard-import,global-statement,redefined-outer-name,cyclic-import
"""Modules related to the configuration of an AiiDA instance."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from .config import *
from .options import *
from .profile import *

CONFIG = None
PROFILE = None
BACKEND_UUID = None  # This will be set to the UUID of the profile as soon as its corresponding backend is loaded

# This is used (and should be set to true) for the correct compilation of the documentation on readthedocs
IN_RT_DOC_MODE = False

__all__ = (config.__all__ + options.__all__ + profile.__all__ + ('get_config', 'get_config_option', 'load_profile'))


def load_profile(profile=None):
    """Load a profile.

    .. note:: if a profile is already loaded and no explicit profile is specified, nothing will be done

    :param profile: the name of the profile to load, by default will use the one marked as default in the config
    :return: the loaded `Profile` instance
    :raises `aiida.common.exceptions.InvalidOperation`: if the backend of another profile has already been loaded
    """
    from aiida.common import InvalidOperation
    from aiida.common.log import configure_logging
    from aiida.manage.manager import get_manager, reset_manager

    global PROFILE
    global BACKEND_UUID

    # If a profile is loaded and the specified profile name is None or that of the currently loaded, do nothing
    if PROFILE and (profile is None or PROFILE.name is profile):
        return PROFILE

    profile = get_config().get_profile(profile)

    if BACKEND_UUID is not None and BACKEND_UUID != profile.uuid:
        raise InvalidOperation('cannot switch profile because backend of another profile is already loaded')

    # Set the global variable and make sure the repository is configured
    PROFILE = profile
    PROFILE.configure_repository()

    # Reconfigure the logging to make sure that profile specific logging configuration options are taken into account.
    # Also set `with_orm=True` to make sure that the `DBLogHandler` is configured as well.
    configure_logging(with_orm=True)

    manager = get_manager()
    manager.unload_backend()
    reset_manager()

    return PROFILE


def load_config(create=False):
    """Instantiate the Config object representing the configuration file of the current AiiDA instance.

    :param create: when set to True, will create the configuration file if it does not already exist
    :return: the config
    :rtype: :class:`~aiida.manage.configuration.config.Config`
    :raises aiida.common.MissingConfigurationError: if the configuration file could not be found and create=False
    """
    import io
    import os
    from aiida.common import exceptions
    from aiida.common import json
    from .config import Config
    from .migrations import check_and_migrate_config
    from .settings import AIIDA_CONFIG_FOLDER, DEFAULT_CONFIG_FILE_NAME
    from aiida.manage.external.postgres import DEFAULT_DBINFO

    if IN_RT_DOC_MODE:
        # The following is a dummy config.json configuration that it is used for the
        # proper compilation of the documentation on readthedocs.
        return ({
            'default_profile': 'default',
            'profiles': {
                'default': {
                    'AIIDADB_ENGINE': 'postgresql_psycopg2',
                    'AIIDADB_BACKEND': 'django',
                    'AIIDADB_HOST': DEFAULT_DBINFO['host'],
                    'AIIDADB_PORT': DEFAULT_DBINFO['port'],
                    'AIIDADB_NAME': 'aiidadb',
                    'AIIDADB_PASS': '123',
                    'default_user_email': 'aiida@epfl.ch',
                    'TIMEZONE': 'Europe/Zurich',
                    'AIIDADB_REPOSITORY_URI': 'file:///repository',
                    'AIIDADB_USER': 'aiida'
                }
            }
        })

    filepath = os.path.join(AIIDA_CONFIG_FOLDER, DEFAULT_CONFIG_FILE_NAME)

    if not os.path.isfile(filepath):
        if not create:
            raise exceptions.MissingConfigurationError('configuration file {} does not exist'.format(filepath))
        else:
            config_dictionary = {}
    else:
        try:
            with io.open(filepath, 'r', encoding='utf8') as handle:
                config_dictionary = json.load(handle)
        except ValueError:
            raise exceptions.ConfigurationError('configuration file {} contains invalid JSON'.format(filepath))

    config = Config(filepath, check_and_migrate_config(config_dictionary))
    config.store()

    return config


def get_profile():
    """Return the currently loaded profile.

    :return: the globally loaded `Profile` instance or `None`
    """
    global PROFILE
    return PROFILE


def reset_profile():
    """Reset the globally loaded profile.

    .. warning:: This is experimental functionality and should for now be used only internally. If the reset is unclean
        weird unknown side-effects may occur that end up corrupting or destroying data.
    """
    global PROFILE
    global BACKEND_UUID
    PROFILE = None
    BACKEND_UUID = None


def get_config(create=False):
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
        CONFIG = load_config(create=create)

    return CONFIG


def get_config_option(option_name):
    """Return the value for the given configuration option.

    This function will attempt to load the value of the option as defined for the current profile or otherwise as
    defined configuration wide. If no configuration is yet loaded, this function will fall back on the default that may
    be defined for the option itself. This is useful for options that need to be defined at loading time of AiiDA when
    no configuration is yet loaded or may not even yet exist. In cases where one expects a profile to be loaded,
    preference should be given to retrieving the option through the Config instance and its `get_option` method.

    :param option_name: the name of the configuration option
    :return: option value as specified for the profile/configuration if loaded, otherwise option default
    """
    from aiida.common import exceptions

    option = options.get_option(option_name)

    try:
        config = get_config(create=True)
    except exceptions.ConfigurationError:
        value = option.default if option.default is not options.NO_DEFAULT else None
    else:
        if config.current_profile:
            # Try to get the option for the profile, but do not return the option default
            value_profile = config.get_option(option_name, scope=config.current_profile.name, default=False)
        else:
            value_profile = None

        # Value is the profile value if defined or otherwise the global value, which will be None if not set
        value = value_profile if value_profile else config.get_option(option_name)

    return value
