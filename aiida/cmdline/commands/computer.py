# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi computer` commands"""
import sys
import click

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.common.exceptions import ValidationError
from aiida.cmdline.commands import verdi, verdi_computer, ensure_scripts
from aiida.cmdline.params import options, arguments
from aiida.cmdline.utils import echo
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.cmdline.params import types
from aiida.cmdline.params.options.interactive import InteractiveOption
from aiida.cmdline.params.types import (
    ShebangParamType, MpirunCommandParamType, NonemptyStringParamType)
from aiida.control.computer import ComputerBuilder


def get_computer_names():
    """
    Retrieve the list of computers in the DB.
    """
    from aiida.orm.querybuilder import QueryBuilder
    qb = QueryBuilder()
    qb.append(type='computer', project=['name'])
    if qb.count() > 0:
        return zip(*qb.all())[0]
    else:
        return []

@with_dbenv()
def get_computer(name):
    """
    Get a Computer object with given name, or raise NotExistent
    """
    from aiida.orm.computer import Computer as AiidaOrmComputer
    return AiidaOrmComputer.get(name)


@with_dbenv()
def prompt_for_computer_configuration(computer):
    import inspect, readline
    from aiida.orm.computer import Computer
    from aiida.common.exceptions import ValidationError

def shouldcall_default_mpiprocs_per_machine(ctx):
    """
    Return True if the scheduler can accept 'default_mpiprocs_per_machine',
    False otherwise.

    If there is a problem in determining the scheduler, return True to
    avoid exceptions.
    """
    scheduler_ep = ctx.params['scheduler']
    if scheduler_ep is not None:
        try:
            SchedulerClass = scheduler_ep.load()
        except ImportError:
            raise ImportError("Unable to load the '{}' scheduler".format(scheduler_ep.name))
    else:
        raise ValidationError(
            "The shouldcall_... function should always be run (and prompted) AFTER asking for a scheduler")

    JobResourceClass = SchedulerClass._job_resource_class
    if JobResourceClass is None:
        # Odd situation...
        return False

    return JobResourceClass.accepts_default_mpiprocs_per_machine()
    
def _computer_test_get_jobs(transport,scheduler,authinfo):
    """
    Internal test to check if it is possible to check the queue state.

    :param transport: an open transport
    :param scheduler: the corresponding scheduler class
    :param authinfo: the AuthInfo object (from which one can get
      computer and aiidauser)
    :return: True if the test succeeds, False if it fails.
    """
    echo.echo("> Getting job list...")
    found_jobs = scheduler.getJobs(as_dict=True)
    # For debug
    # for jid, data in found_jobs.iteritems():
    #    print jid, data['submission_time'], data['dispatch_time'], data['job_state']
    echo.echo("  `-> OK, {} jobs found in the queue.".format(len(found_jobs)))
    return True

