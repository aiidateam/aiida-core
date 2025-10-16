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
import pathlib
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import typing as t
from typing import TYPE_CHECKING

import psutil

from aiida.common.exceptions import AiidaException, ConfigurationError
from aiida.common.lang import type_check
from aiida.common.log import AIIDA_LOGGER
from aiida.manage.configuration import get_config, get_config_option
from aiida.manage.configuration.profile import Profile
from aiida.manage.manager import get_manager

if TYPE_CHECKING:
    from circus.client import CircusClient

LOGGER = AIIDA_LOGGER.getChild('engine.daemon.client')

VERDI_BIN = shutil.which('verdi')
# Recent versions of virtualenv create the environment variable VIRTUAL_ENV
VIRTUALENV = os.environ.get('VIRTUAL_ENV', None)

__all__ = ('DaemonClient', 'get_daemon_client')


class ControllerProtocol(enum.Enum):
    """The protocol to use for the controller of the Circus daemon."""

    IPC = 0
    TCP = 1


class DaemonException(AiidaException):
    """Base class for exceptions related to the daemon."""


class DaemonNotRunningException(DaemonException):
    """Raised when a connection to the daemon is attempted but it is not running."""


class DaemonTimeoutException(DaemonException):
    """Raised when a connection to the daemon is attempted but it times out."""


class DaemonStalePidException(DaemonException):
    """Raised when a connection to the daemon is attempted but it fails and the PID file appears to be stale."""


def get_daemon_client(profile_name: str | None = None) -> 'DaemonClient':
    """Return the daemon client for the given profile or the current profile if not specified.

    :param profile_name: Optional profile name to load.
    :return: The daemon client.

    :raises aiida.common.MissingConfigurationError: if the configuration file cannot be found.
    :raises aiida.common.ProfileConfigurationError: if the given profile does not exist.
    """
    profile = get_manager().load_profile(profile_name)
    return DaemonClient(profile)


