import sys

from aiida.cmdline.baseclass import VerdiCommand
from aiida.common.utils import load_django

class Upf(VerdiCommand):
    """
    Setup and manage upf to be used

    This command allows to list and configure upf.
    """
    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        self.valid_subcommands = {
            'upload_family': (self.upload_family, self.complete_none)
            }

    def run(self,*args):       
        try:
            function_to_call = self.valid_subcommands[args[0]][0]
        except IndexError:
            function_to_call = self.no_subcommand
        except KeyError:
            function_to_call = self.invalid_subcommand
            
        function_to_call(*args[1:])

    def complete(self,subargs_idx, subargs):
        if subargs_idx == 0:
            print "\n".join(self.valid_subcommands.keys())
        elif subargs_idx == 1:
            try:
                first_subarg = subargs[0]
            except  IndexError:
                first_subarg = ''
            try:
                complete_function = self.valid_subcommands[first_subarg][1] 
            except KeyError:
                print ""
                return
            print complete_function()

    def complete_none(self):
        return ""
        
    def no_subcommand(self,*args):
        print >> sys.stderr, ("You have to pass a valid subcommand to "
                              "'upf'. Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    def invalid_subcommand(self):
        print >> sys.stderr, ("You passed an invalid subcommand to 'upf'. "
                              "Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    #
    #
    #
    
    def upload_family(self, *args):
        """
        Setup a new or existing computer
        """
        import inspect
        import readline
        import os.path
        
        from aiida.common.exceptions import NotExistent, ValidationError
        from aiida.orm import Computer as AiidaOrmComputer
        
        if not len(args) == 3 and not len(args) == 4:
            print >> sys.stderr, ("\n after 'upf upload_family' there should be three "
                                  "arguments: folder, group_name, group_description [optional --stop_if_existing]\n")
            sys.exit(1)
        
        folder            = os.path.abspath(args[0])
        group_name        = args[1]
        group_description = args[2]
        stop_if_existing  = False
        
        if len(args)==4:
            if args[3]=="--stop_if_existing":
                stop_if_existing  = True
            else:
                raise ValidationError('Unknown directive: '+args[3])
        
        if (not os.path.isdir(folder)):
            raise ValidationError('Cannot find diretory: '+folder)
        
        load_django()
        
        import aiida.orm.data.upf as upfd
        upfd.upload_upf_family(folder, group_name, group_description, stop_if_existing)
        
        
        
     