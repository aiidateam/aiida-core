import sys
import os
import subprocess

from aiida.cmdline.baseclass import VerdiCommand


class Calculation(VerdiCommand):
    """
    Manage the AiiDA calculation manager
    
    Valid subcommands are:
    * list: list the running calculations running and their state. Pass a -h
            option for further help on valid options.
    * kill: kill a given calculation
    """


    def __init__(self):
        """
        A dictionary with valid commands and functions to be called:
        list.
        """
        self.valid_subcommands = {
            'list': self.calculation_list,
            'kill': self.calculation_kill,
            }

    def run(self,*args):       
        """
        Run the specified workflow subcommand.
        """
        try:
            function_to_call = self.valid_subcommands.get(
                args[0], self.invalid_subcommand)
        except IndexError:
            function_to_call = self.no_subcommand
            
        function_to_call(*args[1:])

    def complete(self,subargs_idx, subargs):
        """
        Complete the calculation subcommand.
        """
        if subargs_idx == 0:
            print "\n".join(self.valid_subcommands.keys())
        else:
            print ""

    def no_subcommand(self):
        print >> sys.stderr, ("You have to pass a valid subcommand to "
                              "'workflow'. Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    def invalid_subcommand(self,*args):
        print >> sys.stderr, ("You passed an invalid subcommand to 'workflow'. "
                              "Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

        
    def calculation_list(self, *args):
        """
        Return a list of calculations on screen. 
        """
        from aiida.common.utils import load_django
        load_django()
        
        import argparse
        from aiida.orm.calculation import Calculation as calc
        
        parser = argparse.ArgumentParser(description='List AiiDA calculations.')
        parser.add_argument('-s', '--only-state', type=str,
                            help="show only the AiiDA calculations with given state")
        parser.add_argument('-p', '--past-days', metavar='N', help="add a filter to show only calculations created in the past N days",
                            action='store', type=int)
        parser.add_argument('pks', type=int, nargs='*',
                            help="a list of calculations to show. If empty, all running calculations are shown. If non-empty, ignores the -p and -r options.")
        
        args = list(args)
        parsed_args = parser.parse_args(args)
        
        print calc.list_calculations(only_state=parsed_args.only_state,
                                     past_days=parsed_args.past_days, 
                                     pks=parsed_args.pks) 
    
    def calculation_kill(self, *args):
        """
        Kill a calculation. 
        
        Pass a list of workflow PKs to kill them.
        If you also pass the -f option, no confirmation will be asked.
        """
        from aiida.common.utils import load_django
        load_django()
        
        from aiida.cmdline import wait_for_confirmation
        from aiida.orm.calculation import Calculation as Calc
        from aiida.common.exceptions import NotExistent
        
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
        print >> sys.stderr, "{} calculation{} killed.".format(counter,
            "" if counter==1 else "s")

    