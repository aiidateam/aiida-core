# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-many-statements,too-many-branches
"""`verdi computer` command."""
from functools import partial

import click
import tabulate

from aiida.cmdline.commands.cmd_verdi import VerdiCommandGroup, verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.params.options.commands import computer as options_computer
from aiida.cmdline.utils import echo
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.exceptions import EntryPointError, ValidationError
from aiida.plugins.entry_point import get_entry_point_names


@verdi.group('computer')
def verdi_computer():
    """Setup and manage computers."""


def get_computer_names():
    """
    Retrieve the list of computers in the DB.
    """
    from aiida.orm.querybuilder import QueryBuilder
    builder = QueryBuilder()
    builder.append(entity_type='computer', project=['label'])
    if builder.count() > 0:
        return next(zip(*builder.all()))  # return the first entry

    return []


def prompt_for_computer_configuration(computer):  # pylint: disable=unused-argument
    pass


def _computer_test_get_jobs(transport, scheduler, authinfo):  # pylint: disable=unused-argument
    """Internal test to check if it is possible to check the queue state.

    :param transport: an open transport
    :param scheduler: the corresponding scheduler class
    :param authinfo: the AuthInfo object (from which one can get computer and aiidauser)
    :return: tuple of boolean indicating success or failure and an optional string message
    """
    found_jobs = scheduler.get_jobs(as_dict=True)
    return True, f'{len(found_jobs)} jobs found in the queue'


def _computer_test_no_unexpected_output(transport, scheduler, authinfo):  # pylint: disable=unused-argument
    """Test that there is no unexpected output from the connection.

    This can happen if e.g. there is some spurious command in the
    .bashrc or .bash_profile that is not guarded in case of non-interactive
    shells.

    :param transport: an open transport
    :param scheduler: the corresponding scheduler class
    :param authinfo: the AuthInfo object (from which one can get computer and aiidauser)
    :return: tuple of boolean indicating success or failure and an optional string message
    """
    # Execute a command that should not return any error
    retval, stdout, stderr = transport.exec_command_wait('echo -n')
    if retval != 0:
        return False, f'The command `echo -n` returned a non-zero return code ({retval})'

    template = """
We detected some spurious output in the {} when connecting to the computer, as shown between the bars
=====================================================================================================
{}
=====================================================================================================
Please check that you don't have code producing output in your ~/.bash_profile, ~/.bashrc or similar.
If you don't want to remove the code, but just to disable it for non-interactive shells, see comments
in this troubleshooting section of the online documentation: https://bit.ly/2FCRDc5
"""
    if stdout:
        return False, template.format('stdout', stdout)

    if stderr:
        return False, template.format('stderr', stderr)

    return True, None


def _computer_get_remote_username(transport, scheduler, authinfo):  # pylint: disable=unused-argument
    """Internal test to check if it is possible to determine the username on the remote.

    :param transport: an open transport
    :param scheduler: the corresponding scheduler class
    :param authinfo: the AuthInfo object
    :return: tuple of boolean indicating success or failure and an optional string message
    """
    remote_user = transport.whoami()
    return True, remote_user


