###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi status` command."""

from __future__ import annotations

import enum
import sys
from typing import TYPE_CHECKING, Any

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options
from aiida.cmdline.utils import echo
from aiida.common.exceptions import CorruptStorage, IncompatibleStorageSchema, UnreachableStorage
from aiida.common.log import override_log_level
from aiida.common.warnings import warn_deprecation

from ..utils.echo import ExitCode

if TYPE_CHECKING:
    from aiida.manage.configuration import Profile
    from aiida.orm.implementation import StorageBackend


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
def verdi_status(print_traceback: bool, no_rmq: bool) -> None:
    """Print status of AiiDA services."""
    from aiida import __version__
    from aiida.cmdline.utils.daemon import validate_daemon_env
    from aiida.common.docs import URL_NO_BROKER
    from aiida.engine.daemon.client import DaemonException, DaemonNotRunningException
    from aiida.manage.configuration.settings import AiiDAConfigDir
    from aiida.manage.manager import get_manager

    exit_code = ExitCode.SUCCESS
    configure_directory = AiiDAConfigDir.get()

    print_status(ServiceStatus.UP, 'version', f'AiiDA v{__version__}')
    print_status(ServiceStatus.UP, 'config', str(configure_directory))

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
    storage_backend = None
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

    # Getting the daemon and broker status
    broker = manager.get_broker()

    from aiida.brokers.zeromq.broker import ZeromqBroker

    if broker:
        # For RabbitMQ: verify broker connectivity as a separate status line
        # For ZeroMQ: broker info is shown alongside the daemon status below
        if not isinstance(broker, ZeromqBroker):
            try:
                broker.get_communicator()
            except Exception as exc:
                message = f'Unable to connect to broker: {broker}'
                print_status(ServiceStatus.ERROR, 'broker', message, exception=exc, print_traceback=print_traceback)
                exit_code = ExitCode.CRITICAL
            else:
                print_status(ServiceStatus.UP, 'broker', str(broker))
            finally:
                broker.close()

    # Getting the daemon status
    if profile.process_control_backend is None:
        try:
            daemon_client = manager.get_daemon_client()
            is_daemon_running = daemon_client.is_daemon_running
        except Exception as exception:
            message = 'Error getting daemon status'
            print_status(ServiceStatus.ERROR, 'daemon', message, exception=exception, print_traceback=print_traceback)
            exit_code = ExitCode.CRITICAL
        else:
            if is_daemon_running:
                print_status(
                    ServiceStatus.WARNING,
                    'daemon',
                    'Daemon appears to be running but no broker is defined for this profile. '
                    'The daemon has no functionality because messages cannot passed to workers.\n'
                    f'See {URL_NO_BROKER}.',
                )
    else:
        try:
            daemon_client = manager.get_daemon_client()
            status = daemon_client.get_status()
        except DaemonNotRunningException as exception:
            print_status(ServiceStatus.WARNING, 'daemon', str(exception))
        except DaemonException as exception:
            print_status(ServiceStatus.ERROR, 'daemon', str(exception))
            exit_code = ExitCode.CRITICAL
        except Exception as exception:
            message = 'Error getting daemon status'
            print_status(ServiceStatus.ERROR, 'daemon', message, exception=exception, print_traceback=print_traceback)
            exit_code = ExitCode.CRITICAL
        else:
            daemon_status = ServiceStatus.UP
            daemon_msg = f'Daemon is running with PID {status["pid"]}'
            # Append broker info for managed brokers (e.g., ZeroMQ)

            if broker and isinstance(broker, ZeromqBroker):
                status_info = broker.probe_service_status()
                if status_info.get('connected', False):
                    broker_pid = status_info.get('pid', '?')
                    pending = status_info.get('pending_tasks', '?')
                    processing = status_info.get('processing_tasks', '?')
                    daemon_msg += f', Broker PID {broker_pid} [{pending} pending, {processing} processing]'
                else:
                    daemon_msg += ', Broker is NOT running (run `verdi daemon status` for more information)'
                    daemon_status = ServiceStatus.ERROR
                    exit_code = ExitCode.CRITICAL

            daemon_lines = [daemon_msg]

            # Check for package mismatches
            drift_error = validate_daemon_env(daemon_client)
            if drift_error is not None:
                if daemon_status == ServiceStatus.UP:
                    daemon_status = ServiceStatus.WARNING
                daemon_lines.append(drift_error)

            print_status(daemon_status, 'daemon', '\n'.join(daemon_lines))

    # Getting the collab status
    from aiida.tools.collab.config import is_enabled

    if is_enabled():
        print_collab_status(profile, storage_backend)

    if storage_backend is not None:
        storage_backend.close()

    # Note: click does not forward return values to the exit code, see https://github.com/pallets/click/issues/747
    if exit_code != ExitCode.SUCCESS:
        sys.exit(exit_code)


