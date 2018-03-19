# -*- coding: utf-8 -*-
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
CIRCUS_CONTROLLER_SOCKET_TEMPLATE = os.path.join(CONFIG_DIR, DAEMON_DIR, 'circus-{}.controller.socket')
CIRCUS_PUBSUB_SOCKET_TEMPLATE = os.path.join(CONFIG_DIR, DAEMON_DIR, 'circus-{}.pubsub.socket')
CIRCUS_STATS_SOCKET_TEMPLATE = os.path.join(CONFIG_DIR, DAEMON_DIR, 'circus-{}.stats.socket') 


def get_current_profile_name():
    """
    Return the currently configured profile name or if not set, the default profile
    """
    return settings.AIIDADB_PROFILE or setup.get_default_profile()


def get_current_profile_config():
    """
    Return the configuration of the currently active profile or if not set, the default profile
    """
    return setup.get_profile_config(get_current_profile_name())


class ProfileConfig(object):
    """
    Convenience class that loads the current profile name and corresponding configuration and
    can subsequently provide profile specific information
    """

    _RMQ_PREFIX = 'aiida-{uuid}'

    def __init__(self, profile_name=None):
        """
        Construct the ProfileConfig for the given profile_name or retrieve it from
        the backend settings
        """
        if not profile_name:
            self.profile_name = get_current_profile_name()
            self.profile_config = get_current_profile_config()
        else:
            self.profile_name = profile_name
            self.profile_config = setup.get_profile_config(profile_name)

    @property
    def rmq_prefix(self):
    	profile_uuid = self.profile_config[setup.PROFILE_UUID_KEY]
        return self._RMQ_PREFIX.format(uuid=profile_uuid)

    @property
    def filepaths(self):
        return {
            'circus': {
                'log': CIRCUS_LOG_FILE_TEMPLATE.format(self.profile_name),
                'pid': CIRCUS_PID_FILE_TEMPLATE.format(self.profile_name),
                'port': CIRCUS_PORT_FILE_TEMPLATE.format(self.profile_name),
                'socket': {
                    'controller': CIRCUS_CONTROLLER_SOCKET_TEMPLATE.format(self.profile_name),
                    'pubsub': CIRCUS_PUBSUB_SOCKET_TEMPLATE.format(self.profile_name),
                    'stats': CIRCUS_STATS_SOCKET_TEMPLATE.format(self.profile_name),
                }
            },
            'daemon': {
                'log': DAEMON_LOG_FILE_TEMPLATE.format(self.profile_name),
                'pid': DAEMON_PID_FILE_TEMPLATE.format(self.profile_name),
            }
        }