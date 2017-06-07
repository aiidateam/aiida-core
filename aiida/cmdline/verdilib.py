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
Command line commands for the main executable 'verdi' of aiida

If you want to define a new command line parameter, just define a new
class inheriting from VerdiCommand, and define a run(self,*args) method
accepting a variable-length number of parameters args
(the command-line parameters), which will be invoked when
this executable is called as
verdi NAME

Don't forget to add the docstring to the class: the first line will be the
short description, the following ones the long description.
"""
import sys
import os
import contextlib
import click

import aiida
from aiida.common.exceptions import (
    AiidaException, ConfigurationError, ProfileConfigurationError)
from aiida.cmdline.baseclass import VerdiCommand, VerdiCommandRouter
from aiida.cmdline import pass_to_django_manage
from aiida.backends import settings as settings_profile

# Import here from other files; once imported, it will be found and
# used as a command-line parameter
from aiida.cmdline.commands.user import User
from aiida.cmdline.commands.calculation import Calculation
from aiida.cmdline.commands.code import Code
from aiida.cmdline.commands.computer import Computer
from aiida.cmdline.commands.daemon import Daemon
from aiida.cmdline.commands.data import Data
from aiida.cmdline.commands.devel import Devel
from aiida.cmdline.commands.exportfile import Export
from aiida.cmdline.commands.group import Group
from aiida.cmdline.commands.graph import Graph
from aiida.cmdline.commands.importfile import Import
from aiida.cmdline.commands.node import Node
from aiida.cmdline.commands.profile import Profile
from aiida.cmdline.commands.workflow import Workflow
from aiida.cmdline.commands.work import Work
from aiida.cmdline.commands.comment import Comment
from aiida.cmdline.commands.shell import Shell
from aiida.cmdline.commands.restapi import Restapi
from aiida.cmdline.commands.quicksetup import Quicksetup
from aiida.cmdline import execname



class ProfileParsingException(AiidaException):
    """
    Exception raised when parsing the profile command line option, if only
    -p is provided, and no profile is specified
    """

    def __init__(self, *args, **kwargs):
        self.minus_p_provided = kwargs.pop('minus_p_provided', False)

        super(ProfileParsingException, self).__init__(*args, **kwargs)


def parse_profile(argv, merge_equal=False):
    """
    Parse the argv to see if a profile has been specified, return it with the
    command position shift (index where the commands start)

    :param merge_equal: if True, merge things like
      ('verdi', '--profile', '=', 'x', 'y') to ('verdi', '--profile=x', 'y')
      but then return the correct index for the original array.

    :raise ProfileParsingException: if there is only 'verdi' specified, or
      if only 'verdi -p' (in these cases, one has respectively
      exception.minus_p_provided equal to False or True)
    """
    if merge_equal:
        if len(argv) >= 3:
            if argv[1] == '--profile' and argv[2] == '=':
                internal_argv = [argv[0], "".join(argv[1:4])] + list(argv[4:])
                shift = 2
            else:
                internal_argv = list(argv)
                shift = 0
        else:
            internal_argv = list(argv)
            shift = 0
    else:
        internal_argv = list(argv)
        shift = 0

    profile = None  # Use default profile if nothing is specified
    command_position = 1  # If there is no profile option
    try:
        profile_switch = internal_argv[1]
    except IndexError:
        raise ProfileParsingException(minus_p_provided=False)
    long_profile_prefix = '--profile='
    if profile_switch == '-p':
        try:
            profile = internal_argv[2]
        except IndexError:
            raise ProfileParsingException(minus_p_provided=True)
        command_position = 3
    elif profile_switch.startswith(long_profile_prefix):
        profile = profile_switch[len(long_profile_prefix):]
        command_position = 2
    else:
        # No profile switch, continue using argv[1] as the command name
        pass

    return profile, command_position + shift


@contextlib.contextmanager
def update_environment(new_argv):
    """
    Used as a context manager, changes sys.argv with the
    new_argv argument, and restores it upon exit.
    """
    import sys

    _argv = sys.argv[:]
    sys.argv = new_argv[:]
    yield

    # Restore old parameters when exiting from the context manager
    sys.argv = _argv


########################################################################
# HERE STARTS THE COMMAND FUNCTION LIST
########################################################################

class CompletionCommand(VerdiCommand):
    """
    Return the bash completion function to put in ~/.bashrc

    This command prints on screen the function to be inserted in
    your .bashrc command. You can copy and paste the output, or simply
    add
    eval "`verdi completioncommand`"
    to your .bashrc, *AFTER* having added the aiida/bin directory to the path.
    """

    def run(self, *args):
        """
        I put the documentation here, and I don't print it, so we
        don't clutter too much the .bashrc.

        * "${THE_WORDS[@]}" (with the @) puts each element as a different
          parameter; note that the variable expansion etc. is performed

        * I add a 'x' at the end and then remove it; in this way, $( ) will
          not remove trailing spaces

        * If the completion command did not print anything, we use
          the default bash completion for filenames

        * If instead the code prints something empty, thanks to the workaround
          above $OUTPUT is not empty, so we do go the the 'else' case
          and then, no substitution is suggested.
        """

        print r"""