def _computer_create_temp_file(transport, scheduler, authinfo):  # pylint: disable=unused-argument
    """
    Internal test to check if it is possible to create a temporary file
    and then delete it in the work directory

    :note: exceptions could be raised

    :param transport: an open transport
    :param scheduler: the corresponding scheduler class
    :param authinfo: the AuthInfo object (from which one can get computer and aiidauser)
    :return: tuple of boolean indicating success or failure and an optional string message
    """
    import datetime
    import os
    import tempfile

    file_content = f"Test from 'verdi computer test' on {datetime.datetime.now().isoformat()}"
    workdir = authinfo.get_workdir().format(username=transport.whoami())

    try:
        transport.chdir(workdir)
    except IOError:
        transport.makedirs(workdir)
        transport.chdir(workdir)

    with tempfile.NamedTemporaryFile(mode='w+') as tempf:
        fname = os.path.split(tempf.name)[1]
        remote_file_path = os.path.join(workdir, fname)
        tempf.write(file_content)
        tempf.flush()
        transport.putfile(tempf.name, remote_file_path)

    if not transport.path_exists(remote_file_path):
        return False, f'failed to create the file `{remote_file_path}` on the remote'

    handle, destfile = tempfile.mkstemp()
    os.close(handle)

    try:
        transport.getfile(remote_file_path, destfile)
        with open(destfile, encoding='utf8') as dfile:
            read_string = dfile.read()

        if read_string != file_content:
            message = 'retrieved file content is different from what was expected'
            message += f'\n  Expected: {file_content}'
            message += f'\n  Retrieved: {read_string}'
            return False, message

    finally:
        os.remove(destfile)

    transport.remove(remote_file_path)

    return True, None


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
    from aiida.orm.utils.builders.computer import ComputerBuilder
    ctx.computer_builder = ComputerBuilder.from_computer(value)
    return value


@verdi_computer.command('setup')
@options_computer.LABEL()
@options_computer.HOSTNAME()
@options_computer.DESCRIPTION()
@options_computer.TRANSPORT()
@options_computer.SCHEDULER()
@options_computer.SHEBANG()
@options_computer.WORKDIR()
@options_computer.MPI_RUN_COMMAND()
@options_computer.MPI_PROCS_PER_MACHINE()
@options_computer.DEFAULT_MEMORY_PER_MACHINE()
@options_computer.USE_DOUBLE_QUOTES()
@options_computer.PREPEND_TEXT()
@options_computer.APPEND_TEXT()
@options.NON_INTERACTIVE()
@options.CONFIG_FILE()
@click.pass_context
@with_dbenv()
def computer_setup(ctx, non_interactive, **kwargs):
    """Create a new computer."""
    from aiida.orm.utils.builders.computer import ComputerBuilder

    if kwargs['label'] in get_computer_names():
        echo.echo_critical(
            'A computer called {c} already exists. '
            'Use "verdi computer duplicate {c}" to set up a new '
            'computer starting from the settings of {c}.'.format(c=kwargs['label'])
        )

    kwargs['transport'] = kwargs['transport'].name
    kwargs['scheduler'] = kwargs['scheduler'].name

    computer_builder = ComputerBuilder(**kwargs)
    try:
        computer = computer_builder.new()
    except (ComputerBuilder.ComputerValidationError, ValidationError) as e:
        echo.echo_critical(f'{type(e).__name__}: {e}')

    try:
        computer.store()
    except ValidationError as err:
        echo.echo_critical(f'unable to store the computer: {err}. Exiting...')
    else:
        echo.echo_success(f'Computer<{computer.pk}> {computer.label} created')

    echo.echo_report('Note: before the computer can be used, it has to be configured with the command:')

    profile = ctx.obj['profile']
    echo.echo_report(f'  verdi -p {profile.name} computer configure {computer.transport_type} {computer.label}')


