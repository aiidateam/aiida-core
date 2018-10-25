# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
It defines subcommands for verdi group command.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import click

from aiida.common.exceptions import UniquenessError
from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import echo
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.cmdline.params import options, arguments


@verdi.group('group')
def verdi_group():
    """Inspect, create and manage groups."""
    pass


@verdi_group.command("removenodes")
@options.GROUP()
@arguments.NODES()
@options.FORCE(help="Force to remove the nodes from group.")
@with_dbenv()
def group_removenodes(group, nodes, force):
    """
    Remove NODES from a given AiiDA group.
    """
    if not force:
        click.confirm(
            "Are you sure to remove {} nodes from the group with PK = {} "
            "({})?".format(len(nodes), group.pk, group.name),
            abort=True)

    group.remove_nodes(nodes)


@verdi_group.command("addnodes")
@options.GROUP()
@options.FORCE(help="Force to add nodes in the group.")
@arguments.NODES()
@with_dbenv()
def group_addnodes(group, force, nodes):
    """
    Add NODES to a given AiiDA group.
    """

    if not force:
        click.confirm(
            "Are you sure to add {} nodes the group with PK = {} "
            "({})?".format(len(nodes), group.pk, group.name),
            abort=True)

    group.add_nodes(nodes)


@verdi_group.command("delete")
@arguments.GROUP()
@options.FORCE(help="Force deletion of the group even if it "
               "is not empty. Note that this deletes only the "
               "group and not the nodes.")
@with_dbenv()
def group_delete(group, force):
    """
    Pass the GROUP to delete an existing group.
    """
    group_pk = group.pk
    group_name = group.name

    num_nodes = len(group.nodes)
    if num_nodes > 0 and not force:
        echo.echo_critical(("Group '{}' is not empty (it contains {} "
                            "nodes). Pass the -f option if you really want to delete "
                            "it.".format(group_name, num_nodes)))

    if not force:
        click.confirm('Are you sure to kill the group with PK = {} ({})?'.format(group_pk, group_name), abort=True)

    group.delete()
    echo.echo_success("Group '{}' (PK={}) deleted.".format(group_name, group_pk))


@verdi_group.command("rename")
@arguments.GROUP()
@click.argument("name", nargs=1, type=click.STRING)
@with_dbenv()
def group_rename(group, name):
    """
    Rename an existing group. Pass the GROUP for which you want to rename and its
    new NAME.
    """
    try:
        group.name = name
    except UniquenessError as exception:
        echo.echo_critical("Error: {}.".format(exception))
    else:
        echo.echo_success('Name successfully changed')


@verdi_group.command("description")
@arguments.GROUP()
@click.argument("description", type=click.STRING)
@with_dbenv()
def group_description(group, description):
    """
    Change the description of a given group.
    Pass the GROUP for which you want to edit the description and its
    new DESCRIPTION. If DESCRIPTION is not provided, just show the current description.

    """
    group.description = description


@verdi_group.command("show")
@options.RAW(help="Show only a space-separated list of PKs of the calculations in the group")
@click.option(
    '-u',
    '--uuid',
    is_flag=True,
    default=False,
    help="Show UUIDs together with PKs. Note: if the --raw option is also passed, PKs are not printed, but oly UUIDs.")
@arguments.GROUP()
@with_dbenv()
def group_show(group, raw, uuid):
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
        for node in group.nodes:
            row = []
            if uuid:
                row.append(node.uuid)
            row.append(node.pk)
            row.append(get_plugin_type_from_type_string(node.type).rsplit(".", 1)[1])
            row.append(str_timedelta(now - node.ctime, short=True, negative_to_zero=True))
            table.append(row)
        echo.echo(tabulate(table, headers=header))


# pylint: disable=too-many-arguments, too-many-locals
@verdi_group.command("list")
@options.ALL_USERS(help="Show groups for all users, rather than only for the current user")
@click.option(
    '-u',
    '--user',
    'user_email',
    type=click.STRING,
    help="Add a filter to show only groups belonging to a specific user")
@click.option(
    '-t',
    '--type',
    'group_type',
    type=click.STRING,
    help="Show groups of a specific type, instead of user-defined groups")
@click.option(
    '-d', '--with-description', 'with_description', is_flag=True, default=False, help="Show also the group description")
@click.option('-C', '--count', is_flag=True, default=False, help="Show also the number of nodes in the group")
@options.PAST_DAYS(help="add a filter to show only groups created in the past N days", default=None)
@click.option(
    '-s',
    '--startswith',
    type=click.STRING,
    default=None,
    help="add a filter to show only groups for which the name begins with STRING")
@click.option(
    '-e',
    '--endswith',
    type=click.STRING,
    default=None,
    help="add a filter to show only groups for which the name ends with STRING")
@click.option(
    '-c',
    '--contains',
    type=click.STRING,
    default=None,
    help="add a filter to show only groups for which the name contains STRING")
@options.NODE(help="Show only the groups that contain the node")
@with_dbenv()
def group_list(all_users, user_email, group_type, with_description, count, past_days, startswith, endswith, contains,
               node):
    """
    List AiiDA user-defined groups.
    """
    import datetime
    from aiida.utils import timezone
    from aiida.orm.group import get_group_type_mapping
    from aiida.orm.backends import construct_backend
    from tabulate import tabulate

    if all_users and user_email is not None:
        echo.echo_critical("argument -A/--all-users: not allowed with argument -u/--user")

    backend = construct_backend()

    if all_users:
        user = None
    else:
        if user_email:
            user = user_email
        else:
            # By default: only groups of this user
            user = backend.users.get_automatic_user()

    type_string = ""
    if group_type is not None:
        try:
            type_string = get_group_type_mapping()[group_type]
        except KeyError:
            echo.echo_critical("Invalid group type. Valid group types are: {}".format(",".join(
                sorted(get_group_type_mapping().keys()))))

    n_days_ago = None
    if past_days:
        n_days_ago = (timezone.now() - datetime.timedelta(days=past_days))

    name_filters = {'startswith': startswith, 'endswith': endswith, 'contains': contains}

    # Depending on --nodes option use or not key "nodes"
    from aiida.orm.implementation import Group as OrmGroup

    if node:
        result = OrmGroup.query(
            user=user, type_string=type_string, nodes=node, past_days=n_days_ago, name_filters=name_filters)
    else:
        result = OrmGroup.query(user=user, type_string=type_string, past_days=n_days_ago, name_filters=name_filters)

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

    if with_description:
        projection_header.append('Description')
        projection_fields.append('description')

    if count:
        projection_header.append('Node count')
        projection_fields.append('count')

    for group in result:
        table.append([projection_lambdas[field](group) for field in projection_fields])

    echo.echo(tabulate(table, headers=projection_header))


@verdi_group.command("create")
@click.argument('group_name', nargs=1, type=click.STRING)
@with_dbenv()
def group_create(group_name):
    """
    Create a new empty group with the name GROUP_NAME
    """

    from aiida.orm import Group as OrmGroup

    group, created = OrmGroup.get_or_create(name=group_name)

    if created:
        echo.echo_success("Group created with PK = {} and name '{}'".format(group.pk, group.name))
    else:
        echo.echo_info("Group '{}' already exists, PK = {}".format(group.name, group.pk))
