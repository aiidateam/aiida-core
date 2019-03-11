# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This allows to setup and configure a user from command line.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from functools import partial
import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params.types.user import UserParamType
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.cmdline.params import options


@verdi.group('user')
def verdi_user():
    """Inspect and manage users."""


def get_default(value, ctx):
    """
    Get the default argument using a user instance property
    :param value: The name of the property to use
    :param ctx: The click context (which will be used to get the user)
    :return: The default value, or None
    """
    user = ctx.params['user']
    value = getattr(user, value)
    # In our case the empty string means there is no default
    if value == "":
        return None
    return value


PASSWORD_UNCHANGED = '***'  # noqa


@verdi_user.command()
@click.argument('user', metavar='USER', type=UserParamType(create=True))
@options.NON_INTERACTIVE()
@click.option(
    '--first-name',
    prompt='First name',
    type=str,
    contextual_default=partial(get_default, 'first_name'),
    cls=options.interactive.InteractiveOption)
@click.option(
    '--last-name',
    prompt='Last name',
    type=str,
    contextual_default=partial(get_default, 'last_name'),
    cls=options.interactive.InteractiveOption)
@click.option(
    '--institution',
    prompt='Institution',
    type=str,
    contextual_default=partial(get_default, 'institution'),
    cls=options.interactive.InteractiveOption)
@click.option(
    '--password',
    prompt='Password',
    hide_input=True,
    required=False,
    type=str,
    default=PASSWORD_UNCHANGED,
    confirmation_prompt=True,
    cls=options.interactive.InteractiveOption)
@with_dbenv()
def configure(user, first_name, last_name, institution, password, non_interactive):
    """
    Create or update a user.  Email address us taken as the user identiier.
    """
    # pylint: disable=unused-argument,unused-variable

    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if institution is not None:
        user.institution = institution
    if password != PASSWORD_UNCHANGED:
        user.password = password

    if user.is_stored:
        action = 'updated'
    else:
        action = 'created'
    user.store()
    click.echo(">> User {} {} ({}) {}. <<".format(user.first_name, user.last_name, user.email, action))
    if not user.has_usable_password():
        click.echo("** NOTE: no password set for this user, ")
        click.echo("         so they will not be able to login")
        click.echo("         via the REST API and the Web Interface.")


# pylint: disable=too-many-branches
@verdi_user.command('list')
@click.option('--color', is_flag=True, help='Show results with colors', default=False)
@with_dbenv()
def user_list(color):
    """
    List all the users.
    :param color: Show the list using colors
    """
    from aiida.manage.manager import get_manager
    from aiida import orm

    manager = get_manager()

    current_user = manager.get_profile().default_user_email

    if current_user is not None:
        pass
    else:
        click.echo("### No default user configured yet, run 'verdi install'! ###", err=True)

    for user in orm.User.objects.all():
        name_pieces = []
        if user.first_name:
            name_pieces.append(user.first_name)
        if user.last_name:
            name_pieces.append(user.last_name)
        full_name = ' '.join(name_pieces)
        if full_name:
            full_name = " {}".format(full_name)

        institution_str = " ({})".format(user.institution) if user.institution else ""

        permissions_list = []
        if not user.has_usable_password():
            permissions_list.append("NO_PWD")
            color_id = 'black'  # Dark gray
        else:
            color_id = 'blue'  # Blue
        permissions_str = ",".join(permissions_list)
        if permissions_str:
            permissions_str = " [{}]".format(permissions_str)

        if user.email == current_user:
            symbol = ">"
            color_id = 'red'
        else:
            symbol = "*"

        if not color:
            color_id = None

        click.secho("{}{}".format(symbol, user.email), fg=color_id, bold=True, nl=False)
        click.secho(":{}{}{}".format(full_name, institution_str, permissions_str), fg=color_id)
