###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi bug-report` command."""

from __future__ import annotations

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
from aiida.common.log import AIIDA_LOGGER

SENSITIVE_KEY_FRAGMENTS = ('password', 'passphrase', 'secret', 'token')
SENSITIVE_CONFIG_KEYS = ('AIIDADB_PASS',)
REDACTED_VALUE = '***'

# Maximum number of bytes included per log file; longer logs are truncated to their tail
MAX_LOG_BYTES = 1024 * 1024

LOGGER = AIIDA_LOGGER.getChild('cmdline.commands.bug_report')


def _format_exception(exception: Exception) -> str:
    """Return a stable string representation for an exception."""
    return f'{type(exception).__name__}: {exception}'


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


def _check_storage() -> dict[str, Any]:
    """Return storage connection information."""
    from aiida.manage import get_manager

    manager = get_manager()
    storage_loaded = manager.profile_storage_loaded

    try:
        storage = manager.get_profile_storage()
        status = str(storage)
        connected = True
    except Exception as exception:
        connected = False
        status = _format_exception(exception)
    finally:
        if not storage_loaded:
            try:
                manager.reset_profile_storage()
            except Exception as exception:
                LOGGER.warning(f'Failed to reset storage while collecting bug report diagnostics: {exception}')

    return {'connected': connected, 'status': status}


def _check_broker() -> dict[str, Any]:
    """Return broker connection information for the current profile."""
    from aiida.manage import get_manager

    manager = get_manager()
    # There is no public accessor to determine whether the manager already cached a broker instance. We need to know
    # this to avoid resetting a broker that was already loaded before running diagnostics, so use the private cache
    # attribute here and only reset brokers that this check caused to be loaded.
    broker_loaded = manager._broker is not None
    status: dict[str, Any] | str | None = None

    try:
        broker = manager.get_broker()

        if broker is None:
            return {'connected': False, 'status': 'No broker configured for this profile.'}

        status = broker.get_service_status()
        connected = status is not None
    except Exception as exception:
        connected = False
        status = _format_exception(exception)
    finally:
        if not broker_loaded:
            try:
                manager.reset_broker()
            except Exception as exception:
                LOGGER.warning(f'Failed to reset broker while collecting bug report diagnostics: {exception}')

    return {'connected': connected, 'status': status}


def _check_daemon() -> dict[str, Any]:
    """Return daemon connection information for the current profile."""
    from aiida.manage import get_manager

    try:
        status = get_manager().get_daemon_client().get_status()
    except Exception as exception:
        return {'connected': False, 'status': _format_exception(exception)}

    return {'connected': True, 'status': status}


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
    """Return the contents of the AiiDA configuration file with secrets redacted."""
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

    services = {
        'storage': _check_storage(),
        'broker': _check_broker(),
        'daemon': _check_daemon(),
    }

    config = None
    config_error = None

    try:
        config = _get_config_data()
    except Exception as exception:
        config_error = _format_exception(exception)

    diagnostics = {
        'generated_at': datetime.now().astimezone().isoformat(),
        'aiida_version': aiida.__version__,
        'python': _collect_python_info(),
        'platform': {
            'platform': platform.platform(),
            'system': platform.system(),
            'release': platform.release(),
            'machine': platform.machine(),
        },
        'profile': {'name': profile.name} if profile is not None else None,
        'config': config,
        'services': services,
    }

    if config_error is not None:
        diagnostics['config_error'] = config_error

    return diagnostics


def _get_log_files() -> list[pathlib.Path]:
    """Return the log files to include."""
    from aiida.manage import get_manager
    from aiida.manage.configuration import get_config

    profile = get_manager().get_profile()

    if profile is None:
        return []

    filepaths = get_config().filepaths(profile)
    files = []

    log_filepaths = [
        filepaths['profile']['log'],
        filepaths['circus']['log'],
        filepaths['daemon']['log'],
        filepaths['zmq_broker_service']['log'],
    ]

    for log_filepath in log_filepaths:
        path = pathlib.Path(log_filepath)
        if path.exists():
            files.append(path)

    return files


def _read_log_tail(filepath: pathlib.Path, max_bytes: int = MAX_LOG_BYTES) -> bytes:
    """Return the contents of the log file, truncated to the last ``max_bytes`` bytes."""
    size = filepath.stat().st_size

    with filepath.open('rb') as handle:
        if size <= max_bytes:
            return handle.read()

        header = f'... (truncated from {size} bytes)\n'.encode('utf-8')

        if len(header) >= max_bytes:
            return header[:max_bytes]

        payload_bytes = max_bytes - len(header)
        handle.seek(size - payload_bytes)
        data = handle.read(payload_bytes)
        return header + data.decode('utf-8', errors='ignore').encode('utf-8')


@verdi.command('bug-report')
@click.option(
    '-o',
    '--output',
    type=click.Path(dir_okay=True, file_okay=True, writable=True, path_type=pathlib.Path),
    default=None,
    help=(
        'Output zip file path or directory where to put the zip. Defaults to '
        'aiida-bug-report-<timestamp>.zip in current directory.'
    ),
)
def verdi_bug_report(output: str | None) -> None:
    """Create a zip file with diagnostic information for bug reports.

    Bundles profile configuration, service status, and log files into a
    zip archive that can be attached to a GitHub issue.
    """
    if output is None:
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        output = f'aiida-bug-report-{timestamp}.zip'

    output_path = pathlib.Path(output)

    if output_path.exists() and output_path.is_dir():
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        output_path = output_path / f'aiida-bug-report-{timestamp}.zip'

    if output_path.exists():
        echo.echo_critical(f'Output file `{output_path}` already exists.')

    echo.echo('Collecting diagnostic information...')

    diagnostics = _collect_diagnostics()
    log_files = _get_log_files()

    contents: list[tuple[str, int]] = []

    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('diagnostics.json', json.dumps(diagnostics, indent=2, sort_keys=True, default=str))
            for filepath in log_files:
                data = _read_log_tail(filepath)
                zf.writestr(filepath.name, data)
                contents.append((filepath.name, len(data)))
    except OSError as exception:
        if output_path.exists():
            try:
                output_path.unlink()
            except OSError:
                pass
        echo.echo_critical(f'Failed to write bug report to `{output_path}`: {exception}')

    echo.echo_success(f'Bug report written to: {output_path}')
    echo.echo_info('Contents:')
    echo.echo('  diagnostics.json')
    for archive_name, num_bytes in contents:
        echo.echo(f'  {archive_name} ({num_bytes} bytes)')
    echo.echo('')
    echo.echo('Attach this file to your post at Discourse:')
    echo.echo('https://aiida.discourse.group')
