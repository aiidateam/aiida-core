###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""``verdi notebook`` commands."""

from __future__ import annotations

import sys
import typing as t

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import echo

if t.TYPE_CHECKING:
    from jupyter_client.kernelspec import KernelSpec


@verdi.group('notebook')
def verdi_notebook():
    """Manage Jupyter notebooks."""


def get_existing_spec(name: str) -> KernelSpec | None:
    """Return the registered kernel spec called ``name``, if any.

    :param name: the name the kernel was registered under.
    :return: the spec, or `None` when no kernel is registered under ``name`` or it cannot be read.
    """
    from jupyter_client.kernelspec import KernelSpecManager, NoSuchKernel

    try:
        return KernelSpecManager().get_kernel_spec(name)
    except NoSuchKernel:
        return None
    except Exception as exc:
        echo.echo_warning(f'could not read the existing kernel `{name}` ({exc}), it will be overwritten.')
        return None


@verdi_notebook.command('install')
@click.option('--name', default='aiida', show_default=True, help='Name to register the kernel under.')
@click.option('--display-name', help='Name shown by the Jupyter kernel picker. [default: keep existing, else derived]')
@click.option(
    '--user/--sys-prefix',
    default=True,
    show_default=True,
    help='Register for the current user, or inside the active environment.',
)
@click.option('--force', is_flag=True, help='Overwrite an already registered kernel without asking.')
def notebook_install(name: str, display_name: str | None, user: bool, force: bool) -> None:
    """Register a Jupyter kernel for this environment and configuration directory.

    A kernel is started by the Jupyter server, so it inherits neither the active virtual environment nor
    ``AIIDA_PATH``. A profile that works in the terminal is then missing in a notebook. Both are written into
    the kernel specification, so that whichever way the notebook is opened it reads the same configuration.
    """
    try:
        from ipykernel.kernelspec import install
    except ImportError:
        echo.echo_critical('`ipykernel` is not installed. Install it with `pip install aiida-core[notebook]`.')

    from aiida.manage.configuration import get_config

    dirpath_config = str(get_config().dirpath)
    existing = get_existing_spec(name)
    existing_env: dict[str, str] = dict(existing.env or {}) if existing is not None else {}
    existing_argv = existing.argv[0] if existing is not None and existing.argv else None
    default_display = f'AiiDA ({dirpath_config})'

    if existing is not None and existing.display_name == f'AiiDA ({existing_env.get("AIIDA_PATH")})':
        existing_display: str | None = None  # stale auto-derived name, regenerate it below
    elif existing is not None:
        existing_display = existing.display_name
    else:
        existing_display = None

    resolved_display = display_name or existing_display or default_display
    env = {**existing_env, 'AIIDA_PATH': dirpath_config}

    if (
        existing is not None
        and existing_env.get('AIIDA_PATH') == dirpath_config
        and existing_argv == sys.executable
        and existing.display_name == resolved_display
    ):
        echo.echo_report(f'kernel `{name}` is already up to date.')
        return

    if existing is not None:
        echo.echo_warning(f'a kernel `{name}` is already registered.')
        if existing_env.get('AIIDA_PATH') != dirpath_config:
            echo.echo_report(f'configuration: `{existing_env.get("AIIDA_PATH")}` -> `{dirpath_config}`')
        if existing_argv != sys.executable:
            echo.echo_report(f'interpreter: `{existing_argv}` -> `{sys.executable}`')
        retained = sorted(key for key in existing_env if key != 'AIIDA_PATH')
        if retained:
            echo.echo_report(f'retained variables: {", ".join(f"`{key}`" for key in retained)}')
        if not force:
            click.confirm('Overwrite it?', abort=True)

    dirpath_kernel = install(
        user=user,
        kernel_name=name,
        display_name=resolved_display,
        prefix=None if user else sys.prefix,
        env=env,
    )

    echo.echo_success(f'registered the kernel `{name}` in `{dirpath_kernel}`')
    echo.echo_report(f'it reads the configuration in `{dirpath_config}` and runs `{sys.executable}`')
