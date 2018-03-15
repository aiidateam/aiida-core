# -*- coding: utf-8 -*-
import enum
import os
import socket
import sys

from circus.client import CircusClient
from circus.exc import CallError

from aiida.common.profile import ProfileConfig


VERDI_BIN = os.path.abspath(os.path.join(sys.executable, '../verdi'))
VIRTUALENV = os.path.abspath(os.path.join(sys.executable, '../../'))


class ControllerProtocol(enum.Enum):
    """
    The protocol to use to for the controller of the Circus daemon
    """

    IPC = 0
    TCP = 1


class DaemonClient(ProfileConfig):
    """
    Extension of the ProfileConfig which also provides handles to retrieve profile specific
    properties related to the daemon client
    """

    DAEMON_ERROR = 'daemon-error'
    _DAEMON_NAME = 'aiida-{name}'
    _DEFAULT_LOGLEVEL = 'INFO'
    _ENDPOINT_PROTOCOL = ControllerProtocol.IPC

    @property
    def daemon_name(self):
        """
        Get the daemon name which is tied to the profile name
        """
        return self._DAEMON_NAME.format(name=self.profile_name)

    @property
    def cmd_string(self):
        """
        Return the command string to start the AiiDA daemon
        """
        return '{} -p {} devel run_daemon'.format(VERDI_BIN, self.profile_name)

    @property
    def loglevel(self):
        return self._DEFAULT_LOGLEVEL

    @property
    def virtualenv(self):
        return VIRTUALENV

    @property
    def circus_sockets(self):
        return self.filepaths['circus']['socket']

    @property
    def circus_log_file(self):
        return self.filepaths['circus']['log']

    @property
    def circus_pid_file(self):
        return self.filepaths['circus']['pid']

    @property
    def circus_port_file(self):
        return self.filepaths['circus']['port']

    @property
    def daemon_log_file(self):
        return self.filepaths['daemon']['log']

    @property
    def daemon_pid_file(self):
        return self.filepaths['daemon']['pid']

    @property
    def get_circus_port(self):
        """
        Retrieve the port for the circus controller, which should be written to the circus port file. If the 
        daemon is running, the port file should exist and contain the port to which the controller is connected.
        If it cannot be read, a RuntimeError will be thrown. If the daemon is not running, an available port
        will be requested from the operating system, written to the port file and returned

        :return: the port for the circus controller
        """
        if self.is_daemon_running:
            try:
                return int(open(self.circus_port_file, 'r').read().strip())
            except (ValueError, IOError):
                raise RuntimeError('daemon is running so port file should have been there but could not read it')
        else:
            port = self.get_available_port()
            with open(self.circus_port_file, 'w') as handle:
                handle.write(str(port))

            return port

    @property
    def get_daemon_pid(self):
        """
        Get the daemon pid which should be written in the daemon pid file specific to the profile

        :return: the pid of the circus daemon process or None if not found
        """
        if os.path.isfile(self.circus_pid_file):
            try:
                return int(open(self.circus_pid_file, 'r').read().strip())
            except (ValueError, IOError):
                return None
        else:
            return None

    @property
    def is_daemon_running(self):
        """
        Return whether the daemon is running, which is determined by seeing if the daemon pid file is present

        :return: True if daemon is running, False otherwise
        """
        return self.get_daemon_pid is not None

    def get_available_port(self):
        """
        Get an available port from the operating system

        :return: a currently available port
        """
        open_socket = socket.socket()
        open_socket.bind(('', 0))
        return open_socket.getsockname()[1]

    def get_controller_endpoint(self):
        """
        Get the endpoint string for the circus controller. For the IPC protocol a profile specific
        socket will be used, whereas for the TCP protocol an available port will be found and
        saved in the profile specific port file

        :return: the endpoint string
        """
        if self._ENDPOINT_PROTOCOL == ControllerProtocol.IPC:
            endpoint = self.get_ipc_endpoint(self.circus_sockets['controller'])
        elif  self._ENDPOINT_PROTOCOL == ControllerProtocol.TCP:
            endpoint = self.get_tcp_endpoint(self.get_circus_port)
        else:
            raise ValueError('invalid controller protocol {}'.format(self._ENDPOINT_PROTOCOL))

        return endpoint

    def get_pubsub_endpoint(self):
        """
        Get the endpoint string for the circus pubsub endpoint. For the IPC protocol a profile specific
        socket will be used, whereas for the TCP protocol any available port will be used

        :return: the endpoint string
        """
        if self._ENDPOINT_PROTOCOL == ControllerProtocol.IPC:
            endpoint = self.get_ipc_endpoint(self.circus_sockets['pubsub'])
        elif  self._ENDPOINT_PROTOCOL == ControllerProtocol.TCP:
            endpoint = self.get_tcp_endpoint()
        else:
            raise ValueError('invalid controller protocol {}'.format(self._ENDPOINT_PROTOCOL))

        return endpoint

    def get_stats_endpoint(self):
        """
        Get the endpoint string for the circus stats endpoint. For the IPC protocol a profile specific
        socket will be used, whereas for the TCP protocol any available port will be used

        :return: the endpoint string
        """
        if self._ENDPOINT_PROTOCOL == ControllerProtocol.IPC:
            endpoint = self.get_ipc_endpoint(self.circus_sockets['stats'])
        elif  self._ENDPOINT_PROTOCOL == ControllerProtocol.TCP:
            endpoint = self.get_tcp_endpoint()
        else:
            raise ValueError('invalid controller protocol {}'.format(self._ENDPOINT_PROTOCOL))

        return endpoint

    def get_ipc_endpoint(self, socket):
        """
        Get the ipc endpoint string for a circus daemon endpoint for a given socket

        :param socket: absolute path to socket
        :return: the ipc endpoint string
        """
        template = 'ipc://{socket}'
        endpoint = template.format(socket=socket)

        return endpoint

    def get_tcp_endpoint(self, port=None):
        """
        Get the tcp endpoint string for a circus daemon endpoint. If the port is unspecified,
        the operating system will be asked for a currently available port.

        :param port: a port to use for the endpoint
        :return: the tcp endpoint string
        """
        if port is None:
            port = self.get_available_port()

        template = 'tcp://127.0.0.1:{port}'
        endpoint = template.format(port=port)

        return endpoint

    @property
    def client(self):
        """
        Return an instance of the CircusClient with the endpoint defined by the controller endpoint, which
        used the port that was written to the port file upon starting of the daemon

        :return: CircucClient instance
        """
        return CircusClient(endpoint=self.get_controller_endpoint(), timeout=0.5)

    def call_client(self, command):
        """
        Call the client with a specific command. Will check whether the daemon is running first
        by checking for the pid file. When the pid is found yet the call still fails with a
        timeout, this means the daemon was actually not running and it was terminated unexpectedly
        causing the pid file to not be cleaned up properly

        :param command: command to call the circus client with
        :return: the result of the circus client call
        """
        if not self.get_daemon_pid:
            return {'status': self.DAEMON_ERROR}

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

        :return: the client call response
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

        :return: the client call response
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

        :return: the client call response
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
        :return: the client call response
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
        :return: the client call response
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
        :return: the client call response
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
        :return: the client call response
        """
        command = {
            'command': 'restart',
            'properties': {
                'name': self.daemon_name,
                'waiting': wait
            }
        }

        return self.call_client(command)
