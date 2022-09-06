# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Client to interact with the daemon."""
from __future__ import annotations

import contextlib
import enum
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import typing as t
from typing import TYPE_CHECKING

from aiida.common.exceptions import AiidaException, ConfigurationError
from aiida.common.lang import type_check
from aiida.manage.configuration import get_config, get_config_option
from aiida.manage.configuration.profile import Profile
from aiida.manage.manager import get_manager

if TYPE_CHECKING:
    from circus.client import CircusClient

VERDI_BIN = shutil.which('verdi')
# Recent versions of virtualenv create the environment variable VIRTUAL_ENV
VIRTUALENV = os.environ.get('VIRTUAL_ENV', None)

# see https://github.com/python/typing/issues/182
JsonDictType = t.Dict[str, t.Any]

__all__ = ('DaemonClient',)


class ControllerProtocol(enum.Enum):
    """The protocol to use for the controller of the Circus daemon."""

    IPC = 0
    TCP = 1


class DaemonException(AiidaException):
    """Raised when the starting of the daemon failed."""


def get_daemon_client(profile_name: str | None = None) -> 'DaemonClient':
    """Return the daemon client for the given profile or the current profile if not specified.

    :param profile_name: Optional profile name to load.
    :return: The daemon client.

    :raises aiida.common.MissingConfigurationError: if the configuration file cannot be found.
    :raises aiida.common.ProfileConfigurationError: if the given profile does not exist.
    """
    profile = get_manager().load_profile(profile_name)
    return DaemonClient(profile)