def _computer_create_temp_file(transport, scheduler, authinfo):
    """
    Internal test to check if it is possible to create a temporary file
    and then delete it in the work directory

    :note: exceptions could be raised

    :param transport: an open transport
    :param scheduler: the corresponding scheduler class
    :param authinfo: the AuthInfo object (from which one can get
      computer and aiidauser)
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

    with tempfile.NamedTemporaryFile() as tempf:
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
            print "      [Content OK]"
    finally:
        os.remove(destfile)

    echo.echo("  `-> Removing the file...")
    transport.remove(remote_file_path)
    echo.echo("  [Deleted successfully]")
    return True

@verdi_computer.command('setup')
@click.pass_context
@options.LABEL(prompt='Computer label', cls=InteractiveOption, required=True, type=NonemptyStringParamType())
@options.HOSTNAME(prompt='Hostname', cls=InteractiveOption, required=True,
    help="The fully qualified host-name of this computer; for local transports, use 'localhost'")
@options.DESCRIPTION(prompt='Description', cls=InteractiveOption,
                     help="A human-readable description of this computer")
@click.option('-e/-d', '--enabled/--disabled', is_flag=True, default=True,
    help='if created with the disabled flag, calculations '
         'associated with it will not be submitted until when it is '
         're-enabled',
    prompt="Enable the computer?",
    cls=InteractiveOption,
    # IMPORTANT! Do not specify explicitly type=click.BOOL,
    # Otherwise you would not get a default value when prompting
 )
@options.TRANSPORT(prompt="Transport plugin", cls=InteractiveOption)
@options.SCHEDULER(prompt="Scheduler plugin", cls=InteractiveOption)
@click.option(
   '--shebang',
    prompt='Shebang line (first line of each script, starting with #!)',
    default="#!/bin/bash",
    cls=InteractiveOption,
    help='this line specifies the first line of the submission script for this computer',
    type=ShebangParamType())
@click.option(
    '-w', '--work-dir',
    prompt='work directory on the computer',
    default="/scratch/{username}/aiida/",
    cls=InteractiveOption,
    help="The absolute path of the directory on the computer where AiiDA will "
         "run the calculations (typically, the scratch of the computer). You "
         "can use the {username} replacement, that will be replaced by your "
         "username on the remote computer")
@click.option(
    '-m', '--mpirun-command',
    prompt="mpirun command",
    default="mpirun -np {tot_num_mpiprocs}",
    cls=InteractiveOption,
    help="The mpirun command needed on the cluster to run parallel MPI "
         "programs. You can use the {tot_num_mpiprocs} replacement, that will be "
         "replaced by the total number of cpus, or the other scheduler-dependent "
         "replacement fields (see the scheduler docs for more information)",
    type=MpirunCommandParamType())
@click.option(
    '--mpiprocs-per-machine',
    prompt="default number of CPUs per machine",
    cls=InteractiveOption,
    help="Enter here the default number of MPI processes per machine (node) that "
         "should be used if nothing is otherwise specified. Pass the digit 0 "
         "if you do not want to provide a default value.",
    prompt_fn=shouldcall_default_mpiprocs_per_machine,
    required_fn=False,
    type=click.INT,
) # Note: this can still be passed from the command line in non-interactive mode
@options.PREPEND_TEXT()
@options.APPEND_TEXT()
@options.NON_INTERACTIVE()
@with_dbenv()
def setup_computer(ctx, non_interactive, **kwargs):
    """Add a Computer."""
    from aiida.common.exceptions import ValidationError
    #from aiida.cmdline.utils.echo import ExitCode

    if kwargs['label'] in get_computer_names():
        echo.echo_critical('A computer called {} already exists.\n'
            'Use "verdi computer update" to update it, and be '
            'careful if you really want to modify a database '
            'entry!'.format(kwargs['label']))

    if not non_interactive:
        pre, post = ensure_scripts(kwargs.pop('prepend_text', ''), kwargs.pop('append_text', ''), kwargs)
        kwargs['prepend_text'] = pre
        kwargs['append_text'] = post

    computer_builder = ComputerBuilder(**kwargs)
    try:
        computer = computer_builder.new()
    except (ComputerBuilder.ComputerValidationError, ValidationError) as e:
        echo.echo_critical('{}: {}'.format(type(e).__name__, e))


    try:
        computer.store()
    except ValidationError as err:
        echo.echo_critical('unable to store the computer: {}. Exiting...'.format(err))

    echo.echo_success('computer "{}" stored in DB.'.format(computer.name))
    echo.echo_info('pk: {}, uuid: {}'.format(computer.pk, computer.uuid))

    echo.echo_info("Note: before using it with AiiDA, configure it using the command")
    echo.echo_info("  verdi computer configure {}".format(computer.name))
    echo.echo_info("(Note: machine_dependent transport parameters cannot be set via ")
    echo.echo_info("the command-line interface at the moment)")


@verdi_computer.command('enable')
@click.pass_context
@click.option(
    '-u',
    '--only-for-user',
    type=types.UserParamType(),
    required=False,
    help="Enable a computer only for the given user. If not specified, enables the computer globally.")
@arguments.COMPUTER()
@with_dbenv()
def enable_computer(ctx, only_for_user, computer):
    """Enable a computer"""
    from aiida.common.exceptions import NotExistent

    if only_for_user is None:
        if computer.is_enabled():
            echo.echo_info("Computer '{}' already enabled.".format(computer.name))
        else:
            computer.set_enabled_state(True)
            echo.echo_info("Computer '{}' enabled.".format(computer.name))
    else:
        try:
            authinfo = computer.get_authinfo(only_for_user)
        except NotExistent:
            echo.echo_critical("User with email '{}' is not configured for computer '{}' yet.".format(
                only_for_user.email, computer.name))

        if not authinfo.enabled:
            authinfo.enabled = True
            echo.echo_info("Computer '{}' enabled for user {}.".format(computer.name, only_for_user.get_full_name()))
        else:
            echo.echo_info("Computer '{}' was already enabled for user {} {}.".format(
                computer.name, only_for_user.first_name, only_for_user.last_name))


@verdi_computer.command('disable')
@click.pass_context
@click.option(
    '-u',
    '--only-for-user',
    type=types.UserParamType(),
    required=False,
    help="Disable a computer only for the given user. If not specified, disables the computer globally.")
@arguments.COMPUTER()
@with_dbenv()
def disable_computer(ctx, only_for_user, computer):
    """Disable a computer. Useful, for instance, when a computer is under maintenance."""
    from aiida.common.exceptions import NotExistent

    if only_for_user is None:
        if not computer.is_enabled():
            echo.echo_info("Computer '{}' already disabled.".format(computer.name))
        else:
            computer.set_enabled_state(False)
            echo.echo_info("Computer '{}' disabled.".format(computer.name))
    else:
        try:
            authinfo = computer.get_authinfo(only_for_user)
        except NotExistent:
            echo.echo_critical("User with email '{}' is not configured for computer '{}' yet.".format(
                only_for_user.email, computer.name))

        if authinfo.enabled:
            authinfo.enabled = False
            echo.echo_info("Computer '{}' disabled for user {}.".format(computer.name, only_for_user.get_full_name()))
        else:
            echo.echo_info("Computer '{}' was already disabled for user {} {}.".format(
                computer.name, only_for_user.first_name, only_for_user.last_name))


@verdi_computer.command('list')
@click.option(
    '-o',
    '--only-usable',
    is_flag=True,
    help="Show only computers that are usable (i.e., "
    "configured for the given user and enabled)")
@click.option(
    '-p',
    '--parsable',
    is_flag=True,
    help="Show only the computer names, one per line, "
    "without any other information or string.")
@click.option('-a', '--all-comps', is_flag=True, help="Show also disabled or unconfigured computers")
@with_dbenv()
def computer_list(only_usable, parsable, all_comps):
    """
    List available computers
    """
    from aiida.orm.computer import Computer as AiiDAOrmComputer
    from aiida.orm.backend import construct_backend

    backend = construct_backend()

    computer_names = get_computer_names()

    if not parsable:
        echo.echo("# List of configured computers:")
        echo.echo("# (use 'verdi computer show COMPUTERNAME' " "to see the details)")
    if computer_names:
        for name in sorted(computer_names):
            computer = AiiDAOrmComputer.get(name)

            is_configured = computer.is_user_configured(backend.users.get_automatic_user())
            is_user_enabled = computer.is_user_enabled(backend.users.get_automatic_user())

            is_usable = False  # True if both enabled and configured

            if not all_comps:
                if not is_configured or not is_user_enabled or not computer.is_enabled():
                    continue

            if computer.is_enabled():
                if is_configured:
                    configured_str = ""
                    if is_user_enabled:
                        symbol = "*"
                        color = 'green'
                        enabled_str = ""
                        is_usable = True
                    else:
                        symbol = "x"
                        color = 'red'
                        enabled_str = "[DISABLED for this user]"
                else:
                    symbol = "x"
                    color = 'reset'
                    enabled_str = ""
                    configured_str = " [unconfigured]"
            else:  # GLOBALLY DISABLED
                symbol = "x"
                color = 'red'
                if is_configured and not is_user_enabled:
                    enabled_str = " [DISABLED globally AND for this user]"
                else:
                    enabled_str = " [DISABLED globally]"
                if is_configured:
                    configured_str = ""
                else:
                    configured_str = " [unconfigured]"

            if parsable:
                echo.echo(click.style("{}".format(name), fg=color))
            else:
                if (not only_usable) or is_usable:
                    echo.echo(click.style("{} ".format(symbol), fg=color), nl=False)
                    echo.echo(click.style("{} ".format(name), bold=True, fg=color), nl=False)
                    echo.echo(click.style("{}{}".format(enabled_str, configured_str), fg=color))

    else:
        echo.echo("# No computers configured yet. Use 'verdi computer setup'")


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
    from aiida.common.exceptions import UniquenessError, ValidationError

    old_name = computer.get_name()

    if old_name == new_name:
        echo.echo_critical("The old and new names are the same.")

    try:
        computer.set_name(new_name)
        computer.store()
    except ValidationError as error:
        echo.echo_critical("Invalid input! {}".format(error.message))
    except UniquenessError as error:
        echo.echo_critical("Uniqueness error encountered! Probably a "
                           "computer with name '{}' already exists"
                           "".format(new_name))
        echo.echo_critical("(Message was: {})".format(error.message))

    echo.echo_success("Computer '{}' renamed to '{}'".format(old_name, new_name))


@verdi_computer.command('test')
@options.USER(
    required=False,
    help="Test the connection for a given AiiDA user, specified by"
    "their email address. If not specified, uses the current "
    "default user.",
)
@click.option(
    '-t',
    '--print-traceback',
    is_flag=True,
    help="Print the full traceback in case an exception "
    "is raised",
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
    from aiida.orm.backend import construct_backend

    backend = construct_backend()

    # Set a user automatically if one is not specified in the command line
    if user is None:
        user = backend.users.get_automatic_user()

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
                        echo.echo("** {}: {}".format(error.__class__.__name__, error.message))
                        echo.echo("** (use the --traceback option to see the " "full traceback)")
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
            echo.echo("{}: {}".format(error.__class__.__name__, error.message))
            echo.echo("(use the --traceback option to see the " "full traceback)")
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
    from aiida.common.exceptions import (NotExistent, InvalidOperation)
    from aiida.orm.computer import delete_computer

    compname = computer.get_name()

    try:
        delete_computer(computer)
    except InvalidOperation as error:
        echo.echo_critical(error.message)

    echo.echo_success("Computer '{}' deleted.".format(compname))


class Computer(VerdiCommandWithSubcommands):
    """
    Setup and manage computers to be used

    This command allows to list, add, modify and configure computers.
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        super(Computer, self).__init__()

        self.valid_subcommands = {
            'list': (verdi, self.complete_none),
            'show': (verdi, self.complete_computers),
            'setup': (verdi, self.complete_none),
            'update': (self.computer_update, self.complete_computers),
            'enable': (verdi, self.complete_computers),
            'disable': (verdi, self.complete_computers),
            'rename': (verdi, self.complete_computers),
            'configure': (self.computer_configure, self.complete_computers),
            'test': (verdi, self.complete_computers),
            'delete': (verdi, self.complete_computers),
        }

    def complete_computers(self, subargs_idx, subargs):
        if not is_dbenv_loaded():
            load_dbenv()
        computer_names = get_computer_names()
        print computer_names
        return "\n".join(computer_names)

    def computer_update(self, *args):
        """
        Update an existing computer
        """
        import argparse
        from aiida.common.exceptions import NotExistent

        if not is_dbenv_loaded():
            load_dbenv()

        from aiida.orm.computer import Computer

        parser = argparse.ArgumentParser(prog=self.get_full_command_name(), description='Update a computer')
        # The default states are those that are shown if no option is given
        parser.add_argument('computer_name', help="The name of the computer")
        parsed_args = parser.parse_args(args)
        computer_name = parsed_args.computer_name

        try:
            computer = Computer.get(computer_name)
        except NotExistent:
            print "No computer {} was found".format(computer_name)
            sys.exit(1)

        calculation_on_computer = computer.get_calculations_on_computer()

        if calculation_on_computer:
            # Note: this is an artificial comment.
            # If you comment the following lines, you will be able to overwrite
            # the old computer anyway, at your own risk.
            print "You cannot modify a computer, after you run some calculations on it."
            print "Disable this computer and set up a new one."
            sys.exit(1)

        print "*" * 75
        print "WARNING! Modifying existing computer with name '{}'".format(computer_name)
        print "Are you sure you want to continue? The UUID will remain the same!"
        print "Continue only if you know what you are doing."
        print "If you just want to rename a computer, use the 'verdi computer rename'"
        print "command. In most cases, it is better to create a new computer."
        print "Moreover, if you change the transport, you must also reconfigure"
        print "each computer for each user!"
        print "*" * 75
        print "Press [Enter] to continue, or [Ctrl]+C to exit."
        raw_input()

        prompt_for_computer_configuration(computer)

        try:
            computer.store()
        except ValidationError as e:
            print "Unable to store the computer: {}. Exiting...".format(e.message)
            sys.exit(1)

        print "Computer '{}' successfully updated.".format(computer_name)
        print "pk: {}, uuid: {}".format(computer.pk, computer.uuid)
        print "(Note: machine_dependent transport parameters cannot be set via "
        print "the command-line interface at the moment)"

        print "OK"
        pass


    def computer_configure(self, *args):
        """
        Configure the authentication information for a given computer
        """
        if not is_dbenv_loaded():
            load_dbenv()

        import readline
        import inspect

        from aiida.common.exceptions import (NotExistent, ValidationError, MultipleObjectsError)
        from aiida.common.utils import get_configured_user_email

        import argparse

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(), description='Configure a computer for a given AiiDA user.')
        # The default states are those that are shown if no option is given
        parser.add_argument(
            '-u',
            '--user',
            type=str,
            metavar='EMAIL',
            help="Configure the computer for the given AiiDA user (otherwise, configure the current default user)",
        )
        parser.add_argument('computer', type=str, help="The name of the computer that you want to configure")

        parsed_args = parser.parse_args(args)

        user_email = parsed_args.user
        computername = parsed_args.computer

        try:
            computer = get_computer(name=computername)
        except NotExistent:
            print >> sys.stderr, "No computer exists with name '{}'".format(computername)
            sys.exit(1)
        if user_email is None:
            user = self.backend.users.get_automatic_user()
        else:
            try:
                user = self.backend.users.get(email=user_email)
            except (NotExistent, MultipleObjectsError) as e:
                print >> sys.stderr, ("{}".format(e))
                sys.exit(1)

        try:
            authinfo = self.backend.authinfos.get(computer=computer, user=user)
        except NotExistent:
            authinfo = self.backend.authinfos.create(computer=computer, user=user)
        old_authparams = authinfo.get_auth_params()

        Transport = computer.get_transport_class()

        print("Configuring computer '{}' for the AiiDA user '{}'".format(computername, user.email))

        print "Computer {} has transport of type {}".format(computername, computer.get_transport_type())

        if user.email != get_configured_user_email():
            print "*" * 72
            print "** {:66s} **".format("WARNING!")
            print "** {:66s} **".format("  You are configuring a different user.")
            print "** {:66s} **".format("  Note that the default suggestions are taken from your")
            print "** {:66s} **".format("  local configuration files, so they may be incorrect.")
            print "*" * 72

        valid_keys = Transport.get_valid_auth_params()

        default_authparams = {}
        for k in valid_keys:
            if k in old_authparams:
                default_authparams[k] = old_authparams.pop(k)
        if old_authparams:
            print("WARNING: the following keys were previously in the " "authorization parameters,")
            print "but have not been recognized and have been deleted:"
            print ", ".join(old_authparams.keys())

        print ""
        print "Note: to leave a field unconfigured, leave it empty and press [Enter]"

        # I strip out the old auth_params that are not among the valid keys
        new_authparams = {}

        for k in valid_keys:
            key_set = False
            while not key_set:
                try:
                    converter_name = '_convert_{}_fromstring'.format(k)
                    try:
                        converter = dict(inspect.getmembers(Transport))[converter_name]
                    except KeyError:
                        print >> sys.stderr, ("Internal error! "
                                              "No {} defined in Transport {}".format(
                                                  converter_name, computer.get_transport_type()))
                        sys.exit(1)

                    if k in default_authparams:
                        readline.set_startup_hook(lambda: readline.insert_text(str(default_authparams[k])))
                    else:
                        # Use suggestion only if parameters were not already set
                        suggester_name = '_get_{}_suggestion_string'.format(k)
                        try:
                            suggester = dict(inspect.getmembers(Transport))[suggester_name]
                            suggestion = suggester(computer)
                            readline.set_startup_hook(lambda: readline.insert_text(suggestion))
                        except KeyError:
                            readline.set_startup_hook()

                    txtval = raw_input("=> {} = ".format(k))
                    if txtval:
                        new_authparams[k] = converter(txtval)
                    key_set = True
                except ValidationError as e:
                    print "Error in the inserted value: {}".format(e.message)

        if not valid_keys:
            print "There are no special keys to be configured. Configuration completed."

        authinfo.set_auth_params(new_authparams)
        authinfo.store()
        print "Configuration stored for your user on computer '{}'.".format(computername)
