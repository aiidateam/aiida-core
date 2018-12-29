# -*- coding: utf-8 -*-
"""Definition of known configuration options and methods to parse and get option values."""
from __future__ import absolute_import

import io
import os

from aiida.common import exceptions
from aiida.common import json

from .config import Config
from .migrations import check_and_migrate_config
from .options import get_option
from .settings import DEFAULT_CONFIG_FILE_NAME

__all__ = ('get_config_option', 'load_config')


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
    option = get_option(option_name)

    try:
        config = load_config()
    except exceptions.ConfigurationError:
        value = option.default
    else:
        if config.current_profile:
            value = config.option_get(option_name, scope=config.current_profile.name)
        else:
            value = config.option_get(option_name)

    return value


def load_config(create=False):
    """Instantiate the Config object representing the configuration file of the current AiiDA instance.

    :param create: when set to True, will create the configuration file if it does not already exist
    :return: the config
    :rtype: :class:`~aiida.manage.configuration.config.Config`
    :raises MissingConfigurationError: if the configuration file could not be found and create=False
    """
    from .settings import AIIDA_CONFIG_FOLDER
    from aiida.backends.settings import IN_RT_DOC_MODE, DUMMY_CONF_FILE

    if IN_RT_DOC_MODE:
        return DUMMY_CONF_FILE

    filepath = os.path.join(AIIDA_CONFIG_FOLDER, DEFAULT_CONFIG_FILE_NAME)

    if not os.path.isfile(filepath):
        if not create:
            raise exceptions.MissingConfigurationError('configuration file {} does not exist'.format(filepath))
        else:
            config = Config(filepath, {}).store()
    else:
        try:
            with io.open(filepath, 'r', encoding='utf8') as handle:
                config = Config(filepath, json.load(handle))
        except ValueError:
            raise exceptions.ConfigurationError('configuration file {} contains invalid JSON'.format(filepath))

    return check_and_migrate_config(config, store=True)