function _aiida_verdi_completion
{
    OUTPUT=$( $1 completion "$COMP_CWORD" "${COMP_WORDS[@]}" ; echo 'x')
    OUTPUT=${OUTPUT%x}
    if [ -z "$OUTPUT" ]
    then
    # Only newline is a valid separator
        local IFS=$'\n'

        COMPREPLY=( $(compgen -o default -- "${COMP_WORDS[COMP_CWORD]}" ) )
    # Add either a slash or a space, depending on whether it is a folder
    # or a file. printf %q escapes the filename if there are spaces.
        for ((i=0; i < ${#COMPREPLY[@]}; i++)); do
            [ -d "${COMPREPLY[$i]}" ] && \
               COMPREPLY[$i]=$(printf %q%s "${COMPREPLY[$i]}" "/") || \
               COMPREPLY[$i]=$(printf %q%s "${COMPREPLY[$i]}" " ")
        done

    else
        COMPREPLY=( $(compgen -W "$OUTPUT" -- "${COMP_WORDS[COMP_CWORD]}" ) )
        # Always add a space after each command
        for ((i=0; i < ${#COMPREPLY[@]}; i++)); do
            COMPREPLY[$i]="${COMPREPLY[$i]} "
        done
    fi
}
complete -o nospace -F _aiida_verdi_completion verdi
"""

    def complete(self, subargs_idx, subargs):
        # disable further completion
        print ""


class Completion(VerdiCommand):
    """
    Manage bash completion

    Return a list of available commands, separated by spaces.
    Calls the correct function of the command if the TAB has been
    pressed after the first command.

    Returning without printing will use the default bash completion.
    """

    # TODO: manage completion at a deeper level

    def run(self, *args):
        try:
            cword = int(args[0])
            if cword <= 0:
                cword = 1
        except IndexError:
            cword = 1
        except ValueError:
            return

        try:
            profile, command_position = parse_profile(args[1:],
                                                      merge_equal=True)
        except ProfileParsingException as e:
            cword_offset = 0
        else:
            cword_offset = command_position - 1

        if cword == 1 + cword_offset:
            print " ".join(sorted(short_doc.keys()))
            return
        else:
            try:
                # args[0] is cword;
                # args[1] is the executable (verdi)
                # args[2] is the command for verdi
                # args[3:] are the following subargs
                command = args[2 + cword_offset]
            except IndexError:
                return
            try:
                CommandClass = list_commands[command]
            except KeyError:
                return
            CommandClass().complete(subargs_idx=cword - 2 - cword_offset,
                                    subargs=args[3 + cword_offset:])


class ListParams(VerdiCommand):
    """
    List available commands

    List available commands and their short description.
    For the long description, use the 'help' command.
    """

    def run(self, *args):
        print get_listparams()


class Help(VerdiCommand):
    """
    Describe a specific command

    Pass a further argument to get a description of a given command.
    """

    def run(self, *args):
        try:
            command = args[0]
        except IndexError:
            print get_listparams()
            print ""
            print (
            "Before each command you can specify the AiiDA profile to use,"
            " with 'verdi -p <profile> <command>' or "
            "'verdi --profile=<profile> <command>'")
            print ""
            print ("Use '{} help <command>' for more information "
                   "on a specific command.".format(execname))
            sys.exit(1)

        if command in short_doc:
            print "Description for '%s %s'" % (execname, command)
            print ""
            print "**", short_doc[command]
            if command in long_doc:
                print long_doc[command]
        else:
            print >> sys.stderr, (
                "{}: '{}' is not a valid command. "
                "See '{} help' for more help.".format(
                    execname, command, execname))
            get_command_suggestion(command)
            sys.exit(1)

    def complete(self, subargs_idx, subargs):
        if subargs_idx == 0:
            print " ".join(sorted(short_doc.keys()))
        else:
            print ""


class Install(VerdiCommand):
    """
    Install/setup aiida for the current user

    This command creates the ~/.aiida folder in the home directory
    of the user, interactively asks for the database settings and
    the repository location, does a setup of the daemon and runs
    a migrate command to create/setup the database.
    """

    def run(self, *args):
        click.echo('\nwarning: verdi install is deprecated, use verdi setup.\n')
        ctx = _setup_cmd.make_context('setup', list(args))
        with ctx:
            _setup_cmd.invoke(ctx)

    def complete(self, subargs_idx, subargs):
        """
        No completion after 'verdi install'.
        """
        print ""


class Setup(VerdiCommand):
    """
    Setup aiida for the current user

    This command creates the ~/.aiida folder in the home directory
    of the user, interactively asks for the database settings and
    the repository location, does a setup of the daemon and runs
    a migrate command to create/setup the database.
    """
    def run(self, *args):
        from aiida.cmdline.aiida_verdi.commands.setup import setup
        setup.main(args=args, standalone_mode=False, prog_name='verdi setup')

    def complete(self, subargs_idx, subargs):
        """
        No completion after 'verdi install'.
        """
        print ""


class Run(VerdiCommand):
    """
    Execute an AiiDA script
    """

    def run(self, *args):
        from aiida.backends.utils import load_dbenv,is_dbenv_loaded

        if not is_dbenv_loaded():
            load_dbenv()
        import argparse
        from aiida.cmdline.commands.shell import default_modules_list
        import aiida.orm.autogroup
        from aiida.orm.autogroup import Autogroup

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Execute an AiiDA script.')
        parser.add_argument('-g', '--group', type=bool, default=True,
                            help='Enables the autogrouping, default = True')
        parser.add_argument('-n', '--groupname', type=str, default=None,
                            help='Specify the name of the auto group')
        # parser.add_argument('-o','--grouponly', type=str, nargs='+', default=['all'],
        #                            help='Limit the grouping to specific classes (by default, all classes are grouped')
        parser.add_argument('-e', '--exclude', type=str, nargs='+', default=[],
                            help=('Autogroup only specific calculation classes.'
                                  " Select them by their module name.")
                            )
        parser.add_argument('-E', '--excludesubclasses', type=str, nargs='+',
                            default=[],
                            help=('Autogroup only specific calculation classes.'
                                  " Select them by their module name.")
                            )
        parser.add_argument('-i', '--include', type=str, nargs='+',
                            default=['all'],
                            help=('Autogroup only specific data classes.'
                                  " Select them by their module name.")
                            )
        parser.add_argument('-I', '--includesubclasses', type=str, nargs='+',
                            default=[],
                            help=('Autogroup only specific code classes.'
                                  " Select them by their module name.")
                            )
        parser.add_argument('scriptname', metavar='ScriptName', type=str,
                            help='The name of the script you want to execute')
        parser.add_argument('new_args', metavar='ARGS',
                            nargs=argparse.REMAINDER, type=str,
                            help='Further parameters to pass to the script')
        parsed_args = parser.parse_args(args)

        # Prepare the environment for the script to be run
        globals_dict = {
            '__builtins__': globals()['__builtins__'],
            '__name__': '__main__',
            '__file__': parsed_args.scriptname,
            '__doc__': None,
            '__package__': None}

        ## dynamically load modules (the same of verdi shell) - but in
        ## globals_dict, not in the current environment
        for app_mod, model_name, alias in default_modules_list:
            globals_dict["{}".format(alias)] = getattr(
                __import__(app_mod, {}, {}, model_name), model_name)

        if parsed_args.group:
            automatic_group_name = parsed_args.groupname
            if automatic_group_name is None:
                import datetime

                now = datetime.datetime.now()
                automatic_group_name = "Verdi autogroup on " + now.strftime(
                    "%Y-%m-%d %H:%M:%S")

            aiida_verdilib_autogroup = Autogroup()
            aiida_verdilib_autogroup.set_exclude(parsed_args.exclude)
            aiida_verdilib_autogroup.set_include(parsed_args.include)
            aiida_verdilib_autogroup.set_exclude_with_subclasses(
                parsed_args.excludesubclasses)
            aiida_verdilib_autogroup.set_include_with_subclasses(
                parsed_args.includesubclasses)
            aiida_verdilib_autogroup.set_group_name(automatic_group_name)
            ## Note: this is also set in the exec environment!
            ## This is the intended behavior
            aiida.orm.autogroup.current_autogroup = aiida_verdilib_autogroup

        try:
            f = open(parsed_args.scriptname)
        except IOError:
            print >> sys.stderr, "{}: Unable to load file '{}'".format(
                self.get_full_command_name(), parsed_args.scriptname)
            sys.exit(1)
        else:
            try:
                # Must add also argv[0]
                new_argv = [parsed_args.scriptname] + parsed_args.new_args
                with update_environment(new_argv=new_argv):
                    # Add local folder to sys.path
                    sys.path.insert(0, os.path.abspath(os.curdir))
                    # Pass only globals_dict
                    exec (f, globals_dict)
                    # print sys.argv
            except SystemExit as e:
                ## Script called sys.exit()
                # print sys.argv, "(sys.exit {})".format(e.message)

                ## Note: remember to re-raise, the exception to have
                ## the error code properly returned at the end!
                raise
            finally:
                f.close()


########################################################################
# HERE ENDS THE COMMAND FUNCTION LIST
########################################################################
# From here on: utility functions

def get_listparams():
    """
    Return a string with the list of parameters, to be printed

    The advantage of this function is that the calling routine can
    choose to print it on stdout or stderr, depending on the needs.
    """
    max_length = max(len(i) for i in short_doc.keys())

    name_desc = [(cmd.ljust(max_length + 2), desc.strip())
                 for cmd, desc in short_doc.iteritems()]

    name_desc = sorted(name_desc)

    return ("List of the most relevant available commands:" + os.linesep +
            os.linesep.join(["  * {} {}".format(name, desc)
                             for name, desc in name_desc]))


def get_command_suggestion(command):
    """
    A function that prints on stderr a list of similar commands
    """
    import difflib

    similar_cmds = difflib.get_close_matches(command, short_doc.keys())
    if similar_cmds:
        print >> sys.stderr, ""
        print >> sys.stderr, "Did you mean this?"
        print >> sys.stderr, "\n".join(["     {}".format(i)
                                        for i in similar_cmds])


def print_usage(execname):
    print >> sys.stderr, ("Usage: {} [--profile=PROFILENAME|-p PROFILENAME] "
                          "COMMAND [<args>]".format(execname))
    print >> sys.stderr, ""
    print >> sys.stderr, get_listparams()
    print >> sys.stderr, "See '{} help' for more help.".format(execname)


def exec_from_cmdline(argv):
    """
    The main function to be called. Pass as parameter the sys.argv.
    """
    ### This piece of code takes care of creating a list of valid
    ### commands and of their docstrings for dynamic management of
    ### the code.
    ### It defines a few global variables

    global execname
    global list_commands
    global short_doc
    global long_doc

    # import itself
    from aiida.cmdline import verdilib
    import inspect

    # List of command names that should be hidden or not completed.
    hidden_commands = ['completion', 'completioncommand', 'listparams']

    # Retrieve the list of commands
    verdilib_namespace = verdilib.__dict__

    list_commands = {v.get_command_name(): v for v in
                     verdilib_namespace.itervalues()
                     if inspect.isclass(v) and not v == VerdiCommand and
                     issubclass(v, VerdiCommand)
                     and not v.__name__.startswith('_')
                     and not v._abstract}

    # Retrieve the list of docstrings, managing correctly the
    # case of empty docstrings. Each value is a list of lines
    raw_docstrings = {k: (v.__doc__ if v.__doc__ else "").splitlines()
                      for k, v in list_commands.iteritems()}

    short_doc = {}
    long_doc = {}
    for k, v in raw_docstrings.iteritems():
        if k in hidden_commands:
            continue
        lines = [l.strip() for l in v]
        empty_lines = [bool(l) for l in lines]
        try:
            first_idx = empty_lines.index(True)  # The first non-empty line
        except ValueError:
            # All False
            short_doc[k] = "No description available"
            long_doc[k] = ""
            continue
        short_doc[k] = lines[first_idx]
        long_doc[k] = os.linesep.join(lines[first_idx + 1:])

    execname = os.path.basename(argv[0])

    try:
        profile, command_position = parse_profile(argv)
    except ProfileParsingException as e:
        print_usage(execname)
        sys.exit(1)

    # We now set the internal variable, if needed
    if profile is not None:
        settings_profile.AIIDADB_PROFILE = profile
    # I set the process to verdi
    settings_profile.CURRENT_AIIDADB_PROCESS = "verdi"

    # Finally, we parse the commands and their options
    try:
        command = argv[command_position]
    except IndexError:
        print_usage(execname)
        sys.exit(1)

    try:
        if command in list_commands:
            CommandClass = list_commands[command]()
            CommandClass.run(*argv[command_position + 1:])
        else:
            print >> sys.stderr, ("{}: '{}' is not a valid command. "
                                  "See '{} help' for more help.".format(
                execname, command, execname))
            get_command_suggestion(command)
            sys.exit(1)
    except ProfileConfigurationError as e:
        print >> sys.stderr, "The profile specified is not valid!"
        print >> sys.stderr, e.message
        sys.exit(1)

def run():
    try:
        aiida.cmdline.verdilib.exec_from_cmdline(sys.argv)
    except KeyboardInterrupt:
        pass # print "CTRL+C caught, exiting from verdi..."
    except EOFError:
        pass # print "CTRL+D caught, exiting from verdi..."
