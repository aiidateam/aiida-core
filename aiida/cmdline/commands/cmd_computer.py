# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-many-statements,too-many-branches
"""`verdi computer` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import sys
from functools import partial
from six.moves import zip

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options, arguments
from aiida.cmdline.params.options.commands import computer as options_computer
from aiida.cmdline.utils import echo
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.cmdline.utils.multi_line_input import ensure_scripts
from aiida.common.exceptions import ValidationError, InputValidationError
from aiida.control.computer import ComputerBuilder
from aiida.plugins.entry_point import get_entry_points
from aiida.transport import cli as transport_cli


@verdi.group('computer')
def verdi_computer():
    """Setup and manage computers."""
    pass


def get_computer_names():
    """
    Retrieve the list of computers in the DB.
    """
    from aiida.orm.querybuilder import QueryBuilder
    builder = QueryBuilder()
    builder.append(type='computer', project=['name'])
    if builder.count() > 0:
        return next(zip(*builder.all()))  # return the first entry

    return []


def prompt_for_computer_configuration(computer):  # pylint: disable=unused-argument
    pass


def _computer_test_get_jobs(transport, scheduler, authinfo):  # pylint: disable=unused-argument
    """
    Internal test to check if it is possible to check the queue state.

    :param transport: an open transport
    :param scheduler: the corresponding scheduler class
    :param authinfo: the AuthInfo object (from which one can get computer and aiidauser)
    :return: True if the test succeeds, False if it fails.
    """
    echo.echo("> Getting job list...")
    found_jobs = scheduler.getJobs(as_dict=True)
    echo.echo("  `-> OK, {} jobs found in the queue.".format(len(found_jobs)))
    return True


def _computer_create_temp_file(transport, scheduler, authinfo):  # pylint: disable=unused-argument
    """
    Internal test to check if it is possible to create a temporary file
    and then delete it in the work directory

    :note: exceptions could be raised

    :param transport: an open transport
    :param scheduler: the corresponding scheduler class
    :param authinfo: the AuthInfo object (from which one can get computer and aiidauser)
    :return: True if the test succeeds, False if it fails.
    """
    import tempfile
    import datetime
    import os

    file_content = "Test from 'verdi computer test' on {}".format(datetime.datetime.now().isoformat())
    echo.echo("> Creating a temporary file in the work directory...")
    echo.echo("  `-> Getting the remote user name...")
    remote_user = transport.whoami()
    echo.echo("      [remote username: {}]".format(remote_user))
    workdir = authinfo.get_workdir().format(username=remote_user)
    echo.echo("      [Checking/creating work directory: {}]".format(workdir))

    try:
        transport.chdir(workdir)
    except IOError:
        transport.makedirs(workdir)
        transport.chdir(workdir)

    with tempfile.NamedTemporaryFile(mode='w+') as tempf:
        fname = os.path.split(tempf.name)[1]
        echo.echo("  `-> Creating the file {}...".format(fname))
        remote_file_path = os.path.join(workdir, fname)
        tempf.write(file_content)
        tempf.flush()
        transport.putfile(tempf.name, remote_file_path)
    echo.echo("  `-> Checking if the file has been created...")
    if not transport.path_exists(remote_file_path):
        echo.echo_error("* ERROR! The file was not found!")
        return False
    else:
        echo.echo("      [OK]")
    echo.echo("  `-> Retrieving the file and checking its content...")

    handle, destfile = tempfile.mkstemp()
    os.close(handle)
    try:
        transport.getfile(remote_file_path, destfile)
        with open(destfile) as dfile:
            read_string = dfile.read()
        echo.echo("      [Retrieved]")
        if read_string != file_content:
            echo.echo_error("* ERROR! The file content is different from what was " "expected!")
            echo.echo("** Expected:")
            echo.echo(file_content)
            echo.echo("** Found:")
            echo.echo(read_string)
            return False
        else:
            echo.echo("      [Content OK]")
    finally:
        os.remove(destfile)

    echo.echo("  `-> Removing the file...")
    transport.remove(remote_file_path)
    echo.echo("  [Deleted successfully]")
    return True


def get_parameter_default(parameter, ctx):
    """
    Get the value for a specific parameter from the computer_builder or the default value of that option

    :param parameter: parameter name
    :param ctx: click context of the command
    :return: parameter default value, or None
    """
    default = None

    for param in ctx.command.get_params(ctx):
        if param.name == parameter:
            default = param.default

    try:
        value = getattr(ctx.computer_builder, parameter)
        if value == '' or value is None:
            value = default
    except KeyError:
        value = default

    return value


# pylint: disable=unused-argument
def set_computer_builder(ctx, param, value):
    """Set the computer spec for defaults of following options."""
    ctx.computer_builder = ComputerBuilder.from_computer(value)
    return value


@verdi_computer.command('setup')
@options_computer.LABEL()
@options_computer.HOSTNAME()
@options_computer.DESCRIPTION()
@options_computer.ENABLED()
@options_computer.TRANSPORT()
@options_computer.SCHEDULER()
@options_computer.SHEBANG()
@options_computer.WORKDIR()
@options_computer.MPI_RUN_COMMAND()
@options_computer.MPI_PROCS_PER_MACHINE()
@options.PREPEND_TEXT()
@options.APPEND_TEXT()
@options.NON_INTERACTIVE()
@click.pass_context
@with_dbenv()
def computer_setup(ctx, non_interactive, **kwargs):
    """Add a Computer."""
    if kwargs['label'] in get_computer_names():
        echo.echo_critical('A computer called {c} already exists. '
                           'Use "verdi computer duplicate {c}" to set up a new '
                           'computer starting from the settings of {c}.'.format(c=kwargs['label']))

    if not non_interactive:
        try:
            pre, post = ensure_scripts(kwargs.pop('prepend_text', ''), kwargs.pop('append_text', ''), kwargs)
        except InputValidationError as exception:
            raise click.BadParameter('invalid prepend and or append text: {}'.format(exception))

        kwargs['prepend_text'] = pre
        kwargs['append_text'] = post

    kwargs['transport'] = kwargs['transport'].name
    kwargs['scheduler'] = kwargs['scheduler'].name

    computer_builder = ComputerBuilder(**kwargs)
    try:
        computer = computer_builder.new()
    except (ComputerBuilder.ComputerValidationError, ValidationError) as e:
        echo.echo_critical('{}: {}'.format(type(e).__name__, e))

    try:
        computer.store()
    except ValidationError as err:
        echo.echo_critical('unable to store the computer: {}. Exiting...'.format(err))
    else:
        echo.echo_success('Computer<{}> {} created'.format(computer.pk, computer.name))

    echo.echo_info('Note: before the computer can be used, it has to be configured with the command:')
    echo.echo_info('  verdi computer configure {} {}'.format(computer.get_transport_type(), computer.name))


@verdi_computer.command('duplicate')
@arguments.COMPUTER(callback=set_computer_builder)
@options_computer.LABEL(contextual_default=partial(get_parameter_default, 'label'))
@options_computer.HOSTNAME(contextual_default=partial(get_parameter_default, 'hostname'))
@options_computer.DESCRIPTION(contextual_default=partial(get_parameter_default, 'description'))
@options_computer.ENABLED(contextual_default=partial(get_parameter_default, 'enabled'))
@options_computer.TRANSPORT(contextual_default=partial(get_parameter_default, 'transport'))
@options_computer.SCHEDULER(contextual_default=partial(get_parameter_default, 'scheduler'))
@options_computer.SHEBANG(contextual_default=partial(get_parameter_default, 'shebang'))
@options_computer.WORKDIR(contextual_default=partial(get_parameter_default, 'work_dir'))
@options_computer.MPI_RUN_COMMAND(contextual_default=partial(get_parameter_default, 'mpirun_command'))
@options_computer.MPI_PROCS_PER_MACHINE(contextual_default=partial(get_parameter_default, 'mpiprocs_per_machine'))
@options.PREPEND_TEXT()
@options.APPEND_TEXT()
@options.NON_INTERACTIVE()
@click.pass_context
@with_dbenv()
def computer_duplicate(ctx, computer, non_interactive, **kwargs):
    """Duplicate a Computer."""
    from aiida.orm.backends import construct_backend

    if kwargs['label'] in get_computer_names():
        echo.echo_critical('A computer called {} already exists'.format(kwargs['label']))

    if not non_interactive:
        try:
            pre, post = ensure_scripts(kwargs.pop('prepend_text', ''), kwargs.pop('append_text', ''), kwargs)
        except InputValidationError as exception:
            raise click.BadParameter('invalid prepend and or append text: {}'.format(exception))

        kwargs['prepend_text'] = pre
        kwargs['append_text'] = post

    kwargs['transport'] = kwargs['transport'].name
    kwargs['scheduler'] = kwargs['scheduler'].name

    computer_builder = ctx.computer_builder
    for key, value in kwargs.items():
        if value is not None:
            setattr(computer_builder, key, value)

    try:
        computer = computer_builder.new()
    except (ComputerBuilder.ComputerValidationError, ValidationError) as e:
        echo.echo_critical('{}: {}'.format(type(e).__name__, e))
    else:
        echo.echo_success('stored computer {}<{}>'.format(computer.name, computer.pk))

    try:
        computer.store()
    except ValidationError as err:
        echo.echo_critical('unable to store the computer: {}. Exiting...'.format(err))
    else:
        echo.echo_success('Computer<{}> {} created'.format(computer.pk, computer.name))

    backend = construct_backend()
    is_configured = computer.is_user_configured(backend.users.get_default())

    if not is_configured:
        echo.echo_info('Note: before the computer can be used, it has to be configured with the command:')
        echo.echo_info('  verdi computer configure {} {}'.format(computer.get_transport_type(), computer.name))


@verdi_computer.command('enable')
@options.USER(required=False, help='Enable only for this user instead of globally.')
@arguments.COMPUTER()
@with_dbenv()
def computer_enable(user, computer):
    """Enable a computer."""
    from aiida.common.exceptions import NotExistent

    if user is None:
        if computer.is_enabled():
            echo.echo_info("Computer '{}' already enabled.".format(computer.name))
        else:
            computer.set_enabled_state(True)
            echo.echo_info("Computer '{}' enabled.".format(computer.name))
    else:
        try:
            authinfo = computer.get_authinfo(user)
        except NotExistent:
            echo.echo_critical("User with email '{}' is not configured for computer '{}' yet.".format(
                user.email, computer.name))

        if not authinfo.enabled:
            authinfo.enabled = True
            echo.echo_info("Computer '{}' enabled for user {}.".format(computer.name, user.get_full_name()))
        else:
            echo.echo_info("Computer '{}' was already enabled for user {} {}.".format(
                computer.name, user.first_name, user.last_name))


@verdi_computer.command('disable')
@options.USER(required=False, help='Disable only for this user instead of globally.')
@arguments.COMPUTER()
@with_dbenv()
def computer_disable(user, computer):
    """Disable a computer. Useful, for instance, when a computer is under maintenance."""
    from aiida.common.exceptions import NotExistent

    if user is None:
        if not computer.is_enabled():
            echo.echo_info("Computer '{}' already disabled.".format(computer.name))
        else:
            computer.set_enabled_state(False)
            echo.echo_info("Computer '{}' disabled.".format(computer.name))
    else:
        try:
            authinfo = computer.get_authinfo(user)
        except NotExistent:
            echo.echo_critical("User with email '{}' is not configured for computer '{}' yet.".format(
                user.email, computer.name))

        if authinfo.enabled:
            authinfo.enabled = False
            echo.echo_info("Computer '{}' disabled for user {}.".format(computer.name, user.get_full_name()))
        else:
            echo.echo_info("Computer '{}' was already disabled for user {} {}.".format(
                computer.name, user.first_name, user.last_name))


@verdi_computer.command('list')
@options.ALL(help='Show also disabled or unconfigured computers.')
@options.RAW(help='Show only the computer names, one per line.')
@with_dbenv()
def computer_list(all_entries, raw):
    """List available computers."""
    from aiida.orm.backends import construct_backend

    backend = construct_backend()

    computer_names = get_computer_names()

    if not raw:
        echo.echo_info("List of configured computers:")
        echo.echo_info("(use 'verdi computer show COMPUTERNAME' to see the details)")
    if computer_names:
        for name in sorted(computer_names):
            computer = backend.computers.get(name=name)

            is_configured = computer.is_user_configured(backend.users.get_default())
            is_user_enabled = computer.is_user_enabled(backend.users.get_default())

            if not all_entries:
                if not is_configured or not is_user_enabled or not computer.is_enabled():
                    continue

            if computer.is_enabled():
                if is_configured:
                    configured_str = ''
                    if is_user_enabled:
                        symbol = '*'
                        color = 'green'
                        enabled_str = ''
                    else:
                        symbol = 'x'
                        color = 'red'
                        enabled_str = '[DISABLED for this user]'
                else:
                    symbol = 'x'
                    color = 'reset'
                    enabled_str = ''
                    configured_str = ' [unconfigured]'
            else:  # GLOBALLY DISABLED
                symbol = 'x'
                color = 'red'
                if is_configured and not is_user_enabled:
                    enabled_str = ' [DISABLED globally AND for this user]'
                else:
                    enabled_str = ' [DISABLED globally]'
                if is_configured:
                    configured_str = ''
                else:
                    configured_str = ' [unconfigured]'

            if raw:
                echo.echo(click.style('{}'.format(name), fg=color))
            else:
                echo.echo(click.style('{} '.format(symbol), fg=color), nl=False)
                echo.echo(click.style('{} '.format(name), bold=True, fg=color), nl=False)
                echo.echo(click.style('{}{}'.format(enabled_str, configured_str), fg=color))

    else:
        echo.echo_info("No computers configured yet. Use 'verdi computer setup'")


@verdi_computer.command('show')
@arguments.COMPUTER()
@with_dbenv()
def computer_show(computer):
    """
    Show information on a given computer
    """
    return echo.echo(computer.full_text_info)


@verdi_computer.command('rename')
@arguments.COMPUTER()
@arguments.LABEL('NEW_NAME')
@with_dbenv()
def computer_rename(computer, new_name):
    """
    Rename a computer
    """
    from aiida.common.exceptions import UniquenessError

    old_name = computer.get_name()

    if old_name == new_name:
        echo.echo_critical("The old and new names are the same.")

    try:
        computer.set_name(new_name)
        computer.store()
    except ValidationError as error:
        echo.echo_critical("Invalid input! {}".format(error))
    except UniquenessError as error:
        echo.echo_critical("Uniqueness error encountered! Probably a "
                           "computer with name '{}' already exists"
                           "".format(new_name))
        echo.echo_critical("(Message was: {})".format(error))

    echo.echo_success("Computer '{}' renamed to '{}'".format(old_name, new_name))


@verdi_computer.command('test')
@options.USER(
    required=False,
    help="Test the connection for a given AiiDA user, specified by"
    "their email address. If not specified, uses the current default user.",
)
@click.option(
    '-t',
    '--print-traceback',
    is_flag=True,
    help="Print the full traceback in case an exception is raised",
)
@arguments.COMPUTER()
@with_dbenv()
def computer_test(user, print_traceback, computer):
    """
    Test the connection to a computer.

    It tries to connect, to get the list of calculations on the queue and
    to perform other tests.
    """
    import traceback
    from aiida.common.exceptions import NotExistent
    from aiida.orm.backends import construct_backend

    backend = construct_backend()

    # Set a user automatically if one is not specified in the command line
    if user is None:
        user = backend.users.get_default()

    echo.echo("Testing computer '{}' for user {}...".format(computer.get_name(), user.email))
    try:
        authinfo = computer.get_authinfo(user)
    except NotExistent:
        echo.echo_critical("User with email '{}' is not yet configured "
                           "for computer '{}' yet.".format(user.email, computer.get_name()))

    warning_string = None
    if not authinfo.enabled:
        warning_string = ("** NOTE! Computer is disabled for the "
                          "specified user!\n   Do you really want to test it? [y/N] ")
    if not computer.is_enabled():
        warning_string = ("** NOTE! Computer is disabled!\n" "   Do you really want to test it? [y/N] ")
    if warning_string:
        if not click.confirm(warning_string):
            sys.exit(0)

    sched = authinfo.computer.get_scheduler()
    trans = authinfo.get_transport()

    ## STARTING TESTS HERE
    num_failures = 0
    num_tests = 0

    try:
        echo.echo("> Testing connection...")
        with trans:
            sched.set_transport(trans)
            num_tests += 1
            for test in [_computer_test_get_jobs, _computer_create_temp_file]:
                num_tests += 1
                try:
                    succeeded = test(transport=trans, scheduler=sched, authinfo=authinfo)
                # pylint:disable=broad-except
                except Exception as error:
                    echo.echo_error("* The test raised an exception!")
                    if print_traceback:
                        echo.echo("** Full traceback:")
                        # Indent
                        echo.echo("\n".join(["   {}".format(l) for l in traceback.format_exc().splitlines()]))
                    else:
                        echo.echo("** {}: {}".format(error.__class__.__name__, error))
                        echo.echo("** (use the --print-traceback option to see the " "full traceback)")
                    succeeded = False

                if not succeeded:
                    num_failures += 1

        if num_failures:
            echo.echo("Some tests failed! ({} out of {} failed)".format(num_failures, num_tests))
        else:
            echo.echo("Test completed (all {} tests succeeded)".format(num_tests))
    # pylint:disable=broad-except
    except Exception as error:
        echo.echo_error("** Error while trying to connect to the computer! Cannot "
                        "   perform following tests, stopping.")
        if print_traceback:
            echo.echo("** Full traceback:")
            # Indent
            echo.echo("\n".join(["   {}".format(l) for l in traceback.format_exc().splitlines()]))
        else:
            echo.echo("{}: {}".format(error.__class__.__name__, error))
            echo.echo("(use the --print-traceback option to see the " "full traceback)")
        succeeded = False


@verdi_computer.command('delete')
@arguments.COMPUTER()
@with_dbenv()
def computer_delete(computer):
    """
    Configure the authentication information for a given computer

    Does not delete the computer if there are calculations that are using
    it.
    """
    from aiida.common.exceptions import InvalidOperation
    from aiida.orm.backends import construct_backend

    backend = construct_backend()

    compname = computer.name

    try:
        backend.computers.delete(computer.id)
    except InvalidOperation as error:
        echo.echo_critical(str(error))

    echo.echo_success("Computer '{}' deleted.".format(compname))


@verdi_computer.group('configure')
def computer_configure():
    """Configure a computer with one of the available transport types."""
    pass


@computer_configure.command('show')
@click.option(
    '--defaults', is_flag=True, default=False, help='Show the default configuration settings for this computer.')
@click.option('--as-option-string', is_flag=True)
@options.USER()
@arguments.COMPUTER()
def computer_config_show(computer, user, defaults, as_option_string):
    """Show the current or default configuration for COMPUTER."""
    import tabulate
    from aiida.common.utils import escape_for_bash

    transport_cls = computer.get_transport_class()
    option_list = [
        param for param in transport_cli.create_configure_cmd(computer.get_transport_type()).params
        if isinstance(param, click.core.Option)
    ]
    option_list = [option for option in option_list if option.name in transport_cls.get_valid_auth_params()]

    if defaults:
        config = {option.name: transport_cli.transport_option_default(option.name, computer) for option in option_list}
    else:
        config = computer.get_configuration(user)

    option_items = []
    if as_option_string:
        for option in option_list:
            t_opt = transport_cls.auth_options[option.name]
            if config.get(option.name) or config.get(option.name) is False:
                if t_opt.get('switch'):
                    option_value = option.opts[-1] if config.get(option.name) else '--no-{}'.format(
                        option.name.replace('_', '-'))
                elif t_opt.get('is_flag'):
                    is_default = config.get(option.name) == transport_cli.transport_option_default(
                        option.name, computer)
                    option_value = option.opts[-1] if is_default else ''
                else:
                    option_value = '{}={}'.format(option.opts[-1], config[option.name])
                option_items.append(option_value)
        opt_string = ' '.join(option_items)
        echo.echo(escape_for_bash(opt_string))
    else:
        table = []
        for name in transport_cls.get_valid_auth_params():
            if name in config:
                table.append(('* ' + name, config[name]))
            else:
                table.append(('* ' + name, '-'))
        echo.echo(tabulate.tabulate(table, tablefmt='plain'))


for ep in get_entry_points('aiida.transports'):
    computer_configure.add_command(transport_cli.create_configure_cmd(ep.name))
