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
from aiida.cmdline.params import options, arguments, types
from aiida.cmdline.utils import echo
from aiida.cmdline.utils.decorators import with_dbenv


@verdi.group('group')
def verdi_group():
    """Inspect, create and manage groups."""


@verdi_group.command("removenodes")
@options.GROUP(required=True)
@arguments.NODES()
@options.FORCE(help="Force to remove the nodes from group.")
@with_dbenv()
def group_removenodes(group, nodes, force):
    """Remove NODES from a given AiiDA group."""

    if not force:
        click.confirm(
            "Are you sure to remove {} nodes from the group with PK = {} "
            "({})?".format(len(nodes), group.id, group.label),
            abort=True)

    group.remove_nodes(nodes)


@verdi_group.command("addnodes")
@options.GROUP(required=True)
@options.FORCE(help="Force to add nodes in the group.")
@arguments.NODES()
@with_dbenv()
def group_addnodes(group, force, nodes):
    """Add NODES to a given AiiDA group."""

    if not force:
        click.confirm(
            "Are you sure to add {} nodes the group with PK = {} "
            "({})?".format(len(nodes), group.id, group.label),
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
    from aiida import orm
    group_id = group.id
    group_label = group.label

    num_nodes = len(group.nodes)
    if num_nodes > 0 and not force:
        echo.echo_critical(("Group '{}' is not empty (it contains {} "
                            "nodes). Pass the -f option if you really want to delete "
                            "it.".format(group_label, num_nodes)))

    if not force:
        click.confirm('Are you sure to kill the group with PK = {} ({})?'.format(group_id, group_label), abort=True)

    orm.Group.objects.delete(group_id)
    echo.echo_success("Group '{}' (PK={}) deleted.".format(group_label, group_id))


@verdi_group.command("rename")
@arguments.GROUP()
@click.argument("label", nargs=1, type=click.STRING)
@with_dbenv()
def group_rename(group, label):
    """Rename an existing group. Pass the GROUP which you want to rename and its new LABEL."""
    try:
        group.label = label
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
    """Show information on a given group. Pass the GROUP as a parameter."""
    from tabulate import tabulate

    from aiida.common.utils import str_timedelta
    from aiida.common import timezone

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
        table.append(["Group label", group.label])
        table.append(["Group type_string", type_string])
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
            row.append(node.node_type.rsplit('.', 2)[1])
            row.append(str_timedelta(now - node.ctime, short=True, negative_to_zero=True))
            table.append(row)
        echo.echo(tabulate(table, headers=header))


@with_dbenv()
def valid_group_type_strings():
    from aiida.orm import GroupTypeString
    return tuple(i.value for i in GroupTypeString)


@with_dbenv()
def user_defined_group():
    from aiida.orm import GroupTypeString
    return GroupTypeString.USER.value


# pylint: disable=too-many-arguments, too-many-locals
@verdi_group.command("list")
@options.ALL_USERS(help="Show groups for all users, rather than only for the current user")
@click.option(
    '-u',
    '--user',
    'user_email',
    type=click.STRING,
    help="Add a filter to show only groups belonging to a specific user")
@click.option('-a', '--all-types', is_flag=True, default=False, help="Show groups of all types")
@click.option(
    '-t',
    '--type',
    'group_type',
    type=types.LazyChoice(valid_group_type_strings),
    default=user_defined_group,
    help="Show groups of a specific type, instead of user-defined groups. Start with semicolumn if you want to "
    "specify aiida-internal type")
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
def group_list(all_users, user_email, all_types, group_type, with_description, count, past_days, startswith, endswith,
               contains, node):
    # pylint: disable=too-many-branches
    """Show a list of groups."""
    import datetime
    from aiida.common.escaping import escape_for_sql_like
    from aiida.common import timezone
    from aiida.orm import Group
    from aiida.orm import QueryBuilder
    from aiida.orm import User
    from aiida import orm
    from tabulate import tabulate

    query = QueryBuilder()
    filters = {}

    # Specify group types
    if not all_types:
        filters = {'type_string': {'==': group_type}}

    # Creation time
    if past_days:
        filters['time'] = {'>': timezone.now() - datetime.timedelta(days=past_days)}

    # Query for specific group names
    filters['or'] = []
    if startswith:
        filters['or'].append({'label': {'like': '{}%'.format(escape_for_sql_like(startswith))}})
    if endswith:
        filters['or'].append({'label': {'like': '%{}'.format(escape_for_sql_like(endswith))}})
    if contains:
        filters['or'].append({'label': {'like': '%{}%'.format(escape_for_sql_like(contains))}})

    query.append(Group, filters=filters, tag='group', project='*')

    # Query groups that belong to specific user
    if user_email:
        user = user_email
    else:
        # By default: only groups of this user
        user = orm.User.objects.get_default().email

    # Query groups that belong to all users
    if not all_users:
        query.append(User, filters={'email': {'==': user}}, with_group='group')

    # Query groups that contain a particular node
    if node:
        from aiida.orm import Node
        query.append(Node, filters={'id': {'==': node.id}}, with_group='group')

    query.order_by({Group: {'id': 'asc'}})
    result = query.all()

    projection_lambdas = {
        'pk': lambda group: str(group.pk),
        'label': lambda group: group.label,
        'type_string': lambda group: group.type_string,
        'count': lambda group: group.count(),
        'user': lambda group: group.user.email.strip(),
        'description': lambda group: group.description
    }

    table = []
    projection_header = ['PK', 'Label', 'Type string', 'User']
    projection_fields = ['pk', 'label', 'type_string', 'user']

    if with_description:
        projection_header.append('Description')
        projection_fields.append('description')

    if count:
        projection_header.append('Node count')
        projection_fields.append('count')

    for group in result:
        table.append([projection_lambdas[field](group[0]) for field in projection_fields])

    if not all_types:
        echo.echo_info("If you want to see the groups of all types, please add -a/--all-types option")
    echo.echo(tabulate(table, headers=projection_header))


@verdi_group.command("create")
@click.argument('group_label', nargs=1, type=click.STRING)
@with_dbenv()
def group_create(group_label):
    """Create a new empty group with the name GROUP_NAME."""
    from aiida import orm
    from aiida.orm import GroupTypeString

    group, created = orm.Group.objects.get_or_create(label=group_label, type_string=GroupTypeString.USER)

    if created:
        echo.echo_success("Group created with PK = {} and name '{}'".format(group.id, group.label))
    else:
        echo.echo_info("Group '{}' already exists, PK = {}".format(group.label, group.id))


@verdi_group.command("copy")
@arguments.GROUP('source_group')
@click.argument('destination_group', nargs=1, type=click.STRING)
@with_dbenv()
def group_copy(source_group, destination_group):
    """Add all nodes that belong to source group to the destination group (which may or may not exist)."""
    from aiida import orm
    from aiida.orm import GroupTypeString

    dest_group = orm.Group.objects.get_or_create(
        label=destination_group, type_string=GroupTypeString(source_group.type_string))[0]
    dest_group.add_nodes(list(source_group.nodes))
    echo.echo_success("Nodes copied from group<{}> to group<{}>".format(source_group, destination_group))
