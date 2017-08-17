#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import yaml
try:
    from collections import ChainMap
except ImportError:
    from chainmap import ChainMap

from aiida.common.extendeddicts import Enumerate
from aiida.common.setup import AIIDA_CONFIG_FOLDER
from aiida.backends.utils import get_current_profile

__all__ = ['CONFIG']

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

def _get_config():
    try:
        with open(os.path.join(os.path.expanduser(AIIDA_CONFIG_FOLDER), 'cache_config.yml'), 'r') as f:
            config = yaml.load(f)[get_current_profile()]
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
            config[key] = ChainMap(config.get(key, {}), default_config)
        return config

    # no config file, or no config for this profile
    except (OSError, IOError, KeyError):
        return DEFAULT_CONFIG

CONFIG = _get_config()

def get_use_cache_default():
    return CONFIG[config_keys.use_cache][config_keys.default]

def get_fast_forward_enabled(class_name):
    fast_forward_config = CONFIG[config_keys.fast_forward]
    enabled = class_name in fast_forward_config[config_keys.enabled]
    disabled = class_name in fast_forward_config[config_keys.disabled]
    if enabled and disabled:
        raise ValueError('Invalid configuration: Fast-forwarding for {} is both enabled and disabled.'.format(class_name))
    elif enabled:
        return True
    elif disabled:
        return False
    else:
        return fast_forward_config[config_keys.default]
