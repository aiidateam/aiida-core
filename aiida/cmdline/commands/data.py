import sys

from aiida.cmdline.baseclass import VerdiCommand
from aiida.common.utils import load_django

class Data(VerdiCommand):
    """
    Setup and manage data specific types
    
    There is a list of subcommands for managing specific types of data.
    For instance, 'data upf' manages pseudopotentials in the UPF format.
    """
    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        
        ## Add here the classes to be supported.
        self.valid_subcommands = {
            'upf': _Upf,
            }

    def no_subcommand(self,*args):
        print >> sys.stderr, ("You have to pass a valid subcommand to "
                              "'data'. Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    def invalid_subcommand(self,*args):
        print >> sys.stderr, ("You passed an invalid subcommand to 'data'. "
                              "Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    def run(self,*args):       
        try:
            function_to_call = self.valid_subcommands[args[0]]().run
        except IndexError:
            function_to_call = self.no_subcommand
        except KeyError:
            function_to_call = self.invalid_subcommand
            
        function_to_call(*args[1:])

    def complete(self,subargs_idx, subargs):
        if subargs_idx == 0:
            print "\n".join(self.valid_subcommands.keys())
        elif subargs_idx >= 1:
            try:
                first_subarg = subargs[0]
            except  IndexError:
                first_subarg = ''
            try:
                complete_function = self.valid_subcommands[first_subarg]().complete 
            except KeyError:
                print ""
                return
            complete_function(subargs_idx - 1, subargs[1:])

        
# Note: this class should not be exposed directly in the main module,
# otherwise it becomes a command of 'verdi'. Instead, we want it to be a 
# subcommand of verdi data.
class _Upf(VerdiCommand):
    """
    Setup and manage upf to be used

    This command allows to list and configure upf.
    """
    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        self.valid_subcommands = {
            'uploadfamily': (self.uploadfamily, self.complete_auto),
            'listfamilies': (self.listfamilies, self.complete_none),
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
            complete_data = complete_function()
            if complete_data is not None:
                print complete_data

    def complete_none(self):
        return ""

    def complete_auto(self):
        return None
        
    def no_subcommand(self,*args):
        print >> sys.stderr, ("You have to pass a valid subcommand to "
                              "'upf'. Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    def invalid_subcommand(self,*args):
        print >> sys.stderr, ("You passed an invalid subcommand to 'upf'. "
                              "Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    #
    #
    #
    
    def uploadfamily(self, *args):
        """
        Upload a new pseudopotential family.
        
        Call without parameters to get some help.
        """
        import inspect
        import readline
        import os.path
        
        from aiida.common.exceptions import NotExistent, ValidationError
        from aiida.orm import Computer as AiidaOrmComputer
        
        if not len(args) == 3 and not len(args) == 4:
            print >> sys.stderr, ("\n after 'upf uploadfamily' there should be three "
                                  "arguments: folder, group_name, group_description [optional --stop-if-existing]\n")
            sys.exit(1)
        
        folder            = os.path.abspath(args[0])
        group_name        = args[1]
        group_description = args[2]
        stop_if_existing  = False
        
        if len(args)==4:
            if args[3]=="--stop-if-existing":
                stop_if_existing  = True
            else:
                print >> sys.stderr, 'Unknown directive: '+args[3]
                sys.exit(1)
        
        if (not os.path.isdir(folder)):
            print >> sys.stderr, 'Cannot find directory: '+folder
            sys.exit(1)
            
        load_django()
        
        import aiida.orm.data.upf as upf
        upf.upload_upf_family(folder, group_name, 
                              group_description, stop_if_existing)
        

    def listfamilies(self, *args):
        """
        Print on screen the list of upf families installed
        """
        # note that the following command requires that the upfdata has a
        # key called element. As such, it is not well separated.
        import argparse
        parser = argparse.ArgumentParser(description='List AiiDA workflows.')
        parser.add_argument('-e','--element',nargs='+', type=str, default=None)
        
        args = list(args)
        parsed_args = parser.parse_args(args)

        load_django()
        
        from aiida.orm import DataFactory
        
        
        UpfData = DataFactory('upf')
        
        groups = UpfData.get_upf_groups(filter_elements=parsed_args.element)
            
        if groups:
            for g in groups:
                pseudos = UpfData.query(dbgroups__name=g.name).distinct()
                num_pseudos = pseudos.count()

                pseudos_list = pseudos.filter(
                                      dbattributes__key="_element").values_list(
                                      'dbattributes__tval', flat=True)
                
                new_ps = pseudos.filter(
                                dbattributes__key="_element").values_list(
                                'dbattributes__tval', flat=True)
                
                if num_pseudos != len(set(pseudos_list)):
                    print ("x {} [INVALID: {} pseudos, for {} elements]"
                           .format(g.name,num_pseudos,len(set(pseudos_list))))
                    print ("  Maybe the pseudopotential family wasn't "
                           "setup with the uploadfamily function?")

                else:
                     print "* {} [{} pseudos]".format(g.name, num_pseudos)
        else:
            print "No valid UPF pseudopotential family found."
         
            
        
    
  
     