@verdi_computer.command('duplicate')
@arguments.COMPUTER(callback=set_computer_builder)
@options_computer.LABEL(contextual_default=partial(get_parameter_default, 'label'))
@options_computer.HOSTNAME(contextual_default=partial(get_parameter_default, 'hostname'))
@options_computer.DESCRIPTION(contextual_default=partial(get_parameter_default, 'description'))
@options_computer.TRANSPORT(contextual_default=partial(get_parameter_default, 'transport'))
@options_computer.SCHEDULER(contextual_default=partial(get_parameter_default, 'scheduler'))
@options_computer.SHEBANG(contextual_default=partial(get_parameter_default, 'shebang'))
@options_computer.WORKDIR(contextual_default=partial(get_parameter_default, 'work_dir'))
@options_computer.MPI_RUN_COMMAND(contextual_default=partial(get_parameter_default, 'mpirun_command'))
@options_computer.MPI_PROCS_PER_MACHINE(contextual_default=partial(get_parameter_default, 'mpiprocs_per_machine'))
@options_computer.DEFAULT_MEMORY_PER_MACHINE(
    contextual_default=partial(get_parameter_default, 'default_memory_per_machine')
)
@options_computer.PREPEND_TEXT(contextual_default=partial(get_parameter_default, 'prepend_text'))
@options_computer.APPEND_TEXT(contextual_default=partial(get_parameter_default, 'append_text'))
@options.NON_INTERACTIVE()
@click.pass_context
@with_dbenv()
def computer_duplicate(ctx, computer, non_interactive, **kwargs):
    """Duplicate a computer allowing to change some parameters."""
    from aiida.orm.utils.builders.computer import ComputerBuilder

    if kwargs['label'] in get_computer_names():
        echo.echo_critical(f"A computer called {kwargs['label']} already exists")

    kwargs['transport'] = kwargs['transport'].name
    kwargs['scheduler'] = kwargs['scheduler'].name

    computer_builder = ctx.computer_builder
    for key, value in kwargs.items():
        if value is not None:
            setattr(computer_builder, key, value)

    try:
        computer = computer_builder.new()
    except (ComputerBuilder.ComputerValidationError, ValidationError) as e:
        echo.echo_critical(f'{type(e).__name__}: {e}')
    else:
        echo.echo_success(f'stored computer {computer.label}<{computer.pk}>')

    try:
        computer.store()
    except ValidationError as err:
        echo.echo_critical(f'unable to store the computer: {err}. Exiting...')
    else:
        echo.echo_success(f'Computer<{computer.pk}> {computer.label} created')

    if not computer.is_configured:
        echo.echo_report('Note: before the computer can be used, it has to be configured with the command:')

        profile = ctx.obj['profile']
        echo.echo_report(f'  verdi -p {profile.name} computer configure {computer.transport_type} {computer.label}')


@verdi_computer.command('enable')
@arguments.COMPUTER()
@arguments.USER()
@with_dbenv()
def computer_enable(computer, user):
    """Enable the computer for the given user."""
    from aiida.common.exceptions import NotExistent

    try:
        authinfo = computer.get_authinfo(user)
    except NotExistent:
        echo.echo_critical(f"User with email '{user.email}' is not configured for computer '{computer.label}' yet.")

    if not authinfo.enabled:
        authinfo.enabled = True
        echo.echo_report(f"Computer '{computer.label}' enabled for user {user.get_full_name()}.")
    else:
        echo.echo_report(
            f"Computer '{computer.label}' was already enabled for user {user.first_name} {user.last_name}."
        )


@verdi_computer.command('disable')
@arguments.COMPUTER()
@arguments.USER()
@with_dbenv()
def computer_disable(computer, user):
    """Disable the computer for the given user.

    Thi can be useful, for example, when a computer is under maintenance."""
    from aiida.common.exceptions import NotExistent

    try:
        authinfo = computer.get_authinfo(user)
    except NotExistent:
        echo.echo_critical(f"User with email '{user.email}' is not configured for computer '{computer.label}' yet.")

    if authinfo.enabled:
        authinfo.enabled = False
        echo.echo_report(f"Computer '{computer.label}' disabled for user {user.get_full_name()}.")
    else:
        echo.echo_report(
            f"Computer '{computer.label}' was already disabled for user {user.first_name} {user.last_name}."
        )


@verdi_computer.command('list')
@options.ALL(help='Show also disabled or unconfigured computers.')
@options.RAW(help='Show only the computer labels, one per line.')
@with_dbenv()
def computer_list(all_entries, raw):
    """List all available computers."""
    from aiida.orm import Computer, User

    if not raw:
        echo.echo_report('List of configured computers')
        echo.echo_report("Use 'verdi computer show COMPUTERLABEL' to display more detailed information")

    computers = Computer.collection.all()
    user = User.collection.get_default()

    if not computers:
        echo.echo_report("No computers configured yet. Use 'verdi computer setup'")

    sort = lambda computer: computer.label
    highlight = lambda comp: comp.is_configured and comp.is_user_enabled(user)
    hide = lambda comp: not (comp.is_configured and comp.is_user_enabled(user)) and not all_entries
    echo.echo_formatted_list(computers, ['label'], sort=sort, highlight=highlight, hide=hide)


