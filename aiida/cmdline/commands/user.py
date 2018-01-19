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
import sys

import click

from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.cmdline.commands import user, verdi
from aiida.control.user import get_or_new_user

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class User(VerdiCommandWithSubcommands):
    """
    List and configure new AiiDA users.

    Allow to see the list of AiiDA users, their permissions, and to configure
    old and new users.
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        self.valid_subcommands = {
            'configure': (self.cli, self.complete_emails),
            'list': (self.cli, self.complete_none),
        }

    def cli(self, *args):
        verdi()

    def complete_emails(self, subargs_idx, subargs):
        load_dbenv()

        from aiida.backends.djsite.db import models

        emails = models.DbUser.objects.all().values_list('email', flat=True)
        return "\n".join(emails)


def do_configure(email, first_name, last_name, institution, no_password, non_interactive=False, force=False, **kwargs):
    if not is_dbenv_loaded():
        load_dbenv()

    from aiida.orm import User as UserModel
    import readline
    import getpass

    configure_user = False
    user, created = get_or_new_user(email=email)

    if not created:
        click.echo("\nAn AiiDA user for email '{}' is already present "
                   "in the DB:".format(email))

        if not non_interactive:
            reply = click.confirm("Do you want to reconfigure it?")
            if reply:
                configure_user = True
        elif force:
            configure_user = True
    else:
        configure_user = True
        click.echo("Configuring a new user with email '{}'".format(email))

    if configure_user:
        if not non_interactive:
            try:
                attributes = {}
                for field in UserModel.REQUIRED_FIELDS:
                    verbose_name = field.capitalize()
                    readline.set_startup_hook(lambda: readline.insert_text(
                        getattr(user, field)))
                    if field == 'first_name' and first_name:
                        attributes[field] = first_name
                    elif field == 'last_name' and last_name:
                        attributes[field] = last_name
                    elif field == 'institution' and institution:
                        attributes[field] = institution
                    else:
                        attributes[field] = raw_input('{}: '.format(verbose_name))
            finally:
                readline.set_startup_hook(lambda: readline.insert_text(""))
        else:
            attributes = kwargs.copy()
            attributes['first_name'] = first_name
            attributes['last_name'] = last_name
            attributes['institution'] = institution

        for k, v in attributes.iteritems():
            setattr(user, k, v)

        change_password = False
        if no_password:
            user.password = None
        else:
            if user.has_usable_password():
                reply = raw_input("Do you want to replace the user password? [y/N] ")
                reply = reply.strip()
                if not reply:
                    pass
                elif reply.lower() == 'n':
                    pass
                elif reply.lower() == 'y':
                    change_password = True
                else:
                    click.echo("Invalid answer, assuming answer was 'NO'")
            else:
                reply = raw_input("The user has no password, do you want to set one? [y/N] ")
                reply = reply.strip()
                if not reply:
                    pass
                elif reply.lower() == 'n':
                    pass
                elif reply.lower() == 'y':
                    change_password = True
                else:
                    click.echo("Invalid answer, assuming answer was 'NO'")

            if change_password:
                match = False
                while not match:
                    new_password = getpass.getpass("Insert the new password: ")
                    new_password_check = getpass.getpass(
                        "Insert the new password (again): ")
                    if new_password == new_password_check:
                        match = True
                    else:
                        click.echo("ERROR, the two passwords do not match.")
                ## Set the password here
                user.password = new_password
            else:
                user.password = None

        user.force_save()
        click.echo(">> User {} {} saved. <<".format(user.first_name,
                                               user.last_name))
        if not user.has_usable_password():
            click.echo("** NOTE: no password set for this user, ")
            click.echo("         so he/she will not be able to login")
            click.echo("         via the REST API and the Web Interface.")

@user.command(context_settings=CONTEXT_SETTINGS)
@click.argument('email', type=str)
@click.option('--first-name', prompt='First Name', type=str)
@click.option('--last-name', prompt='Last Name', type=str)
@click.option('--institution', prompt='Institution', type=str)
@click.option('--no-password', is_flag=True)
@click.option('--force-reconfigure', is_flag=True)
def configure(email, first_name, last_name, institution, no_password, force_reconfigure):
    do_configure(email=email, first_name=first_name,
            last_name=last_name, institution=institution,
            no_password=no_password, force_reconfigure=force_reconfigure)

@user.command()
@click.option('--color', is_flag=True, help='Show results with colors', default=False)
def list(color):
    if not is_dbenv_loaded():
        load_dbenv()

    from aiida.orm.implementation import User
    from aiida.common.utils import get_configured_user_email

    from aiida.common.exceptions import ConfigurationError

    try:
        current_user = get_configured_user_email()
    except ConfigurationError:
        current_user = None

    if current_user is not None:
        pass
    else:
        click.echo("### No default user configured yet, run 'verdi install'! ###", err=True)

    for user in User.get_all_users():
        name_pieces = []
        if user.first_name:
            name_pieces.append(user.first_name)
        if user.last_name:
            name_pieces.append(user.last_name)
        full_name = " ".join(name_pieces)
        if full_name:
            full_name = " {}".format(full_name)

        institution_str = " ({})".format(
            user.institution) if user.institution else ""

        color_id = 39  # Default foreground color
        permissions_list = []
        if user.is_staff:
            permissions_list.append("STAFF")
        if user.is_superuser:
            permissions_list.append("SUPERUSER")
        if not user.has_usable_password():
            permissions_list.append("NO_PWD")
            color_id = 90  # Dark gray
        else:
            color_id = 34  # Blue
        permissions_str = ",".join(permissions_list)
        if permissions_str:
            permissions_str = " [{}]".format(permissions_str)

        if user.email == current_user:
            symbol = ">"
            color_id = 31
        else:
            symbol = "*"

        if color:
            start_color = "\x1b[{}m".format(color_id)
            end_color = "\x1b[0m"
            bold_sequence = "\x1b[1;{}m".format(color_id)
            nobold_sequence = "\x1b[0;{}m".format(color_id)
        else:
            start_color = ""
            end_color = ""
            bold_sequence = ""
            nobold_sequence = ""

        click.echo("{}{} {}{}{}:{}{}{}{}".format(
            start_color, symbol,
            bold_sequence, user.email, nobold_sequence,
            full_name, institution_str, permissions_str, end_color))


