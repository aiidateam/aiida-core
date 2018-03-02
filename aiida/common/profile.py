# -*- coding: utf-8 -*-
import os
import sys

from aiida.backends import settings
from aiida.common import setup
from aiida.cmdline.dbenv_lazyloading import with_dbenv


VERDI_BIN = os.path.abspath(os.path.join(sys.executable, '../verdi'))
VIRTUALENV = os.path.abspath(os.path.join(sys.executable, '../../'))


@with_dbenv()
def get_current_profile():
    return settings.AIIDADB_PROFILE


@with_dbenv()
def get_current_profile_config():
    return setup.get_profile_config(get_current_profile())


@with_dbenv()
def get_daemon_files():
    return {
        'circus': {
            'pid': setup.CIRCUS_PID_FILE_TEMPLATE.format(get_current_profile()),
            'log': setup.CIRCUS_LOG_FILE_TEMPLATE.format(get_current_profile()),
        },
        'daemon': {
            'pid': setup.DAEMON_PID_FILE_TEMPLATE.format(get_current_profile()),
            'log': setup.DAEMON_LOG_FILE_TEMPLATE.format(get_current_profile()),
        }
    }


class ProfileConfig(object):
    """
    Upon construction, the current profile name will be retrieved from the settings
    and the corresponding profile configuration will be loaded. The instance can
    then be used to inquire about all sorts of profile specific settings
    """

    _RMQ_PREFIX = 'aiida-{uuid}'
    _DAEMON_NAME = 'aiida-{name}'
    _ENDPOINT_TPL = 'tcp://127.0.0.1:{port}'

    def __init__(self):
        self.profile = get_current_profile()
        self.profile_config = get_current_profile_config()

    def get_endpoint(self, port_incr=0):
        port = self.profile_config[setup.CIRCUS_PORT_KEY]
        return self._ENDPOINT_TPL.format(port=port + port_incr)

    def get_client(self):
        return CircusClient(endpoint=self.get_endpoint(), timeout=0.5)

    @property
    def rmq_prefix(self):
    	profile_uuid = self.profile_config[setup.PROFILE_UUID_KEY]
        return self._RMQ_PREFIX.format(uuid=profile_uuid)

    @property
    def daemon_name(self):
        return self._DAEMON_NAME.format(name=self.profile)

    @property
    def cmd_string(self):
        return '{} -p {} devel run_daemon'.format(VERDI_BIN, self.profile)

    @classmethod
    def get_daemon_pid(cls):
        circus_pid_file = self.circus_pid_file
        if os.path.isfile(circus_pid_file):
            try:
                return int(open(circus_pid_file, 'r').read().strip())
            except (ValueError, IOError):
                return None
        else:
            return None

    @property
    def virtualenv(self):
    	return VIRTUALENV

    @property
    def circus_log_file(self):
        return get_daemon_files()['circus']['pid']

    @property
    def circus_pid_file(self):
        return get_daemon_files()['circus']['log']

    @property
    def daemon_pid_file(self):
        return get_daemon_files()['daemon']['pid']

    @property
    def daemon_log_file(self):
        return get_daemon_files()['daemon']['log']
