# -*- coding: utf-8 -*-
import click
import sys

from circus.exc import CallError
from click_spinner import spinner as cli_spinner

from aiida.cmdline.utils import decorators
from aiida.daemon.client import ProfileDaemonClient


@decorators.only_if_daemon_pid
def try_calling_running_client(client, cmd):
    """
    Call a given circus client with a given command only if pid file exists, handle timeout
    """
    result = None

    try:
        with cli_spinner():
            result = client.call(cmd)
    except CallError as err:
        if str(err) == 'Timed out.':
            click.echo('Daemon was not running but a PID file was found. '
                       'This indicates the daemon was terminated unexpectedly; '
                       'no action is required but proceed with caution.')
            sys.exit(0)
        raise err

    return result


class CircusClient(object):

    def __init__(self, profile_name):
        self._profile = ProfileDaemonClient(profile_name)

    @property
    def profile(self):
        return self._profile

    @property
    def profile_client(self):
        return self.profile.get_client()

    @property
    def is_daemon_running(self):
        return self.profile.get_daemon_pid is not None

    def get_status(self):
        """
        Get the daemon running status
        """
        command = {
            'command': 'status',
            'properties': {
                'name': self.profile.daemon_name
            }
        }

        return try_calling_running_client(self.profile_client, command)

    def get_worker_info(self):
        """
        Get workers statistics for this daemon
        """
        command = {
            'command': 'stats',
            'properties': {
                'name': self.profile.daemon_name
            }
        }

        return try_calling_running_client(self.profile_client, command)

    def get_daemon_info(self):
        """
        Get statistics about this daemon itself
        """
        command = {
            'command': 'dstats', 
            'properties': {}
        }

        return try_calling_running_client(self.profile_client, command)
