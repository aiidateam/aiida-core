# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA profile related code"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os

from aiida.common import extendeddicts

from .settings import DAEMON_DIR, DAEMON_LOG_DIR

__all__ = ('Profile',)

CIRCUS_PID_FILE_TEMPLATE = os.path.join(DAEMON_DIR, 'circus-{}.pid')
DAEMON_PID_FILE_TEMPLATE = os.path.join(DAEMON_DIR, 'aiida-{}.pid')
CIRCUS_LOG_FILE_TEMPLATE = os.path.join(DAEMON_LOG_DIR, 'circus-{}.log')
DAEMON_LOG_FILE_TEMPLATE = os.path.join(DAEMON_LOG_DIR, 'aiida-{}.log')
CIRCUS_PORT_FILE_TEMPLATE = os.path.join(DAEMON_DIR, 'circus-{}.port')
CIRCUS_SOCKET_FILE_TEMPATE = os.path.join(DAEMON_DIR, 'circus-{}.sockets')
CIRCUS_CONTROLLER_SOCKET_TEMPLATE = 'circus.c.sock'
CIRCUS_PUBSUB_SOCKET_TEMPLATE = 'circus.p.sock'
CIRCUS_STATS_SOCKET_TEMPLATE = 'circus.s.sock'


class Profile(object):  # pylint: disable=useless-object-inheritance
    """
    Convenience class that loads the current profile name and corresponding configuration and
    can subsequently provide profile specific information
    """

    KEY_DEFAULT_USER = 'default_user_email'
    KEY_PROFILE_UUID = 'PROFILE_UUID'
    RMQ_PREFIX = 'aiida-{uuid}'

    def __init__(self, name, dictionary):
        self._name = name
        self._dictionary = extendeddicts.AttributeDict(dictionary)

        # Currently, whether a profile is a test profile is solely determined by its name starting with 'test_'
        self._test_profile = bool(self.name.startswith('test_'))

    @staticmethod
    def generate_uuid():
        """
        Return a UUID for a new profile

        :returns: the hexadecimal represenation of a uuid4 UUID
        """
        from uuid import uuid4
        return uuid4().hex

    @property
    def dictionary(self):
        """
        Get the profile configuration dictionary

        :return: the profile configuration
        :rtype: dict
        """
        return self._dictionary

    @property
    def name(self):
        """
        Get the profile name

        :return: the profile name
        :rtype: str
        """
        return self._name

    @property
    def uuid(self):
        """
        Get the UUID of this profile

        :return: the profile UUID
        """
        return self.dictionary[self.KEY_PROFILE_UUID]

    @uuid.setter
    def uuid(self, uuid):
        """
        Set the UUID of this profile

        :param uuid: the UUID to set
        """
        self.dictionary[self.KEY_PROFILE_UUID] = uuid

    @property
    def rmq_prefix(self):
        """
        Get the RMQ prefix

        :return: the rmq prefix string
        :rtype: str
        """
        return self.RMQ_PREFIX.format(uuid=self.uuid)

    @property
    def is_test_profile(self):
        """
        Is this a test profile

        :return: True if test profile, False otherwise
        :rtype: bool
        """
        return self._test_profile

    @property
    def default_user_email(self):
        """
        Return the email (that is used as the username) configured during the first verdi setup.

        :return: the currently configured user email address or None if not defined
        :rtype: str or None
        """
        try:
            email = self.dictionary[self.KEY_DEFAULT_USER]
        except KeyError:
            email = None

        return email

    @property
    def filepaths(self):
        """
        Get the filepaths used by this profile

        :return: a dictionary of filepaths
        :rtype: dict
        """
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
