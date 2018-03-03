# -*- coding: utf-8 -*-
from aiida.backends import settings
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common import setup


@with_dbenv()
def get_current_profile_name():
    """
    Return the currently configured profile name
    """
    return settings.AIIDADB_PROFILE


@with_dbenv()
def get_current_profile_config():
    """
    Return the configuration of the currently active profile
    """
    return setup.get_profile_config(get_current_profile_name())


class ProfileConfig(object):
    """
    Convenience class that loads the current profile name and corresponding configuration and
    can subsequently provide profile specific information
    """

    _RMQ_PREFIX = 'aiida-{uuid}'

    def __init__(self):
        self.profile_name = get_current_profile_name()
        self.profile_config = get_current_profile_config()

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