@verdi_computer.command('show')
@arguments.COMPUTER()
@with_dbenv()
def computer_show(computer):
    """Show detailed information for a computer."""
    table = [
        ['Label', computer.label],
        ['PK', computer.pk],
        ['UUID', computer.uuid],
        ['Description', computer.description],
        ['Hostname', computer.hostname],
        ['Transport type', computer.transport_type],
        ['Scheduler type', computer.scheduler_type],
        ['Work directory', computer.get_workdir()],
        ['Shebang', computer.get_shebang()],
        ['Mpirun command', ' '.join(computer.get_mpirun_command())],
        ['Default #procs/machine', computer.get_default_mpiprocs_per_machine()],
        ['Default memory (kB)/machine', computer.get_default_memory_per_machine()],
        ['Prepend text', computer.get_prepend_text()],
        ['Append text', computer.get_append_text()],
    ]
    echo.echo(tabulate.tabulate(table))


@verdi_computer.command('relabel')
@arguments.COMPUTER()
@arguments.LABEL('LABEL')
@with_dbenv()
def computer_relabel(computer, label):
    """Relabel a computer."""
    from aiida.common.exceptions import UniquenessError

    old_label = computer.label

    if old_label == label:
        echo.echo_critical('The old and new labels are the same.')

    try:
        computer.label = label
        computer.store()
    except ValidationError as error:
        echo.echo_critical(f'Invalid input! {error}')
    except UniquenessError as error:
        echo.echo_critical(
            f"Uniqueness error encountered! Probably a computer with label '{label}' already exists: {error}"
        )

    echo.echo_success(f"Computer '{old_label}' relabeled to '{label}'")


@verdi_computer.command('test')
@options.USER(
    required=False,
    help='Test the connection for a given AiiDA user, specified by'
    'their email address. If not specified, uses the current default user.',
)
@options.PRINT_TRACEBACK()
@arguments.COMPUTER()
@with_dbenv()
def computer_test(user, print_traceback, computer):
    """
    Test the connection to a computer.

    It tries to connect, to get the list of calculations on the queue and
    to perform other tests.
    """
    import traceback

    from aiida import orm
    from aiida.common.exceptions import NotExistent

    # Set a user automatically if one is not specified in the command line
    if user is None:
        user = orm.User.collection.get_default()

    echo.echo_report(f'Testing computer<{computer.label}> for user<{user.email}>...')

    try:
        authinfo = computer.get_authinfo(user)
    except NotExistent:
        echo.echo_critical(f'Computer<{computer.label}> is not yet configured for user<{user.email}>')

    if not authinfo.enabled:
        echo.echo_warning(f'Computer<{computer.label}> is disabled for user<{user.email}>')
        click.confirm('Do you really want to test it?', abort=True)

    scheduler = authinfo.computer.get_scheduler()
    transport = authinfo.get_transport()

    # STARTING TESTS HERE
    num_failures = 0
    num_tests = 0

    tests = {
        _computer_test_no_unexpected_output: 'Checking for spurious output',
        _computer_test_get_jobs: 'Getting number of jobs from scheduler',
        _computer_get_remote_username: 'Determining remote user name',
        _computer_create_temp_file: 'Creating and deleting temporary file'
    }

    try:
        echo.echo('* Opening connection... ', nl=False)

        with transport:
            num_tests += 1

            echo.echo('[OK]', fg=echo.COLORS['success'])

            scheduler.set_transport(transport)

            for test, test_label in tests.items():

                echo.echo(f'* {test_label}... ', nl=False)
                num_tests += 1
                try:
                    success, message = test(transport=transport, scheduler=scheduler, authinfo=authinfo)
                except Exception as exception:  # pylint:disable=broad-except
                    success = False
                    message = f'{exception.__class__.__name__}: {str(exception)}'

                    if print_traceback:
                        message += '\n  Full traceback:\n'
                        message += '\n'.join([f'  {l}' for l in traceback.format_exc().splitlines()])
                    else:
                        message += '\n  Use the `--print-traceback` option to see the full traceback.'

                if not success:
                    num_failures += 1
                    if message:
                        echo.echo('[Failed]: ', fg=echo.COLORS['error'], nl=False)
                        echo.echo(message)
                    else:
                        echo.echo('[Failed]', fg=echo.COLORS['error'])
                else:
                    if message:
                        echo.echo('[OK]: ', fg=echo.COLORS['success'], nl=False)
                        echo.echo(message)
                    else:
                        echo.echo('[OK]', fg=echo.COLORS['success'])

        if num_failures:
            echo.echo_warning(f'{num_failures} out of {num_tests} tests failed')
        else:
            echo.echo_success(f'all {num_tests} tests succeeded')

    except Exception:  # pylint:disable=broad-except
        echo.echo('[FAILED]: ', fg=echo.COLORS['error'], nl=False)
        message = 'Error while trying to connect to the computer'

        if print_traceback:
            message += '\n  Full traceback:\n'
            message += '\n'.join([f'  {l}' for l in traceback.format_exc().splitlines()])
        else:
            message += '\n  Use the `--print-traceback` option to see the full traceback.'

        echo.echo(message)
        echo.echo_warning(f'{1} out of {num_tests} tests failed')


