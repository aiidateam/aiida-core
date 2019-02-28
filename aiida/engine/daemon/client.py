# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Controls the daemon
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import enum
import io
import os
import shutil
import socket
import tempfile

import six

from aiida.common.files import which
from aiida.manage.configuration import get_config

VERDI_BIN = which('verdi')
# Recent versions of virtualenv create the environment variable VIRTUAL_ENV
VIRTUALENV = os.environ.get('VIRTUAL_ENV', None)


class ControllerProtocol(enum.Enum):  # pylint: disable=too-few-public-methods
    """
    The protocol to use to for the controller of the Circus daemon
    """

    IPC = 0
    TCP = 1


def get_daemon_client(profile_name=None):
    """
    Return the daemon client for the given profile or the current profile if not specified.

    :param profile_name: the profile name, will use the current profile if None
    :return: the daemon client
    :rtype: :class:`aiida.engine.daemon.client.DaemonClient`
    :raises aiida.common.MissingConfigurationError: if the configuration file cannot be found
    :raises aiida.common.ProfileConfigurationError: if the given profile does not exist
    """
    config = get_config()

    if profile_name:
        profile = config.get_profile(profile_name)
    else:
        profile = config.current_profile

    return DaemonClient(profile)


class DaemonClient(object):  # pylint: disable=too-many-public-methods,useless-object-inheritance
    """
    Extension of the Profile which also provides handles to retrieve profile specific
    properties related to the daemon client
    """

    DAEMON_ERROR_NOT_RUNNING = 'daemon-error-not-running'
    DAEMON_ERROR_TIMEOUT = 'daemon-error-timeout'

    _DAEMON_NAME = 'aiida-{name}'
    _DEFAULT_LOGLEVEL = 'INFO'
    _ENDPOINT_PROTOCOL = ControllerProtocol.IPC

    def __init__(self, profile):
        """
        Construct a DaemonClient instance for a given profile

        :param profile: the profile instance :class:`aiida.manage.configuration.profile.Profile`
        """
        config = get_config()
        self._profile = profile
        self._SOCKET_DIRECTORY = None  # pylint: disable=invalid-name
        self._DAEMON_TIMEOUT = config.option_get('daemon.timeout')  # pylint: disable=invalid-name

    @property
    def profile(self):
        return self._profile

    @property
    def daemon_name(self):
        """
        Get the daemon name which is tied to the profile name
        """
        return self._DAEMON_NAME.format(name=self.profile.name)

    @property
    def cmd_string(self):
        """
        Return the command string to start the AiiDA daemon
        """
        from aiida.common.exceptions import ConfigurationError
        if VERDI_BIN is None:
            raise ConfigurationError("Unable to find 'verdi' in the path. Make sure that you are working "
                                     "in a virtual environment, or that at least the 'verdi' executable is on the PATH")
        return '{} -p {} devel run_daemon'.format(VERDI_BIN, self.profile.name)

    @property
    def loglevel(self):
        return self._DEFAULT_LOGLEVEL

    @property
    def virtualenv(self):
        return VIRTUALENV

    @property
    def circus_log_file(self):
        return self.profile.filepaths['circus']['log']

    @property
    def circus_pid_file(self):
        return self.profile.filepaths['circus']['pid']

    @property
    def circus_port_file(self):
        return self.profile.filepaths['circus']['port']

    @property
    def circus_socket_file(self):
        return self.profile.filepaths['circus']['socket']['file']

    @property
    def circus_socket_endpoints(self):
        return self.profile.filepaths['circus']['socket']

    @property
    def daemon_log_file(self):
        return self.profile.filepaths['daemon']['log']

    @property
    def daemon_pid_file(self):
        return self.profile.filepaths['daemon']['pid']

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
                with io.open(self.circus_port_file, 'r', encoding='utf8') as fhandle:
                    return int(fhandle.read().strip())
            except (ValueError, IOError):
                raise RuntimeError('daemon is running so port file should have been there but could not read it')
        else:
            port = self.get_available_port()
            with io.open(self.circus_port_file, 'w', encoding='utf8') as fhandle:
                fhandle.write(six.text_type(port))

            return port

    def get_circus_socket_directory(self):
        """
        Retrieve the absolute path of the directory where the circus sockets are stored if the IPC protocol is
        used and the daemon is running. If the daemon is running, the sockets file should exist and contain the
        absolute path of the directory that contains the sockets of the circus endpoints. If it cannot be read,
        a RuntimeError will be thrown. If the daemon is not running, a temporary directory will be created and
        its path will be written to the sockets file and returned.

        .. note:: A temporary folder needs to be used for the sockets because UNIX limits the filepath length to
            107 bytes. Placing the socket files in the AiiDA config folder might seem like the more logical choice
            but that folder can be placed in an arbitrarily nested directory, the socket filename will exceed the
            limit. The solution is therefore to always store them in the temporary directory of the operation system
            whose base path is typically short enough as to not exceed the limit

        :return: the absolute path of directory to write the sockets to
        """
        if self.is_daemon_running:
            try:
                return io.open(self.circus_socket_file, 'r', encoding='utf8').read().strip()
            except (ValueError, IOError):
                raise RuntimeError('daemon is running so sockets file should have been there but could not read it')
        else:

            # The SOCKET_DIRECTORY is already set, a temporary directory was already created and the same should be used
            if self._SOCKET_DIRECTORY is not None:
                return self._SOCKET_DIRECTORY

            socket_dir_path = tempfile.mkdtemp()
            with io.open(self.circus_socket_file, 'w', encoding='utf8') as fhandle:
                fhandle.write(six.text_type(socket_dir_path))

            self._SOCKET_DIRECTORY = socket_dir_path
            return socket_dir_path

    def get_daemon_pid(self):
        """
        Get the daemon pid which should be written in the daemon pid file specific to the profile

        :return: the pid of the circus daemon process or None if not found
        """
        if os.path.isfile(self.circus_pid_file):
            try:
                return int(io.open(self.circus_pid_file, 'r', encoding='utf8').read().strip())
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
        return self.get_daemon_pid() is not None

    def delete_circus_socket_directory(self):
        """
        Attempt to delete the directory used to store the circus endpoint sockets. Will not raise if the
        directory does not exist
        """
        directory = self.get_circus_socket_directory()

        try:
            shutil.rmtree(directory)
        except OSError as exception:
            if exception.errno == 2:
                pass
            else:
                raise

    @classmethod
    def get_available_port(cls):
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
            endpoint = self.get_ipc_endpoint('controller')
        elif self._ENDPOINT_PROTOCOL == ControllerProtocol.TCP:
            endpoint = self.get_tcp_endpoint(self.get_circus_port())
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
            endpoint = self.get_ipc_endpoint('pubsub')
        elif self._ENDPOINT_PROTOCOL == ControllerProtocol.TCP:
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
            endpoint = self.get_ipc_endpoint('stats')
        elif self._ENDPOINT_PROTOCOL == ControllerProtocol.TCP:
            endpoint = self.get_tcp_endpoint()
        else:
            raise ValueError('invalid controller protocol {}'.format(self._ENDPOINT_PROTOCOL))

        return endpoint

    def get_ipc_endpoint(self, endpoint):
        """
        Get the ipc endpoint string for a circus daemon endpoint for a given socket

        :param endpoint: the circus endpoint for which to return a socket
        :return: the ipc endpoint string
        """
        filepath = self.get_circus_socket_directory()
        filename = self.circus_socket_endpoints[endpoint]
        template = 'ipc://{filepath}/{filename}'
        endpoint = template.format(filepath=filepath, filename=filename)

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
        from circus.client import CircusClient
        return CircusClient(endpoint=self.get_controller_endpoint(), timeout=self._DAEMON_TIMEOUT)

    def call_client(self, command):
        """
        Call the client with a specific command. Will check whether the daemon is running first
        by checking for the pid file. When the pid is found yet the call still fails with a
        timeout, this means the daemon was actually not running and it was terminated unexpectedly
        causing the pid file to not be cleaned up properly

        :param command: command to call the circus client with
        :return: the result of the circus client call
        """
        from circus.exc import CallError

        if not self.get_daemon_pid():
            return {'status': self.DAEMON_ERROR_NOT_RUNNING}

        try:
            result = self.client.call(command)
        except CallError as exception:
            if str(exception) == 'Timed out.':
                return {'status': self.DAEMON_ERROR_TIMEOUT}
            raise exception

        return result

    def get_status(self):
        """
        Get the daemon running status

        :return: the client call response
        """
        command = {'command': 'status', 'properties': {'name': self.daemon_name}}

        return self.call_client(command)

    def get_worker_info(self):
        """
        Get workers statistics for this daemon

        :return: the client call response
        """
        command = {'command': 'stats', 'properties': {'name': self.daemon_name}}

        return self.call_client(command)

    def get_daemon_info(self):
        """
        Get statistics about this daemon itself

        :return: the client call response
        """
        command = {'command': 'dstats', 'properties': {}}

        return self.call_client(command)

    def increase_workers(self, number):
        """
        Increase the number of workers

        :param number: the number of workers to add
        :return: the client call response
        """
        command = {'command': 'incr', 'properties': {'name': self.daemon_name, 'nb': number}}

        return self.call_client(command)

    def decrease_workers(self, number):
        """
        Decrease the number of workers

        :param number: the number of workers to remove
        :return: the client call response
        """
        command = {'command': 'decr', 'properties': {'name': self.daemon_name, 'nb': number}}

        return self.call_client(command)

    def stop_daemon(self, wait):
        """
        Stop the daemon

        :param wait: boolean to indicate whether to wait for the result of the command
        :return: the client call response
        """
        command = {'command': 'quit', 'properties': {'waiting': wait}}

        result = self.call_client(command)

        if self._ENDPOINT_PROTOCOL == ControllerProtocol.IPC:
            self.delete_circus_socket_directory()

        return result

    def restart_daemon(self, wait):
        """
        Restart the daemon

        :param wait: boolean to indicate whether to wait for the result of the command
        :return: the client call response
        """
        command = {'command': 'restart', 'properties': {'name': self.daemon_name, 'waiting': wait}}

        return self.call_client(command)
