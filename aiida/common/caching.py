#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import yaml
try:
    from collections import ChainMap
except ImportError:
    from chainmap import ChainMap

from plum.util import load_class
from future.utils import raise_from
from plum.exceptions import ClassNotFoundException

import aiida
from aiida.common.exceptions import ConfigurationError
from aiida.common.extendeddicts import Enumerate
from aiida.common.setup import AIIDA_CONFIG_FOLDER
from aiida.backends.utils import get_current_profile

__all__ = ['get_use_cache', 'get_use_cache_default']

config_keys = Enumerate((
    'default', 'enabled', 'disabled'
))

DEFAULT_CONFIG = {
    config_keys.default: False,
    config_keys.enabled: [],
    config_keys.disabled: [],
}

def _get_config(config_file):
    try:
        with open(config_file, 'r') as f:
            config = yaml.load(f)[get_current_profile()]
    # no config file, or no config for this profile
    except (OSError, IOError, KeyError):
        return DEFAULT_CONFIG

    # validate configuration
    for key in config:
        if key not in DEFAULT_CONFIG:
            raise ValueError(
                "Configuration error: Invalid key '{}' in cache_config.yml".format(key)
            )

    # add defaults where config is missing
    for key, default_config in DEFAULT_CONFIG.items():
        config[key] = config.get(key, default_config)

    # load classes
    try:
        for key in [config_keys.enabled, config_keys.disabled]:
            config[key] = [load_class(c) for c in config[key]]
    except (ImportError, ClassNotFoundException) as err:
        raise_from(
            ConfigurationError("Unknown class given in 'cache_config.yml': '{}'".format(err)),
            err
        )
    return config

_CONFIG = {}

def configure(config_file=os.path.join(os.path.expanduser(AIIDA_CONFIG_FOLDER), 'cache_config.yml')):
    """
    Reads the caching configuration file and sets the _CONFIG variable.
    """
    global _CONFIG
    _CONFIG.clear()
    _CONFIG.update(_get_config(config_file=config_file))

def get_use_cache_default():
    if not _CONFIG:
        configure()
    return _CONFIG[config_keys.default]

def get_use_cache(calc_class):
    if not _CONFIG:
        configure()
    enabled = calc_class in _CONFIG[config_keys.enabled]
    disabled = calc_class in _CONFIG[config_keys.disabled]
    if enabled and disabled:
        raise ValueError('Invalid configuration: Fast-forwarding for {} is both enabled and disabled.'.format(calc_class))
    elif enabled:
        return True
    elif disabled:
        return False
    else:
        return get_use_cache_default()