class DaemonClient:
    """Client to interact with the daemon."""

    _DAEMON_NAME = 'aiida-{name}'
    if sys.platform == 'win32':
        _ENDPOINT_PROTOCOL = ControllerProtocol.TCP
    else:
        _ENDPOINT_PROTOCOL = ControllerProtocol.IPC

    def __init__(self, profile: Profile):
        """Construct an instance for a given profile.

        :param profile: The profile instance.
        """
        from aiida.common.docs import URL_NO_BROKER

        type_check(profile, Profile)
        self._config = get_config()
        self._profile = profile
        self._socket_directory: str | None = None
        self._daemon_timeout: int = self._config.get_option('daemon.timeout', scope=profile.name)

        if self._profile.process_control_backend is None:
            raise ConfigurationError(
                f'profile `{self._profile.name}` does not define a broker so the daemon cannot be used. '
                f'See {URL_NO_BROKER} for more details.'
            )

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
        return self._config.filepaths(self.profile)['circus']['log']

    @property
    def circus_pid_file(self) -> str:
        return self._config.filepaths(self.profile)['circus']['pid']

    @property
    def circus_port_file(self) -> str:
        return self._config.filepaths(self.profile)['circus']['port']

    @property
    def circus_socket_file(self) -> str:
        return self._config.filepaths(self.profile)['circus']['socket']['file']

    @property
    def circus_socket_endpoints(self) -> dict[str, str]:
        return self._config.filepaths(self.profile)['circus']['socket']

    @property
    def daemon_log_file(self) -> str:
        return self._config.filepaths(self.profile)['daemon']['log']

    @property
    def daemon_pid_file(self) -> str:
        return self._config.filepaths(self.profile)['daemon']['pid']

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
            except (ValueError, OSError):
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
            except (ValueError, OSError):
                raise RuntimeError('daemon is running so sockets file should have been there but could not read it')
        else:
            # The SOCKET_DIRECTORY is already set, a temporary directory was already created and the same should be used
            if self._socket_directory is not None:
                return self._socket_directory

            socket_dir_path = tempfile.mkdtemp()
            with open(self.circus_socket_file, 'w', encoding='utf8') as fhandle:
                fhandle.write(str(socket_dir_path))

            self._socket_directory = socket_dir_path
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
            except (ValueError, OSError):
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
    def get_client(self, timeout: int | None = None) -> 'CircusClient':
        """Return an instance of the CircusClient.

        The endpoint is defined by the controller endpoint, which used the port that was written to the port file upon
        starting of the daemon.

        :param timeout: Optional timeout to set for trying to reach the circus daemon. Default is set on the client upon
            instantiation taken from the ``daemon.timeout`` config option.
        :return: CircusClient instance
        """
        from circus.client import CircusClient

        try:
            client = CircusClient(endpoint=self.get_controller_endpoint(), timeout=timeout or self._daemon_timeout)
            yield client
        finally:
            client.stop()

    def call_client(self, command: dict[str, t.Any], timeout: int | None = None) -> dict[str, t.Any]:
        """Call the client with a specific command.

        Will check whether the daemon is running first by checking for the pid file. When the pid is found yet the call
        still fails with a timeout, this means the daemon was actually not running and it was terminated unexpectedly
        causing the pid file to not be cleaned up properly.

        :param command: Command to call the circus client with.
        :param timeout: Optional timeout to set for trying to reach the circus daemon. Default is set on the client upon
            instantiation taken from the ``daemon.timeout`` config option.
        :return: The result of the circus client call.
        :raises DaemonException: If the daemon is not running or cannot be reached.
        :raises DaemonTimeoutException: If the connection to the daemon timed out.
        :raises DaemonException: If the connection to the daemon failed for any other reason.
        """
        from circus.exc import CallError

        try:
            with self.get_client(timeout=timeout) as client:
                result = client.call(command)
        except CallError as exception:
            if self.get_daemon_pid() is None:
                raise DaemonNotRunningException('The daemon is not running.') from exception

            if self._is_pid_file_stale:
                raise DaemonStalePidException(
                    'The daemon could not be reached, seemingly because of a stale PID file. Either stop or start the '
                    'daemon to remove it and restore the daemon to a functional state.'
                ) from exception

            if str(exception) == 'Timed out.':
                raise DaemonTimeoutException('Connection to the daemon timed out.') from exception

            raise DaemonException('Connection to the daemon failed.') from exception

        return result

    def get_status(self, timeout: int | None = None) -> dict[str, t.Any]:
        """Return the status of the daemon.

        :param timeout: Optional timeout to set for trying to reach the circus daemon. Default is set on the client upon
            instantiation taken from the ``daemon.timeout`` config option.
        :returns: The client call response. If successful, will contain 'pid' key.
        """
        command = {'command': 'status', 'properties': {'name': self.daemon_name}}
        response = self.call_client(command, timeout=timeout)
        response['pid'] = self.get_daemon_pid()
        return response

    def get_numprocesses(self, timeout: int | None = None) -> dict[str, t.Any]:
        """Get the number of running daemon processes.

        :param timeout: Optional timeout to set for trying to reach the circus daemon. Default is set on the client upon
            instantiation taken from the ``daemon.timeout`` config option.
        :return: The client call response. If successful, will contain 'numprocesses' key.
        """
        command = {'command': 'numprocesses', 'properties': {'name': self.daemon_name}}
        return self.call_client(command, timeout=timeout)

    def get_worker_info(self, timeout: int | None = None) -> dict[str, t.Any]:
        """Get workers statistics for this daemon.

        :param timeout: Optional timeout to set for trying to reach the circus daemon. Default is set on the client upon
            instantiation taken from the ``daemon.timeout`` config option.
        :return: The client call response. If successful, will contain 'info' key.
        """
        command = {'command': 'stats', 'properties': {'name': self.daemon_name}}
        return self.call_client(command, timeout=timeout)

    def get_number_of_workers(self, timeout: int | None = None) -> int:
        """Get number of workers."""
        return len(self.get_worker_info(timeout).get('info', []))

    def get_daemon_info(self, timeout: int | None = None) -> dict[str, t.Any]:
        """Get statistics about this daemon itself.

        :param timeout: Optional timeout to set for trying to reach the circus daemon. Default is set on the client upon
            instantiation taken from the ``daemon.timeout`` config option.
        :return: The client call response. If successful, will contain 'info' key.
        """
        command = {'command': 'dstats', 'properties': {}}
        return self.call_client(command, timeout=timeout)

    def increase_workers(self, number: int, timeout: int | None = None) -> dict[str, t.Any]:
        """Increase the number of workers.

        :param number: The number of workers to add.
        :param timeout: Optional timeout to set for trying to reach the circus daemon. Default is set on the client upon
            instantiation taken from the ``daemon.timeout`` config option.
        :return: The client call response.
        """
        command = {'command': 'incr', 'properties': {'name': self.daemon_name, 'nb': number}}
        return self.call_client(command, timeout=timeout)

    def decrease_workers(self, number: int, timeout: int | None = None) -> dict[str, t.Any]:
        """Decrease the number of workers.

        :param number: The number of workers to remove.
        :param timeout: Optional timeout to set for trying to reach the circus daemon. Default is set on the client upon
            instantiation taken from the ``daemon.timeout`` config option.
        :return: The client call response.
        """
        command = {'command': 'decr', 'properties': {'name': self.daemon_name, 'nb': number}}
        return self.call_client(command, timeout=timeout)

    def start_daemon(
        self, number_workers: int = 1, foreground: bool = False, wait: bool = True, timeout: int | None = None
    ) -> None:
        """Start the daemon in a sub process running in the background.

        :param number_workers: Number of daemon workers to start.
        :param foreground: Whether to launch the subprocess in the background or not.
        :param wait: Boolean to indicate whether to wait for the result of the command.
        :param timeout: Optional timeout to set for trying to reach the circus daemon after the subprocess has started.
            Default is set on the client upon instantiation taken from the ``daemon.timeout`` config option.
        :raises DaemonException: If the command to start the daemon subprocess excepts.
        :raises DaemonTimeoutException: If the daemon starts but then is unresponsive or in an unexpected state.
        """
        self._clean_potentially_stale_pid_file()

        env = self.get_env()
        command = self.cmd_start_daemon(number_workers, foreground)
        timeout = timeout or self._daemon_timeout

        try:
            subprocess.check_output(command, env=env, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exception:
            # CalledProcessError is not passing the subprocess stderr in its message so we add it in DaemonException
            raise DaemonException(f'The daemon failed to start with error:\n{exception.stdout.decode()}') from exception

        if not wait:
            return

        self._await_condition(
            lambda: self.is_daemon_running,
            DaemonTimeoutException(f'The daemon failed to start or is unresponsive after {timeout} seconds.'),
            timeout=timeout,
        )

    def restart_daemon(self, wait: bool = True, timeout: int | None = None) -> dict[str, t.Any]:
        """Restart the daemon.

        :param wait: Boolean to indicate whether to wait for the result of the command.
        :param timeout: Optional timeout to set for trying to reach the circus daemon. Default is set on the client upon
            instantiation taken from the ``daemon.timeout`` config option.
        :returns: The client call response.
        :raises DaemonException: If the daemon is not running or cannot be reached.
        :raises DaemonTimeoutException: If the connection to the daemon timed out.
        :raises DaemonException: If the connection to the daemon failed for any other reason.
        """
        command = {'command': 'restart', 'properties': {'name': self.daemon_name, 'waiting': wait}}
        return self.call_client(command, timeout=timeout)

    def stop_daemon(self, wait: bool = True, timeout: int | None = None) -> dict[str, t.Any]:
        """Stop the daemon.

        :param wait: Boolean to indicate whether to wait for the result of the command.
        :param timeout: Optional timeout to set for trying to reach the circus daemon. Default is set on the client upon
            instantiation taken from the ``daemon.timeout`` config option.
        :returns: The client call response.
        :raises DaemonException: If the daemon is not running or cannot be reached.
        :raises DaemonTimeoutException: If the connection to the daemon timed out.
        :raises DaemonException: If the connection to the daemon failed for any other reason.
        """
        self._clean_potentially_stale_pid_file()

        command = {'command': 'quit', 'properties': {'waiting': wait}}
        response = self.call_client(command, timeout=timeout)

        if self._ENDPOINT_PROTOCOL == ControllerProtocol.IPC:
            self.delete_circus_socket_directory()

        return response

    def _clean_potentially_stale_pid_file(self) -> None:
        """Check the daemon PID file and delete it if it is likely to be stale."""
        try:
            self._check_pid_file()
        except DaemonException as exception:
            pathlib.Path(self.circus_pid_file).unlink(missing_ok=True)
            LOGGER.warning(f'Deleted apparently stale daemon PID file: {exception}')

    @property
    def _is_pid_file_stale(self) -> bool:
        """Return whether the daemon PID file is likely to be stale.

        :returns: ``True`` if the PID file is likely to be stale, ``False`` otherwise.
        """
        try:
            self._check_pid_file()
        except DaemonException:
            return True

        return False

    def _check_pid_file(self) -> None:
        """Check that the daemon's PID file is not stale.

        Checks if the PID contained in the circus PID file matches a valid running ``verdi`` process. The PID file is
        considered stale if any of the following conditions are true:

        * The process with the given PID no longer exists
        * The process name does not match the command of the circus daemon
        * The process username does not match the username of this Python interpreter

        In the latter two cases, the process with the PID of the PID file exists, but it is very likely that it is not
        the original process that created the PID file, since the command or user is different, indicating the original
        process died and the PID was recycled for a new process.

        The PID file can got stale if a system is shut down suddenly and so the process is killed but the PID file is
        not deleted in time. When the `get_daemon_pid()` method is called, an incorrect PID is returned. Alternatively,
        another process or the user may have meddled with the PID file in some way, corrupting it.

        :raises DaemonException: If the PID file is likely to be stale.
        """
        pid = self.get_daemon_pid()

        if pid is None:
            return

        try:
            process = psutil.Process(pid)

            # The circus daemon process can appear as ``start-circus`` or ``circusd``. See this issue comment for
            # details: https://github.com/aiidateam/aiida-core/issues/5336#issuecomment-1376093322
            if not any(cmd in process.cmdline() for cmd in ['start-circus', 'circusd']):
                raise DaemonException(
                    f'process command `{process.cmdline()}` of PID `{pid}` does not match expected AiiDA daemon command'
                )

            process_user = process.username()
            current_user = psutil.Process().username()

            if process_user != current_user:
                raise DaemonException(
                    f'process user `{process_user}` of PID `{pid}` does not match current user `{current_user}`'
                )

        except (psutil.AccessDenied, psutil.NoSuchProcess, DaemonException) as exception:
            raise DaemonException(exception) from exception

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
            'watchers': [
                {
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
                }
            ],
        }

        if not foreground:
            daemonize()

        arbiter = get_arbiter(**arbiter_config)
        pidfile = Pidfile(arbiter.pidfile)
        pidfile.create(os.getpid())

        # Configure the logger
        loggerconfig = arbiter.loggerconfig or None
        configure_logger(circus_logger, loglevel, logoutput, loggerconfig)

        # Main loop
        should_restart = True

        while should_restart:
            try:
                future = arbiter.start()
                should_restart = False
                if check_future_exception_and_log(future) is None:
                    should_restart = arbiter._restarting
            except Exception as exception:
                # Emergency stop
                arbiter.loop.run_sync(arbiter._emergency_stop)
                raise exception
            except KeyboardInterrupt:
                pass
            finally:
                arbiter = None
                if pidfile is not None:
                    pidfile.unlink()