# One probe may take this long before its peer counts as offline; the probes run concurrently, so this is also
# roughly the total time the collab section adds to `verdi status`, however many peers there are.
COLLAB_PROBE_TIMEOUT = 2.0


def print_collab_status(profile: Profile, backend: StorageBackend | None) -> None:
    """Print one line per active peer — reachable or not — the last sync, and what this profile itself serves.

    Dormant peers are left out entirely: they have not been seen under the current token, and a collab that
    rotated away from a member, or split in two, should carry no trace of the branch it left behind.

    The probes run concurrently and write nothing anywhere.

    :param backend: the storage opened for the storage row, or ``None`` when it could not be opened, in which case
        the section reports on the collab alone.
    """
    from concurrent.futures import ThreadPoolExecutor
    from http import HTTPStatus

    from aiida.common import timezone
    from aiida.common.utils import str_timedelta
    from aiida.manage.configuration import get_config_option
    from aiida.tools.archive.abstract import get_format
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.config import OPTION_ONLINE, OPTION_PEERS, OPTION_POLICY, OPTION_TOKEN
    from aiida.tools.collab.protocol import REKEY_HINT, CollabRequestError, PeerInfo
    from aiida.tools.collab.state import CollabState
    from aiida.tools.collab.sync import withheld_seeds

    peers = {uuid: entry for uuid, entry in get_config_option(OPTION_PEERS).items() if entry['active']}
    token = get_config_option(OPTION_TOKEN)
    policy = get_config_option(OPTION_POLICY)

    def probe(entry: dict[str, Any]) -> PeerInfo | CollabRequestError:
        with CollabClient(entry['url'], token, timeout=COLLAB_PROBE_TIMEOUT) as client:
            try:
                return client.info()
            except CollabRequestError as exception:
                # Kept rather than folded into "offline": a peer that answered said why, and after a rotation
                # what it says — 401, rekey — is the whole point of looking here.
                return exception

    infos: list[PeerInfo | CollabRequestError] = []

    if peers:
        with ThreadPoolExecutor(max_workers=len(peers)) as pool:
            infos = list(pool.map(probe, peers.values()))

    archive_schema = get_format().latest_version

    for entry, info in zip(peers.values(), infos):
        nickname = entry['nickname']

        if isinstance(info, CollabRequestError) and info.status == HTTPStatus.UNAUTHORIZED:
            # The steady state for a member that has not rekeyed since the collab rotated. It is up, it answered,
            # and this is the only place that says so before the user tries to sync.
            print_status(
                ServiceStatus.DOWN, f'peer {nickname}', f'{entry["url"]} refuses the current key — {REKEY_HINT}'
            )
        elif isinstance(info, CollabRequestError):
            # A peer that has never answered is called out apart from one that is merely down: it is the only
            # way a wrong address announced at join can surface, since nothing can probe back at join time.
            reachability = 'has never answered' if not entry.get('seen') else 'offline'
            print_status(ServiceStatus.DOWN, f'peer {nickname}', f'{entry["url"]} {reachability}')
        # The archive format is what a delta travels as, so it alone decides compatibility; the storage schema of
        # either side is its own concern. Zero-padded versions (`main_0002`), so string comparison orders them.
        elif info.archive_schema > archive_schema:
            print_status(
                ServiceStatus.WARNING,
                f'peer {nickname}',
                f'{entry["url"]} online, writes a newer archive format than this profile can read '
                f'(aiida-core {info.version})',
            )
        else:
            print_status(ServiceStatus.UP, f'peer {nickname}', f'{entry["url"]} online (aiida-core {info.version})')

    state = CollabState.load(profile)
    # A `served` row is a peer's sync, not this profile's: counting it would let a peer pulling from here keep the
    # line fresh while this profile has not synced in a week, which is the one thing it is read for.
    own = [event for event in state.events if event.direction != 'served']
    last_sync = f'last sync {own[-1].time.isoformat(timespec="seconds")}' if own else 'no syncs yet'
    online = sum(1 for info in infos if isinstance(info, PeerInfo))
    status = ServiceStatus.UP if online == len(peers) else ServiceStatus.WARNING

    print_status(status, 'collab', f'{online}/{len(peers)} peer(s) reachable, {last_sync}')

    # The probes above are outbound and say nothing about being reachable oneself, so a profile that was taken
    # out of service has no other symptom here: to its peers it is simply a member that is down.
    if not get_config_option(OPTION_ONLINE):
        print_status(
            ServiceStatus.WARNING,
            'collab offline',
            'peers cannot reach this profile; run `verdi collab online` to serve again',
        )

    # A sealed process whose provenance reaches one that is still running is held out of every delta until that
    # child seals, and nothing else says so. When the child never seals — a killed daemon, a stuck process — its
    # whole subgraph stops travelling for good, and the only other symptom is a peer that never receives it.
    held = withheld_seeds(backend) if backend is not None else []

    if held:
        age = str_timedelta(timezone.delta(min(held)), short=True, negative_to_zero=True)
        print_status(
            ServiceStatus.WARNING,
            'collab held',
            f'{len(held)} sealed process(es) no delta can carry, each waiting on a process that has not sealed '
            f'(oldest {age})',
        )

    # Shown here because it is shown nowhere else: the policy is fixed when the collab is created, so it is stored
    # as one dictionary, and `verdi config set` cannot write dict options.
    print_status(
        ServiceStatus.UP,
        'collab policy',
        f'extras `{policy["extras_mode"]}`, groups `{policy["groups_mode"]}` (fixed at creation)',
    )

    # Advisory and nothing else: whoever signalled it holds the token being retired, and so does anyone that was
    # just excluded, so the only thing it may do is tell the user where to look.
    signalled = [entry['nickname'] for entry in peers.values() if entry['signalled']]

    if signalled:
        print_status(ServiceStatus.WARNING, 'collab rotation', f'signalled by {", ".join(signalled)} — {REKEY_HINT}')


def print_status(
    status: ServiceStatus,
    service: str,
    msg: str = '',
    exception: Exception | None = None,
    print_traceback: bool = False,
) -> None:
    """Print status message.

    Includes colored indicator.

    :param status: a ServiceStatus code
    :param service: string for service name
    :param msg:  message string
    """
    symbol = STATUS_SYMBOLS[status]
    echo.echo(f' {symbol["string"]} ', fg=symbol['color'], nl=False)
    echo.echo(f'{service + ":":12s} ', nl=False)
    lines = msg.split('\n')
    echo.echo(lines[0])
    for line in lines[1:]:
        echo.echo(f'{"":15s} {line}')

    if exception is not None:
        echo.echo_error(f'{type(exception).__name__}: {exception}')

    if print_traceback:
        import traceback

        traceback.print_exc()
