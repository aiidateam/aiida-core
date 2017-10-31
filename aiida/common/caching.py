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

__all__ = ['get_fast_forward_enabled', 'get_use_cache_default']

config_keys = Enumerate((
    'use_cache', 'fast_forward', 'default', 'enabled', 'disabled'
))

DEFAULT_CONFIG = {
    config_keys.use_cache: {config_keys.default: False},
    config_keys.fast_forward: {
        config_keys.default: False,
        config_keys.enabled: [],
        config_keys.disabled: [],
    }
}

def _get_config(config_file):
    try:
        with open(config_file, 'r') as f:
            config = yaml.load(f)[get_current_profile()]
    # no config file, or no config for this profile
    except (OSError, IOError, KeyError):
        return DEFAULT_CONFIG

    # validate configuration
    for key, value in config.items():
        error_msg = "Configuration error: Invalid key '{}' in cache_config.yml"
        if key not in DEFAULT_CONFIG:
            raise ValueError(error_msg.format(key))
        for sub_key in value:
            if sub_key not in DEFAULT_CONFIG[key]:
                raise ValueError(error_msg.format(sub_key))

    # add defaults where config is missing
    for key, default_config in DEFAULT_CONFIG.items():
        config[key] = config.get(key, {})
        for sub_key, sub_default_config in default_config.items():
            config[key][sub_key] = config[key].get(sub_key, sub_default_config)

    # load classes
    try:
        for config_part in config.values():
            for key in [config_keys.enabled, config_keys.disabled]:
                if key in config_part:
                    config_part[key] = [load_class(c) for c in config_part[key]]
    except (ImportError, ClassNotFoundException) as err:
        raise_from(
            ConfigurationError("Unknown class given in 'cache_config.yml': '{}'".format(err)),
            err
        )
    return config

CONFIG = {}

def configure(config_file=os.path.join(os.path.expanduser(AIIDA_CONFIG_FOLDER), 'cache_config.yml')):
    """
    Reads the caching configuration file and sets the CONFIG variable.
    """
    global CONFIG
    CONFIG.clear()
    CONFIG.update(_get_config(config_file=config_file))

def get_use_cache_default():
    if not CONFIG:
        configure()
    return CONFIG[config_keys.use_cache][config_keys.default]

def get_fast_forward_enabled(calc_class):
    if not CONFIG:
        configure()
    fast_forward_config = CONFIG[config_keys.fast_forward]
    enabled = calc_class in fast_forward_config[config_keys.enabled]
    disabled = calc_class in fast_forward_config[config_keys.disabled]
    if enabled and disabled:
        raise ValueError('Invalid configuration: Fast-forwarding for {} is both enabled and disabled.'.format(calc_class))
    elif enabled:
        return True
    elif disabled:
        return False
    else:
        return fast_forward_config[config_keys.default]
