# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Defines utilities for verifying the version of the configuration file and migrating it when necessary."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.common import exceptions
from .migrations import _MIGRATION_LOOKUP, CURRENT_CONFIG_VERSION

__all__ = ('check_and_migrate_config',)


def check_and_migrate_config(config):
    """Checks if the config needs to be migrated, and performs the migration if needed.

    :param config: the configuration dictionary
    :return: the migrated configuration dictionary
    """
    if config_needs_migrating(config):
        config = migrate_config(config)

    return config


def config_needs_migrating(config):
    """Checks if the config needs to be migrated.

    If the oldest compatible version of the configuration is higher than the current configuration version defined
    in the code, the config cannot be used and so the function will raise.

    :return: True if the configuration has an older version and needs to be migrated, False otherwise
    :raises ConfigurationVersionError: if the oldest compatible version of the config is higher than the current.
    """
    current_version = get_current_version(config)
    oldest_compatible_version = get_oldest_compatible_version(config)

    if oldest_compatible_version > CURRENT_CONFIG_VERSION:
        raise exceptions.ConfigurationVersionError(
            'The configuration file has version {} which is not compatible with the current version {}.'.format(
                current_version, CURRENT_CONFIG_VERSION))

    return CURRENT_CONFIG_VERSION > current_version


def migrate_config(config):
    """Run the registered configuration migrations until the version matches the current configuration version.

    :param config: the configuration dictionary
    :return: the migrated configuration dictionary
    """
    while get_current_version(config) < CURRENT_CONFIG_VERSION:
        config = _MIGRATION_LOOKUP[get_current_version(config)].apply(config)

    return config


def get_current_version(config):
    """Return the current version of the config.

    :return: current config version or 0 if not defined
    """
    return config.get('CONFIG_VERSION', {}).get('CURRENT', 0)


def get_oldest_compatible_version(config):
    """Return the current oldest compatible version of the config.

    :return: current oldest compatible config version or 0 if not defined
    """
    return config.get('CONFIG_VERSION', {}).get('OLDEST_COMPATIBLE', 0)
