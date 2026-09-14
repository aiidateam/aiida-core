###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi user` command."""

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options, types
from aiida.cmdline.params.options.commands import setup as options_setup
from aiida.cmdline.utils import decorators, echo


@verdi.group('user')
def verdi_user():
    """Inspect and manage users."""


@verdi_user.command('list')
@decorators.with_dbenv()
def user_list():
    """Show a list of all users."""
    from aiida.orm import User

    table = []

    for user in sorted(User.collection.all(), key=lambda user: user.email):
        row = ['*' if user.is_default else '', user.email, user.first_name, user.last_name, user.institution]
        if user.is_default:
            table.append(list(map(echo.highlight_string, row)))
        else:
            table.append(row)

    echo.echo_tabulate(table, headers=['', 'Email', 'First name', 'Last name', 'Institution'])
    echo.echo('')

    if User.collection.get_default() is None:
        echo.echo_warning('No default user has been configured')
    else:
        echo.echo_report('The user highlighted and marked with a * is the default user.')


@verdi_user.command('configure')
@click.option(
    '--email',
    'user',
    prompt='User email',
    help='Email address that serves as the user name and a way to identify data created by it.',
    type=types.UserParamType(create=True),
    cls=options.interactive.InteractiveOption,
)
@options_setup.SETUP_USER_FIRST_NAME(contextual_default=lambda ctx: ctx.params['user'].first_name)
@options_setup.SETUP_USER_LAST_NAME(contextual_default=lambda ctx: ctx.params['user'].last_name)
@options_setup.SETUP_USER_INSTITUTION(contextual_default=lambda ctx: ctx.params['user'].institution)
@click.option(
    '--set-default',
    prompt='Set as default?',
    help='Set the user as the default user.',
    is_flag=True,
    cls=options.interactive.InteractiveOption,
    contextual_default=lambda ctx: ctx.params['user'].is_default,
)
@click.pass_context
@decorators.with_dbenv()
def user_configure(ctx, user, first_name, last_name, institution, set_default):
    """Configure a new or existing user.

    An e-mail address is used as the user name.
    """
    action = 'updated' if user.is_stored else 'created'
    user.first_name = first_name
    user.last_name = last_name
    user.institution = institution
    user.store()

    echo.echo_success(f'Successfully {action} `{user.email}`.')

    if set_default:
        ctx.invoke(user_set_default, user=user)


@verdi_user.command('set-default')
@arguments.USER()
@click.pass_context
@decorators.with_dbenv()
def user_set_default(ctx, user):
    """Set a user as the default user for the profile."""
    from aiida.manage import get_manager

    get_manager().set_default_user_email(ctx.obj.profile, user.email)
    echo.echo_success(f'Set `{user.email}` as the default user for profile `{ctx.obj.profile.name}.`')
