# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import os
import sys

from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.cmdline import delayed_load_node as load_node
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands


class Calculation(VerdiCommandWithSubcommands):
    """
    Query and interact with calculations

    Different subcommands allow to list the running calculations, show the
    content of the input/output files, see the logs, etc.
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called:
        list.
        """
        from aiida.cmdline.commands.node import _Label, _Description

        labeler = _Label('calculation')
        descriptioner = _Description('calculation')

        self.valid_subcommands = {
            'gotocomputer': (self.calculation_gotocomputer, self.complete_none),
            'list': (self.calculation_list, self.complete_none),
            'logshow': (self.calculation_logshow, self.complete_none),
            'kill': (self.calculation_kill, self.complete_none),
            'inputls': (self.calculation_inputls, self.complete_none),
            'outputls': (self.calculation_outputls, self.complete_none),
            'inputcat': (self.calculation_inputcat, self.complete_none),
            'outputcat': (self.calculation_outputcat, self.complete_none),
            'res': (self.calculation_res, self.complete_none),
            'show': (self.calculation_show, self.complete_none),
            'plugins': (self.calculation_plugins, self.complete_plugins),
            'cleanworkdir': (self.calculation_cleanworkdir, self.complete_none),
            'label': (labeler.run, self.complete_none),
            'description': (descriptioner.run, self.complete_none),
        }

    def complete_plugins(self, subargs_idx, subargs):
        """
        Return the list of plugins of the JobCalculation subclass of Calculation
        """
        if not is_dbenv_loaded():
            load_dbenv()

        from aiida.common.pluginloader import all_plugins

        plugins = sorted(all_plugins('calculations'))
        # Do not return plugins that are already on the command line
        other_subargs = subargs[:subargs_idx] + subargs[subargs_idx + 1:]
        return_plugins = [_ for _ in plugins if _ not in other_subargs]
        # print >> sys.stderr, "*", subargs
        return "\n".join(return_plugins)

    def calculation_gotocomputer(self, *args):
        """
        Open a shell to the calc folder on the cluster

        This command opens a ssh connection to the scratch folder on the remote
        computer on which the calculation is being/has been executed.
        """
        from aiida.common.exceptions import NotExistent
        if not is_dbenv_loaded():
            load_dbenv()

        try:
            calc_id = args[0]
        except IndexError:
            print >> sys.stderr, "Pass as further argument a calculation ID or UUID."
            sys.exit(1)
        try:
            pk = int(calc_id)
            is_pk = True
        except ValueError:
            uuid = calc_id
            is_pk = False

        print "Loading environment..."
        from aiida.orm import JobCalculation

        try:
            if is_pk:
                calc = load_node(pk)
            else:
                calc = load_node(uuid)
        except NotExistent:
            print >> sys.stderr, "No node exists with ID={}.".format(calc_id)
            sys.exit(1)

        if not isinstance(calc, JobCalculation):
            print >> sys.stderr, "Node with ID={} is not a calculation; it is a {}".format(
                calc_id, calc.__class__.__name__)
            sys.exit(1)

        # get the transport
        try:
            t = calc._get_transport()
        except NotExistent as e:
            print >> sys.stderr, e.message
            sys.exit(1)
        # get the remote directory
        remotedir = calc._get_remote_workdir()
        if not remotedir:
            print >> sys.stderr, "No remote work directory is set for this calculation!"
            print >> sys.stderr, "(It is possible that the daemon did not submit the calculation yet)"
            sys.exit(1)

        # get the command to run (does not require to open the connection!)
        cmd_to_run = t.gotocomputer_command(remotedir)
        # Connect (execute command)
        print "Going the the remote folder..."
        # print cmd_to_run
        os.system(cmd_to_run)

    def calculation_list(self, *args):
        """
        Return a list of calculations on screen.
        """
        if not is_dbenv_loaded():
            load_dbenv()

        from aiida.common.datastructures import calc_states

        import argparse
        from aiida.orm.calculation.job import JobCalculation as C

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='List AiiDA calculations.')
        # The default states are those that are shown if no option is given
        parser.add_argument('-s', '--states', nargs='+', type=str,
                            help="show only the AiiDA calculations with given state",
                            default=[calc_states.WITHSCHEDULER,
                                     calc_states.NEW,
                                     calc_states.TOSUBMIT,
                                     calc_states.SUBMITTING,
                                     calc_states.COMPUTED,
                                     calc_states.RETRIEVING,
                                     calc_states.PARSING,
                                     ])

        parser.add_argument('-p', '--past-days', metavar='N',
                            help="add a filter to show only calculations created in the past N days",
                            action='store', type=int)
        parser.add_argument('-g', '--group', '--group-name',
                            metavar='GROUPNAME',
                            help="add a filter to show only calculations within a given group",
                            action='store', type=str)
        parser.add_argument('-G', '--group-pk', metavar='GROUPPK',
                            help="add a filter to show only calculations within a given group",
                            action='store', type=int)
        parser.add_argument('pks', type=int, nargs='*',
                            help="a list of calculations to show. If empty, all running calculations are shown. If non-empty, ignores the -p and -r options.")
        parser.add_argument('-a', '--all-states',
                            dest='all_states', action='store_true',
                            help="Overwrite manual set of states if present, and look for calculations in every possible state")
        parser.set_defaults(all_states=False)
        parser.add_argument('-A', '--all-users',
                            dest='all_users', action='store_true',
                            help="Show calculations for all users, rather than only for the current user")
        parser.set_defaults(all_users=False)
        parser.add_argument('-t', '--absolute-time',
                            dest='relative_ctime', action='store_false', default=True,
                            help="Print the absolute creation time, rather than the relative creation time")
        parser.add_argument('-l', '--limit',
                            type=int, default=None,
                            help='set a limit to the number of rows returned')
        parser.add_argument('-o', '--order-by',
                            choices=['id', 'ctime'],
                            default='ctime',
                            help='order the results')
        parser.add_argument('--project',
                            choices=(
                                    'pk', 'state', 'ctime', 'sched', 'computer',
                                    'type', 'description', 'label', 'uuid',
                                    'mtime', 'user'
                                ),
                            nargs='+',
                            default=('pk', 'state', 'ctime', 'sched', 'computer', 'type'),
                            help="Define the list of properties to show"
                        )

        args = list(args)
        parsed_args = parser.parse_args(args)

        capital_states = [i.upper() for i in parsed_args.states]
        parsed_args.states = capital_states

        if parsed_args.all_states:
            parsed_args.states = None

        C._list_calculations(
            states=parsed_args.states,
            past_days=parsed_args.past_days,
            pks=parsed_args.pks,
            all_users=parsed_args.all_users,
            group=parsed_args.group,
            group_pk=parsed_args.group_pk,
            relative_ctime=parsed_args.relative_ctime,
            # with_scheduler_state=parsed_args.with_scheduler_state,
            order_by=parsed_args.order_by,
            limit=parsed_args.limit,
            projections=parsed_args.project,
        )

    def calculation_res(self, *args):
        """
        Print all or somoe data from the "res" output node.
        """
        from aiida.common.exceptions import NotExistent
        from aiida.cmdline import print_dictionary

        import argparse

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Show calculation results (from calc.res)')
        parser.add_argument('PK', type=int, default=None,
                            help="PK of the calculation object whose results "
                                 "must be shown.")
        parser.add_argument('-f', '--format', type=str, default='json+date',
                            help="Format for the output.")
        parser.add_argument('-k', '--keys', nargs='+', type=str,
                            help="Show only the selected keys.")
        args = list(args)
        parsed_args = parser.parse_args(args)

        if not is_dbenv_loaded():
            load_dbenv()

        try:
            calc = load_node(int(parsed_args.PK))
        except ValueError:
            print >> sys.stderr, "*** {}: Not a valid PK".format(parsed_args.PK)
            sys.exit(1)
        except NotExistent:
            print >> sys.stderr, "*** {}: Not a valid calculation".format(
                parsed_args.PK)
            sys.exit(1)

        full_dict = calc.res._get_dict()
        if parsed_args.keys:
            try:
                the_dict = {k: full_dict[k] for k in parsed_args.keys}
            except KeyError as e:
                print >> sys.stderr, ("The key '{}' was not found in the .res "
                                      "dictionary".format(e.message))
                sys.exit(1)
        else:
            # Return all elements
            the_dict = full_dict

        print_dictionary(the_dict, format=parsed_args.format)

    def calculation_show(self, *args):
        from aiida.common.exceptions import NotExistent
        from aiida.cmdline.common import print_node_info

        if not is_dbenv_loaded():
            load_dbenv()

        table_headers = ['Link label', 'PK', 'Type']
        for calc_pk in args:
            try:
                calc = load_node(int(calc_pk))
            except ValueError:
                print "*** {}: Not a valid PK".format(calc_pk)
                continue
            except NotExistent:
                print "*** {}: Not a valid calculation".format(calc_pk)
                continue

            print_node_info(calc)

    def calculation_logshow(self, *args):
        from aiida.common.exceptions import NotExistent
        from aiida.backends.utils import get_log_messages
        from aiida.common.datastructures import calc_states

        if not is_dbenv_loaded():
            load_dbenv()

        for calc_pk in args:
            try:
                calc = load_node(int(calc_pk))
            except ValueError:
                print "*** {}: Not a valid PK".format(calc_pk)
                continue
            except NotExistent:
                print "*** {}: Not a valid calculation".format(calc_pk)
                continue

            log_messages = get_log_messages(calc)
            label_string = " [{}]".format(calc.label) if calc.label else ""
            state = calc.get_state()
            if state == calc_states.WITHSCHEDULER:
                sched_state = calc.get_scheduler_state()
                if sched_state is None:
                    sched_state = "(unknown)"
                state += ", scheduler state: {}".format(sched_state)
            print "*** {}{}: {}".format(calc_pk, label_string, state)

            sched_out = calc.get_scheduler_output()
            sched_err = calc.get_scheduler_error()
            if sched_out is None:
                print "*** Scheduler output: N/A"
            elif sched_out:
                print "*** Scheduler output:"
                print sched_out
            else:
                print "*** (empty scheduler output file)"

            if sched_err is None:
                print "*** Scheduler errors: N/A"
            elif sched_err:
                print "*** Scheduler errors:"
                print sched_err
            else:
                print "*** (empty scheduler errors file)"

            if log_messages:
                print "*** {} LOG MESSAGES:".format(len(log_messages))
            else:
                print "*** 0 LOG MESSAGES"

            for log in log_messages:
                print "+-> {} at {}".format(log['levelname'], log['time'])
                # Print the message, with a few spaces in front of each line
                print "\n".join(["|   {}".format(_)
                                 for _ in log['message'].splitlines()])

    def calculation_plugins(self, *args):
        if not is_dbenv_loaded():
            load_dbenv()

        from aiida.orm import CalculationFactory
        from aiida.orm.calculation.job import JobCalculation
        from aiida.common.pluginloader import all_plugins
        from aiida.common.exceptions import MissingPluginError

        if args:
            for arg in args:
                try:
                    C = CalculationFactory(arg)
                    print "* {}".format(arg)
                    docstring = C.__doc__
                    if docstring is None:
                        docstring = "(No documentation available)"
                    docstring = docstring.strip()
                    print "\n".join(["    {}".format(_.strip())
                                     for _ in docstring.splitlines()])
                    print "  Inputs:"
                    for key, val in C._use_methods.iteritems():
                        print "    {}: {}".format(key,
                                                  val['valid_types'].__name__)
                    print("  Module location: {}".format(C.__module__))

                except MissingPluginError:
                    print "! {}: NOT FOUND!".format(arg)
        else:
            plugins = sorted(all_plugins('calculations'))
            if plugins:
                print("## Pass as a further parameter one (or more) "
                      "plugin names to get more details on a given plugin.")
                for plugin in plugins:
                    print "* {}".format(plugin)
            else:
                print "## No calculation plugins found"

    def calculation_inputcat(self, *args):
        """
        Show an input file of a calculation node.

        It shows the files in the raw_input subdirectory.
        Use the -h option for more help on the command line options.
        """
        from aiida.cmdline.commands.node import cat_repo_files
        from aiida.common.exceptions import NotExistent

        import argparse

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Output the content of a file in the repository folder.')
        parser.add_argument('calc', metavar='PK', type=int,
                            help='The pk of the calculation')
        parser.add_argument('-p', '--path', type=str, default=None, nargs='?',
                            help="The relative path of the file you "
                                 "want to show. Take the default input file if "
                                 "it is not specified")

        args = list(args)
        parsed_args = parser.parse_args(args)

        if not is_dbenv_loaded():
            load_dbenv()
        from aiida.common.old_pluginloader import get_class_typestring

        try:
            calc = load_node(parsed_args.calc)
        except NotExistent as e:
            print >> sys.stderr, e.message
            sys.exit(1)

        path = parsed_args.path
        if path is None:
            path = calc._DEFAULT_INPUT_FILE
            if path is None:
                base_class, plugin_string, class_name = get_class_typestring(
                    calc._plugin_type_string)
                print >> sys.stderr, ("Calculation '{}' does not define a "
                                      "default input file. Please specify a path "
                                      "explicitly".format(plugin_string))
                sys.exit(1)

        try:
            cat_repo_files(calc, os.path.join('raw_input', path))
        except ValueError as e:
            print >> sys.stderr, e.message
            sys.exit(1)
        except IOError as e:
            import errno
            # Ignore Broken pipe errors, re-raise everything else
            if e.errno == errno.EPIPE:
                pass
            else:
                raise

    def calculation_inputls(self, *args):
        """
        Show the list of input files of a calculation node.

        It shows the files in the raw_input subdirectory.
        Use the -h option for more help on the command line options.
        """
        import argparse
        from aiida.common.exceptions import NotExistent
        from aiida.cmdline.commands.node import list_repo_files

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='List input files in the repository folder.')

        parser.add_argument('calc', metavar='PK', type=int,
                            help='The pk of the calculation')
        parser.add_argument('-p', '--path', type=str, default='', nargs='?',
                            help="The relative path of the file you "
                                 "want to show. If not specified, show content"
                                 " of all the 'raw_input' directory")
        parser.add_argument('-c', '--color', action='store_true',
                            help="Color folders with a different color")

        args = list(args)
        parsed_args = parser.parse_args(args)

        if not is_dbenv_loaded():
            load_dbenv()

        try:
            calc = load_node(parsed_args.calc)
        except NotExistent as e:
            print >> sys.stderr, e.message
            sys.exit(1)

        try:
            list_repo_files(calc, os.path.join('raw_input', parsed_args.path),
                            parsed_args.color)
        except ValueError as e:
            print >> sys.stderr, e.message
            sys.exit(1)

    def calculation_outputls(self, *args):
        """
        Show the list of output files of a calculation node.

        It lists the files in the 'path' subdirectory of the output node
        of files retrieved by the parser. Therefore, this will not work
        before files are retrieved by the daemon.
        Use the -h option for more help on the command line options.
        """
        import argparse
        from aiida.common.exceptions import NotExistent
        from aiida.cmdline.commands.node import list_repo_files

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='List ourput files in the repository folder.')

        parser.add_argument('calc', metavar='PK', type=int,
                            help='The pk of the calculation')
        parser.add_argument('-p', '--path', type=str, default='', nargs='?',
                            help="The relative path of the file you "
                                 "want to show. If not specified, show content"
                                 " of all the 'path' directory")
        parser.add_argument('-c', '--color', action='store_true',
                            help="Color folders with a different color")

        args = list(args)
        parsed_args = parser.parse_args(args)

        if not is_dbenv_loaded():
            load_dbenv()

        try:
            calc = load_node(parsed_args.calc)
        except NotExistent as e:
            print >> sys.stderr, e.message
            sys.exit(1)

        try:
            parsed_node = calc.out.retrieved
        except AttributeError:
            print >> sys.stderr, ("No 'retrieved' node found. Have the "
                                  "calculation files already been retrieved?")
            sys.exit(1)

        try:
            list_repo_files(parsed_node,
                            os.path.join('path', parsed_args.path),
                            parsed_args.color)
        except ValueError as e:
            print >> sys.stderr, e.message
            sys.exit(1)

    def calculation_outputcat(self, *args):
        """
        Show an output file of a calculation node.

        It shows the files in the 'path' subdirectory of the output node
        of files retrieved by the parser. Therefore, this will not work
        before files are retrieved by the daemon.
        Use the -h option for more help on the command line options.
        """
        from aiida.cmdline.commands.node import cat_repo_files
        from aiida.common.exceptions import NotExistent

        import argparse

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Output the content of a file in the repository folder.')
        parser.add_argument('calc', metavar='PK', type=int,
                            help='The pk of the calculation')
        parser.add_argument('-p', '--path', type=str, default=None, nargs='?',
                            help="The relative path of the file you "
                                 "want to show. Take the default output file if "
                                 "it is not specified")
        args = list(args)
        parsed_args = parser.parse_args(args)

        if not is_dbenv_loaded():
            load_dbenv()
        from aiida.common.old_pluginloader import get_class_typestring

        try:
            calc = load_node(parsed_args.calc)
        except NotExistent as e:
            print >> sys.stderr, e.message
            sys.exit(1)

        path = parsed_args.path
        if path is None:
            path = calc._DEFAULT_OUTPUT_FILE
            if path is None:
                base_class, plugin_string, class_name = get_class_typestring(
                    calc._plugin_type_string)
                print >> sys.stderr, ("Calculation '{}' does not define a "
                                      "default output file. Please specify a path "
                                      "explicitly".format(plugin_string))
                sys.exit(1)

        try:
            parsed_node = calc.out.retrieved
        except AttributeError:
            print >> sys.stderr, ("No 'retrieved' node found. Have the "
                                  "calculation files already been retrieved?")
            sys.exit(1)

        try:
            cat_repo_files(parsed_node, os.path.join('path', path))
        except ValueError as e:
            print >> sys.stderr, e.message
            sys.exit(1)
        except IOError as e:
            import errno
            # Ignore Broken pipe errors, re-raise everything else
            if e.errno == errno.EPIPE:
                pass
            else:
                raise

    def calculation_kill(self, *args):
        """
        Kill a calculation.

        Pass a list of calculation PKs to kill them.
        If you also pass the -f option, no confirmation will be asked.
        """
        if not is_dbenv_loaded():
            load_dbenv()

        from aiida.cmdline import wait_for_confirmation
        from aiida.orm.calculation.job import JobCalculation as Calc
        from aiida.common.exceptions import NotExistent, InvalidOperation, \
            RemoteOperationError

        import argparse

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Kill AiiDA calculations.')
        parser.add_argument('calcs', metavar='PK', type=int, nargs='+',
                            help='The principal key (PK) of the calculations to kill')
        parser.add_argument('-f', '--force',
                            help='Force the kill of calculations',
                            action="store_true")
        args = list(args)
        parsed_args = parser.parse_args(args)

        if not parsed_args.force:
            sys.stderr.write(
                "Are you sure to kill {} calculation{}? [Y/N] ".format(
                    len(parsed_args.calcs),
                    "" if len(parsed_args.calcs) == 1 else "s"))
            if not wait_for_confirmation():
                sys.exit(0)

        counter = 0
        for calc_pk in parsed_args.calcs:
            try:
                c = load_node(calc_pk, parent_class=Calc)

                c.kill()  # Calc.kill(calc_pk)
                counter += 1
            except NotExistent:
                print >> sys.stderr, ("WARNING: calculation {} "
                                      "does not exist.".format(calc_pk))
            except (InvalidOperation, RemoteOperationError) as e:
                print >> sys.stderr, (e.message)
        print >> sys.stderr, "{} calculation{} killed.".format(counter,
                                                               "" if counter == 1 else "s")

    def calculation_cleanworkdir(self, *args):
        """
        Clean all the content of all the output remote folders of calculations,
        passed as a list of pks, or identified by modification time.

        If a list of calculation PKs is not passed through -c option, one of
        the option -p or -u has to be specified (if both are given, a logical
        AND is done between the 2 - you clean out calculations modified AFTER
        [-p option] days from now but BEFORE [-o option] days from now).
        If you also pass the -f option, no confirmation will be asked.
        """
        import argparse

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description="Clean work directory (i.e. remote folder) of AiiDA "
                        "calculations.")
        parser.add_argument("-k", "--pk", metavar="PK", type=int, nargs="+",
                            help="The principal key (PK) of the calculations "
                                 "to clean the workdir of", dest="pk")
        parser.add_argument("-f", "--force", action="store_true",
                            help="Force the cleaning (no prompt)")
        parser.add_argument("-p", "--past-days", metavar="N",
                            help="Add a filter to clean workdir of "
                                 "calculations modified during the past N "
                                 "days", type=int, action="store",
                            dest="past_days")
        parser.add_argument("-o", "--older-than", metavar="N",
                            help="Add a filter to clean workdir of "
                                 "calculations that have been modified on a "
                                 "date before N days ago", type=int,
                            action="store", dest="older_than")
        parser.add_argument("-c", "--computers", metavar="label", nargs="+",
                            help="Add a filter to clean workdir of "
                                 "calculations on this computer(s) only",
                            type=str, action="store", dest="computer")

        if not is_dbenv_loaded():
            load_dbenv()

        from aiida.backends.utils import get_automatic_user
        from aiida.backends.utils import get_authinfo
        from aiida.common.utils import query_yes_no
        from aiida.orm.computer import Computer as OrmComputer
        from aiida.orm.user import User as OrmUser
        from aiida.orm.calculation import Calculation as OrmCalculation
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.utils import timezone
        import datetime

        parsed_args = parser.parse_args(args)

        # If a pk is given then the -o & -p options should not be specified
        if parsed_args.pk is not None:
            if ((parsed_args.past_days is not None) or
                    (parsed_args.older_than is not None)):
                print("You cannot specify both a list of calculation pks and "
                      "the -p or -o options")
                return
        # If no pk is given then at least one of the -o & -p options should be
        # specified
        else:
            if ((parsed_args.past_days is None) and
                    (parsed_args.older_than is None)):
                print("You should specify at least a list of calculations or "
                      "the -p, -o options")
                return

        # At this point we know that either the pk or the -p -o options are
        # specified

        # We also check that not both -o & -p options are specified
        if ((parsed_args.past_days is not None) and
                (parsed_args.older_than is not None)):
            print("Not both of the -p, -o options can be specified in the "
                  "same time")
            return

        qb_user_filters = dict()
        user = OrmUser(dbuser=get_automatic_user())
        qb_user_filters["email"] = user.email

        qb_computer_filters = dict()
        if parsed_args.computer is not None:
            qb_computer_filters["name"] = {"in": parsed_args.computer}

        qb_calc_filters = dict()
        if parsed_args.past_days is not None:
            pd_ts = timezone.now() - datetime.timedelta(
                days=parsed_args.past_days)
            qb_calc_filters["mtime"] = {">": pd_ts}
        if parsed_args.older_than is not None:
            ot_ts = timezone.now() - datetime.timedelta(
                days=parsed_args.older_than)
            qb_calc_filters["mtime"] = {"<": ot_ts}
        if parsed_args.pk is not None:
            print("parsed_args.pk: ", parsed_args.pk)
            qb_calc_filters["id"] = {"in": parsed_args.pk}

        qb = QueryBuilder()
        qb.append(OrmCalculation, tag="calc",
                  filters=qb_calc_filters,
                  project=["id", "uuid", "attributes.remote_workdir"])
        qb.append(OrmComputer, computer_of="calc",
                  project=["*"],
                  filters=qb_computer_filters)
        qb.append(OrmUser, creator_of="calc",
                  project=["*"],
                  filters=qb_user_filters)

        no_of_calcs = qb.count()
        if no_of_calcs == 0:
            print("No calculations found with the given criteria.")
            return

        print("Found {} calculations with the given criteria.".format(
            no_of_calcs))

        if not parsed_args.force:
            if not query_yes_no("Are you sure you want to clean the work "
                                "directory?", "no"):
                return

        # get the uuids of all calculations matching the filters
        calc_list_data = qb.dict()

        # get all computers associated to the calc uuids above, and load them
        # we group them by uuid to avoid computer duplicates
        comp_uuid_to_computers = {_["computer"]["*"].uuid: _["computer"]["*"] for _ in calc_list_data}

        # now build a dictionary with the info of folders to delete
        remotes = {}
        for computer in comp_uuid_to_computers.values():
            # initialize a key of info for a given computer
            remotes[computer.name] = {'transport': get_authinfo(
                computer=computer, aiidauser=user._dbuser).get_transport(),
                                      'computer': computer,
            }

            # select the calc pks done on this computer
            this_calc_pks = [_["calc"]["id"] for _ in calc_list_data
                             if _["computer"]["*"].id == computer.id]

            this_calc_uuids = [unicode(_["calc"]["uuid"])
                               for _ in calc_list_data
                               if _["computer"]["*"].id == computer.id]

            remote_workdirs = [_["calc"]["attributes.remote_workdir"]
                               for _ in calc_list_data
                               if _["calc"]["id"] in this_calc_pks
                               if _["calc"]["attributes.remote_workdir"]
                               is not None]

            remotes[computer.name]['remotes'] = remote_workdirs
            remotes[computer.name]['uuids'] = this_calc_uuids

        # now proceed to cleaning
        for computer, dic in remotes.iteritems():
            print("Cleaning the work directory on computer {}.".format(computer))
            counter = 0
            t = dic['transport']
            with t:
                remote_user = remote_user = t.whoami()
                aiida_workdir = dic['computer'].get_workdir().format(
                    username=remote_user)

                t.chdir(aiida_workdir)
                # Hardcoding the sharding equal to 3 parts!
                existing_folders = t.glob('*/*/*')

                folders_to_delete = [i for i in existing_folders if
                                     i.replace("/", "") in dic['uuids']]

                for folder in folders_to_delete:
                    t.rmtree(folder)
                    counter += 1
                    if counter % 20 == 0 and counter > 0:
                        print("Deleted work directories: {}".format(counter))

            print("{} remote folder(s) cleaned.".format(counter))
