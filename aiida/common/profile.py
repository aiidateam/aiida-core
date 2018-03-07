# -*- coding: utf-8 -*-
from aiida.backends import settings
from aiida.common import setup


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
    def circus_port(self):
        circus_port = self.profile_config[setup.CIRCUS_PORT_KEY]
        return circus_port

    @property
    def rmq_prefix(self):
    	profile_uuid = self.profile_config[setup.PROFILE_UUID_KEY]
        return self._RMQ_PREFIX.format(uuid=profile_uuid)

    @property
    def filepaths(self):
        return {
            'circus': {
                'pid': setup.CIRCUS_PID_FILE_TEMPLATE.format(self.profile_name),
                'log': setup.CIRCUS_LOG_FILE_TEMPLATE.format(self.profile_name),
            },
            'daemon': {
                'pid': setup.DAEMON_PID_FILE_TEMPLATE.format(self.profile_name),
                'log': setup.DAEMON_LOG_FILE_TEMPLATE.format(self.profile_name),
            }
        }