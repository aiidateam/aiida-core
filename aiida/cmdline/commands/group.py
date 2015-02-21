# -*- coding: utf-8 -*-
import sys

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida import load_dbenv

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.3.0"

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
        import datetime
        import argparse
        from aiida.orm import Group as G
        from django.db.models import Q
        from django.utils import timezone
        
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
        parser.add_argument('-p', '--past-days', metavar='N', 
                            help="add a filter to show only groups created in the past N days",
                            action='store', type=int)
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
        
        if parsed_args.past_days is not None:
            now = timezone.now()
            n_days_ago = now - datetime.timedelta(days=parsed_args.past_days)
        else:
            n_days_ago = None
            
        groups = G.query(user=user, type_string=type_string, past_days=n_days_ago)
        
        # nice formatting
        # gather all info
        
        users = []
        names = []
        nodes = []
        for group in groups:
            names.append(group.name)
            nodes.append(len(group.nodes))
            users.append(group.user.email.strip())
        
        # get the max length
        max_names_len = max([len(i) for i in names]) if names else 4
        max_nodes_len = max([len(str(i)) for i in nodes]) if nodes else 4
        max_users_len = max([len(i) for i in users]) if users else 4
        
        tolerated_name_length = 80-8-max_nodes_len-max_users_len-1

        if parsed_args.with_description:
            print "# Format: GroupName | NumNodes | User | Description"
            
            descriptions = [ g.description for g in groups ]
            fmt_string = "* {:<" + str(max_names_len) + "} | "
            fmt_string += "{:"+str(max_nodes_len) + "d} | "
            fmt_string += "{:"+str(max_users_len) + "s} | {}"
            for nam,nod,usr,desc in zip(names,nodes,users,descriptions):
                print fmt_string.format(nam,nod,usr,desc)
                        
        else:
            print "# Format: GroupName | NumNodes | User"
            
            first_fmt_string = "* {:<" + str(tolerated_name_length) + "} | "
            first_fmt_string += "{:"+str(max_nodes_len) + "d} | "
            first_fmt_string += "{:"+str(max_users_len) + "s}"
            
            extra_fmt_string = "  {:<" + str(tolerated_name_length) + "} | "
            extra_fmt_string += " "*max_nodes_len+" | "
            extra_fmt_string += " "*max_users_len
            
            for nam,nod,usr in zip(names,nodes,users):
                the_nams = [nam[i:i+tolerated_name_length] for i in range(0, len(nam), tolerated_name_length)]
                print first_fmt_string.format(the_nams[0],nod,usr)
                for i in the_nams[1:]:
                    print extra_fmt_string.format(i)
                    
                
                
                    
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
