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
from collections import namedtuple
from functools import partial

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options, arguments
from aiida.cmdline.params.options.interactive import InteractiveOption
from aiida.cmdline.params.options.commands import computer as options_computer
from aiida.cmdline.utils import echo
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.cmdline.utils.multi_line_input import ensure_scripts
from aiida.common.exceptions import ValidationError, InputValidationError, NotExistent
from aiida.plugins.entry_point import get_entry_points, load_entry_point
from aiida.transports import cli as transport_cli

VALID_OPTION_ORIGINS = namedtuple('ValidOptionOrigins', ['TRANSPORT', 'AUTHINFO'])

CONFIGURE_ENTRYPOINT_GROUP = 'aiida.cmdline.computer.configure'


def create_option(name, spec, originates_from):
    """Create a click option from a name and partial specs.

    This is used in transport auth_options and in the common_authinfo options.
    :param spec: a dictionary of valid click specifiers
    :param originates_from: a valid origin of this option (tranport, authinfo, ...).
        It must be a value in the VALID_OPTION_ORIGINS NamedTuple.
    """
    from copy import deepcopy
    spec = deepcopy(spec)
    name_dashed = name.replace('_', '-')
    option_name = '--{}'.format(name_dashed)
    existing_option = spec.pop('option', None)
    if spec.pop('switch', False):
        option_name = '--{name}/--no-{name}'.format(name=name_dashed)
    kwargs = {}

    if 'default' in spec:
        kwargs['show_default'] = True
    else:
        kwargs['contextual_default'] = interactive_default(
            name, also_noninteractive=spec.pop('non_interactive_default', False), originates_from=originates_from
        )

    kwargs['cls'] = InteractiveOption
    kwargs.update(spec)
    if existing_option:
        return existing_option(**kwargs)
    return click.option(option_name, **kwargs)


def interactive_default(key, also_noninteractive, originates_from):
    """Create a contextual_default value callback for an auth_param key.

    :param key: the key
    :param also_noninteractive: whether this
    :param originates_from: a valid origin of this option (tranport, authinfo, ...).
        It must be a value in the VALID_OPTION_ORIGINS NamedTuple.
    """

    @with_dbenv()
    def get_default(ctx):
        """Determine the default value from the context."""
        from aiida import orm

        user = ctx.params['user'] or orm.User.objects.get_default()
        computer = ctx.params['computer']
        try:
            authinfo = orm.AuthInfo.objects.get(dbcomputer_id=computer.id, aiidauser_id=user.id)
        except NotExistent:
            authinfo = orm.AuthInfo(computer=computer, user=user)
        non_interactive = ctx.params['non_interactive']
        if not also_noninteractive and non_interactive:
            raise click.MissingParameter()

        if originates_from == VALID_OPTION_ORIGINS.TRANSPORT:
            old_authparams = authinfo.get_auth_params()
            suggestion = old_authparams.get(key)
            suggestion = suggestion or transport_cli.transport_option_default(key, computer)
            return suggestion
        if originates_from == VALID_OPTION_ORIGINS.AUTHINFO:
            return authinfo.get_metadata_field(key, authinfo.get_default_for_metadata_field(key))
        raise ValueError('unknown value of `originates_from`: {}'.format(originates_from.value))

    return get_default


@verdi.group('computer')
def verdi_computer():
    """Setup and manage computers."""


