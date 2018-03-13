# -*- coding: utf-8 -*-
import os
import sys

from aiida.common.profile import ProfileConfig


VERDI_BIN = os.path.abspath(os.path.join(sys.executable, '../verdi'))
VIRTUALENV = os.path.abspath(os.path.join(sys.executable, '../../'))


class DaemonClient(ProfileConfig):
    """
    Extension of the ProfileConfig which also provides handles to retrieve profile specific
    properties related to the daemon client
    """

    _DAEMON_NAME = 'aiida-{name}'

    @property
    def name(self):
        return self._DAEMON_NAME.format(name=self.profile_name)

    @property
    def cmd_string(self):
        return '{} -p {} devel run_daemon'.format(VERDI_BIN, self.profile_name)

    @property
    def get_daemon_pid(self):
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
        return self.filepaths['circus']['log']

    @property
    def circus_pid_file(self):
        return self.filepaths['circus']['pid']

    @property
    def daemon_log_file(self):
        return self.filepaths['daemon']['log']

    @property
    def daemon_pid_file(self):
        return self.filepaths['daemon']['pid']