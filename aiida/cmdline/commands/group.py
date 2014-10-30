# -*- coding: utf-8 -*-
import sys

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida import load_dbenv

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

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
    from aiida.orm.autogroup import VERDIAUTOGROUP_TYPE
    
    return {'data.upf': UPFGROUP_TYPE,
            'import': IMPORTGROUP_TYPE,
            'autogroup.run':VERDIAUTOGROUP_TYPE}

class Group(VerdiCommandWithSubcommands):
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

    def group_list(self, *args):
        """
        Print a list of groups in the DB. 
        """
        load_dbenv()
        from aiida.common.datastructures import calc_states
        from aiida.djsite.utils import get_automatic_user
        
        import argparse
        from aiida.orm import Group as G
        
        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='List AiiDA user-defined groups.')
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
            
            
            
            
            
            
            
            
            