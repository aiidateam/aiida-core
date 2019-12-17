# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Definition of caching mechanism and configuration for calculations."""
import os
import copy
import warnings
from enum import Enum
from contextlib import contextmanager

import yaml
from wrapt import decorator

from aiida.common import exceptions
from aiida.common.warnings import AiidaDeprecationWarning

__all__ = ('get_use_cache', 'enable_caching', 'disable_caching')


class ConfigKeys(Enum):
    """Valid keys for caching configuration."""

    DEFAULT = 'default'
    ENABLED = 'enabled'
    DISABLED = 'disabled'


DEFAULT_CONFIG = {
    ConfigKeys.DEFAULT.value: False,
    ConfigKeys.ENABLED.value: [],
    ConfigKeys.DISABLED.value: [],
}


def _get_config(config_file):
    """Return the caching configuration.

    :param config_file: the absolute path to the caching configuration file
    :return: the configuration dictionary
    """
    from aiida.manage.configuration import get_profile
    from aiida.plugins.entry_point import is_valid_entry_point_string, load_entry_point_from_string

    profile = get_profile()

    if profile is None:
        exceptions.ConfigurationError('no profile has been loaded')

    try:
        with open(config_file, 'r', encoding='utf8') as handle:
            config = yaml.safe_load(handle)[profile.name]
    except (OSError, IOError, KeyError):
        # No config file, or no config for this profile
        return DEFAULT_CONFIG

    # Validate configuration
    for key in config:
        if key not in DEFAULT_CONFIG:
            raise ValueError("Configuration error: Invalid key '{}' in cache_config.yml".format(key))

    # Add defaults where key is either completely missing or specifies no values in which case it will be `None`
    for key, default_config in DEFAULT_CONFIG.items():
        if key not in config or config[key] is None:
            config[key] = default_config

    # Validate the entry point identifiers
    for key in [ConfigKeys.ENABLED.value, ConfigKeys.DISABLED.value]:

        # If the key is defined in the file but contains no values, it will be `None`
        if config[key] is None:
            continue

        for identifier in config[key]:
            if not is_valid_entry_point_string(identifier):
                raise exceptions.ConfigurationError(
                    "entry point '{}' in 'cache_config.yml' is not a valid entry point string.".format(identifier)
                )

            try:
                load_entry_point_from_string(identifier)
            except exceptions.EntryPointError as exception:
                raise exceptions.ConfigurationError(
                    "entry point '{}' in 'cache_config.yml' can not be loaded: {}.".format(identifier, exception)
                )

    return config


_CONFIG = {}


def configure(config_file=None):
    """Reads the caching configuration file and sets the _CONFIG variable."""
    # pylint: disable=global-statement
    if config_file is None:
        from aiida.manage.configuration import get_config

        config = get_config()
        config_file = os.path.join(config.dirpath, 'cache_config.yml')

    global _CONFIG
    _CONFIG.clear()
    _CONFIG.update(_get_config(config_file=config_file))


@decorator
def _with_config(wrapped, _, args, kwargs):
    """Function decorator to load the caching configuration for the scope of the wrapped function."""
    if not _CONFIG:
        configure()
    return wrapped(*args, **kwargs)


@_with_config
def get_use_cache(node_class=None, identifier=None):
    """Return whether the caching mechanism should be used for the given entry point according to the configuration.

    :param node_class: the Node class or sub class to check if enabled for caching
    :param identifier: the full entry point string of the process, e.g. `aiida.calculations:arithmetic.add`
    :return: boolean, True if caching is enabled, False otherwise
    :raises ValueError: if the configuration is invalid by defining the class both enabled and disabled
    """
    from aiida.common.lang import type_check

    if node_class is not None:
        warnings.warn(  # pylint: disable=no-member
            'the `node_class` argument is deprecated and will be removed in `v2.0.0`. '
            'Use the `identifier` argument instead', AiidaDeprecationWarning
        )

    if identifier is not None:
        type_check(identifier, str)

        enabled = identifier in _CONFIG[ConfigKeys.ENABLED.value]
        disabled = identifier in _CONFIG[ConfigKeys.DISABLED.value]

        if enabled and disabled:
            raise ValueError('Invalid configuration: caching for {} is both enabled and disabled.'.format(identifier))
        elif enabled:
            return True
        elif disabled:
            return False

    return _CONFIG[ConfigKeys.DEFAULT.value]


@contextmanager
@_with_config
def _reset_config():
    """Reset the configuration by clearing the contents of the global config variable."""
    # pylint: disable=global-statement
    global _CONFIG
    config_copy = copy.deepcopy(_CONFIG)
    yield
    _CONFIG.clear()
    _CONFIG.update(config_copy)


@contextmanager
def enable_caching(node_class=None, identifier=None):
    """Context manager to enable caching, either for a specific node class, or globally.

    .. warning:: this does not affect the behavior of the daemon, only the local Python interpreter.

    :param node_class: Node class for which caching should be enabled.
    :param identifier: the full entry point string of the process, e.g. `aiida.calculations:arithmetic.add`
    """
    if node_class is not None:
        warnings.warn(  # pylint: disable=no-member
            'the `node_class` argument is deprecated and will be removed in `v2.0.0`. '
            'Use the `identifier` argument instead', AiidaDeprecationWarning
        )

    with _reset_config():
        if identifier is None:
            _CONFIG[ConfigKeys.DEFAULT.value] = True
        else:
            _CONFIG[ConfigKeys.ENABLED.value].append(identifier)
            try:
                _CONFIG[ConfigKeys.DISABLED.value].remove(identifier)
            except ValueError:
                pass
        yield


@contextmanager
def disable_caching(node_class=None, identifier=None):
    """Context manager to disable caching, either for a specific node class, or globally.

    .. warning:: this does not affect the behavior of the daemon, only the local Python interpreter.

    :param node_class: Node class for which caching should be disabled.
    :param identifier: the full entry point string of the process, e.g. `aiida.calculations:arithmetic.add`
    """
    if node_class is not None:
        warnings.warn(  # pylint: disable=no-member
            'the `node_class` argument is deprecated and will be removed in `v2.0.0`. '
            'Use the `identifier` argument instead', AiidaDeprecationWarning
        )

    with _reset_config():
        if identifier is None:
            _CONFIG[ConfigKeys.DEFAULT.value] = False
        else:
            _CONFIG[ConfigKeys.DISABLED.value].append(identifier)
            try:
                _CONFIG[ConfigKeys.ENABLED.value].remove(identifier)
            except ValueError:
                pass
        yield
