# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi user` command."""
from functools import partial

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options, types
from aiida.cmdline.utils import decorators, echo


def get_user_attribute_default(attribute, ctx):
    """Return the default value for the given attribute of the user passed in the context.

    :param attribute: attribute for which to get the current value
    :param ctx: click context which should contain the selected user
    :return: user attribute default value if set, or None
    """
    default = getattr(ctx.params['user'], attribute)

    # None or empty string means there is no default
    if not default:
        return None

    return default


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
    cls=options.interactive.InteractiveOption
)
@click.option(
    '--first-name',
    prompt='First name',
    help='First name of the user.',
    type=click.STRING,
    contextual_default=partial(get_user_attribute_default, 'first_name'),
    cls=options.interactive.InteractiveOption
)
@click.option(
    '--last-name',
    prompt='Last name',
    help='Last name of the user.',
    type=click.STRING,
    contextual_default=partial(get_user_attribute_default, 'last_name'),
    cls=options.interactive.InteractiveOption
)
@click.option(
    '--institution',
    prompt='Institution',
    help='Institution of the user.',
    type=click.STRING,
    contextual_default=partial(get_user_attribute_default, 'institution'),
    cls=options.interactive.InteractiveOption
)
@click.option(
    '--set-default',
    prompt='Set as default?',
    help='Set the user as the default user for the current profile.',
    is_flag=True,
    cls=options.interactive.InteractiveOption
)
@click.pass_context
@decorators.with_dbenv()
def user_configure(ctx, user, first_name, last_name, institution, set_default):
    """Configure a new or existing user.

    An e-mail address is used as the user name.
    """
    # pylint: disable=too-many-arguments
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if institution is not None:
        user.institution = institution

    action = 'updated' if user.is_stored else 'created'

    user.store()

    echo.echo_success(f'{user.email} successfully {action}')

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
    echo.echo_success(f'set `{user.email}` as the new default user for profile `{ctx.obj.profile.name}`')
