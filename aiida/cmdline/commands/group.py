# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import argparse
import sys
import click

from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.common.exceptions import NotExistent, UniquenessError
from aiida.cmdline.commands import verdi, verdi_group
from aiida.cmdline.utils import echo
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.cmdline.params import options, arguments


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
            'show': (self.cli, self.complete_none),
            'description': (self.cli, self.complete_none),
            'create': (self.cli, self.complete_none),
            'rename': (self.cli, self.complete_none),
            'delete': (self.cli, self.complete_none),
            'addnodes': (self.cli, self.complete_none),
            'removenodes': (self.cli, self.complete_none),
        }

    @staticmethod
    def cli(*args):  # pylint: disable=unused-argument
        verdi.main()

    def group_list(self, *args):
        """
        Print a list of groups in the DB.
        """
        if not is_dbenv_loaded():
            load_dbenv()

        import datetime
        from aiida.utils import timezone
        from aiida.orm.group import get_group_type_mapping
        from aiida.orm.backend import construct_backend
        from tabulate import tabulate

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
        parser.add_argument('-C', '--count', action='store_true',
                            help="Show also the number of nodes in the group")
        parser.add_argument('-p', '--past-days', metavar='N',
                            help="add a filter to show only groups created in the past N days",
                            action='store', type=int)
        parser.add_argument('-s', '--startswith', metavar='STRING',
                            default=None,
                            help="add a filter to show only groups for which the name begins with STRING",
                            action='store', type=str)
        parser.add_argument('-e', '--endswith', metavar='STRING', default=None,
                            help="add a filter to show only groups for which the name ends with STRING",
                            action='store', type=str)
        parser.add_argument('-c', '--contains', metavar='STRING', default=None,
                            help="add a filter to show only groups for which the name contains STRING",
                            action='store', type=str)
        parser.add_argument('-n', '--node', metavar='PK', default=None,
                            help="Show only the groups that contain the node specified by PK",
                            action='store', type=int)
        parser.set_defaults(all_users=False)
        parser.set_defaults(with_description=False)

        args = list(args)
        parsed_args = parser.parse_args(args)

        backend = construct_backend()

        if parsed_args.all_users:
            user = None
        else:
            if parsed_args.user:
                user = parsed_args.user
            else:
                # By default: only groups of this user
                user = backend.users.get_automatic_user()

        type_string = ""
        if parsed_args.type is not None:
            try:
                type_string = get_group_type_mapping()[parsed_args.type]
            except KeyError:
                print >> sys.stderr, "Invalid group type. Valid group types are:"
                print >> sys.stderr, ",".join(sorted(
                    get_group_type_mapping().keys()))
                sys.exit(1)

        name_filters = dict((k, getattr(parsed_args, k))
                            for k in ['startswith', 'endswith', 'contains'])

        n_days_ago = None
        if parsed_args.past_days:
            n_days_ago = (timezone.now() -
                          datetime.timedelta(days=parsed_args.past_days))

        # Depending on --nodes option use or not key "nodes"
        from aiida.orm.implementation import Group
        from aiida.orm import load_node

        node_pk = parsed_args.node
        if node_pk is not None:
            try:
                node = load_node(node_pk)
            except NotExistent as e:
                print >> sys.stderr, "Error: {}.".format(e.message)
                sys.exit(1)
            result = Group.query(user=user, type_string=type_string, nodes=node,
                              past_days=n_days_ago, name_filters=name_filters)
        else:
            result = Group.query(user=user, type_string=type_string,
                              past_days=n_days_ago, name_filters=name_filters)

        projection_lambdas = {
            'pk': lambda group: str(group.pk),
            'name': lambda group: group.name,
            'count': lambda group: len(group.nodes),
            'user': lambda group: group.user.email.strip(),
            'description': lambda group: group.description
        }

        table = []
        projection_header = ['PK', 'Name', 'User']
        projection_fields = ['pk', 'name', 'user']

        if parsed_args.with_description:
            projection_header.append('Description')
            projection_fields.append('description')

        if parsed_args.count:
            projection_header.append('Node count')
            projection_fields.append('count')

        for group in result:
            table.append([projection_lambdas[field](group) for field in projection_fields])

        print(tabulate(table, headers=projection_header))


@verdi_group.command("removenodes")
@options.GROUP()
@arguments.NODES()
@with_dbenv()
def group_addnodes(group, nodes, *args):
    """
    Remove NODES from a given AiiDA group.
    """
    from aiida.cmdline import wait_for_confirmation

    group_pk = group.pk
    group_name = group.name

    echo.echo("Are you sure to remove {} nodes from the group with PK = {} "
            "({})? [Y/N] ".format(len(nodes), group_pk, group_name))
    if not wait_for_confirmation():
        sys.exit(0)

    group.remove_nodes(nodes)


@verdi_group.command("addnodes")
@options.GROUP()
@arguments.NODES()
@with_dbenv()
def group_addnodes(group, nodes, *args):
    """
    Add NODES to a given AiiDA group.
    """
    from aiida.cmdline import wait_for_confirmation

    group_pk = group.pk
    group_name = group.name

    echo.echo("Are you sure to add {} nodes the group with PK = {} "
            "({})? [Y/N] ".format(len(nodes), group_pk, group_name))
    if not wait_for_confirmation():
        sys.exit(0)

    group.add_nodes(nodes)

