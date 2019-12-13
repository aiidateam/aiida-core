# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Common cli utilities for transport plugins."""
import inspect
from functools import partial

import click

from aiida.cmdline.params import options, arguments
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.cmdline.utils import echo
from aiida.manage.manager import get_manager

TRANSPORT_PARAMS = []


# pylint: disable=unused-argument
def match_comp_transport(ctx, param, computer, transport_type):
    """Check the computer argument against the transport type."""
    if computer.get_transport_type() != transport_type:
        echo.echo_critical(
            'Computer {} has transport of type "{}", not {}!'.format(
                computer.name, computer.get_transport_type(), transport_type
            )
        )
    return computer


@with_dbenv()
def configure_computer_main(computer, user, **kwargs):
    """Configure a computer via the CLI."""
    from aiida import orm

    user = user or orm.User.objects.get_default()

    echo.echo_info('Configuring computer {} for user {}.'.format(computer.name, user.email))
    if user.email != get_manager().get_profile().default_user:
        echo.echo_info('Configuring different user, defaults may not be appropriate.')

    computer.configure(user=user, **kwargs)
    echo.echo_success('{} successfully configured for {}'.format(computer.name, user.email))


def common_params(command_func):
    """Decorate a command function with common click parameters for all transport plugins."""
    params = [i for i in TRANSPORT_PARAMS]
    params.reverse()
    for param in params:
        command_func = param(command_func)
    return command_func


def transport_option_default(name, computer):
    """Determine the default value for an auth_param key."""
    transport_cls = computer.get_transport_class()
    suggester_name = '_get_{}_suggestion_string'.format(name)
    members = dict(inspect.getmembers(transport_cls))
    suggester = members.get(suggester_name, None)
    default = None
    if suggester:
        default = suggester(computer)
    return default


def list_transport_options(transport_type):
    """Create and list all click CLI option classes.

    These are created by reading the appropriate tranport auth_options."""
    from aiida.plugins import TransportFactory
    from aiida.cmdline.commands.cmd_computer import create_option, VALID_OPTION_ORIGINS

    options_list = [
        create_option(key, option, originates_from=VALID_OPTION_ORIGINS.TRANSPORT)
        for key, option in TransportFactory(transport_type).auth_options.items()
    ]
    return options_list


def transport_options(transport_type):
    """Decorate a command with all options for a computer configure subcommand for transport_type."""

    def apply_options(func):
        """Decorate the command function with the appropriate options for the transport type."""
        options_list = list_transport_options(transport_type)
        options_list.reverse()
        func = arguments.COMPUTER(callback=partial(match_comp_transport, transport_type=transport_type))(func)
        func = options.NON_INTERACTIVE()(func)
        for option in options_list:
            func = option(func)
        func = options.USER()(func)
        func = options.CONFIG_FILE()(func)
        return func

    return apply_options


def create_configure_cmd_transport_only(transport_type):  # pylint: disable=invalid-name
    """Create verdi computer configure subcommand for a transport type."""
    help_text = """Configure COMPUTER for {} transport.""".format(transport_type)

    # pylint: disable=unused-argument
    def transport_configure_command(computer, user, non_interactive, **kwargs):
        """Configure COMPUTER for a type of transport."""
        configure_computer_main(computer, user, **kwargs)

    transport_configure_command.__doc__ = help_text

    return click.command(transport_type)(transport_options(transport_type)(transport_configure_command))
