###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi status` command."""

import enum
import sys

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options
from aiida.cmdline.utils import echo
from aiida.common.exceptions import CorruptStorage, IncompatibleStorageSchema, UnreachableStorage
from aiida.common.log import override_log_level
from aiida.common.warnings import warn_deprecation

from ..utils.echo import ExitCode


class ServiceStatus(enum.IntEnum):
    """Describe status of services for 'verdi status' command."""

    UP = 0
    ERROR = 1
    WARNING = 2
    DOWN = 3


STATUS_SYMBOLS = {
    ServiceStatus.UP: {
        'color': 'green',
        'string': '\u2714',
    },
    ServiceStatus.ERROR: {
        'color': 'red',
        'string': '\u2718',
    },
    ServiceStatus.WARNING: {
        'color': 'yellow',
        'string': '\u23fa',
    },
    ServiceStatus.DOWN: {
        'color': 'red',
        'string': '\u2718',
    },
}


@verdi.command('status')
@options.PRINT_TRACEBACK()
@click.option('--no-rmq', is_flag=True, help='Do not check RabbitMQ status')
def verdi_status(print_traceback, no_rmq):
    """Print status of AiiDA services."""
    from aiida import __version__
    from aiida.common.docs import URL_NO_BROKER
    from aiida.common.exceptions import ConfigurationError
    from aiida.engine.daemon.client import DaemonException, DaemonNotRunningException
    from aiida.manage.configuration.settings import AiiDAConfigDir
    from aiida.manage.manager import get_manager

    exit_code = ExitCode.SUCCESS
    configure_directory = AiiDAConfigDir.get()

    print_status(ServiceStatus.UP, 'version', f'AiiDA v{__version__}')
    print_status(ServiceStatus.UP, 'config', configure_directory)

    manager = get_manager()

    try:
        profile = manager.get_profile()

        if profile is None:
            print_status(ServiceStatus.WARNING, 'profile', 'no profile configured yet')
            echo.echo_report(
                'Run `verdi presto` to automatically setup a profile using all defaults or use `verdi profile setup` '
                'for more control.'
            )
            return

        print_status(ServiceStatus.UP, 'profile', profile.name)

    except Exception as exc:
        message = 'Unable to read AiiDA profile'
        print_status(ServiceStatus.ERROR, 'profile', message, exception=exc, print_traceback=print_traceback)
        sys.exit(ExitCode.CRITICAL)  # stop here - without a profile we cannot access anything

    # Check the backend storage
    storage_head_version = None
    try:
        with override_log_level():  # temporarily suppress noisy logging
            storage_cls = profile.storage_cls
            storage_head_version = storage_cls.version_head()
            storage_backend = storage_cls(profile)
    except UnreachableStorage as exc:
        message = "Unable to connect to profile's storage."
        print_status(ServiceStatus.DOWN, 'storage', message, exception=exc, print_traceback=print_traceback)
        exit_code = ExitCode.CRITICAL
    except IncompatibleStorageSchema:
        message = (
            f'Storage schema version is incompatible with the code version {storage_head_version!r}. '
            'Run `verdi storage migrate` to solve this.'
        )
        print_status(ServiceStatus.DOWN, 'storage', message)
        exit_code = ExitCode.CRITICAL
    except CorruptStorage as exc:
        message = 'Storage is corrupted.'
        print_status(ServiceStatus.DOWN, 'storage', message, exception=exc, print_traceback=print_traceback)
        exit_code = ExitCode.CRITICAL
    except Exception as exc:
        message = "Unable to instatiate profile's storage."
        print_status(ServiceStatus.ERROR, 'storage', message, exception=exc, print_traceback=print_traceback)
        exit_code = ExitCode.CRITICAL
    else:
        message = str(storage_backend)
        print_status(ServiceStatus.UP, 'storage', message)

    if no_rmq:
        warn_deprecation(
            'The `--no-rmq` option is deprecated. If RabbitMQ is not available, a profile should be configured that '
            'sets the `process_control.backend` attribute to `None`.',
            version=3,
        )

    # Getting the broker status
    broker = manager.get_broker()

    if broker:
        try:
            broker.get_communicator()
        except Exception as exc:
            message = f'Unable to connect to broker: {broker}'
            print_status(ServiceStatus.ERROR, 'broker', message, exception=exc, print_traceback=print_traceback)
            exit_code = ExitCode.CRITICAL
        else:
            print_status(ServiceStatus.UP, 'broker', broker)
    else:
        print_status(
            ServiceStatus.WARNING,
            'broker',
            f'No broker defined for this profile: certain functionality not available. See {URL_NO_BROKER}',
        )

    # Getting the daemon status
    try:
        status = manager.get_daemon_client().get_status()
    except ConfigurationError:
        print_status(
            ServiceStatus.WARNING,
            'daemon',
            'No broker defined for this profile: daemon is not available. See {URL_NO_BROKER}',
        )
    except DaemonNotRunningException as exception:
        print_status(ServiceStatus.WARNING, 'daemon', str(exception))
    except DaemonException as exception:
        print_status(ServiceStatus.ERROR, 'daemon', str(exception))
    except Exception as exception:
        message = 'Error getting daemon status'
        print_status(ServiceStatus.ERROR, 'daemon', message, exception=exception, print_traceback=print_traceback)
        exit_code = ExitCode.CRITICAL
    else:
        print_status(ServiceStatus.UP, 'daemon', f'Daemon is running with PID {status["pid"]}')

    # Note: click does not forward return values to the exit code, see https://github.com/pallets/click/issues/747
    if exit_code != ExitCode.SUCCESS:
        sys.exit(exit_code)


def print_status(status, service, msg='', exception=None, print_traceback=False):
    """Print status message.

    Includes colored indicator.

    :param status: a ServiceStatus code
    :param service: string for service name
    :param msg:  message string
    """
    symbol = STATUS_SYMBOLS[status]
    echo.echo(f" {symbol['string']} ", fg=symbol['color'], nl=False)
    echo.echo(f"{service + ':':12s} {msg}")

    if exception is not None:
        echo.echo_error(f'{type(exception).__name__}: {exception}')

    if print_traceback:
        import traceback

        traceback.print_exc()
