###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi computer` command."""

import pathlib
import traceback
from copy import deepcopy
from functools import partial
from math import isclose

import click

from aiida.cmdline import VerdiCommandGroup
from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.params.options.commands import computer as options_computer
from aiida.cmdline.utils import echo, echo_tabulate
from aiida.cmdline.utils.common import validate_output_filename
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.exceptions import EntryPointError, ValidationError
from aiida.plugins.entry_point import get_entry_point_names


@verdi.group('computer')
def verdi_computer():
    """Setup and manage computers."""


def get_computer_names():
    """Retrieve the list of computers in the DB."""
    from aiida.orm.querybuilder import QueryBuilder

    builder = QueryBuilder()
    builder.append(entity_type='computer', project=['label'])
    if builder.count() > 0:
        return next(zip(*builder.all()))  # return the first entry

    return []


def prompt_for_computer_configuration(computer):
    pass


def _computer_test_get_jobs(transport, scheduler, authinfo, computer):
    """Internal test to check if it is possible to check the queue state.

    :param transport: an open transport
    :param scheduler: the corresponding scheduler class
    :param authinfo: the AuthInfo object (from which one can get computer and aiidauser)
    :return: tuple of boolean indicating success or failure and an optional string message
    """
    found_jobs = scheduler.get_jobs(as_dict=True)
    return True, f'{len(found_jobs)} jobs found in the queue'


def _computer_test_no_unexpected_output(transport, scheduler, authinfo, computer):
    """Test that there is no unexpected output from the connection.

    This can happen if e.g. there is some spurious command in the
    .bashrc or .bash_profile that is not guarded in case of non-interactive
    shells.
    Note: This test is irrelevant if the transport plugin does not support command execution.

    :param transport: an open transport
    :param scheduler: the corresponding scheduler class
    :param authinfo: the AuthInfo object (from which one can get computer and aiidauser)
    :return: tuple of boolean indicating success or failure and an optional string message
    """
    # Execute a command that should not return any error, except ``NotImplementedError``
    # since not all transport plugins implement remote command execution.
    try:
        retval, stdout, stderr = transport.exec_command_wait('echo -n')
    except NotImplementedError:
        return (
            True,
            f'Skipped, remote command execution is not implemented for the '
            f'`{computer.transport_type}` transport plugin',
        )

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


def _computer_get_remote_username(transport, scheduler, authinfo, computer):
    """Internal test to check if it is possible to determine the username on the remote.

    :param transport: an open transport
    :param scheduler: the corresponding scheduler class
    :param authinfo: the AuthInfo object
    :return: tuple of boolean indicating success or failure and an optional string message
    """
    remote_user = transport.whoami()
    return True, remote_user


