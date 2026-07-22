###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for daemon-related CLI output."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiida.engine.daemon.client import DaemonClient, DaemonEnvInfo, PackageVersionInfo, PackageVersionSnapshot


def format_package_version_info(version_info: PackageVersionInfo) -> str:
    """Return a human-readable string for package version information."""
    version = version_info['version']
    editable_path = version_info.get('editable_path')

    if editable_path is not None:
        return f'{version} @ {editable_path}'

    return version


def package_versions_match(package_version: PackageVersionInfo, current_package_version: PackageVersionInfo) -> bool:
    """Return whether daemon and current package version information match."""
    if package_version['version'] != current_package_version['version']:
        return False

    daemon_path = package_version.get('editable_path')
    current_path = current_package_version.get('editable_path')

    if daemon_path is None and current_path is None:
        return True

    if daemon_path is None or current_path is None:
        return False

    return daemon_path == current_path


def format_package_state_change_lines(
    daemon_packages: PackageVersionSnapshot, current_packages: PackageVersionSnapshot
) -> list[str]:
    """Return formatted package-state mismatch lines."""
    changed: list[str] = []
    added: list[str] = []
    removed: list[str] = []

    for package in sorted(set(daemon_packages) | set(current_packages)):
        package_version = daemon_packages.get(package)
        current_package_version = current_packages.get(package)

        if package_version is not None and current_package_version is not None:
            if package_versions_match(package_version, current_package_version):
                continue
            changed.append(
                f'{package} ({format_package_version_info(package_version)} '
                f'-> {format_package_version_info(current_package_version)})'
            )
        elif current_package_version is not None:
            added.append(f'{package} ({format_package_version_info(current_package_version)})')
        elif package_version is not None:
            removed.append(f'{package} ({format_package_version_info(package_version)})')

    lines: list[str] = []
    if changed:
        lines.append(f'Changed packages: {", ".join(changed)}')
    if added:
        lines.append(f'Added packages: {", ".join(added)}')
    if removed:
        lines.append(f'Removed packages: {", ".join(removed)}')
    return lines


def validate_python_binary(env_info: DaemonEnvInfo) -> str | None:
    """Return an error message if the daemon's Python binary differs from the current one, or None if they match."""
    if env_info['python_binary'] == sys.executable:
        return None

    return (
        'The daemon is running with a different Python binary than the current one. '
        'Run `verdi daemon restart` to use the current Python binary.\n'
        f'Daemon: {env_info["python_binary"]}\n'
        f'Current: {sys.executable}'
    )


def validate_package_versions(env_info: DaemonEnvInfo) -> str | None:
    """Return an error message if daemon and current package versions differ, or None if they match."""
    from aiida.engine.daemon.client import DaemonClient

    current_packages = DaemonClient.get_package_version_snapshot()
    validated = DaemonClient._validate_package_version_snapshot(current_packages)
    if validated is None:
        return None
    change_lines = format_package_state_change_lines(env_info['packages'], validated)
    if not change_lines:
        return None

    header = (
        'The daemon was started with different package versions than currently installed. '
        'Running processes may use the old versions and behave unexpectedly. '
        'Run `verdi daemon restart` to pick up the new versions.'
    )
    return '\n'.join([header, *change_lines])


def validate_daemon_env(client: DaemonClient) -> str | None:
    """Return an error message if the daemon environment differs from the current one, or None if they match."""
    env_info = client.get_daemon_env_info()
    if env_info is None:
        return None

    if (error := validate_python_binary(env_info)) is not None:
        return error

    return validate_package_versions(env_info)
