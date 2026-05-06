###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi bug-report` command."""

import json
import pathlib
import platform
import sys
import zipfile
from datetime import datetime
from typing import Any

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import echo

SENSITIVE_KEY_FRAGMENTS = ('password', 'passphrase', 'secret', 'token')
SENSITIVE_CONFIG_KEYS = ('AIIDADB_PASS',)
REDACTED_VALUE = '***'


def _is_sensitive_key(key: str) -> bool:
    """Return whether the key likely contains a sensitive value."""
    lowercase = key.lower()
    return key in SENSITIVE_CONFIG_KEYS or any(fragment in lowercase for fragment in SENSITIVE_KEY_FRAGMENTS)


def _redact_sensitive_values(value: Any) -> Any:
    """Redact values that are likely to contain secrets."""
    if isinstance(value, dict):
        redacted = {}

        for key, subvalue in value.items():
            if _is_sensitive_key(key) and subvalue is not None:
                redacted[key] = REDACTED_VALUE
            else:
                redacted[key] = _redact_sensitive_values(subvalue)

        return redacted

    if isinstance(value, list):
        return [_redact_sensitive_values(subvalue) for subvalue in value]

    return value


def _check_storage(profile) -> dict[str, Any]:
    """Return storage connection information for the current profile."""
    try:
        storage = profile.storage_cls(profile)
    except Exception as exception:
        return {'connected': False, 'message': f'{type(exception).__name__}: {exception}'}

    try:
        return {'connected': True, 'message': str(storage)}
    finally:
        storage.close()


def _check_broker(manager) -> dict[str, Any]:
    """Return broker connection information for the current profile."""
    broker = manager.get_broker()

    if broker is None:
        return {'connected': False, 'message': 'No broker configured for this profile.'}

    try:
        broker.get_communicator()
    except Exception as exception:
        return {'connected': False, 'message': f'{type(exception).__name__}: {exception}'}
    finally:
        try:
            broker.close()
        except Exception:
            pass

    return {'connected': True, 'message': broker.__class__.__name__}


def _check_daemon(manager) -> dict[str, Any]:
    """Return daemon connection information for the current profile."""
    try:
        status = manager.get_daemon_client().get_status()
    except Exception as exception:
        return {'connected': False, 'message': f'{type(exception).__name__}: {exception}'}

    pid = status.get('pid')
    message = 'Daemon status retrieved successfully.'

    if pid is not None:
        message = f'Daemon is running with PID {pid}'

    return {'connected': True, 'message': message, 'status': status}


def _collect_python_info() -> dict[str, Any]:
    """Return structured information on the Python interpreter."""
    return {
        'version': platform.python_version(),
        'major': sys.version_info.major,
        'minor': sys.version_info.minor,
        'micro': sys.version_info.micro,
        'implementation': platform.python_implementation(),
        'compiler': platform.python_compiler(),
        'build': list(platform.python_build()),
        'executable': sys.executable,
    }


def _get_config_data() -> dict[str, Any] | None:
    """Return the contents of the AiiDA configuration file."""
    from aiida.manage.configuration import get_config
    from aiida.manage.configuration.settings import DEFAULT_CONFIG_FILE_NAME

    filepath = pathlib.Path(get_config().dirpath) / DEFAULT_CONFIG_FILE_NAME

    if not filepath.exists():
        return None

    return _redact_sensitive_values(json.loads(filepath.read_text(encoding='utf-8')))


def _collect_diagnostics() -> dict[str, Any]:
    """Collect structured diagnostic information for the bug report."""
    import aiida
    from aiida.manage import get_manager

    manager = get_manager()
    profile = manager.get_profile()

    profile_data = None

    if profile is not None:
        profile_data = {'name': profile.name}

    services = {'storage': {'connected': False, 'message': 'No profile loaded.'}}

    if profile is not None:
        services['storage'] = _check_storage(profile)

    services['broker'] = _check_broker(manager)
    services['daemon'] = _check_daemon(manager)

    return {
        'generated_at': datetime.now().isoformat(),
        'aiida_version': aiida.__version__,
        'python': _collect_python_info(),
        'platform': {
            'platform': platform.platform(),
            'system': platform.system(),
            'release': platform.release(),
            'machine': platform.machine(),
        },
        'profile': profile_data,
        'config': _get_config_data(),
        'services': services,
    }


def _get_log_files() -> list[tuple[str, pathlib.Path]]:
    """Return a list of (archive_name, path) for log files to include."""
    from aiida.manage import get_manager
    from aiida.manage.configuration import get_config

    files = []

    try:
        manager = get_manager()
        profile = manager.get_profile()

        if profile is not None:
            client_log = pathlib.Path(get_config().filepaths(profile)['client']['log'])
            if client_log.exists():
                files.append(('client.log', client_log))

        from aiida.engine.daemon.client import get_daemon_client

        client = get_daemon_client()

        daemon_log = pathlib.Path(client.daemon_log_file)
        if daemon_log.exists():
            files.append(('daemon.log', daemon_log))

        circus_log = pathlib.Path(client.circus_log_file)
        if circus_log.exists():
            files.append(('circus.log', circus_log))

        broker = manager.get_broker()
        if broker is not None:
            broker_log = broker.get_log_file()
            if broker_log is not None:
                files.append((broker_log.name, broker_log))
    except Exception:
        pass

    return files


@verdi.command('bug-report')
@click.option(
    '-o',
    '--output',
    type=click.Path(),
    default=None,
    help='Output zip file path. Default: aiida-bug-report-<timestamp>.zip in current directory.',
)
def verdi_bug_report(output):
    """Create a zip file with diagnostic information for bug reports.

    Bundles profile configuration, service status, and log files into a
    zip archive that can be attached to a GitHub issue.
    """
    if output is None:
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        output = f'aiida-bug-report-{timestamp}.zip'

    output_path = pathlib.Path(output)

    echo.echo('Collecting diagnostic information...')

    diagnostics = _collect_diagnostics()
    log_files = _get_log_files()

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('diagnostics.json', json.dumps(diagnostics, indent=2, sort_keys=True, default=str))
        for archive_name, filepath in log_files:
            zf.write(filepath, archive_name)

    echo.echo_success(f'Bug report written to: {output_path}')
    echo.echo_info('Contents:')
    echo.echo('  diagnostics.json')
    for archive_name, filepath in log_files:
        size = filepath.stat().st_size
        echo.echo(f'  {archive_name} ({size} bytes)')
    echo.echo('')
    echo.echo('Attach this file to your GitHub issue at:')
    echo.echo('https://github.com/aiidateam/aiida-core/issues/new')
