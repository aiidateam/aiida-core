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
            'structure': _Structure,
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
        
        Returns the numbers of files found and the number of nodes uploaded.
        
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
        files_found, files_uploaded = upf.upload_upf_family(folder, group_name, 
                                                            group_description, stop_if_existing)
        
        print "UPF files found: {}. New files uploaded: {}".format(files_found,files_uploaded)
        

    def listfamilies(self, *args):
        """
        Print on screen the list of upf families installed
        """
        # note that the following command requires that the upfdata has a
        # key called element. As such, it is not well separated.
        import argparse
        
        from aiida.orm.data.upf import UPFGROUP_TYPE
        
        parser = argparse.ArgumentParser(description='List AiiDA upf families.')
        parser.add_argument('-e','--element',nargs='+', type=str, default=None,
                            help="Filter the families only to those containing "
                                 "a pseudo for each of the specified elements")
        parser.add_argument('-d', '--with-description',
                            dest='with_description',action='store_true',
                            help="Show also the description for the UPF family")
        parser.set_defaults(with_description=False)
        
        args = list(args)
        parsed_args = parser.parse_args(args)

        load_django()
        
        from aiida.orm import DataFactory
        
        
        UpfData = DataFactory('upf')
        
        groups = UpfData.get_upf_groups(filter_elements=parsed_args.element)
            
        if groups:
            for g in groups:
                pseudos = UpfData.query(dbgroups=g.dbgroup).distinct()
                num_pseudos = pseudos.count()

                pseudos_list = pseudos.filter(
                                      dbattributes__key="element").values_list(
                                      'dbattributes__tval', flat=True)
                
                new_ps = pseudos.filter(
                                dbattributes__key="element").values_list(
                                'dbattributes__tval', flat=True)
                
                if parsed_args.with_description:
                    description_string = ": {}".format(g.description)
                else:
                    description_string = ""
                
                if num_pseudos != len(set(pseudos_list)):
                    print ("x {} [INVALID: {} pseudos, for {} elements]{}"
                           .format(g.name,num_pseudos,len(set(pseudos_list)),
                                   description_string))
                    print ("  Maybe the pseudopotential family wasn't "
                           "setup with the uploadfamily function?")

                else:
                     print "* {} [{} pseudos]{}".format(g.name, num_pseudos,
                                                        description_string)
        else:
            print "No valid UPF pseudopotential family found."
         
            
        
    
class _Structure(VerdiCommand):
    """
    Visualize AiIDA structures
    """
    
    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        self.valid_subcommands = {
            'show': (self.show, self.complete_visualizers),
            'list': (self.list, self.complete_none),
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

    def complete_visualizers(self):
        plugin_names = self.get_show_plugins().keys()
        return "\n".join(plugin_names)
        
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
    def list(self, *args):
        """
        List all AiiDA structures
        """
        import argparse
        parser = argparse.ArgumentParser(description='List AiiDA structures.')
        parser.add_argument('-e','--element',nargs='+', type=str, default=None,
                            help="Print all structures containing desired elements")
        parser.add_argument('-eo','--element-only', type=bool, default=False,
                            help="If set, structures do not contain different elements")
        parser.add_argument('-p', '--past-days', metavar='N', 
                            help="add a filter to show only structures created in the past N days",
                            type=int, action='store')
         
        load_django()        
        import datetime
        from aiida.orm import DataFactory
        from django.db.models import Q
        from django.utils import timezone
        from aiida.djsite.utils import get_automatic_user
        
        args = list(args)
        parsed_args = parser.parse_args(args)
        
        StructureData = DataFactory('structure')
        now = timezone.now()
        q_object = Q(user=get_automatic_user())

        if parsed_args.past_days is not None:
            now = timezone.now()
            n_days_ago = now - datetime.timedelta(days=parsed_args.past_days)
            q_object.add(Q(ctime__gte=n_days_ago), Q.AND)
        if parsed_args.element is not None:
            print "Not implemented element search"
            sys.exit(1)

        struc_list = StructureData.query(q_object).distinct().order_by('ctime')
        
        if struc_list:
            to_print = 'ID\n'
            for struc in struc_list:
                to_print += '{}\n'.format(struc.pk)
                
            print to_print

    def show(self, *args):
        """
        Show the AiiDA structure node with a visualisation program.
        """
        # DEVELOPER NOTE: to add a new plugin, just add a _plugin_xxx() method.
        import argparse,os
        parser = argparse.ArgumentParser(description='Visualise AiiDA structure.')
        parser.add_argument('exec_name', type=str, default=None,
                    help="Name or path to the executable of the visualization program.")
        parser.add_argument('structure_id', type=int, default=None,
                            help="ID of the structure to be plotted.")
        args = list(args)
        parsed_args = parser.parse_args(args)
        
        exec_name = parsed_args.exec_name
        structure_id = parsed_args.structure_id
        
        # I can give in input the whole path to executable
        code_name = os.path.split(exec_name)[-1]
        
        try:
            func = self.get_show_plugins()[code_name]
        except KeyError:
            print "Not implemented; implemented plugins are:"
            print "{}.".format(",".join(self.get_show_plugins()))
            sys.exit(1)
        
        load_django()
        from aiida.orm import DataFactory
        StructureData = DataFactory('structure')
        st = StructureData.get_subclass_from_pk(structure_id)
        
        func(exec_name, st)

    def get_show_plugins(self):
        """
        Get the list of all implemented plugins for visualizing the structure.
        """
        prefix = '_plugin_'
        method_names = dir(self) # get list of class methods names
        valid_formats = [ i[len(prefix):] for i in method_names 
                         if i.startswith(prefix)] # filter them
        
        return {k: getattr(self,prefix + k) for k in valid_formats}
    
    def _plugin_xcrysden(self,exec_name,structure):
        """
        Plugin for xcrysden
        """
        import tempfile,subprocess
        with tempfile.NamedTemporaryFile(suffix='.xsf') as f:
            f.write(structure.exportstring('xsf'))
            f.flush()
            
            try:
                subprocess.check_output([exec_name, '--xsf', f.name])
            except subprocess.CalledProcessError:
                # The program died: just print a message
                print "Note: the call to {} ended with an error.".format(
                    exec_name)
            except OSError as e:
                if e.errno == 2:
                    print ("No executable '{}' found. Add to the path, "
                           "or try with an absolute path.".format(
                           exec_name))
                    sys.exit(1)
                else:
                    raise
                

    def _plugin_vmd(self,exec_name,structure):
        """
        Plugin for vmd
        """
        import tempfile,subprocess
        with tempfile.NamedTemporaryFile(suffix='.xsf') as f:
            f.write(structure.exportstring('xsf'))
            f.flush()
            
            try:
                subprocess.check_output([exec_name, f.name])
            except subprocess.CalledProcessError:
                # The program died: just print a message
                print "Note: the call to {} ended with an error.".format(
                    exec_name)
            except OSError as e:
                if e.errno == 2:
                    print ("No executable '{}' found. Add to the path, "
                           "or try with an absolute path.".format(
                           exec_name))
                    sys.exit(1)
                else:
                    raise

