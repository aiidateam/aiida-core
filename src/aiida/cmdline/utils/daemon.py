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
    from aiida.engine.daemon.client import DaemonClient, DaemonVersionInfo, PackageVersionInfo, PackageVersionSnapshot


def format_package_version_info(version_info: PackageVersionInfo) -> str:
    """Return a human-readable string for package version information."""
    version = version_info['version']
    editable_path = version_info.get('editable_path')

    if editable_path is not None:
        return f'{version} @ {editable_path}'

    return version


def package_versions_match(daemon_version: PackageVersionInfo, current_version: PackageVersionInfo) -> bool:
    """Return whether daemon and current package version information match."""
    if daemon_version['version'] != current_version['version']:
        return False

    daemon_path = daemon_version.get('editable_path')
    current_path = current_version.get('editable_path')

    if daemon_path is None and current_path is None:
        return True

    if daemon_path is None or current_path is None:
        return False

    return daemon_path == current_path


def format_package_state_change_lines(
    daemon_versions: PackageVersionSnapshot, current_versions: PackageVersionSnapshot
) -> list[str]:
    """Return formatted package-state mismatch lines."""
    changed: list[str] = []
    added: list[str] = []
    removed: list[str] = []

    for package in sorted(set(daemon_versions) | set(current_versions)):
        daemon_version = daemon_versions.get(package)
        current_version = current_versions.get(package)

        if daemon_version is not None and current_version is not None:
            if package_versions_match(daemon_version, current_version):
                continue
            changed.append(
                f'{package} ({format_package_version_info(daemon_version)} '
                f'-> {format_package_version_info(current_version)})'
            )
        elif current_version is not None:
            added.append(f'{package} ({format_package_version_info(current_version)})')
        elif daemon_version is not None:
            removed.append(f'{package} ({format_package_version_info(daemon_version)})')

    lines: list[str] = []
    if changed:
        lines.append(f'Changed packages: {", ".join(changed)}')
    if added:
        lines.append(f'Added packages: {", ".join(added)}')
    if removed:
        lines.append(f'Removed packages: {", ".join(removed)}')
    return lines


def validate_python_binary(version_info: DaemonVersionInfo) -> str | None:
    """Return an error message if the daemon's Python binary differs from the current one, or None if they match."""
    import os

    daemon_binary = os.path.realpath(version_info['python_binary'])
    current_binary = os.path.realpath(sys.executable)
    if daemon_binary == current_binary:
        return None

    return (
        'The daemon is running with a different Python binary than the current one. '
        'Run `verdi daemon restart` to use the current Python binary.\n'
        f'Daemon: {version_info["python_binary"]}\n'
        f'Current: {sys.executable}'
    )


def validate_package_versions(version_info: DaemonVersionInfo) -> str | None:
    """Return an error message if daemon and current package versions differ, or None if they match."""
    from aiida.engine.daemon.client import DaemonClient

    current_versions = DaemonClient.get_package_version_snapshot()
    validated = DaemonClient._validate_package_version_snapshot(current_versions)
    if validated is None:
        return None
    change_lines = format_package_state_change_lines(version_info['packages'], validated)
    if not change_lines:
        return None

    header = (
        'The daemon was started with different package versions than currently installed. '
        'Running processes may use the old versions and behave unexpectedly. '
        'Run `verdi daemon restart` to pick up the new versions.'
    )
    return '\n'.join([header, *change_lines])


def validate_daemon_version(client: DaemonClient) -> str | None:
    """Return an error message if the daemon environment differs from the current one, or None if they match."""
    version_info = client.get_daemon_version_info()
    if version_info is None:
        return None

    if (error := validate_python_binary(version_info)) is not None:
        return error

    return validate_package_versions(version_info)
