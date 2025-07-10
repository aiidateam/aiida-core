###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi config` command."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments
from aiida.cmdline.utils import echo
from aiida.manage.configuration import MIGRATIONS, downgrade_config, get_config_path
from aiida.manage.configuration.settings import DEFAULT_CONFIG_INDENT_SIZE


@verdi.group('config')
def verdi_config():
    """Manage the AiiDA configuration."""


@verdi_config.command('list')
@click.argument('prefix', metavar='PREFIX', required=False, default='')
@click.option('-d', '--description', is_flag=True, help='Include description of options')
@click.pass_context
def verdi_config_list(ctx, prefix, description: bool):
    """List AiiDA options for the current profile.

    Optionally filtered by a prefix.
    """
    from tabulate import tabulate

    from aiida.manage.configuration import Profile
    from aiida.manage.configuration.config import Config

    config: Config = ctx.obj.config
    profile: Profile | None = ctx.obj.get('profile', None)

    if not profile:
        echo.echo_warning('no profiles configured: run `verdi setup` to create one')

    option_values = config.get_options(profile.name if profile else None)

    def _join(val):
        """Split arrays into multiple lines."""
        if isinstance(val, list):
            return '\n'.join(str(v) for v in val)
        return val

    if description:
        table = [
            [name, source, _join(value), '\n'.join(textwrap.wrap(c.description))]
            for name, (c, source, value) in option_values.items()
            if name.startswith(prefix)
        ]
        headers = ['name', 'source', 'value', 'description']
    else:
        table = [
            [name, source, _join(value)]
            for name, (c, source, value) in option_values.items()
            if name.startswith(prefix)
        ]
        headers = ['name', 'source', 'value']

    # sort by name
    table = sorted(table, key=lambda x: x[0])
    echo.echo(tabulate(table, headers=headers))


@verdi_config.command('show')
@arguments.CONFIG_OPTION(metavar='OPTION_NAME')
@click.pass_context
def verdi_config_show(ctx, option):
    """Show details of an AiiDA option for the current profile."""
    from aiida.manage.configuration import Profile
    from aiida.manage.configuration.config import Config

    config: Config = ctx.obj.config
    profile: Profile | None = ctx.obj.profile

    dct = {
        'schema': option.schema,
        'values': {
            'default': '<NOTSET>' if option.default is None else option.default,
            'global': config.options.get(option.name, '<NOTSET>'),
        },
    }

    if not profile:
        echo.echo_warning('no profiles configured: run `verdi setup` to create one')
    else:
        dct['values']['profile'] = profile.options.get(option.name, '<NOTSET>')

    echo.echo_dictionary(dct, fmt='yaml', sort_keys=False)


@verdi_config.command('get')
@arguments.CONFIG_OPTION(metavar='OPTION_NAME')
def verdi_config_get(option):
    """Get the value of an AiiDA option for the current profile."""
    from aiida import get_config_option

    value = get_config_option(option.name)
    echo.echo(str(value))


@verdi_config.command('set')
@arguments.CONFIG_OPTION(metavar='OPTION_NAME')
@click.argument('value', metavar='OPTION_VALUE')
@click.option('-g', '--global', 'globally', is_flag=True, help='Apply the option configuration wide.')
@click.option('-a', '--append', is_flag=True, help='Append the value to an existing array.')
@click.option('-r', '--remove', is_flag=True, help='Remove the value from an existing array.')
@click.pass_context
def verdi_config_set(ctx, option, value, globally, append, remove):
    """Set an AiiDA option.

    List values are split by whitespace, e.g. "a b" becomes ["a", "b"].
    """
    import typing

    from aiida.common.exceptions import ConfigurationError

    if typing.TYPE_CHECKING:
        from aiida.manage.configuration import Profile
        from aiida.manage.configuration.config import Config

    if append and remove:
        echo.echo_critical('Cannot flag both append and remove')

    config: Config = ctx.obj.config
    profile: Profile | None = ctx.obj.profile

    if option.global_only:
        globally = True

    # Define the string that determines the scope: for specific profile or globally
    scope = profile.name if (not globally and profile) else None
    scope_text = f"for '{profile.name}' profile" if (not globally and profile) else 'globally'

    if append or remove:
        try:
            current = config.get_option(option.name, scope=scope)
        except ConfigurationError as error:
            echo.echo_critical(str(error))
        if not isinstance(current, list):
            echo.echo_critical(f'cannot append/remove to value: {current}')
        if append:
            value = list(set(current + [value]))
        else:
            value = [item for item in current if item != value]
    elif option.valid_type == typing.List[str]:
        value = [value]

    # Set the specified option
    try:
        value = config.set_option(option.name, value, scope=scope)
    except ConfigurationError as error:
        echo.echo_critical(str(error))

    config.store()
    echo.echo_success(f"'{option.name}' set to {value} {scope_text}")


@verdi_config.command('unset')
@arguments.CONFIG_OPTION(metavar='OPTION_NAME')
@click.option('-g', '--global', 'globally', is_flag=True, help='Unset the option configuration wide.')
@click.pass_context
def verdi_config_unset(ctx, option, globally):
    """Unset an AiiDA option."""
    from aiida.manage.configuration import Profile
    from aiida.manage.configuration.config import Config

    config: Config = ctx.obj.config
    profile: Profile | None = ctx.obj.profile

    if option.global_only:
        globally = True

    # Define the string that determines the scope: for specific profile or globally
    scope = profile.name if (not globally and profile) else None
    scope_text = f"for '{profile.name}' profile" if (not globally and profile) else 'globally'

    # Unset the specified option
    config.unset_option(option.name, scope=scope)
    config.store()
    echo.echo_success(f"'{option.name}' unset {scope_text}")


@verdi_config.command('caching')
@click.option('-d', '--disabled', is_flag=True, help='List disabled types instead.')
def verdi_config_caching(disabled):
    """List caching-enabled process types for the current profile."""
    from aiida.manage.caching import get_use_cache
    from aiida.plugins.entry_point import ENTRY_POINT_STRING_SEPARATOR, get_entry_point_names

    for group in ['aiida.calculations', 'aiida.workflows']:
        for entry_point in get_entry_point_names(group):
            identifier = ENTRY_POINT_STRING_SEPARATOR.join([group, entry_point])
            if get_use_cache(identifier=identifier):
                if not disabled:
                    echo.echo(identifier)
            elif disabled:
                echo.echo(identifier)


@verdi_config.command('downgrade')
@click.argument('version', type=click.Choice(sorted(list({str(m.down_revision) for m in MIGRATIONS}))))
def verdi_config_downgrade(version):
    """Print a configuration, downgraded to a specific version."""
    path = Path(get_config_path())
    echo.echo_report(f'Downgrading configuration to v{version}: {path}')
    config = json.loads(path.read_text(encoding='utf8'))
    downgrade_config(config, int(version))
    path.write_text(json.dumps(config, indent=DEFAULT_CONFIG_INDENT_SIZE), encoding='utf8')
    echo.echo_success('Downgraded')
