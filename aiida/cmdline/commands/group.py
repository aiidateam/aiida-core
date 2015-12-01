# -*- coding: utf-8 -*-

import sys
import datetime
import argparse

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands

from aiida.backends.utils import load_dbenv

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi"



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
            'show': (self.group_show, self.complete_none),
            'description': (self.group_description, self.complete_none),
        }

    def group_show(self, *args):
        """
        Show information on a given group. Pass the PK as a parameter.
        """
        load_dbenv()

        import argparse
        from aiida.common.exceptions import NotExistent
        from aiida.orm import Group as G
        from aiida.common.utils import str_timedelta
        from aiida.utils import timezone
        from aiida.orm.node import from_type_to_pluginclassname

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Information on a given AiiDA group.')
        parser.add_argument('-r', '--raw',
                            dest='raw', action='store_true',
                            help="Show only a space-separated list of PKs of "
                            "the calculations in the group")
        parser.add_argument('PK',type=int, help="The PK of the group to show")
        parser.set_defaults(raw=False)

        args = list(args)
        parsed_args = parser.parse_args(args)

        group_pk = parsed_args.PK
        try:
            group = G(dbgroup=group_pk)
        except NotExistent as e:
            print >> sys.stderr, "Error: {}.".format(e.message)
            sys.exit(1)

        if parsed_args.raw:
            print " ".join(str(_.pk) for _ in group.nodes)
        else:
            type_string = group.type_string
            desc = group.description
            now = timezone.now()

            print "# Group name: {}".format(group.name)
            print "# Group type: {}".format(type_string if type_string
                                            else "<user-defined>")
            print "# Group description: {}".format(desc if desc else
                                                   "<no description>")
            print "# Nodes:"
            for n in group.nodes:
                print "* {} - {} - {}".format(
                    n.pk,
                    from_type_to_pluginclassname(n.dbnode.type).rsplit(".", 1)[1],
                    str_timedelta(now - n.ctime, short=True,
                                  negative_to_zero=True))

    def group_description(self, *args):
        """
        Edit the group description.
        """
        load_dbenv()

        import argparse
        from aiida.orm import Group as G
        from aiida.common.exceptions import NotExistent

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Change the description of a given group.')
        parser.add_argument('PK',type=int, help="The PK of the group for which "
                            "you want to edit the description")
        parser.add_argument('description',type=str,
                            help="The new description. If not provided, "
                            "just show the current description.")

        args = list(args)
        parsed_args = parser.parse_args(args)

        group_pk = parsed_args.PK
        try:
            group = G(dbgroup=group_pk)
        except NotExistent as e:
            print >> sys.stderr, "Error: {}.".format(e.message)
            sys.exit(1)

        group.description = parsed_args.description



    def group_list(self, *args):
        """
        Print a list of groups in the DB.
        """
        load_dbenv()

        from aiida.orm.group import get_group_type_mapping
        from aiida.backends.utils import get_automatic_user, get_group_list
        from aiida.utils import timezone

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='List AiiDA user-defined groups.')
        exclusive_group = parser.add_mutually_exclusive_group()
        exclusive_group.add_argument('-A', '--all-users',
                                     dest='all_users', action='store_true',
                                     help="Show groups for all users, rather than only for the current user")
        exclusive_group.add_argument('-u', '--user', metavar='USER_EMAIL',
                                     help="Add a filter to show only groups belonging to a specific user",
                                     action='store', type=str)
        parser.add_argument('-t', '--type', metavar='TYPE',
                            help="Show groups of a specific type, instead of user-defined groups",
                            action='store', type=str)
        parser.add_argument('-d', '--with-description',
                            dest='with_description', action='store_true',
                            help="Show also the group description")
        parser.add_argument('-p', '--past-days', metavar='N',
                            help="add a filter to show only groups created in the past N days",
                            action='store', type=int)
        parser.add_argument('-s', '--startswith', metavar='STRING', default=None,
                            help="add a filter to show only groups for which the name begins with STRING",
                            action='store', type=str)
        parser.add_argument('-e', '--endswith', metavar='STRING', default=None,
                            help="add a filter to show only groups for which the name ends with STRING",
                            action='store', type=str)
        parser.add_argument('-c', '--contains', metavar='STRING', default=None,
                            help="add a filter to show only groups for which the name contains STRING",
                            action='store', type=str)
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

        name_filters = dict((k, getattr(parsed_args, k))
                            for k in ['startswith','endswith','contains'])

        groups = get_group_list(user, type_string,
                                n_days_ago=parsed_args.past_days,
                                name_filters=name_filters)


        # nice formatting
        # gather all info

        # get the max length
        max_pks_len = max([len(i[0]) for i in groups]) if groups else 4
        max_names_len = max([len(i[1]) for i in groups]) if groups else 4
        max_nodes_len = max([len(str(i[2])) for i in groups]) if groups else 4
        max_users_len = max([len(i[3]) for i in groups]) if groups else 4

        tolerated_name_length = (80 - 11 - max_nodes_len -
                                 max_users_len - max_pks_len - 1)

        #print max_names_len, tolerated_name_length


        if parsed_args.with_description:
            print "# Format: PK | GroupName | NumNodes | User | Description"

            fmt_string = "* {:<" + str(max_pks_len) + "} | "
            fmt_string += "{:<" + str(max_names_len) + "} | "
            fmt_string += "{:" + str(max_nodes_len) + "d} | "
            fmt_string += "{:" + str(max_users_len) + "s} | {}"

            for pk, nam, nod, usr, desc in groups:
                print fmt_string.format(pk, nam, nod, usr, desc)

        else:
            print "# Format: PK | GroupName | NumNodes | User"

            first_fmt_string = "* {:<" + str(max_pks_len) + "} | "
            first_fmt_string += "{:<" + str(tolerated_name_length) + "} | "
            first_fmt_string += "{:" + str(max_nodes_len) + "d} | "
            first_fmt_string += "{:" + str(max_users_len) + "s}"

            extra_fmt_string = "  " + " " * max_pks_len  + " | "
            extra_fmt_string += "{:<" + str(tolerated_name_length) + "} | "
            extra_fmt_string += " " * max_nodes_len + " | "
            extra_fmt_string += " " * max_users_len

            for pk, nam, nod, usr, _ in groups:
                the_nams = [nam[i:i + tolerated_name_length] for i in range(0, len(nam), tolerated_name_length)]
                print first_fmt_string.format(pk, the_nams[0], nod, usr)
                for i in the_nams[1:]:
                    print extra_fmt_string.format(i)































