###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi bug-report` command."""

import pathlib
import platform
import sys
import zipfile
from datetime import datetime

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import echo


def _invoke_command(cmd, args=None) -> str:
    """Invoke a click command and capture its output."""
    from click.testing import CliRunner

    runner = CliRunner()
    try:
        result = runner.invoke(verdi, [cmd] + (args or []), catch_exceptions=True)
        return result.output.strip()
    except Exception as exc:
        return f'Error running verdi {cmd}: {exc}'


def _collect_summary() -> str:
    """Collect a summary of the environment and service status."""
    import aiida

    lines = []
    lines.append('# AiiDA Bug Report')
    lines.append(f'Generated: {datetime.now().isoformat()}')
    lines.append(f'AiiDA version: {aiida.__version__}')
    lines.append(f'Python: {sys.version}')
    lines.append(f'Platform: {platform.platform()}')

    # verdi status
    lines.append('')
    lines.append('## verdi status')
    lines.append('```')
    lines.append(_invoke_command('status'))
    lines.append('```')

    # verdi profile show
    lines.append('')
    lines.append('## verdi profile show')
    lines.append('```')
    lines.append(_invoke_command('profile', ['show']))
    lines.append('```')

    return '\n'.join(lines)


def _get_rabbitmq_log_files(profile) -> list[pathlib.Path]:
    """Query the RabbitMQ management API for log file paths."""
    try:
        from aiida.brokers.rabbitmq.client import RabbitmqManagementClient

        config = profile.process_control_config
        client = RabbitmqManagementClient(
            username=config.get('broker_username', 'guest'),
            password=config.get('broker_password', 'guest'),
            hostname=config.get('broker_host', 'localhost'),
            virtual_host=config.get('broker_virtual_host', ''),
        )
        response = client.request('nodes')
        if response.status_code == 200:
            nodes = response.json()
            for node in nodes:
                for log_file in node.get('log_files', []):
                    path = pathlib.Path(log_file)
                    if path.exists():
                        return [path]
    except Exception:
        pass
    return []


def _get_log_files() -> list[tuple[str, pathlib.Path]]:
    """Return a list of (archive_name, path) for log files to include."""
    from aiida.manage import get_manager

    files = []

    try:
        from aiida.engine.daemon.client import get_daemon_client

        client = get_daemon_client()

        daemon_log = pathlib.Path(client.daemon_log_file)
        if daemon_log.exists():
            files.append(('daemon.log', daemon_log))

        circus_log = pathlib.Path(client.circus_log_file)
        if circus_log.exists():
            files.append(('circus.log', circus_log))

        broker = get_manager().get_broker()
        if broker is not None:
            from aiida.brokers.zmq.broker import ZmqBroker

            if isinstance(broker, ZmqBroker):
                status_file = broker.base_path / 'broker.status'
                if status_file.exists():
                    files.append(('broker.status', status_file))

                broker_log = broker.base_path / 'logs' / 'broker.log'
                if broker_log.exists():
                    files.append(('broker.log', broker_log))
            else:
                # RabbitMQ: try to get log file paths from the management API
                for log_path in _get_rabbitmq_log_files(get_manager().get_profile()):
                    files.append((log_path.name, log_path))
    except Exception:
        pass

    return files


@verdi.command('bug-report')
@click.option(
    '-o', '--output', type=click.Path(), default=None,
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

    summary = _collect_summary()
    log_files = _get_log_files()

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('summary.md', summary)
        for archive_name, filepath in log_files:
            zf.write(filepath, archive_name)

    echo.echo_success(f'Bug report written to: {output_path}')
    echo.echo_info('Contents:')
    echo.echo('  summary.md')
    for archive_name, filepath in log_files:
        size = filepath.stat().st_size
        echo.echo(f'  {archive_name} ({size} bytes)')
    echo.echo('')
    echo.echo('Attach this file to your GitHub issue at:')
    echo.echo('https://github.com/aiidateam/aiida-core/issues/new')
