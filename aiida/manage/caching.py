# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Definition of caching mechanism and configuration for calculations."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import io
import os
import copy
from enum import Enum
from functools import wraps
from contextlib import contextmanager

import yaml
import six

from aiida.backends.utils import get_current_profile
from aiida.common import exceptions
from aiida.common.utils import get_object_from_string

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
    try:
        with io.open(config_file, 'r', encoding='utf8') as handle:
            config = yaml.load(handle)[get_current_profile()]
    # no config file, or no config for this profile
    except (OSError, IOError, KeyError):
        return DEFAULT_CONFIG

    # validate configuration
    for key in config:
        if key not in DEFAULT_CONFIG:
            raise ValueError("Configuration error: Invalid key '{}' in cache_config.yml".format(key))

    # add defaults where config is missing
    for key, default_config in DEFAULT_CONFIG.items():
        config[key] = config.get(key, default_config)

    # load classes
    try:
        for key in [ConfigKeys.ENABLED.value, ConfigKeys.DISABLED.value]:
            config[key] = [get_object_from_string(c) for c in config[key]]
    except (ValueError) as err:
        six.raise_from(
            exceptions.ConfigurationError("Unknown class given in 'cache_config.yml': '{}'".format(err)), err)
    return config


_CONFIG = {}


def configure(config_file=None):
    """
    Reads the caching configuration file and sets the _CONFIG variable.
    """
    # pylint: disable=global-statement
    if config_file is None:
        from aiida.manage.configuration import get_config

        config = get_config()
        config_file = os.path.join(config.dirpath, 'cache_config.yml')

    global _CONFIG
    _CONFIG.clear()
    _CONFIG.update(_get_config(config_file=config_file))


def _with_config(func):
    """Function decorator to load the caching configuration for the scope of the wrapped function."""

    @wraps(func)
    def inner(*args, **kwargs):
        if not _CONFIG:
            configure()
        return func(*args, **kwargs)

    return inner


@_with_config
def get_use_cache(node_class=None):
    """Return whether the caching mechanism should be used for the given node class according to the configuration.

    :param node_class: the Node class or sub class to check if enabled for caching
    :return: boolean, True if caching is enabled, False otherwise
    :raises ValueError: if the configuration is invalid by defining the class both enabled and disabled
    """
    if node_class is not None:
        enabled = node_class in _CONFIG[ConfigKeys.ENABLED.value]
        disabled = node_class in _CONFIG[ConfigKeys.DISABLED.value]
        if enabled and disabled:
            raise ValueError('Invalid configuration: Caching for {} is both enabled and disabled.'.format(node_class))
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
def enable_caching(node_class=None):
    """
    Context manager to enable caching, either for a specific node class, or globally.
    Note that this does not affect the behavior of the daemon, only the local Python instance.

    :param node_class: Node class for which caching should be enabled.
    """
    with _reset_config():
        if node_class is None:
            _CONFIG[ConfigKeys.DEFAULT.value] = True
        else:
            _CONFIG[ConfigKeys.ENABLED.value].append(node_class)
            try:
                _CONFIG[ConfigKeys.DISABLED.value].remove(node_class)
            except ValueError:
                pass
        yield


@contextmanager
def disable_caching(node_class=None):
    """
    Context manager to disable caching, either for a specific node class, or globally.
    Note that this does not affect the behavior of the daemon, only the local Python instance.

    :param node_class: Node class for which caching should be disabled.
    """
    with _reset_config():
        if node_class is None:
            _CONFIG[ConfigKeys.DEFAULT.value] = False
        else:
            _CONFIG[ConfigKeys.DISABLED.value].append(node_class)
            try:
                _CONFIG[ConfigKeys.ENABLED.value].remove(node_class)
            except ValueError:
                pass
        yield