def _computer_create_temp_file(transport, scheduler, authinfo, computer):
    """Internal test to check if it is possible to create a temporary file
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

    transport.makedirs(workdir, ignore_existing=True)

    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tempf:
        fname = os.path.split(tempf.name)[1]
        remote_file_path = os.path.join(workdir, fname)
        tempf.write(file_content)
        tempf.flush()
        tempf.close()
        transport.putfile(tempf.name, remote_file_path)
        os.remove(tempf.name)

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


def time_use_login_shell(authinfo, auth_params, use_login_shell: bool, iterations: int = 3) -> float:
    """Execute the ``whoami`` over the transport for the given ``use_login_shell`` and report the time taken.

    :param authinfo: The ``AuthInfo`` instance to use.
    :param auth_params: The base authentication parameters.
    :param use_login_shell: Whether to use a login shell or not.
    :param iterations: The number of iterations of the command to call. Command will return the average call time.
    :return: The average call time of the ``Transport.whoami`` command.
    """
    import time

    auth_params['use_login_shell'] = use_login_shell
    authinfo.set_auth_params(auth_params)

    timings = []

    for _ in range(iterations):
        time_start = time.time()
        with authinfo.get_transport() as transport:
            transport.whoami()
        timings.append(time.time() - time_start)

    return sum(timings) / iterations


def _computer_use_login_shell_performance(transport, scheduler, authinfo, computer):
    """Execute a command over the transport with and without the ``use_login_shell`` option enabled.

    By default, AiiDA uses a login shell when connecting to a computer in order to operate in the same environment as a
    user connecting to the computer. However, loading the login scripts of the shell can take time, which can
    significantly slow down all commands executed by AiiDA and impact the throughput of calculation jobs. This test
    executes a simple command both with and without using a login shell and emits a warning if the login shell is slower
    by at least 100 ms. If the computer is already configured to avoid using a login shell, the test is skipped and the
    function returns a successful test result.
    """
    rel_tol = 0.5  # Factor of two
    abs_tol = 0.1  # 100 ms
    iterations = 3

    auth_params = authinfo.get_auth_params()

    # If ``use_login_shell=False`` we don't need to test for it being slower.
    if not auth_params.get('use_login_shell', True):
        return True, None

    auth_params_clone = deepcopy(auth_params)

    try:
        timing_false = time_use_login_shell(authinfo, auth_params_clone, False, iterations)
        timing_true = time_use_login_shell(authinfo, auth_params_clone, True, iterations)
    finally:
        authinfo.set_auth_params(auth_params)

    echo.echo_debug(f'Execution time: {timing_true} vs {timing_false} for login shell and normal, respectively')

    if not isclose(timing_true, timing_false, rel_tol=rel_tol, abs_tol=abs_tol):
        return True, (
            f"\n\n{click.style('Warning:', fg='yellow', bold=True)} "
            'The computer is configured to use a login shell, which is slower compared to a normal shell.\n'
            f'Command execution time of {timing_true:.3f} versus {timing_false:.3f} seconds, respectively).\n'
            'Unless this setting is really necessary, consider disabling it with:\n'
            f'\n    verdi computer configure {computer.transport_type} {computer.label} -n --no-use-login-shell\n\n'
            'For details, please refer to the documentation: '
            'https://aiida.readthedocs.io/projects/aiida-core/en/latest/topics/transport.html#login-shells\n'
        )

    return True, None


def get_parameter_default(parameter, ctx):
    """Get the value for a specific parameter from the computer_builder or the default value of that option

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


@verdi_computer.command('setup-many')
@click.argument('config_files', nargs=-1, required=True, type=click.Path(exists=True, path_type=pathlib.Path))
@with_dbenv()
def computer_setup_many(config_files):
    """Create multiple computers from YAML configuration files."""
    import yaml

    from aiida.common.exceptions import IntegrityError
    from aiida.orm.utils.builders.computer import ComputerBuilder

    for config_path in config_files:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            computer_builder = ComputerBuilder(**config_data)
            computer = computer_builder.new()
            computer.store()

            echo.echo_success(f'Computer<{computer.pk}> {computer.label} created')
        except IntegrityError as e:
            if 'UNIQUE constraint failed: db_dbcomputer.label' in str(e):
                msg = (
                    f'Error processing {config_path}: Computer with label "{config_data.get("label", "unknown")}"'
                    'already exists'
                )
                echo.echo_error(msg)
            else:
                echo.echo_error(f'Error processing {config_path}: Database integrity error - {e}')
        except Exception as e:
            echo.echo_error(f'Error processing {config_path}: {e}')


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

    Thi can be useful, for example, when a computer is under maintenance.
    """
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

    sort = lambda computer: computer.label  # noqa: E731
    highlight = lambda comp: comp.is_configured and comp.is_user_enabled(user)  # noqa: E731
    hide = lambda comp: not (comp.is_configured and comp.is_user_enabled(user)) and not all_entries  # noqa: E731
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
    echo_tabulate(table)


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
    """Test the connection to a computer.

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
        _computer_create_temp_file: 'Creating and deleting temporary file',
        _computer_use_login_shell_performance: 'Checking for possible delay from using login shell',
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
                    success, message = test(
                        transport=transport, scheduler=scheduler, authinfo=authinfo, computer=computer
                    )
                except Exception as exception:
                    success = False
                    message = f'{exception.__class__.__name__}: {exception!s}'

                    if print_traceback:
                        message += '\n  Full traceback:\n'
                        message += '\n'.join([f'  {line}' for line in traceback.format_exc().splitlines()])
                    else:
                        message += '\n  Use the `--print-traceback` option to see the full traceback.'

                if not success:
                    num_failures += 1
                    if message:
                        echo.echo('[Failed]: ', fg=echo.COLORS['error'], nl=False)
                        echo.echo(message)
                    else:
                        echo.echo('[Failed]', fg=echo.COLORS['error'])
                elif message:
                    echo.echo('[OK]: ', fg=echo.COLORS['success'], nl=False)
                    echo.echo(message)
                else:
                    echo.echo('[OK]', fg=echo.COLORS['success'])

        if num_failures:
            echo.echo_warning(f'{num_failures} out of {num_tests} tests failed')
        else:
            echo.echo_success(f'all {num_tests} tests succeeded')

    except Exception:
        echo.echo('[FAILED]: ', fg=echo.COLORS['error'], nl=False)
        message = 'Error while trying to connect to the computer'

        if print_traceback:
            message += '\n  Full traceback:\n'
            message += '\n'.join([f'  {line}' for line in traceback.format_exc().splitlines()])
        else:
            message += '\n  Use the `--print-traceback` option to see the full traceback.'

        echo.echo(message)
        echo.echo_warning('1 out of 1 tests failed')