@verdi_computer.command('delete')
@arguments.COMPUTER()
@with_dbenv()
def computer_delete(computer):
    """
    Delete a computer.

    Note that it is not possible to delete the computer if there are calculations that are using it.
    """
    from aiida import orm
    from aiida.common.exceptions import InvalidOperation

    label = computer.label

    try:
        orm.Computer.collection.delete(computer.pk)
    except InvalidOperation as error:
        echo.echo_critical(str(error))

    echo.echo_success(f"Computer '{label}' deleted.")


class LazyConfigureGroup(VerdiCommandGroup):
    """A click group that will lazily load the subcommands for each transport plugin."""

    def list_commands(self, ctx):
        subcommands = super().list_commands(ctx)
        subcommands.extend(get_entry_point_names('aiida.transports'))
        return subcommands

    def get_command(self, ctx, name):  # pylint: disable=arguments-renamed
        from aiida.transports import cli as transport_cli
        try:
            command = transport_cli.create_configure_cmd(name)
        except EntryPointError:
            command = super().get_command(ctx, name)
        return command


@verdi_computer.group('configure', cls=LazyConfigureGroup)
def computer_configure():
    """Configure the Authinfo details for a computer (and user)."""


@computer_configure.command('show')
@click.option(
    '--defaults', is_flag=True, default=False, help='Show the default configuration settings for this computer.'
)
@click.option('--as-option-string', is_flag=True)
@options.USER(
    help='Email address of the AiiDA user for whom to configure this computer (if different from default user).'
)
@arguments.COMPUTER()
def computer_config_show(computer, user, defaults, as_option_string):
    """Show the current configuration for a computer."""
    from aiida.common.escaping import escape_for_bash
    from aiida.transports import cli as transport_cli

    transport_cls = computer.get_transport_class()
    option_list = [
        param for param in transport_cli.create_configure_cmd(computer.transport_type).params
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
                    option_value = option.opts[-1] if config.get(
                        option.name
                    ) else f"--no-{option.name.replace('_', '-')}"
                elif t_opt.get('is_flag'):
                    is_default = config.get(option.name
                                            ) == transport_cli.transport_option_default(option.name, computer)
                    option_value = option.opts[-1] if is_default else ''
                else:
                    option_value = f'{option.opts[-1]}={option.type(config[option.name])}'
                option_items.append(option_value)
        opt_string = ' '.join(option_items)
        echo.echo(escape_for_bash(opt_string))
    else:
        table = []
        for name in transport_cls.get_valid_auth_params():
            if name in config:
                table.append((f'* {name}', config[name]))
            else:
                table.append((f'* {name}', '-'))
        echo.echo(tabulate.tabulate(table, tablefmt='plain'))
