"""Common cli utilities for transport plugins."""
import inspect
from functools import partial

import click

from aiida.cmdline.params import options, arguments
from aiida.cmdline.params.options.interactive import InteractiveOption
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.cmdline.utils import echo
from aiida.common.exceptions import NotExistent

TRANSPORT_PARAMS = []


# pylint: disable=unused-argument
def match_comp_transport(ctx, param, computer, transport_type):
    """Check the computer argument against the transport type."""
    if computer.get_transport_type() != transport_type:
        echo.echo_critical('Computer {} has transport of type "{}", not {}!'.format(computer.name,
                                                                                    computer.get_transport_type(),
                                                                                    transport_type))
    return computer


@with_dbenv()
def configure_computer_main(computer, user, **kwargs):
    """Configure a computer via the CLI."""
    from aiida.orm.backend import construct_backend
    from aiida.control.computer import configure_computer
    from aiida.common.utils import get_configured_user_email
    backend = construct_backend()
    user = user or backend.users.get_automatic_user()

    echo.echo_info('Configuring computer {} for user {}.'.format(computer.name, user.email))
    if user.email != get_configured_user_email():
        echo.echo_info('Configuring different user, defaults may not be appropriate.')

    configure_computer(computer, user=user, **kwargs)
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
    else:
        default = transport_cls.auth_options[name].get('default')
    return default


def interactive_default(transport_type, key, also_noninteractive=False):
    """Create a contextual_default value callback for an auth_param key."""

    @with_dbenv()
    def get_default(ctx):
        """Determine the default value from the context."""
        from aiida.orm.backend import construct_backend
        backend = construct_backend()
        user = ctx.params['user'] or backend.users.get_automatic_user()
        computer = ctx.params['computer']
        try:
            authinfo = backend.authinfos.get(computer=computer, user=user)
        except NotExistent:
            authinfo = backend.authinfos.create(computer=computer, user=user)
        non_interactive = ctx.params['non_interactive']
        old_authparams = authinfo.get_auth_params()
        if not also_noninteractive and non_interactive:
            raise click.MissingParameter()
        suggestion = old_authparams.get(key)
        suggestion = suggestion or transport_option_default(key, computer)
        return suggestion

    return get_default


def create_option(name, spec):
    """Create a click option from a name and partial specs as used in transport auth_options."""
    from copy import deepcopy
    spec = deepcopy(spec)
    name_dashed = name.replace('_', '-')
    option_name = '--{}'.format(name_dashed)
    existing_option = spec.pop('option', None)
    if spec.pop('switch', False):
        option_name = '--{name}/--no-{name}'.format(name=name_dashed)
    kwargs = {}
    if 'default' not in spec:
        kwargs['contextual_default'] = interactive_default(
            'ssh', name, also_noninteractive=spec.pop('non_interactive_default', False))
    kwargs['cls'] = InteractiveOption
    kwargs.update(spec)
    if existing_option:
        return existing_option(**kwargs)
    return click.option(option_name, **kwargs)


def list_transport_options(transport_type):
    from aiida.transport.util import TransportFactory
    options_list = [create_option(*item) for item in TransportFactory(transport_type).auth_options.items()]
    return options_list


def transport_options(transport_type):
    """Decorate a command with all options for a computer configure subcommand for transport_type."""

    def apply_options(func):
        """Decorate the command functionn with the appropriate options for the transport type."""
        options_list = list_transport_options(transport_type)
        options_list.reverse()
        func = arguments.COMPUTER(callback=partial(match_comp_transport, transport_type=transport_type))(func)
        func = options.NON_INTERACTIVE()(func)
        for option in options_list:
            func = option(func)
        func = options.USER()(func)
        return func

    return apply_options


def create_configure_cmd(transport_type):
    """Create verdi computer configure subcommand for a transport type."""
    help_text = """Configure COMPUTER for {} transport.""".format(transport_type)

    # pylint: disable=unused-argument
    def transport_configure_command(computer, user, non_interactive, **kwargs):
        """Configure COMPUTER for a type of transport."""
        configure_computer_main(computer, user, **kwargs)

    transport_configure_command.__doc__ = help_text

    return click.command(transport_type)(transport_options(transport_type)(transport_configure_command))
