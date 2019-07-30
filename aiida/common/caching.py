#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import os
import copy
from functools import wraps
from contextlib import contextmanager

import yaml
from plum.util import load_class
from future.utils import raise_from
from plum.exceptions import ClassNotFoundException

import aiida
from aiida.common.exceptions import ConfigurationError
from aiida.common.extendeddicts import Enumerate
from aiida.common.setup import AIIDA_CONFIG_FOLDER
from aiida.backends.utils import get_current_profile

__all__ = ['get_use_cache', 'enable_caching', 'disable_caching']

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

def _with_config(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if not _CONFIG:
            configure()
        return func(*args, **kwargs)
    return inner

@_with_config
def get_use_cache(node_class=None):
    if node_class is not None:
        enabled = node_class in _CONFIG[config_keys.enabled]
        disabled = node_class in _CONFIG[config_keys.disabled]
        if enabled and disabled:
            raise ValueError('Invalid configuration: Caching for {} is both enabled and disabled.'.format(node_class))
        elif enabled:
            return True
        elif disabled:
            return False
    return _CONFIG[config_keys.default]

@contextmanager
@_with_config
def _reset_config():
    global _CONFIG
    config_copy = copy.deepcopy(_CONFIG)
    yield
    _CONFIG.clear()
    _CONFIG.update(config_copy)

@contextmanager
def enable_caching(node_class=None):
    with _reset_config():
        if node_class is None:
            _CONFIG[config_keys.default] = True
        else:
            _CONFIG[config_keys.enabled].append(node_class)
        yield

@contextmanager
def disable_caching(node_class=None):
    with _reset_config():
        if node_class is None:
            _CONFIG[config_keys.default] = True
        else:
            _CONFIG[config_keys.disabled].append(node_class)
        yield