def get_computer_names():
    """
    Retrieve the list of computers in the DB.
    """
    from aiida.orm.querybuilder import QueryBuilder
    builder = QueryBuilder()
    builder.append(entity_type='computer', project=['name'])
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
    return True, '{} jobs found in the queue'.format(len(found_jobs))


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
        return False, 'The command `echo -n` returned a non-zero return code ({})'.format(retval)

    if stdout:
        return False, u"""
There is some spurious output in the standard output,
that we report below between the === signs:
=========================================================
{}
=========================================================
Please check that you don't have code producing output in
your ~/.bash_profile (or ~/.bashrc). If you don't want to
remove the code, but just to disable it for non-interactive
shells, see comments in issue #1980 on GitHub:
https://github.com/aiidateam/aiida-core/issues/1890
(and in the AiiDA documentation, linked from that issue)
""".format(stdout)

    if stderr:
        return u"""
There is some spurious output in the stderr,
that we report below between the === signs:
=========================================================
{}
=========================================================
Please check that you don't have code producing output in
your ~/.bash_profile (or ~/.bashrc). If you don't want to
remove the code, but just to disable it for non-interactive
shells, see comments in issue #1980 on GitHub:
https://github.com/aiidateam/aiida-core/issues/1890
(and in the AiiDA documentation, linked from that issue)
"""

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
    import tempfile
    import datetime
    import os

    file_content = "Test from 'verdi computer test' on {}".format(datetime.datetime.now().isoformat())
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
        return False, 'failed to create the file `{}` on the remote'.format(remote_file_path)

    handle, destfile = tempfile.mkstemp()
    os.close(handle)

    try:
        transport.getfile(remote_file_path, destfile)
        with open(destfile, encoding='utf8') as dfile:
            read_string = dfile.read()

        if read_string != file_content:
            message = 'retrieved file content is different from what was expected'
            message += '\n  Expected: {}'.format(file_content)
            message += '\n  Retrieved: {}'.format(read_string)
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
@options.PREPEND_TEXT()
@options.APPEND_TEXT()
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
    """Duplicate a computer allowing to change some parameters."""
    from aiida import orm
    from aiida.orm.utils.builders.computer import ComputerBuilder

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

    is_configured = computer.is_user_configured(orm.User.objects.get_default())

    if not is_configured:
        echo.echo_info('Note: before the computer can be used, it has to be configured with the command:')
        echo.echo_info('  verdi computer configure {} {}'.format(computer.get_transport_type(), computer.name))


@verdi_computer.command('enable')
@arguments.COMPUTER()
@arguments.USER()
@with_dbenv()
def computer_enable(computer, user):
    """Enable the computer for the given user."""

    try:
        authinfo = computer.get_authinfo(user)
    except NotExistent:
        echo.echo_critical(
            "User with email '{}' is not configured for computer '{}' yet.".format(user.email, computer.name)
        )

    if not authinfo.enabled:
        authinfo.enabled = True
        echo.echo_info("Computer '{}' enabled for user {}.".format(computer.name, user.get_full_name()))
    else:
        echo.echo_info(
            "Computer '{}' was already enabled for user {} {}.".format(computer.name, user.first_name, user.last_name)
        )


@verdi_computer.command('disable')
@arguments.COMPUTER()
@arguments.USER()
@with_dbenv()
def computer_disable(computer, user):
    """Disable the computer for the given user.

    Thi can be useful, for example, when a computer is under maintenance."""

    try:
        authinfo = computer.get_authinfo(user)
    except NotExistent:
        echo.echo_critical(
            "User with email '{}' is not configured for computer '{}' yet.".format(user.email, computer.name)
        )

    if authinfo.enabled:
        authinfo.enabled = False
        echo.echo_info("Computer '{}' disabled for user {}.".format(computer.name, user.get_full_name()))
    else:
        echo.echo_info(
            "Computer '{}' was already disabled for user {} {}.".format(computer.name, user.first_name, user.last_name)
        )


@verdi_computer.command('list')
@options.ALL(help='Show also disabled or unconfigured computers.')
@options.RAW(help='Show only the computer names, one per line.')
@with_dbenv()
def computer_list(all_entries, raw):
    """List all available computers."""
    from aiida.orm import Computer, User

    if not raw:
        echo.echo_info('List of configured computers')
        echo.echo_info("Use 'verdi computer show COMPUTERNAME' to display more detailed information")

    computers = Computer.objects.all()
    user = User.objects.get_default()

    if not computers:
        echo.echo_info("No computers configured yet. Use 'verdi computer setup'")

    sort = lambda computer: computer.name
    highlight = lambda comp: comp.is_user_configured(user) and comp.is_user_enabled(user)
    hide = lambda comp: not (comp.is_user_configured(user) and comp.is_user_enabled(user)) and not all_entries
    echo.echo_formatted_list(computers, ['name'], sort=sort, highlight=highlight, hide=hide)


@verdi_computer.command('show')
@arguments.COMPUTER()
@with_dbenv()
def computer_show(computer):
    """Show detailed information for a computer."""
    echo.echo(computer.full_text_info)


@verdi_computer.command('rename')
@arguments.COMPUTER()
@arguments.LABEL('NEW_NAME')
@with_dbenv()
def computer_rename(computer, new_name):
    """Rename a computer."""
    from aiida.common.exceptions import UniquenessError

    old_name = computer.get_name()

    if old_name == new_name:
        echo.echo_critical('The old and new names are the same.')

    try:
        computer.set_name(new_name)
        computer.store()
    except ValidationError as error:
        echo.echo_critical('Invalid input! {}'.format(error))
    except UniquenessError as error:
        echo.echo_critical(
            'Uniqueness error encountered! Probably a '
            "computer with name '{}' already exists"
            ''.format(new_name)
        )
        echo.echo_critical('(Message was: {})'.format(error))

    echo.echo_success("Computer '{}' renamed to '{}'".format(old_name, new_name))


