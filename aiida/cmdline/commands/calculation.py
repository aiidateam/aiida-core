import sys
import os
import subprocess
from aiida.common.utils import load_django

from aiida.cmdline.baseclass import VerdiCommand


class Calculation(VerdiCommand):
    """
    Query and interact with calculations
    
    Valid subcommands are:
    * kill:    kill a given calculation
    * list:    list the running calculations running and their state. Pass a -h
    |          option for further help on valid options.
    * logshow: show the log messages for a given calculation
    * plugins: list (and describe) the existing available calculation plugins
    * show:    show more details on a given calculation
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
            'show': (self.calculation_show, self.complete_none),
            'plugins': (self.calculation_plugins, self.complete_plugins),
            }

    def run(self,*args):       
        """
        Run the specified subcommand.
        """
        try:
            function_to_call = self.valid_subcommands[args[0]][0]
        except IndexError:
            function_to_call = self.no_subcommand
        except KeyError:
            function_to_call = self.invalid_subcommand
            
        function_to_call(*args[1:])

    def complete_none(self, subargs_idx, subargs):
        return ""
    
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

    def complete(self,subargs_idx, subargs):
        if subargs_idx == 0:
            print "\n".join(self.valid_subcommands.keys())
        else: # >=1 
            try:
                first_subarg = subargs[0]
            except  IndexError:
                first_subarg = ''
            try:
                complete_function = self.valid_subcommands[first_subarg][1] 
            except KeyError:
                print ""
                return
            print complete_function(subargs_idx-1, subargs[1:])

    def no_subcommand(self):
        print >> sys.stderr, ("You have to pass a valid subcommand to "
                              "'calculation'. Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    def invalid_subcommand(self,*args):
        print >> sys.stderr, ("You passed an invalid subcommand to 'calculation'. "
                              "Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

        
    def calculation_list(self, *args):
        """
        Return a list of calculations on screen. 
        """
        load_django()
        from aiida.common.datastructures import calc_states
        
        import argparse
        from aiida.orm.calculation import Calculation as C
        
        parser = argparse.ArgumentParser(description='List AiiDA calculations.')
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
        parser.add_argument('pks', type=int, nargs='*',
                            help="a list of calculations to show. If empty, all running calculations are shown. If non-empty, ignores the -p and -r options.")
        parser.add_argument('-a', '--all-states',
                            dest='all_states',action='store_true',
                            help="Overwrite manual set of states if present, and look for calculations in every possible state")
        parser.set_defaults(all_states=False)
        
        args = list(args)
        parsed_args = parser.parse_args(args)
        
        capital_states = [i.upper() for i in parsed_args.states]
        parsed_args.states = capital_states
        
        if parsed_args.all_states:
            parsed_args.states = [ i for i in calc_states ]
        
        print C.list_calculations(states=parsed_args.states,
                                     past_days=parsed_args.past_days, 
                                     pks=parsed_args.pks) 
    
    def calculation_show(self, *args):
        from aiida.common.exceptions import NotExistent
        from aiida.orm import Calculation as OrmCalculation
        from aiida.djsite.utils import get_log_messages
        
        load_django()
        
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
 
    def calculation_logshow(self, *args):
        from aiida.common.exceptions import NotExistent
        from aiida.orm import Calculation as OrmCalculation
        from aiida.djsite.utils import get_log_messages
        
        load_django()
        
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
            print "*** {}{}: {} log messages".format(
                calc_pk, label_string, len(log_messages))
            for log in log_messages:
                print "+-> {} at {}".format(log['levelname'], log['time'])
                # Print the message, with a few spaces in front of each line
                print "\n".join(["|   {}".format(_)
                                 for _ in log['message'].splitlines()])

 
    def calculation_plugins(self, *args):
        from aiida.orm import Calculation as OrmCalculation, CalculationFactory
        from aiida.common.pluginloader import existing_plugins
        from aiida.common.exceptions import MissingPluginError
        
        load_django()
        
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
                
    
    def calculation_kill(self, *args):
        """
        Kill a calculation. 
        
        Pass a list of calculation PKs to kill them.
        If you also pass the -f option, no confirmation will be asked.
        """
        from aiida.common.utils import load_django
        load_django()
        
        from aiida.cmdline import wait_for_confirmation
        from aiida.orm.calculation import Calculation as Calc
        from aiida.common.exceptions import NotExistent,InvalidOperation
        
        import argparse
        parser = argparse.ArgumentParser(description='List of AiiDA calculations pks.')
        parser.add_argument('calcs', metavar='N', type=int, nargs='+',
                            help='an integer for the accumulator')
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

    
