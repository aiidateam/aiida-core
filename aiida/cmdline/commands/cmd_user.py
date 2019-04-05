# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi user` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from functools import partial
import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options, types
from aiida.cmdline.utils import decorators, echo

PASSWORD_UNCHANGED = '***'  # noqa


@verdi.group('user')
def verdi_user():
    """Inspect and manage users."""


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


@verdi_user.command('list')
@decorators.with_dbenv()
def user_list():
    """Displays list of all users."""
    from aiida.orm import User

    default_user = User.objects.get_default()

    if default_user is None:
        echo.echo_warning('no default user has been configured')

    attributes = ['email', 'first_name', 'last_name']
    sort = lambda user: user.email
    highlight = lambda x: x.email == default_user.email if default_user else None
    echo.echo_formatted_list(User.objects.all(), attributes, sort=sort, highlight=highlight)


@verdi_user.command()
@click.argument('user', metavar='USER', type=types.UserParamType(create=True))
@options.NON_INTERACTIVE()
@click.option(
    '--first-name',
    prompt='First name',
    type=click.STRING,
    contextual_default=partial(get_user_attribute_default, 'first_name'),
    cls=options.interactive.InteractiveOption)
@click.option(
    '--last-name',
    prompt='Last name',
    type=click.STRING,
    contextual_default=partial(get_user_attribute_default, 'last_name'),
    cls=options.interactive.InteractiveOption)
@click.option(
    '--institution',
    prompt='Institution',
    type=click.STRING,
    contextual_default=partial(get_user_attribute_default, 'institution'),
    cls=options.interactive.InteractiveOption)
@click.option(
    '--password',
    prompt='Password',
    hide_input=True,
    required=False,
    type=click.STRING,
    default=PASSWORD_UNCHANGED,
    confirmation_prompt=True,
    cls=options.interactive.InteractiveOption)
@decorators.with_dbenv()
def configure(user, first_name, last_name, institution, password, non_interactive):  # pylint: disable=unused-argument
    """Create or update a USER."""
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if institution is not None:
        user.institution = institution
    if password != PASSWORD_UNCHANGED:
        user.password = password

    action = 'updated' if user.is_stored else 'created'

    user.store()

    echo.echo_success('{} successfully {}'.format(user.email, action))

    if not user.has_usable_password():
        echo.echo_warning('no password set, so authentication for the REST API will be disabled')
