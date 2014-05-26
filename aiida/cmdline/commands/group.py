import sys

from aiida.cmdline.baseclass import VerdiCommand
from aiida.common.utils import load_django

def get_group_type_mapping():
    """
    Return a dictionary with ``{short_name: proper_long_name_in_DB}`` format,
    where ``short_name`` is the name to use on the command line, while 
    ``proper_long_name_in_DB`` is the string stored in the ``type`` field of the
    DbGroup table.
    
    It is defined as a function so that the import statements are confined
    inside here.
    """
    from aiida.orm.data.upf import UPFGROUP_TYPE
    from aiida.cmdline.commands.importfile import IMPORTGROUP_TYPE
    
    return {'data.upf': UPFGROUP_TYPE,
            'import': IMPORTGROUP_TYPE}

class Group(VerdiCommand):
    """
    Setup and manage groups
    
    There is a list of subcommands to perform specific operation on groups.
    """
    def __init__(self):
        """
        A dictionary with valid commands and functions to be called:
        list.
        """
        self.valid_subcommands = {
            'list': (self.group_list, self.complete_none),
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
                              "'group'. Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    def invalid_subcommand(self,*args):
        print >> sys.stderr, ("You passed an invalid subcommand to 'group'. "
                              "Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

        
    def group_list(self, *args):
        """
        Print a list of groups in the DB. 
        """
        load_django()
        from aiida.common.datastructures import calc_states
        from aiida.djsite.utils import get_automatic_user
        
        import argparse
        from aiida.orm import Group as G
        
        parser = argparse.ArgumentParser(description='List AiiDA user-defined groups.')
        exclusive_group = parser.add_mutually_exclusive_group()
        exclusive_group.add_argument('-A', '--all-users',
            dest='all_users',action='store_true',
            help="Show groups for all users, rather than only for the current user")
        exclusive_group.add_argument('-u', '--user', metavar='USER_EMAIL', 
            help="Add a filter to show only groups belonging to a specific user",
            action='store', type=str)
        parser.add_argument('-t', '--type', metavar='TYPE', 
            help="Show groups of a specific type, instead of user-defined groups",
            action='store', type=str)
        parser.add_argument('-d', '--with-description',
            dest='with_description',action='store_true',
            help="Show also the group description")
        parser.set_defaults(all_users=False)
        parser.set_defaults(with_description=False)
        
        args = list(args)
        parsed_args = parser.parse_args(args)
        
        if parsed_args.all_users:
            user = None
        else:
            if parsed_args.user:
                user = parsed_args.user
            else:
                # By default: only groups of this user
                user = get_automatic_user()
        
        if parsed_args.type is None:
            type_string = ""
        else:
            try:
                type_string = get_group_type_mapping()[parsed_args.type]
            except KeyError:
                print >> sys.stderr, "Invalid group type. Valid group types are:"
                print >> sys.stderr, ",".join(sorted(
                    get_group_type_mapping().keys()))
                sys.exit(1)
        
        groups = G.query(user=user, type_string=type_string)
        
        
        if parsed_args.with_description:
            print "# {:<20} {:<10} {:<20} {}".format("GroupName", "NumNodes", "User", "Description")
            for group in groups:
                print "* {:<20} {:<10} {:<20} {}".format(
                    group.name, len(group.nodes),
                    group.user.email, group.description)
        else:
            print "# {:<20} {:<10} {:<20}".format("GroupName", "NumNodes", "User")
            for group in groups:
                print "* {:<20} {:<10} {:<20}".format(
                    group.name, len(group.nodes),
                    group.user.email)
            
            
            
            
            
            
            
            
            