@verdi_computer.command('test')
@options.USER(
    required=False,
    help='Test the connection for a given AiiDA user, specified by'
    'their email address. If not specified, uses the current default user.',
)
@click.option(
    '-t',
    '--print-traceback',
    is_flag=True,
    help='Print the full traceback in case an exception is raised',
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
    from aiida import orm

    # Set a user automatically if one is not specified in the command line
    if user is None:
        user = orm.User.objects.get_default()

    echo.echo_info('Testing computer<{}> for user<{}>...'.format(computer.name, user.email))

    try:
        authinfo = computer.get_authinfo(user)
    except NotExistent:
        echo.echo_critical('Computer<{}> is not yet configured for user<{}>'.format(computer.name, user.email))

    if not authinfo.enabled:
        echo.echo_warning('Computer<{}> is disabled for user<{}>'.format(computer.name, user.email))
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

            echo.echo_highlight('[OK]', color='success')

            scheduler.set_transport(transport)

            for test, test_label in tests.items():

                echo.echo('* {}... '.format(test_label), nl=False)
                num_tests += 1
                try:
                    success, message = test(transport=transport, scheduler=scheduler, authinfo=authinfo)
                except Exception as exception:  # pylint:disable=broad-except
                    success = False
                    message = '{}: {}'.format(exception.__class__.__name__, str(exception))

                    if print_traceback:
                        message += '\n  Full traceback:\n'
                        message += '\n'.join(['  {}'.format(l) for l in traceback.format_exc().splitlines()])
                    else:
                        message += '\n  Use the `--print-traceback` option to see the full traceback.'

                if not success:
                    num_failures += 1
                    if message:
                        echo.echo_highlight('[Failed]: ', color='error', nl=False)
                        echo.echo(message)
                    else:
                        echo.echo_highlight('[Failed]', color='error')
                else:
                    if message:
                        echo.echo_highlight('[OK]: ', color='success', nl=False)
                        echo.echo(message)
                    else:
                        echo.echo_highlight('[OK]', color='success')

        if num_failures:
            echo.echo_warning('{} out of {} tests failed'.format(num_failures, num_tests))
        else:
            echo.echo_success('all {} tests succeeded'.format(num_tests))

    except Exception as exception:  # pylint:disable=broad-except
        echo.echo_highlight('[FAILED]: ', color='error', nl=False)
        message = 'Error while trying to connect to the computer'

        if print_traceback:
            message += '\n  Full traceback:\n'
            message += '\n'.join(['  {}'.format(l) for l in traceback.format_exc().splitlines()])
        else:
            message += '\n  Use the `--print-traceback` option to see the full traceback.'

        echo.echo(message)
        echo.echo_warning('{} out of {} tests failed'.format(1, num_tests))


@verdi_computer.command('delete')
@arguments.COMPUTER()
@with_dbenv()
def computer_delete(computer):
    """
    Delete a computer.

    Note that it is not possible to delete the computer if there are calculations that are using it.
    """
    from aiida.common.exceptions import InvalidOperation
    from aiida import orm

    compname = computer.name

    try:
        orm.Computer.objects.delete(computer.id)
    except InvalidOperation as error:
        echo.echo_critical(str(error))

    echo.echo_success("Computer '{}' deleted.".format(compname))


@verdi_computer.group('configure')
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
def computer_config_show(computer, user, defaults, as_option_string): # pylint: disable=too-many-locals
    """Show the current configuration for a computer."""
    import tabulate
    from aiida import orm
    from aiida.common.escaping import escape_for_bash

    if user is None:
        user = orm.User.objects.get_default()
    try:
        authinfo = computer.get_authinfo(user)
    except NotExistent:
        echo.echo_critical('Computer<{}> is not yet configured for user<{}>'.format(computer.name, user.email))

    # Dynamically get transport options
    transport_cls = computer.get_transport_class()
    transport_option_list = [
        param for param in transport_cli.create_configure_cmd_transport_only(computer.get_transport_type()).params
        if isinstance(param, click.core.Option) and param.name in transport_cls.get_valid_auth_params()
    ]

    # Dynamically get authinfo options
    authinfo_decorator_list = [
        create_option(key, options, originates_from=VALID_OPTION_ORIGINS.AUTHINFO)
        for key, options in authinfo.COMMON_AUTHINFO_OPTIONS
    ]

    # Previous ones are the decorators, now I have to apply them to a 'pass' function,
    # create a fake command of it, and then extract the parameters
    # This is the same that is does in the `create_configure_cmd_transport_only` above
    authinfo_decorator_list.reverse()
    fake_command = lambda: None
    for decorator_option in authinfo_decorator_list:
        fake_command = decorator_option(fake_command)
    authinfo_option_list = [param for param in click.command()(fake_command).params]

    # Create the full list of options
    option_list = transport_option_list + authinfo_option_list

    origin_mapping = {}
    for t_option in transport_option_list:
        origin_mapping[t_option.name] = VALID_OPTION_ORIGINS.TRANSPORT
    for a_option in authinfo_option_list:
        if a_option.name in origin_mapping:
            raise RuntimeError('The transport plugin is redefining the command "{}"'.format(a_option.name))
        origin_mapping[a_option.name] = VALID_OPTION_ORIGINS.AUTHINFO

    if defaults:
        config = {}
        for option in option_list:
            if origin_mapping[option.name] == VALID_OPTION_ORIGINS.TRANSPORT:
                config[option.name] = transport_cli.transport_option_default(option.name, computer)
            elif origin_mapping[option.name] == VALID_OPTION_ORIGINS.AUTHINFO:
                config[option.name] = authinfo.get_default_for_metadata_field(option.name)
    else:
        config = authinfo.get_auth_params()
        for option_name, _ in authinfo.COMMON_AUTHINFO_OPTIONS:
            try:
                config[option_name] = authinfo.get_metadata_field(option_name)
            except KeyError:
                pass

    option_items = []
    if as_option_string:
        for option in option_list:
            if origin_mapping[option.name] == VALID_OPTION_ORIGINS.TRANSPORT:
                option_data = transport_cls.auth_options[option.name]
            elif origin_mapping[option.name] == VALID_OPTION_ORIGINS.AUTHINFO:
                option_data = dict(authinfo.COMMON_AUTHINFO_OPTIONS)[option.name]
            else:
                raise RuntimeError('Unknwon type "{}"'.format(option.name))
            if config.get(option.name) is not None:
                if option_data.get('switch'):
                    option_value = option.opts[-1] if config.get(option.name
                                                                ) else '--no-{}'.format(option.name.replace('_', '-'))
                elif option_data.get('is_flag'):
                    is_default = False
                    if origin_mapping[option.name] == VALID_OPTION_ORIGINS.TRANSPORT:
                        is_default = config.get(option.name
                                               ) == transport_cli.transport_option_default(option.name, computer)
                    elif origin_mapping[option.name] == VALID_OPTION_ORIGINS.AUTHINFO:
                        is_default = config.get(option.name) == authinfo.get_default_for_metadata_field(option.name)
                    else:
                        raise RuntimeError('Unknwon type "{}"'.format(option.name))

                    option_value = option.opts[-1] if is_default else ''
                else:
                    option_value = '{}={}'.format(
                        option.opts[-1], escape_for_bash(str(option.type(config[option.name])))
                    )
                option_items.append(option_value)
        opt_string = ' '.join(option_items)
        echo.echo(opt_string)
    else:
        table = []
        for name in transport_cls.get_valid_auth_params():
            if name in config:
                table.append(('* ' + name, config[name]))
            else:
                table.append(('* ' + name, '-'))

        for name, _ in authinfo.COMMON_AUTHINFO_OPTIONS:
            if name in config:
                table.append(('* ' + name, config[name]))
            else:
                table.append(('* ' + name, '-'))
        echo.echo(tabulate.tabulate(table, tablefmt='plain'))


for ep in get_entry_points(CONFIGURE_ENTRYPOINT_GROUP):
    from aiida.transports.common import COMMON_AUTHINFO_OPTIONS as _COMMON_AUTHINFO_OPTIONS

    _transport_command = load_entry_point(CONFIGURE_ENTRYPOINT_GROUP, ep.name)

    # Dynamically get authinfo options
    _authinfo_decorator_list = [
        create_option(key, options, originates_from=VALID_OPTION_ORIGINS.AUTHINFO)
        for key, options in _COMMON_AUTHINFO_OPTIONS
    ]
    _authinfo_decorator_list.reverse()

    for _decorator_option in _authinfo_decorator_list:
        _transport_command = _decorator_option(_transport_command)

    computer_configure.add_command(_transport_command)
