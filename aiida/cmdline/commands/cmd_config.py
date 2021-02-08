# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi config` command."""
import textwrap

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments
from aiida.cmdline.utils import decorators, echo


class DeprecatedCommandGroup(click.Group):
    """Overloads the get_command with one that identifies deprecated commands."""

    def get_command(self, ctx, cmd_name):
        """Override the default click.Group get_command with one that identifies deprecated commands."""
        cmd = click.Group.get_command(self, ctx, cmd_name)

        if cmd is not None:
            return cmd

        if cmd_name in [
            'daemon.default_workers', 'logging.plumpy_loglevel', 'daemon.timeout', 'logging.sqlalchemy_loglevel',
            'daemon.worker_process_slots', 'logging.tornado_loglevel', 'db.batch_size', 'runner.poll.interval',
            'logging.aiida_loglevel', 'user.email', 'logging.alembic_loglevel', 'user.first_name',
            'logging.circus_loglevel', 'user.institution', 'logging.db_loglevel', 'user.last_name',
            'logging.kiwipy_loglevel', 'verdi.shell.auto_import', 'logging.paramiko_loglevel',
            'warnings.showdeprecations', 'autofill.user.email', 'autofill.user.first_name', 'autofill.user.last_name',
            'autofill.user.institution'
        ]:
            ctx.obj.deprecated_name = cmd_name
            cmd = click.Group.get_command(self, ctx, '_deprecated')
            return cmd

        ctx.fail(f"'{cmd_name}' is not a verdi config command.")

        return None


@verdi.group('config', cls=DeprecatedCommandGroup)
def verdi_config():
    """Manage AiiDA configuration."""


@verdi_config.command('list')
@click.option('-d', '--description', is_flag=True, help='Include description of options')
@click.pass_context
def verdi_config_list(ctx, description: bool):
    """List AiiDA options for the current profile."""
    from tabulate import tabulate

    from aiida.manage.configuration import Config, Profile

    config: Config = ctx.obj.config
    profile: Profile = ctx.obj.profile

    option_values = config.get_options(profile.name)
    if description:
        table = [[name, source, value, '\n'.join(textwrap.wrap(c.description))]
                 for name, (c, source, value) in option_values.items()]
        headers = ['name', 'source', 'value', 'description']
    else:
        table = [[name, source, value] for name, (c, source, value) in option_values.items()]
        headers = ['name', 'source', 'value']

    # sort by name
    table = sorted(table, key=lambda x: x[0])
    echo.echo(tabulate(table, headers=headers))


@verdi_config.command('show')
@arguments.CONFIG_OPTION(metavar='OPTION_NAME')
@click.pass_context
def verdi_config_show(ctx, option):
    """Show an AiiDA option for the current profile."""
    from aiida.manage.configuration import Config, Profile

    config: Config = ctx.obj.config
    profile: Profile = ctx.obj.profile

    dct = {
        'value': {
            'profile': config.get_option(option.name, scope=profile.name),
            'global': config.get_option(option.name),
        },
        'schema': option.schema
    }

    echo.echo_dictionary(dct, fmt='yaml')


@verdi_config.command('set')
@arguments.CONFIG_OPTION(metavar='OPTION_NAME')
@click.argument('value', metavar='OPTION_VALUE')
@click.option('--global', 'globally', is_flag=True, help='Apply the option configuration wide.')
@click.pass_context
def verdi_config_set(ctx, option, value, globally):
    """Unset an AiiDA option."""
    from aiida.manage.configuration import Config, Profile, ValidationError

    config: Config = ctx.obj.config
    profile: Profile = ctx.obj.profile

    if option.global_only:
        globally = True

    # Define the string that determines the scope: for specific profile or globally
    scope = profile.name if (not globally and profile) else None
    scope_text = f'for {profile.name}' if (not globally and profile) else 'globally'

    # Set the specified option
    try:
        config.set_option(option.name, value, scope=scope)
    except ValidationError as error:
        echo.echo_critical(str(error))
    config.store()
    echo.echo_success(f'{option.name} set to {value} {scope_text}')


@verdi_config.command('unset')
@arguments.CONFIG_OPTION(metavar='OPTION_NAME')
@click.option('--global', 'globally', is_flag=True, help='Apply the option configuration wide.')
@click.pass_context
def verdi_config_unset(ctx, option, globally):
    """Set an AiiDA option."""
    from aiida.manage.configuration import Config, Profile

    config: Config = ctx.obj.config
    profile: Profile = ctx.obj.profile

    if option.global_only:
        globally = True

    # Define the string that determines the scope: for specific profile or globally
    scope = profile.name if (not globally and profile) else None
    scope_text = f'for {profile.name}' if (not globally and profile) else 'globally'

    # Unset the specified option
    config.unset_option(option.name, scope=scope)
    config.store()
    echo.echo_success(f'{option.name} unset {scope_text}')


@verdi_config.command('_deprecated', hidden=True)
@decorators.deprecated_command("This command has been deprecated. Please use 'verdi config show/set/unset' instead.")
@click.argument('value', metavar='OPTION_VALUE', required=False)
@click.option('--global', 'globally', is_flag=True, help='Apply the option configuration wide.')
@click.option('--unset', is_flag=True, help='Remove the line matching the option name from the config file.')
@click.pass_context
def verdi_config_deprecated(ctx, value, globally, unset):
    """"This command has been deprecated. Please use 'verdi config show/set/unset' instead."""
    from aiida.manage.configuration import get_option
    option = get_option(ctx.obj.deprecated_name)
    if unset:
        ctx.invoke(verdi_config_unset, option=option, globally=globally)
    elif value is not None:
        ctx.invoke(verdi_config_set, option=option, value=value, globally=globally)
    else:
        ctx.invoke(verdi_config_show, option=option)