class DaemonClient:  # pylint: disable=too-many-public-methods
    """Client to interact with the daemon."""

    DAEMON_ERROR_NOT_RUNNING = 'daemon-error-not-running'
    DAEMON_ERROR_TIMEOUT = 'daemon-error-timeout'

    _DAEMON_NAME = 'aiida-{name}'
    _ENDPOINT_PROTOCOL = ControllerProtocol.IPC

    def __init__(self, profile: Profile):
        """Construct an instance for a given profile.

        :param profile: The profile instance.
        """
        type_check(profile, Profile)
        config = get_config()
        self._profile = profile
        self._SOCKET_DIRECTORY: str | None = None  # pylint: disable=invalid-name
        self._DAEMON_TIMEOUT: int = config.get_option('daemon.timeout')  # pylint: disable=invalid-name

    @property
    def profile(self) -> Profile:
        return self._profile

    @property
    def daemon_name(self) -> str:
        """Get the daemon name which is tied to the profile name."""
        return self._DAEMON_NAME.format(name=self.profile.name)

    @property
    def _verdi_bin(self) -> str:
        """Return the absolute path to the ``verdi`` binary.

        :raises ConfigurationError: If the path to ``verdi`` could not be found
        """
        if VERDI_BIN is None:
            raise ConfigurationError(
                "Unable to find 'verdi' in the path. Make sure that you are working "
                "in a virtual environment, or that at least the 'verdi' executable is on the PATH"
            )

        return VERDI_BIN

    def cmd_start_daemon(self, number_workers: int = 1, foreground: bool = False) -> list[str]:
        """Return the command to start the daemon.

        :param number_workers: Number of daemon workers to start.
        :param foreground: Whether to launch the subprocess in the background or not.
        """
        command = [self._verdi_bin, '-p', self.profile.name, 'daemon', 'start-circus', str(number_workers)]

        if foreground:
            command.append('--foreground')

        return command

    @property
    def cmd_start_daemon_worker(self) -> list[str]:
        """Return the command to start a daemon worker process."""
        return [self._verdi_bin, '-p', self.profile.name, 'daemon', 'worker']

    @property
    def loglevel(self) -> str:
        return get_config_option('logging.circus_loglevel')

    @property
    def virtualenv(self) -> str | None:
        return VIRTUALENV

    @property
    def circus_log_file(self) -> str:
        return self.profile.filepaths['circus']['log']

    @property
    def circus_pid_file(self) -> str:
        return self.profile.filepaths['circus']['pid']

    @property
    def circus_port_file(self) -> str:
        return self.profile.filepaths['circus']['port']

    @property
    def circus_socket_file(self) -> str:
        return self.profile.filepaths['circus']['socket']['file']

    @property
    def circus_socket_endpoints(self) -> dict[str, str]:
        return self.profile.filepaths['circus']['socket']

    @property
    def daemon_log_file(self) -> str:
        return self.profile.filepaths['daemon']['log']

    @property
    def daemon_pid_file(self) -> str:
        return self.profile.filepaths['daemon']['pid']

    def get_circus_port(self) -> int:
        """Retrieve the port for the circus controller, which should be written to the circus port file.

        If the daemon is running, the port file should exist and contain the port to which the controller is connected.
        If it cannot be read, a RuntimeError will be thrown. If the daemon is not running, an available port will be
        requested from the operating system, written to the port file and returned.

        :return: The port for the circus controller.
        """
        if self.is_daemon_running:
            try:
                with open(self.circus_port_file, 'r', encoding='utf8') as fhandle:
                    return int(fhandle.read().strip())
            except (ValueError, IOError):
                raise RuntimeError('daemon is running so port file should have been there but could not read it')
        else:
            port = self.get_available_port()
            with open(self.circus_port_file, 'w', encoding='utf8') as fhandle:
                fhandle.write(str(port))

            return port

    @staticmethod
    def get_env() -> dict[str, str]:
        """Return the environment for this current process.

        This method is used to pass variables from the environment of the current process to a subprocess that is
        spawned when the daemon or a daemon worker is started.

        It replicates the ``PATH``, ``PYTHONPATH` and the ``AIIDA_PATH`` environment variables. The ``PYTHONPATH``
        variable ensures that all Python modules that can be imported by the parent process, are also importable by
        the subprocess. The ``AIIDA_PATH`` variable ensures that the subprocess will use the same AiiDA configuration
        directory as used by the current process.
        """
        env = os.environ.copy()
        env['PATH'] = ':'.join([os.path.dirname(sys.executable), env['PATH']])
        env['PYTHONPATH'] = ':'.join(sys.path)
        env['AIIDA_PATH'] = get_config().dirpath
        env['PYTHONUNBUFFERED'] = 'True'
        return env

    def get_circus_socket_directory(self) -> str:
        """Retrieve the absolute path of the directory where the circus sockets are stored.

        If the daemon is running, the sockets file should exist and contain the absolute path of the directory that
        contains the sockets of the circus endpoints. If it cannot be read, a ``RuntimeError`` will be thrown. If the
        daemon is not running, a temporary directory will be created and its path will be written to the sockets file
        and returned.

        .. note:: A temporary folder needs to be used for the sockets because UNIX limits the filepath length to
            107 bytes. Placing the socket files in the AiiDA config folder might seem like the more logical choice
            but that folder can be placed in an arbitrarily nested directory, the socket filename will exceed the
            limit. The solution is therefore to always store them in the temporary directory of the operation system
            whose base path is typically short enough as to not exceed the limit

        :return: The absolute path of directory to write the sockets to.
        """
        if self.is_daemon_running:
            try:
                with open(self.circus_socket_file, 'r', encoding='utf8') as fhandle:
                    content = fhandle.read().strip()
                return content
            except (ValueError, IOError):
                raise RuntimeError('daemon is running so sockets file should have been there but could not read it')
        else:

            # The SOCKET_DIRECTORY is already set, a temporary directory was already created and the same should be used
            if self._SOCKET_DIRECTORY is not None:
                return self._SOCKET_DIRECTORY

            socket_dir_path = tempfile.mkdtemp()
            with open(self.circus_socket_file, 'w', encoding='utf8') as fhandle:
                fhandle.write(str(socket_dir_path))

            self._SOCKET_DIRECTORY = socket_dir_path
            return socket_dir_path

    def get_daemon_pid(self) -> int | None:
        """Get the daemon pid which should be written in the daemon pid file specific to the profile.

        :return: The pid of the circus daemon process or None if not found.
        """
        if os.path.isfile(self.circus_pid_file):
            try:
                with open(self.circus_pid_file, 'r', encoding='utf8') as fhandle:
                    content = fhandle.read().strip()
                return int(content)
            except (ValueError, IOError):
                return None
        else:
            return None

    @property
    def is_daemon_running(self) -> bool:
        """Return whether the daemon is running, which is determined by seeing if the daemon pid file is present.

        :return: True if daemon is running, False otherwise.
        """
        return self.get_daemon_pid() is not None

    def delete_circus_socket_directory(self) -> None:
        """Attempt to delete the directory used to store the circus endpoint sockets.

        Will not raise if the directory does not exist.
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
        """Get an available port from the operating system.

        :return: A currently available port.
        """
        open_socket = socket.socket()
        open_socket.bind(('', 0))
        return open_socket.getsockname()[1]

    def get_controller_endpoint(self):
        """Get the endpoint string for the circus controller.

        For the IPC protocol a profile specific socket will be used, whereas for the TCP protocol an available port will
        be found and saved in the profile specific port file.

        :return: The endpoint string.
        """
        if self._ENDPOINT_PROTOCOL == ControllerProtocol.IPC:
            endpoint = self.get_ipc_endpoint('controller')
        elif self._ENDPOINT_PROTOCOL == ControllerProtocol.TCP:
            endpoint = self.get_tcp_endpoint(self.get_circus_port())
        else:
            raise ValueError(f'invalid controller protocol {self._ENDPOINT_PROTOCOL}')

        return endpoint

    def get_pubsub_endpoint(self):
        """Get the endpoint string for the circus pubsub endpoint.

        For the IPC protocol a profile specific socket will be used, whereas for the TCP protocol any available port
        will be used.

        :return: The endpoint string.
        """
        if self._ENDPOINT_PROTOCOL == ControllerProtocol.IPC:
            endpoint = self.get_ipc_endpoint('pubsub')
        elif self._ENDPOINT_PROTOCOL == ControllerProtocol.TCP:
            endpoint = self.get_tcp_endpoint()
        else:
            raise ValueError(f'invalid controller protocol {self._ENDPOINT_PROTOCOL}')

        return endpoint

    def get_stats_endpoint(self):
        """Get the endpoint string for the circus stats endpoint.

        For the IPC protocol a profile specific socket will be used, whereas for the TCP protocol any available port
        will be used.

        :return: The endpoint string.
        """
        if self._ENDPOINT_PROTOCOL == ControllerProtocol.IPC:
            endpoint = self.get_ipc_endpoint('stats')
        elif self._ENDPOINT_PROTOCOL == ControllerProtocol.TCP:
            endpoint = self.get_tcp_endpoint()
        else:
            raise ValueError(f'invalid controller protocol {self._ENDPOINT_PROTOCOL}')

        return endpoint

    def get_ipc_endpoint(self, endpoint):
        """Get the ipc endpoint string for a circus daemon endpoint for a given socket.

        :param endpoint: The circus endpoint for which to return a socket.
        :return: The ipc endpoint string.
        """
        filepath = self.get_circus_socket_directory()
        filename = self.circus_socket_endpoints[endpoint]
        template = 'ipc://{filepath}/{filename}'
        endpoint = template.format(filepath=filepath, filename=filename)

        return endpoint

    def get_tcp_endpoint(self, port=None):
        """Get the tcp endpoint string for a circus daemon endpoint.

        If the port is unspecified, the operating system will be asked for a currently available port.

        :param port: A port to use for the endpoint.
        :return: The tcp endpoint string.
        """
        if port is None:
            port = self.get_available_port()

        template = 'tcp://127.0.0.1:{port}'
        endpoint = template.format(port=port)

        return endpoint

    @contextlib.contextmanager
    def get_client(self) -> 'CircusClient':
        """Return an instance of the CircusClient.

        The endpoint is defined by the controller endpoint, which used the port that was written to the port file upon
        starting of the daemon.

        :return: CircusClient instance
        """
        from circus.client import CircusClient

        try:
            client = CircusClient(endpoint=self.get_controller_endpoint(), timeout=self._DAEMON_TIMEOUT)
            yield client
        finally:
            client.stop()

    def call_client(self, command: JsonDictType) -> JsonDictType:
        """Call the client with a specific command.

        Will check whether the daemon is running first by checking for the pid file. When the pid is found yet the call
        still fails with a timeout, this means the daemon was actually not running and it was terminated unexpectedly
        causing the pid file to not be cleaned up properly.

        :param command: Command to call the circus client with.
        :return: The result of the circus client call.
        """
        from circus.exc import CallError

        if not self.get_daemon_pid():
            return {'status': self.DAEMON_ERROR_NOT_RUNNING}

        try:
            with self.get_client() as client:
                result = client.call(command)
        except CallError as exception:
            if str(exception) == 'Timed out.':
                return {'status': self.DAEMON_ERROR_TIMEOUT}
            raise exception

        return result

    def get_status(self) -> JsonDictType:
        """Get the daemon running status.

        :return: The client call response. If successful, will will contain 'status' key.
        """
        command = {'command': 'status', 'properties': {'name': self.daemon_name}}
        return self.call_client(command)

    def get_numprocesses(self) -> JsonDictType:
        """Get the number of running daemon processes.

        :return: The client call response. If successful, will contain 'numprocesses' key.
        """
        command = {'command': 'numprocesses', 'properties': {'name': self.daemon_name}}
        return self.call_client(command)

    def get_worker_info(self) -> JsonDictType:
        """Get workers statistics for this daemon.

        :return: The client call response. If successful, will contain 'info' key.
        """
        command = {'command': 'stats', 'properties': {'name': self.daemon_name}}
        return self.call_client(command)

    def get_daemon_info(self) -> JsonDictType:
        """Get statistics about this daemon itself.

        :return: The client call response. If successful, will contain 'info' key.
        """
        command = {'command': 'dstats', 'properties': {}}
        return self.call_client(command)

    def increase_workers(self, number: int) -> JsonDictType:
        """Increase the number of workers.

        :param number: The number of workers to add.
        :return: The client call response.
        """
        command = {'command': 'incr', 'properties': {'name': self.daemon_name, 'nb': number}}
        return self.call_client(command)

    def decrease_workers(self, number: int) -> JsonDictType:
        """Decrease the number of workers.

        :param number: The number of workers to remove.
        :return: The client call response.
        """
        command = {'command': 'decr', 'properties': {'name': self.daemon_name, 'nb': number}}
        return self.call_client(command)

    def stop_daemon(self, wait: bool = True, timeout: int = 5) -> JsonDictType:
        """Stop the daemon.

        :param wait: Boolean to indicate whether to wait for the result of the command.
        :param timeout: Wait this number of seconds for the ``is_daemon_running`` to return ``False`` before raising.
        :return: The client call response.
        :raises DaemonException: If ``is_daemon_running`` returns ``True`` after the ``timeout`` has passed.
        """
        command = {'command': 'quit', 'properties': {'waiting': wait}}

        result = self.call_client(command)

        if self._ENDPOINT_PROTOCOL == ControllerProtocol.IPC:
            self.delete_circus_socket_directory()

        if not wait:
            return result

        self._await_condition(
            lambda: not self.is_daemon_running,
            DaemonException(f'The daemon failed to stop within {timeout} seconds.'),
            timeout=timeout,
        )

        return result

    def restart_daemon(self, wait: bool) -> JsonDictType:
        """Restart the daemon.

        :param wait: Boolean to indicate whether to wait for the result of the command.
        :return: The client call response.
        """
        command = {'command': 'restart', 'properties': {'name': self.daemon_name, 'waiting': wait}}
        return self.call_client(command)

    def start_daemon(self, number_workers: int = 1, foreground: bool = False, timeout: int = 5) -> None:
        """Start the daemon in a sub process running in the background.

        :param number_workers: Number of daemon workers to start.
        :param foreground: Whether to launch the subprocess in the background or not.
        :param timeout: Wait this number of seconds for the ``is_daemon_running`` to return ``True`` before raising.
        :raises DaemonException: If the daemon fails to start.
        :raises DaemonException: If the daemon starts but then is unresponsive or in an unexpected state.
        :raises DaemonException: If ``is_daemon_running`` returns ``False`` after the ``timeout`` has passed.
        """
        env = self.get_env()
        command = self.cmd_start_daemon(number_workers, foreground)

        try:
            subprocess.check_output(command, env=env, stderr=subprocess.STDOUT)  # pylint: disable=unexpected-keyword-arg
        except subprocess.CalledProcessError as exception:
            raise DaemonException('The daemon failed to start.') from exception

        self._await_condition(
            lambda: self.is_daemon_running,
            DaemonException(f'The daemon failed to start within {timeout} seconds.'),
            timeout=timeout,
        )

    @staticmethod
    def _await_condition(condition: t.Callable, exception: Exception, timeout: int = 5, interval: float = 0.1):
        """Await a condition to evaluate to ``True`` or raise the exception if the timeout is reached.

        :param condition: A callable that is waited for to return ``True``.
        :param exception: Raise this exception if ``condition`` does not return ``True`` after ``timeout`` seconds.
        :param timeout: Wait this number of seconds for ``condition`` to return ``True`` before raising.
        :param interval: The time in seconds to wait between invocations of ``condition``.
        :raises: The exception provided by ``exception`` if timeout is reached.
        """
        start_time = time.time()

        while not condition():

            time.sleep(interval)

            if time.time() - start_time > timeout:
                raise exception

    def _start_daemon(self, number_workers: int = 1, foreground: bool = False) -> None:
        """Start the daemon.

        .. warning:: This will daemonize the current process and put it in the background. It is most likely not what
            you want to call if you want to start the daemon from the Python API. Instead you probably will want to use
            the :meth:`aiida.engine.daemon.client.DaemonClient.start_daemon` function instead.

        :param number_workers: Number of daemon workers to start.
        :param foreground: Whether to launch the subprocess in the background or not.
        """
        from circus import get_arbiter
        from circus import logger as circus_logger
        from circus.circusd import daemonize
        from circus.pidfile import Pidfile
        from circus.util import check_future_exception_and_log, configure_logger

        if foreground and number_workers > 1:
            raise ValueError('can only run a single worker when running in the foreground')

        loglevel = self.loglevel
        logoutput = '-'

        if not foreground:
            logoutput = self.circus_log_file

        arbiter_config = {
            'controller': self.get_controller_endpoint(),
            'pubsub_endpoint': self.get_pubsub_endpoint(),
            'stats_endpoint': self.get_stats_endpoint(),
            'logoutput': logoutput,
            'loglevel': loglevel,
            'debug': False,
            'statsd': True,
            'pidfile': self.circus_pid_file,
            'watchers': [{
                'cmd': ' '.join(self.cmd_start_daemon_worker),
                'name': self.daemon_name,
                'numprocesses': number_workers,
                'virtualenv': self.virtualenv,
                'copy_env': True,
                'stdout_stream': {
                    'class': 'FileStream',
                    'filename': self.daemon_log_file,
                },
                'stderr_stream': {
                    'class': 'FileStream',
                    'filename': self.daemon_log_file,
                },
                'env': self.get_env(),
            }]
        }  # yapf: disable

        if not foreground:
            daemonize()

        arbiter = get_arbiter(**arbiter_config)
        pidfile = Pidfile(arbiter.pidfile)
        pidfile.create(os.getpid())

        # Configure the logger
        loggerconfig = None
        loggerconfig = loggerconfig or arbiter.loggerconfig or None
        configure_logger(circus_logger, loglevel, logoutput, loggerconfig)

        # Main loop
        should_restart = True

        while should_restart:
            try:
                future = arbiter.start()
                should_restart = False
                if check_future_exception_and_log(future) is None:
                    should_restart = arbiter._restarting  # pylint: disable=protected-access
            except Exception as exception:
                # Emergency stop
                arbiter.loop.run_sync(arbiter._emergency_stop)  # pylint: disable=protected-access
                raise exception
            except KeyboardInterrupt:
                pass
            finally:
                arbiter = None
                if pidfile is not None:
                    pidfile.unlink()