@verdi_computer.command('delete')
@options.DRY_RUN()
@arguments.COMPUTER()
@with_dbenv()
def computer_delete(computer, dry_run):
    """Delete a computer.

    Note: a computer can be deleted even if calculations are currently running on it. The calculation nodes will be
    deleted with the computer if confirmed but the calculations will not be automatically cancelled with the scheduler
    """
    from aiida import orm
    from aiida.common.exceptions import InvalidOperation
    from aiida.orm import Computer, Node
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.tools import delete_nodes

    label = computer.label

    # Sofar, we can only get this info with QueryBuilder
    builder = QueryBuilder()
    builder.append(Computer, filters={'label': label}, tag='computer')
    builder.append(Node, with_computer='computer', project=Node.fields.pk)  # type: ignore[arg-type]
    associated_nodes_pk = builder.all(flat=True)

    echo.echo_report(f'This computer has {len(associated_nodes_pk)} associated nodes')

    def _dry_run_callback(pks):
        if pks:
            echo.echo_report('The nodes with the following pks would be deleted: ' + ' '.join(map(str, pks)))
            echo.echo_warning(
                f'YOU ARE ABOUT TO DELETE {len(pks)} NODES AND COMPUTER {label!r}! THIS CANNOT BE UNDONE!'
            )

        confirm = click.confirm('Shall I continue?', default=False)
        if not confirm:
            raise click.Abort
        return not confirm

    if associated_nodes_pk:
        delete_nodes(associated_nodes_pk, dry_run=dry_run or _dry_run_callback)

    if dry_run:
        return

    # We delete the computer separately from the associated nodes, since the computer pk is in a different table
    try:
        orm.Computer.collection.delete(computer.pk)
    except InvalidOperation as error:
        echo.echo_critical(str(error))

    echo.echo_success(f'Computer `{label}` {"and all its associated nodes " if associated_nodes_pk else ""}deleted.')


class LazyConfigureGroup(VerdiCommandGroup):
    """A click group that will lazily load the subcommands for each transport plugin."""

    def list_commands(self, ctx):
        subcommands = super().list_commands(ctx)
        subcommands.extend(get_entry_point_names('aiida.transports'))
        return subcommands

    def get_command(self, ctx, name):
        from aiida.transports import cli as transport_cli

        try:
            command = transport_cli.create_configure_cmd(name)
        except EntryPointError:
            command = super().get_command(ctx, name)
        return command


@verdi_computer.group('configure', cls=LazyConfigureGroup)
def computer_configure():
    """Configure the transport for a computer and user."""


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
        param
        for param in transport_cli.create_configure_cmd(computer.transport_type).params
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
                    option_value = (
                        option.opts[-1] if config.get(option.name) else f"--no-{option.name.replace('_', '-')}"  # type: ignore[union-attr]
                    )
                elif t_opt.get('is_flag'):
                    is_default = config.get(option.name) == transport_cli.transport_option_default(
                        option.name, computer
                    )
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
        echo_tabulate(table, tablefmt='plain')