@verdi_group.command("delete")
@arguments.GROUP()
@options.FORCE(help="Force deletion of the group even if it "
                    "is not empty. Note that this deletes only the "
                    "group and not the nodes.")
@with_dbenv()
def group_delete(group, force, *args):
    """
    Pass the GROUP to delete an existing group.
    """
    from aiida.cmdline import wait_for_confirmation

    group_pk = group.pk
    group_name = group.name

    num_nodes = len(group.nodes)
    if num_nodes > 0 and not force:
        echo.echo_critical(("Group '{}' is not empty (it contains {} "
                              "nodes). Pass the -f option if you really want to delete "
                              "it.".format(group_name, num_nodes)))

    echo.echo("Are you sure to kill the group with PK = {} ({})? "
                     "[Y/N] ".format(group_pk, group_name))
    if not wait_for_confirmation():
        sys.exit(0)

    group.delete()
    echo.echo_success("Group '{}' (PK={}) deleted.".format(group_name, group_pk))

@verdi_group.command("rename")
@arguments.GROUP()
@click.argument("name", nargs=1, type=click.STRING)
@with_dbenv()
def group_description(group, name, *args):
    """
    Rename an existing group. Pass the GROUP for which you want to rename and its
    new NAME.
    """
    try:
        group.name = name
    except UniquenessError as exception:
        echo.echo_critical("Error: {}.".format(exception.message))
    else:
        echo.echo_success('Name successfully changed')


@verdi_group.command("description")
@arguments.GROUP()
@click.argument("description", type=click.STRING)
@with_dbenv()
def group_description(group, description, *args):
    """
    Change the description of a given group.
    Pass the GROUP for which you want to edit the description and its
    new DESCRIPTION. If DESCRIPTION is not provided, just show the current description.

    """
    group.description = description

@verdi_group.command("show")
@click.option('-r', '--raw', is_flag=True, default=False,
              help="Show only a space-separated list of PKs of the calculations in the group")
@click.option('-u', '--uuid', is_flag=True, default=False,
              help="Show UUIDs together with PKs. Note: if the --raw option is also passed, PKs are not printed, but oly UUIDs.")
@arguments.GROUP()
@with_dbenv()
def group_show(group, raw, uuid, *args):
    """
    Show information on a given group. Pass the GROUP as a parameter.
    """

    from aiida.common.utils import str_timedelta
    from aiida.utils import timezone
    from aiida.plugins.loader import get_plugin_type_from_type_string
    from tabulate import tabulate

    if raw:
        if uuid:
            echo.echo(" ".join(str(_.uuid) for _ in group.nodes))
        else:
            echo.echo(" ".join(str(_.pk) for _ in group.nodes))
    else:
        type_string = group.type_string
        desc = group.description
        now = timezone.now()

        table = []
        table.append(["Group name", group.name])
        table.append(["Group type", type_string if type_string else "<user-defined>"])
        table.append(["Group description", desc if desc else "<no description>"])
        echo.echo(tabulate(table))

        table = []
        header = []
        if uuid:
            header.append('UUID')
        header.extend(['PK', 'Type', 'Created'])
        echo.echo("# Nodes:")
        for n in group.nodes:
            row = []
            if uuid:
                row.append(n.uuid)
            row.append(n.pk)
            row.append(get_plugin_type_from_type_string(n.type).rsplit(".", 1)[1])
            row.append(str_timedelta(now - n.ctime, short=True, negative_to_zero=True))
            table.append(row)
        echo.echo(tabulate(table, headers=header))


@verdi_group.command("list")
@click.option('-A', '--all-users', is_flag=True, default=False,
              help="Show groups for all users, rather than only for the current user")
@click.option('-u', '--user', type=click.STRING, help="Add a filter to show only groups belonging to a specific user")
@click.option('-t', '--type', type=click.STRING, help="Show groups of a specific type, instead of user-defined groups")
@click.option('-d', '--with-description', is_flag=True, default=False, help="Show also the group description")
@click.option('-C', '--count', type=click.INT, help="Show also the number of nodes in the group")
@click.option('-p', '--past-days', type=click.INT, help="add a filter to show only groups created in the past N days")
@click.option('-s', '--startswith', type=click.STRING, default=None,
              help="add a filter to show only groups for which the name begins with STRING")
@click.option('-e', '--endswith', type=click.STRING, default=None,
              help="add a filter to show only groups for which the name ends with STRING")
@click.option('-c', '--contains', type=click.STRING, default=None,
              help="add a filter to show only groups for which the name contains STRING")
@click.option('-n', '--node', type=click.INT, default=None,
              help="Show only the groups that contain the node specified by PK")
@with_dbenv()
def group_list(all_users, user_email, type, with_description, count,
               past_days, starts_with, ends_with, contains, node, *args):
    """
    List AiiDA user-defined groups.
    """
    import datetime
    from aiida.utils import timezone
    from aiida.orm.group import get_group_type_mapping
    from aiida.orm.backend import construct_backend
    from tabulate import tabulate


@verdi_group.command("create")
@click.argument('group_name', nargs=1, type=click.STRING)
@with_dbenv()
def group_create(group_name, *args):
    """
    Create a new empty group with the name GROUP_NAME
    """

    from aiida.orm import Group as G

    group, created = G.get_or_create(name=group_name)

    if created:
        echo.echo_success("Group created with PK = {} and name '{}'".format(group.pk, group.name))
    else:
        echo.echo_info("Group '{}' already exists, PK = {}".format(group.name, group.pk))
