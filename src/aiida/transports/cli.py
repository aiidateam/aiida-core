###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Common cli utilities for transport plugins."""

from functools import partial

import click

from aiida.cmdline.params import arguments, options
from aiida.cmdline.params.options.interactive import InteractiveOption
from aiida.cmdline.utils import echo
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.exceptions import NotExistent

TRANSPORT_PARAMS = []


def match_comp_transport(ctx, param, computer, transport_type):
    """Check the computer argument against the transport type."""
    if computer.transport_type != transport_type:
        echo.echo_critical(
            f'Computer {computer.label} has transport of type "{computer.transport_type}", not {transport_type}!'
        )
    return computer


@with_dbenv()
def configure_computer_main(computer, user, **kwargs):
    """Configure a computer via the CLI."""
    from aiida import orm

    user = user or orm.User.collection.get_default()

    echo.echo_report(f'Configuring computer {computer.label} for user {user.email}.')
    if not user.is_default:
        echo.echo_report('Configuring different user, defaults may not be appropriate.')

    computer.configure(user=user, **kwargs)
    echo.echo_success(f'{computer.label} successfully configured for {user.email}')


def common_params(command_func):
    """Decorate a command function with common click parameters for all transport plugins."""
    for param in TRANSPORT_PARAMS.copy().reverse():
        command_func = param(command_func)
    return command_func


def transport_option_default(name, computer):
    """Determine the default value for an auth_param key."""
    import inspect

    transport_cls = computer.get_transport_class()
    suggester_name = f'_get_{name}_suggestion_string'
    members = dict(inspect.getmembers(transport_cls))
    suggester = members.get(suggester_name, None)
    default = None
    if suggester:
        default = suggester(computer)
    else:
        default = transport_cls.auth_options[name].get('default')
    return default


def interactive_default(key, also_non_interactive=False):
    """Create a contextual_default value callback for an auth_param key.

    :param key: the name of the option.
    :param also_non_interactive: indicates whether this option should provide a default also in non-interactive mode. If
        False, the option will raise `MissingParameter` if no explicit value is specified when the command is called in
        non-interactive mode.
    """

    @with_dbenv()
    def get_default(ctx):
        """Determine the default value from the context."""
        from aiida import orm

        if not also_non_interactive and ctx.params['non_interactive']:
            raise click.MissingParameter()

        user = ctx.params.get('user', None) or orm.User.collection.get_default()
        computer = ctx.params.get('computer', None)

        if computer is None:
            return None

        try:
            authinfo = orm.AuthInfo.collection.get(dbcomputer_id=computer.pk, aiidauser_id=user.pk)
        except NotExistent:
            authinfo = orm.AuthInfo(computer=computer, user=user)

        auth_params = authinfo.get_auth_params()
        suggestion = auth_params.get(key)
        suggestion = suggestion or transport_option_default(key, computer)
        return suggestion

    return get_default


def create_option(name, spec):
    """Create a click option from a name and partial specs as used in transport auth_options."""
    from copy import deepcopy

    spec = deepcopy(spec)
    name_dashed = name.replace('_', '-')
    option_name = f'--{name_dashed}'
    existing_option = spec.pop('option', None)

    if spec.pop('switch', False):
        option_name = '--{name}/--no-{name}'.format(name=name_dashed)

    kwargs = {'cls': InteractiveOption, 'show_default': True}

    non_interactive_default = spec.pop('non_interactive_default', False)
    kwargs['contextual_default'] = interactive_default(name, also_non_interactive=non_interactive_default)

    kwargs.update(spec)

    if existing_option:
        return existing_option(**kwargs)

    return click.option(option_name, **kwargs)


def list_transport_options(transport_type):
    from aiida.plugins import TransportFactory

    options_list = [create_option(*item) for item in TransportFactory(transport_type).auth_options.items()]
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


def create_configure_cmd(transport_type):
    """Create verdi computer configure subcommand for a transport type."""
    help_text = f"""Configure COMPUTER for {transport_type} transport."""

    def transport_configure_command(computer, user, non_interactive, **kwargs):
        """Configure COMPUTER for a type of transport."""
        configure_computer_main(computer, user, **kwargs)

    transport_configure_command.__doc__ = help_text

    return click.command(transport_type)(transport_options(transport_type)(transport_configure_command))