@verdi_computer.group('export')
def computer_export():
    """Export the setup or configuration of a computer."""


@computer_export.command('setup')
@arguments.COMPUTER()
@arguments.OUTPUT_FILE(type=click.Path(exists=False, path_type=pathlib.Path), required=False)
@options.OVERWRITE()
@options.SORT()
@with_dbenv()
def computer_export_setup(computer, output_file, overwrite, sort):
    """Export computer setup to a YAML file."""
    import yaml

    computer_setup = {
        'label': computer.label,
        'hostname': computer.hostname,
        'description': computer.description,
        'transport': computer.transport_type,
        'scheduler': computer.scheduler_type,
        'shebang': computer.get_shebang(),
        'work_dir': computer.get_workdir(),
        'mpirun_command': ' '.join(computer.get_mpirun_command()),
        'mpiprocs_per_machine': computer.get_default_mpiprocs_per_machine(),
        'default_memory_per_machine': computer.get_default_memory_per_machine(),
        'use_double_quotes': computer.get_use_double_quotes(),
        'prepend_text': computer.get_prepend_text(),
        'append_text': computer.get_append_text(),
    }

    if output_file is None:
        output_file = pathlib.Path(f'{computer.label}-setup.yaml')
    try:
        validate_output_filename(output_file=output_file, overwrite=overwrite)
    except (FileExistsError, IsADirectoryError) as exception:
        raise click.BadParameter(str(exception), param_hint='OUTPUT_FILE') from exception

    try:
        output_file.write_text(yaml.dump(computer_setup, sort_keys=sort), 'utf-8')
    except Exception as e:
        error_traceback = traceback.format_exc()
        echo.CMDLINE_LOGGER.debug(error_traceback)
        echo.echo_critical(
            f'Unexpected error while exporting setup for Computer<{computer.pk}> {computer.label}:\n ({e!s}).'
        )
    else:
        echo.echo_success(f"Computer<{computer.pk}> {computer.label} setup exported to file '{output_file}'.")


@computer_export.command('config')
@arguments.COMPUTER()
@arguments.OUTPUT_FILE(type=click.Path(exists=False, path_type=pathlib.Path), required=False)
@options.USER(
    help='Email address of the AiiDA user from whom to export this computer (if different from default user).'
)
@options.OVERWRITE()
@options.SORT()
@with_dbenv()
def computer_export_config(computer, output_file, user, overwrite, sort):
    """Export computer transport configuration for a user to a YAML file."""
    import yaml

    if not computer.is_configured:
        echo.echo_critical(
            f'Computer<{computer.pk}> {computer.label} configuration cannot be exported,'
            ' because computer has not been configured yet.'
        )
    else:
        if output_file is None:
            output_file = pathlib.Path(f'{computer.label}-config.yaml')
        try:
            validate_output_filename(output_file=output_file, overwrite=overwrite)
        except (FileExistsError, IsADirectoryError) as exception:
            raise click.BadParameter(str(exception), param_hint='OUTPUT_FILE') from exception

    try:
        computer_configuration = computer.get_configuration(user)
        output_file.write_text(yaml.dump(computer_configuration, sort_keys=sort), 'utf-8')

    except Exception as exception:
        error_traceback = traceback.format_exc()
        echo.CMDLINE_LOGGER.debug(error_traceback)
        if user is None:
            echo.echo_critical(
                f'Unexpected error while exporting configuration for Computer<{computer.pk}> {computer.label}: {exception!s}.'  # noqa: E501
            )
        else:
            echo.echo_critical(
                f'Unexpected error while exporting configuration for Computer<{computer.pk}> {computer.label}'
                f' and User<{user.pk}> {user.email}: {exception!s}.'
            )
    else:
        echo.echo_success(f'Computer<{computer.pk}> {computer.label} configuration exported to file `{output_file}`.')
