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
                print >> sys.stderr, 'Unknown directive: '+args[3]
                sys.exit(1)
        
        if (not os.path.isdir(folder)):
            print >> sys.stderr, 'Cannot find directory: '+folder
            sys.exit(1)
            
        load_django()
        
        import aiida.orm.data.upf as upfd
        upfd.upload_upf_family(folder, group_name, group_description, stop_if_existing)
        

    def listfamilies(self, *args):
        """
        Setup a new or existing computer
        """
        
        if args:
            print >> sys.stderr, ("after 'upf listfamilies' there should be "
                                  "no parameters")
            sys.exit(1)

        load_django()
        
        from aiida.orm import DataFactory
        from aiida.djsite.db.models import Group
        
        UpfData = DataFactory('upf')
        
        # All groups that contain at least one upf
        groups = Group.objects.filter(
             dbnodes__type__startswith=UpfData._plugin_type_string,
             ).distinct().order_by('name')
        
        if groups:
            for g in groups:
#                match = UpfData.query(groups__name=g.name,
#                                      attributes__key="_element",
#                                      attributes__tval=element)
                pseudos = UpfData.query(groups__name=g.name).distinct()
                num_pseudos = pseudos.count()

                pseudos_list = pseudos.filter(
                    attributes__key="_element").values_list(
                    'attributes__tval', flat=True)
                
                if num_pseudos != len(set(pseudos_list)):
                    print ("x {} [INVALID: {} pseudos, "
                           "but only for {} different elements]".format(
                                g.name, num_pseudos, len(set(pseudos_list))))
                else:
                    print "* {} [{} pseudos]".format(g.name, num_pseudos)
        else:
            print "No valid UPF pseudopotential families found."
        
        
     
