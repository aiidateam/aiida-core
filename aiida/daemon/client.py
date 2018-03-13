# -*- coding: utf-8 -*-
import os
import sys

from circus.client import CircusClient
from circus.exc import CallError

from aiida.common.profile import ProfileConfig


VERDI_BIN = os.path.abspath(os.path.join(sys.executable, '../verdi'))
VIRTUALENV = os.path.abspath(os.path.join(sys.executable, '../../'))


class DaemonClient(ProfileConfig):
    """
    Extension of the ProfileConfig which also provides handles to retrieve profile specific
    properties related to the daemon client
    """

    _DAEMON_NAME = 'aiida-{name}'
    _ENDPOINT_TPL = 'tcp://127.0.0.1:{port}'

    @property
    def daemon_name(self):
        return self._DAEMON_NAME.format(name=self.profile_name)

    @property
    def cmd_string(self):
        return '{} -p {} devel run_daemon'.format(VERDI_BIN, self.profile_name)

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

    @property
    def get_daemon_pid(self):
        if os.path.isfile(self.circus_pid_file):
            try:
                return int(open(self.circus_pid_file, 'r').read().strip())
            except (ValueError, IOError):
                return None
        else:
            return None

    @property
    def is_daemon_running(self):
        return self.get_daemon_pid is not None

    def get_endpoint(self, port_incr=0):
        return self._ENDPOINT_TPL.format(port=self.circus_port + port_incr)

    @property
    def client(self):
        return CircusClient(endpoint=self.get_endpoint(), timeout=0.5)

    def call_client(self, command):
        """
        Call the client with a specific command. Will check whether the daemon is running first
        by checking for the pid file. When the pid is found yet the call still fails with a
        timeout, this means the daemon was actually not running and it was terminated unexpectedly
        causing the pid file to not be cleaned up properly
        """
        if not self.get_daemon_pid:
            return {'status': 'The daemon is not running'}

        try:
            result = self.client.call(command)
        except CallError as exception:
            if str(exception) == 'Timed out.':
                return {
                    'status': 'Daemon was not running but a PID file was found. '
                    'This indicates the daemon was terminated unexpectedly; '
                    'no action is required but proceed with caution.'
                }
            raise exception

        return result

    def get_status(self):
        """
        Get the daemon running status
        """
        command = {
            'command': 'status',
            'properties': {
                'name': self.daemon_name
            }
        }

        return self.call_client(command)

    def get_worker_info(self):
        """
        Get workers statistics for this daemon
        """
        command = {
            'command': 'stats',
            'properties': {
                'name': self.daemon_name
            }
        }

        return self.call_client(command)

    def get_daemon_info(self):
        """
        Get statistics about this daemon itself
        """
        command = {
            'command': 'dstats',
            'properties': {}
        }

        return self.call_client(command)

    def increase_workers(self, number):
        """
        Increase the number of workers

        :param number: the number of workers to add
        """
        command = {
            'command': 'incr',
            'properties': {
                'name': self.daemon_name,
                'nb': number
            }
        }

        return self.call_client(command)

    def decrease_workers(self, number):
        """
        Decrease the number of workers

        :param number: the number of workers to remove
        """
        command = {
            'command': 'decr',
            'properties': {
                'name': self.daemon_name,
                'nb': number
            }
        }

        return self.call_client(command)

    def stop_daemon(self, wait):
        """
        Stop the daemon

        :param wait: boolean to indicate whether to wait for the result of the command
        """
        command = {
            'command': 'quit',
            'properties': {
                'waiting': wait
            }
        }

        return self.call_client(command)

    def restart_daemon(self, wait):
        """
        Restart the daemon

        :param wait: boolean to indicate whether to wait for the result of the command
        """
        command = {
            'command': 'restart',
            'properties': {
                'name': self.daemon_name,
                'waiting': wait
            }
        }

        return self.call_client(command)
