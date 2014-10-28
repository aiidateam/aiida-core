# -*- coding: utf-8 -*-
import sys
import os
import subprocess
from aiida import load_dbenv

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands


__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

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
        self.valid_subcommands = {
            'list': (self.calculation_list, self.complete_none),
            'logshow': (self.calculation_logshow, self.complete_none),
            'kill': (self.calculation_kill, self.complete_none),
            'inputls': (self.calculation_inputls, self.complete_none),
            'outputls': (self.calculation_outputls, self.complete_none),
            'inputcat': (self.calculation_inputcat, self.complete_none),
            'outputcat': (self.calculation_outputcat, self.complete_none),
            'show': (self.calculation_show, self.complete_none),
            'plugins': (self.calculation_plugins, self.complete_plugins),
            }
    
    def complete_plugins(self, subargs_idx, subargs):
        from aiida.common.pluginloader import existing_plugins
        from aiida.orm import Calculation as OrmCalculation
        
        plugins = sorted(existing_plugins(OrmCalculation,
                                          'aiida.orm.calculation'))
        # Do not return plugins that are already on the command line
        other_subargs = subargs[:subargs_idx] + subargs[subargs_idx+1:]
        return_plugins = [_ for _ in plugins if _ not in other_subargs]
#        print >> sys.stderr, "*", subargs
        return "\n".join(return_plugins)

    def calculation_list(self, *args):
        """
        Return a list of calculations on screen. 
        """
        load_dbenv()
        from aiida.common.datastructures import calc_states
        
        import argparse
        from aiida.orm.calculation import Calculation as C
        
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
        parser.add_argument('-g', '--group', metavar='GROUPNAME', 
                            help="add a filter to show only calculations within a given group",
                            action='store', type=str)
        parser.add_argument('pks', type=int, nargs='*',
                            help="a list of calculations to show. If empty, all running calculations are shown. If non-empty, ignores the -p and -r options.")
        parser.add_argument('-a', '--all-states',
                            dest='all_states',action='store_true',
                            help="Overwrite manual set of states if present, and look for calculations in every possible state")
        parser.set_defaults(all_states=False)
        parser.add_argument('-A', '--all-users',
                            dest='all_users',action='store_true',
                            help="Show calculations for all users, rather than only for the current user")
        parser.set_defaults(all_users=False)
        parser.add_argument('-t', '--absolute-time',
                            dest='relative_ctime',action='store_false',
                            help="Print the absolute creation time, rather than the relative creation time")
        parser.set_defaults(relative_ctime=True)
        
        args = list(args)
        parsed_args = parser.parse_args(args)
        
        capital_states = [i.upper() for i in parsed_args.states]
        parsed_args.states = capital_states
        
        if parsed_args.all_states:
            parsed_args.states = None
        
        print C._list_calculations(states=parsed_args.states,
                                     past_days=parsed_args.past_days, 
                                     pks=parsed_args.pks,
                                     all_users=parsed_args.all_users,
                                     group=parsed_args.group,
                                     relative_ctime=parsed_args.relative_ctime) 
    
    def calculation_show(self, *args):
        from aiida.common.exceptions import NotExistent
        from aiida.orm import Calculation as OrmCalculation
        from aiida.djsite.utils import get_log_messages
        
        load_dbenv()
        
        for calc_pk in args:
            try:
                calc = OrmCalculation.get_subclass_from_pk(int(calc_pk))
            except ValueError:
                print "*** {}: Not a valid PK".format(calc_pk)
                continue
            except NotExistent:
                print "*** {}: Not a valid calculation".format(calc_pk)
                continue
            print "*** {} [{}]".format(calc_pk, calc.label)
            code = calc.get_code()
            if code is not None:
                print "Using code: {}".format(code.label)
            print "##### INPUTS:"
            for k, v in calc.get_inputdata_dict().iteritems():
                print k, v.pk, v.__class__.__name__
            print "##### OUTPUTS:"
            for k, v in calc.get_outputs(also_labels=True):
                print k, v.pk, v.__class__.__name__
            log_messages = get_log_messages(calc)
            if log_messages:
                print ("##### NOTE! There are {} log messages for this "
                       "calculation.".format(len(log_messages)))
                print "      Use the 'calculation logshow' command to see them."
            if len(args)>1:
                print ""
 
    def calculation_logshow(self, *args):
        from aiida.common.exceptions import NotExistent
        from aiida.orm import Calculation as OrmCalculation
        from aiida.djsite.utils import get_log_messages
        from aiida.common.datastructures import calc_states
        
        load_dbenv()
        
        for calc_pk in args:
            try:
                calc = OrmCalculation.get_subclass_from_pk(int(calc_pk))
            except ValueError:
                print "*** {}: Not a valid PK".format(calc_pk)
                continue
            except NotExistent:
                print "*** {}: Not a valid calculation".format(calc_pk)
                continue

            log_messages = get_log_messages(calc)
            label_string =  " [{}]".format(calc.label) if calc.label else ""
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
        from aiida.orm import Calculation as OrmCalculation, CalculationFactory
        from aiida.common.pluginloader import existing_plugins
        from aiida.common.exceptions import MissingPluginError
        
        load_dbenv()
        
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
                except MissingPluginError:
                    print "! {}: NOT FOUND!".format(arg)
        else:
            plugins = sorted(existing_plugins(OrmCalculation,
                                              'aiida.orm.calculation'))
            if plugins:                
                print "## Pass as a further parameter one (or more) plugin names"
                print "## to get more details on a given plugin."
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
        parser.add_argument('-p', '--pk', type=int, required=True, 
                            help='The pk of the node')
        parser.add_argument('-d', '--default', action='store_true', 
                            help="Open the default output file, if specified "
                            "by the Calculation plugin. If specified, do not "
                            "pass any 'path'")
        parser.add_argument('path', type=str, default=None, nargs='?',
                            help='The relative path of the file you '
                            'want to show. You must specify it if you do not '
                            'pass the --default flag')
        
        args = list(args)
        parsed_args = parser.parse_args(args)

        if parsed_args.default and parsed_args.path:
            sys.stderr.write(parser.format_usage())
            sys.stderr.write("{}: error: If you pass --default, "
                "you cannot pass also a path.\n".format(
                    self.get_full_command_name()))
            sys.exit(1)
            
        if not parsed_args.default and not parsed_args.path:
            sys.stderr.write(parser.format_usage())
            sys.stderr.write("{}: error: pass either --default "
                "or a path.\n".format(
                    self.get_full_command_name()))
            sys.exit(1)

        load_dbenv()
        from aiida.orm import Calculation as OrmCalculation        
        from aiida.common.pluginloader import get_class_typestring
        
        try:
            n = OrmCalculation.get_subclass_from_pk(parsed_args.pk)
        except NotExistent as e:
            print >> sys.stderr, e.message
            sys.exit(1)

        path = parsed_args.path
        if parsed_args.default:
            path = n._DEFAULT_INPUT_FILE
            if path is None:
                base_class, plugin_string, class_name = get_class_typestring(
                    n._plugin_type_string)
                print >> sys.stderr, ("Calculation '{}' does not define a "
                    "default input file. Please specify a path "
                    "explicitly".format(plugin_string))
                sys.exit(1)
        
        try:
            cat_repo_files(n, os.path.join('raw_input', path))
        except ValueError as e:
            print >> sys.stderr, e.message
            sys.exit(1)

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

        parser.add_argument('-c','--color', action='store_true',
                            help="Color folders with a different color")
        parser.add_argument('-p', '--pk', type=int, required=True, 
                            help='The pk of the node')
        parser.add_argument('path', type=str, default='.', nargs='?',
                            help='The relative path of the file you '
                            'want to show')
        
        args = list(args)
        parsed_args = parser.parse_args(args)

        load_dbenv()
        from aiida.orm import Node as OrmNode        
        
        try:
            n = OrmNode.get_subclass_from_pk(parsed_args.pk)
        except NotExistent as e:
            print >> sys.stderr, e.message
            sys.exit(1)
        
        try:
            list_repo_files(n, os.path.join('raw_input', parsed_args.path),
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

        parser.add_argument('-c','--color', action='store_true',
                            help="Color folders with a different color")
        parser.add_argument('-p', '--pk', type=int, required=True, 
                            help='The pk of the node')
        parser.add_argument('path', type=str, default='.', nargs='?',
                            help='The relative path of the file you '
                            'want to show')
        
        args = list(args)
        parsed_args = parser.parse_args(args)

        load_dbenv()
        from aiida.orm import Node as OrmNode        
        
        try:
            n = OrmNode.get_subclass_from_pk(parsed_args.pk)
        except NotExistent as e:
            print >> sys.stderr, e.message
            sys.exit(1)

        try:
            parsed_node = n.out.retrieved
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
        parser.add_argument('-p', '--pk', type=int, required=True, 
                            help='The pk of the node')
        parser.add_argument('-d', '--default', action='store_true', 
                            help="Open the default output file, if specified "
                            "by the Calculation plugin. If specified, do not "
                            "pass any 'path'")
        parser.add_argument('path', type=str, default=None, nargs='?',
                            help='The relative path of the file you '
                            'want to show. You must specify it if you do not '
                            'pass the --default flag')
        args = list(args)
        parsed_args = parser.parse_args(args)

        if parsed_args.default and parsed_args.path:
            sys.stderr.write(parser.format_usage())
            sys.stderr.write("{}: error: If you pass --default, "
                "you cannot pass also a path.\n".format(
                    self.get_full_command_name()))
            sys.exit(1)
            
        if not parsed_args.default and not parsed_args.path:
            sys.stderr.write(parser.format_usage())
            sys.stderr.write("{}: error: pass either --default "
                "or a path.\n".format(
                    self.get_full_command_name()))
            sys.exit(1)
        
        load_dbenv()
        from aiida.orm import Calculation as OrmCalculation        
        from aiida.common.pluginloader import get_class_typestring
        
        try:
            n = OrmCalculation.get_subclass_from_pk(parsed_args.pk)
        except NotExistent as e:
            print >> sys.stderr, e.message
            sys.exit(1)

        path = parsed_args.path
        if parsed_args.default:
            path = n._DEFAULT_OUTPUT_FILE
            if path is None:
                base_class, plugin_string, class_name = get_class_typestring(
                    n._plugin_type_string)
                print >> sys.stderr, ("Calculation '{}' does not define a "
                    "default output file. Please specify a path "
                    "explicitly".format(plugin_string))
                sys.exit(1)

        try:
            parsed_node = n.out.retrieved
        except AttributeError:
            print >> sys.stderr, ("No 'retrieved' node found. Have the "
                "calculation files already been retrieved?")
            sys.exit(1)
        
        try:
            cat_repo_files(parsed_node, os.path.join('path', path))
        except ValueError as e:
            print >> sys.stderr, e.message
            sys.exit(1)
    
    def calculation_kill(self, *args):
        """
        Kill a calculation. 
        
        Pass a list of calculation PKs to kill them.
        If you also pass the -f option, no confirmation will be asked.
        """
        from aiida import load_dbenv
        load_dbenv()
        
        from aiida.cmdline import wait_for_confirmation
        from aiida.orm.calculation import Calculation as Calc
        from aiida.common.exceptions import NotExistent,InvalidOperation
        
        import argparse
        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Kill AiiDA calculations.')
        parser.add_argument('calcs', metavar='PK', type=int, nargs='+',
                            help='The principal key (PK) of the calculations to kill')
        parser.add_argument('-f','--force', help='Force the kill of calculations',
                            action="store_true")
        args = list(args)
        parsed_args = parser.parse_args(args)
                
        if not parsed_args.force:
            sys.stderr.write("Are you sure to kill {} calculation{}? [Y/N] ".format(
                len(parsed_args.calcs), "" if len(parsed_args.calcs)==1 else "s"))
            if not wait_for_confirmation():
                sys.exit(0)
        
        counter = 0
        for calc_pk in parsed_args.calcs:
            try:
                c = Calc.get_subclass_from_pk(calc_pk)
                c.kill() # Calc.kill(calc_pk)
                counter += 1
            except NotExistent:
                print >> sys.stderr, ("WARNING: calculation {} "
                    "does not exist.".format(calc_pk))
            except InvalidOperation:
                print  >> sys.stderr, ("Calculation {} is not in WITHSCHEDULER "
                    "state: cannot be killed.".format(calc_pk))
        print >> sys.stderr, "{} calculation{} killed.".format(counter,
            "" if counter==1 else "s")

    
