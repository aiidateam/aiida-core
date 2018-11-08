# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import os

from aiida.backends import settings
from aiida.common import setup


CONFIG_DIR = setup.AIIDA_CONFIG_FOLDER
DAEMON_DIR = 'daemon'
DAEMON_LOG_DIR = 'daemon/log'

CIRCUS_PID_FILE_TEMPLATE = os.path.join(CONFIG_DIR, DAEMON_DIR, 'circus-{}.pid')
DAEMON_PID_FILE_TEMPLATE = os.path.join(CONFIG_DIR, DAEMON_DIR, 'aiida-{}.pid')
CIRCUS_LOG_FILE_TEMPLATE = os.path.join(CONFIG_DIR, DAEMON_LOG_DIR, 'circus-{}.log')
DAEMON_LOG_FILE_TEMPLATE = os.path.join(CONFIG_DIR, DAEMON_LOG_DIR, 'aiida-{}.log')
CIRCUS_PORT_FILE_TEMPLATE = os.path.join(CONFIG_DIR, DAEMON_DIR, 'circus-{}.port')
CIRCUS_SOCKET_FILE_TEMPATE = os.path.join(CONFIG_DIR, DAEMON_DIR, 'circus-{}.sockets')
CIRCUS_CONTROLLER_SOCKET_TEMPLATE = 'circus.c.sock'
CIRCUS_PUBSUB_SOCKET_TEMPLATE = 'circus.p.sock'
CIRCUS_STATS_SOCKET_TEMPLATE = 'circus.s.sock'


def get_current_profile_name():
    """
    Return the currently configured profile name or if not set, the default profile
    """
    return settings.AIIDADB_PROFILE or setup.get_default_profile_name()


def get_profile_config(name=None):
    """
    Return the configuration of the currently active profile or if not set, the default profile

    :param name: the profile name whose configuration to return
    :return: the dictionary containing the profile configuration
    :raises MissingConfigurationError: if the configuration file cannot be found
    :raises ProfileConfigurationError: if the name is not found in the configuration file
    """
    from aiida.common.exceptions import MissingConfigurationError, ProfileConfigurationError
    from aiida.common.setup import get_config

    if name is None:
        name = get_current_profile_name()

    try:
        config = get_config()
    except MissingConfigurationError:
        raise MissingConfigurationError('could not load the configuration file')

    try:
        profile = config['profiles'][name]
    except KeyError:
        raise ProfileConfigurationError('invalid profile name "{}"'.format(name))

    return profile


def get_profile(name=None):
    """
    Return the profile for the given name or the default one if not specified.

    :param name: the profile name, will use the default profile if None
    :return: the profile
    :rtype: :class:`aiida.common.profile.Profile`
    :raises MissingConfigurationError: if the configuration file cannot be found
    :raises ProfileConfigurationError: if the name is not found in the configuration file
    """
    if name is None:
        name = get_current_profile_name()

    config = get_profile_config(name)
    return Profile(name, config)


class Profile(object):
    """
    Convenience class that loads the current profile name and corresponding configuration and
    can subsequently provide profile specific information
    """

    _RMQ_PREFIX = 'aiida-{uuid}'

    def __init__(self, name, config):
        self._name = name
        self._config = config

        # Currently, whether a profile is a test profile is solely determined by its name starting with 'test_'
        if self.name.startswith('test_'):
            self._test_profile = True
        else:
            self._test_profile = False

    def get_option(self, option):
        """Return the value of an option of this profile."""
        from aiida.common.setup import get_property
        return get_property(option)

    @property
    def config(self):
        return self._config

    @property
    def name(self):
        return self._name

    @property
    def uuid(self):
        return self.config[setup.PROFILE_UUID_KEY]

    @property
    def rmq_prefix(self):
        return self._RMQ_PREFIX.format(uuid=self.uuid)

    @property
    def is_test_profile(self):
        return self._test_profile

    @property
    def filepaths(self):
        return {
            'circus': {
                'log': CIRCUS_LOG_FILE_TEMPLATE.format(self.name),
                'pid': CIRCUS_PID_FILE_TEMPLATE.format(self.name),
                'port': CIRCUS_PORT_FILE_TEMPLATE.format(self.name),
                'socket': {
                    'file': CIRCUS_SOCKET_FILE_TEMPATE.format(self.name),
                    'controller': CIRCUS_CONTROLLER_SOCKET_TEMPLATE,
                    'pubsub': CIRCUS_PUBSUB_SOCKET_TEMPLATE,
                    'stats': CIRCUS_STATS_SOCKET_TEMPLATE,
                }
            },
            'daemon': {
                'log': DAEMON_LOG_FILE_TEMPLATE.format(self.name),
                'pid': DAEMON_PID_FILE_TEMPLATE.format(self.name),
            }
        }
