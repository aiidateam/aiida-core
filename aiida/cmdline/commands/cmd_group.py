# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi group` commands"""
import warnings
import click

from aiida.common.exceptions import UniquenessError
from aiida.common.warnings import AiidaDeprecationWarning
from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options, arguments
from aiida.cmdline.utils import echo
from aiida.cmdline.utils.decorators import with_dbenv


@verdi.group('group')
def verdi_group():
    """Create, inspect and manage groups of nodes."""


@verdi_group.command('add-nodes')
@options.GROUP(required=True)
@options.FORCE()
@arguments.NODES()
@with_dbenv()
def group_add_nodes(group, force, nodes):
    """Add nodes to the a group."""
    if not force:
        click.confirm(f'Do you really want to add {len(nodes)} nodes to Group<{group.label}>?', abort=True)

    group.add_nodes(nodes)


@verdi_group.command('remove-nodes')
@options.GROUP(required=True)
@arguments.NODES()
@options.GROUP_CLEAR()
@options.FORCE()
@with_dbenv()
def group_remove_nodes(group, nodes, clear, force):
    """Remove nodes from a group."""
    if clear:
        message = f'Do you really want to remove ALL the nodes from Group<{group.label}>?'
    else:
        message = f'Do you really want to remove {len(nodes)} nodes from Group<{group.label}>?'

    if not force:
        click.confirm(message, abort=True)

    if clear:
        group.clear()
    else:
        group.remove_nodes(nodes)


@verdi_group.command('delete')
@arguments.GROUP()
@options.GROUP_CLEAR(
    help='Remove all nodes before deleting the group itself.' +
    ' [deprecated: No longer has any effect. Will be removed in 2.0.0]'
)
@options.FORCE()
@with_dbenv()
def group_delete(group, clear, force):
    """Delete a group.

    Note that this command only deletes groups - nodes contained in the group will remain untouched.
    """
    from aiida import orm

    label = group.label

    if clear:
        warnings.warn('`--clear` is deprecated and no longer has any effect.', AiidaDeprecationWarning)  # pylint: disable=no-member

    if not force:
        click.confirm(f'Are you sure to delete Group<{label}>?', abort=True)

    orm.Group.objects.delete(group.pk)
    echo.echo_success(f'Group<{label}> deleted.')


@verdi_group.command('relabel')
@arguments.GROUP()
@click.argument('label', type=click.STRING)
@with_dbenv()
def group_relabel(group, label):
    """Change the label of a group."""
    try:
        group.label = label
    except UniquenessError as exception:
        echo.echo_critical(f'Error: {exception}.')
    else:
        echo.echo_success(f'Label changed to {label}')


@verdi_group.command('description')
@arguments.GROUP()
@click.argument('description', type=click.STRING, required=False)
@with_dbenv()
def group_description(group, description):
    """Change the description of a group.

    If no DESCRIPTION is defined, the current description will simply be echoed.
    """
    if description:
        group.description = description
        echo.echo_success(f'Changed the description of Group<{group.label}>')
    else:
        echo.echo(group.description)


@verdi_group.command('show')
@options.RAW(help='Show only a space-separated list of PKs of the calculations in the group')
@options.LIMIT()
@click.option(
    '-u',
    '--uuid',
    is_flag=True,
    default=False,
    help='Show UUIDs together with PKs. Note: if the --raw option is also passed, PKs are not printed, but oly UUIDs.'
)
@arguments.GROUP()
@with_dbenv()
def group_show(group, raw, limit, uuid):
    """Show information for a given group."""
    from tabulate import tabulate

    from aiida.common.utils import str_timedelta
    from aiida.common import timezone

    if limit:
        node_iterator = group.nodes[:limit]
    else:
        node_iterator = group.nodes

    if raw:
        if uuid:
            echo.echo(' '.join(str(_.uuid) for _ in node_iterator))
        else:
            echo.echo(' '.join(str(_.pk) for _ in node_iterator))
    else:
        type_string = group.type_string
        desc = group.description
        now = timezone.now()

        table = []
        table.append(['Group label', group.label])
        table.append(['Group type_string', type_string])
        table.append(['Group description', desc if desc else '<no description>'])
        echo.echo(tabulate(table))

        table = []
        header = []
        if uuid:
            header.append('UUID')
        header.extend(['PK', 'Type', 'Created'])
        echo.echo('# Nodes:')
        for node in node_iterator:
            row = []
            if uuid:
                row.append(node.uuid)
            row.append(node.pk)
            row.append(node.node_type.rsplit('.', 2)[1])
            row.append(str_timedelta(now - node.ctime, short=True, negative_to_zero=True))
            table.append(row)
        echo.echo(tabulate(table, headers=header))


@verdi_group.command('list')
@options.ALL_USERS(help='Show groups for all users, rather than only for the current user.')
@options.USER(help='Add a filter to show only groups belonging to a specific user')
@options.ALL(help='Show groups of all types.')
@click.option(
    '-t',
    '--type',
    'group_type',
    default=None,
    help='Show groups of a specific type, instead of user-defined groups. Start with semicolumn if you want to '
    'specify aiida-internal type. [deprecated: use `--type-string` instead. Will be removed in 2.0.0]'
)
@options.TYPE_STRING()
@click.option(
    '-d',
    '--with-description',
    'with_description',
    is_flag=True,
    default=False,
    help='Show also the group description.'
)
@click.option('-C', '--count', is_flag=True, default=False, help='Show also the number of nodes in the group.')
@options.PAST_DAYS(help='Add a filter to show only groups created in the past N days.', default=None)
@click.option(
    '-s',
    '--startswith',
    type=click.STRING,
    default=None,
    help='Add a filter to show only groups for which the label begins with STRING.'
)
@click.option(
    '-e',
    '--endswith',
    type=click.STRING,
    default=None,
    help='Add a filter to show only groups for which the label ends with STRING.'
)
@click.option(
    '-c',
    '--contains',
    type=click.STRING,
    default=None,
    help='Add a filter to show only groups for which the label contains STRING.'
)
@options.ORDER_BY(type=click.Choice(['id', 'label', 'ctime']), default='id')
@options.ORDER_DIRECTION()
@options.NODE(help='Show only the groups that contain the node.')
@with_dbenv()
def group_list(
    all_users, user, all_entries, group_type, type_string, with_description, count, past_days, startswith, endswith,
    contains, order_by, order_dir, node
):
    """Show a list of existing groups."""
    # pylint: disable=too-many-branches,too-many-arguments,too-many-locals,too-many-statements
    import datetime
    from aiida import orm
    from aiida.common import timezone
    from aiida.common.escaping import escape_for_sql_like
    from tabulate import tabulate

    builder = orm.QueryBuilder()
    filters = {}

    if group_type is not None:
        warnings.warn('`--group-type` is deprecated, use `--type-string` instead', AiidaDeprecationWarning)  # pylint: disable=no-member

        if type_string is not None:
            raise click.BadOptionUsage('group-type', 'cannot use `--group-type` and `--type-string` at the same time.')
        else:
            type_string = group_type

    # Have to specify the default for `type_string` here instead of directly in the option otherwise it will always
    # raise above if the user specifies just the `--group-type` option. Once that option is removed, the default can
    # be moved to the option itself.
    if type_string is None:
        type_string = 'core'

    if not all_entries:
        if '%' in type_string or '_' in type_string:
            filters['type_string'] = {'like': type_string}
        else:
            filters['type_string'] = type_string

    # Creation time
    if past_days:
        filters['time'] = {'>': timezone.now() - datetime.timedelta(days=past_days)}

    # Query for specific group names
    filters['or'] = []
    if startswith:
        filters['or'].append({'label': {'like': f'{escape_for_sql_like(startswith)}%'}})
    if endswith:
        filters['or'].append({'label': {'like': f'%{escape_for_sql_like(endswith)}'}})
    if contains:
        filters['or'].append({'label': {'like': f'%{escape_for_sql_like(contains)}%'}})

    builder.append(orm.Group, filters=filters, tag='group', project='*')

    # Query groups that belong to specific user
    if user:
        user_email = user.email
    else:
        # By default: only groups of this user
        user_email = orm.User.objects.get_default().email

    # Query groups that belong to all users
    if not all_users:
        builder.append(orm.User, filters={'email': {'==': user_email}}, with_group='group')

    # Query groups that contain a particular node
    if node:
        builder.append(orm.Node, filters={'id': {'==': node.id}}, with_group='group')

    builder.order_by({orm.Group: {order_by: order_dir}})
    result = builder.all()

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

    if not all_entries:
        echo.echo_info('to show groups of all types, use the `-a/--all` option.')

    if not table:
        echo.echo_info('no groups found matching the specified criteria.')
    else:
        echo.echo(tabulate(table, headers=projection_header))


@verdi_group.command('create')
@click.argument('group_label', nargs=1, type=click.STRING)
@with_dbenv()
def group_create(group_label):
    """Create an empty group with a given name."""
    from aiida import orm

    group, created = orm.Group.objects.get_or_create(label=group_label)

    if created:
        echo.echo_success(f"Group created with PK = {group.id} and name '{group.label}'")
    else:
        echo.echo_info(f"Group '{group.label}' already exists, PK = {group.id}")


@verdi_group.command('copy')
@arguments.GROUP('source_group')
@click.argument('destination_group', nargs=1, type=click.STRING)
@with_dbenv()
def group_copy(source_group, destination_group):
    """Duplicate a group.

    More in detail, add all nodes from the source group to the destination group.
    Note that the destination group may not exist."""
    from aiida import orm

    dest_group, created = orm.Group.objects.get_or_create(label=destination_group)

    # Issue warning if destination group is not empty and get user confirmation to continue
    if not created and not dest_group.is_empty:
        echo.echo_warning(f'Destination group<{dest_group.label}> already exists and is not empty.')
        click.confirm('Do you wish to continue anyway?', abort=True)

    # Copy nodes
    dest_group.add_nodes(list(source_group.nodes))
    echo.echo_success(f'Nodes copied from group<{source_group.label}> to group<{dest_group.label}>')


@verdi_group.group('path')
def verdi_group_path():
    """Inspect groups of nodes, with delimited label paths."""


@verdi_group_path.command('ls')
@click.argument('path', type=click.STRING, required=False)
@options.TYPE_STRING(default='core', help='Filter to only include groups of this type string.')
@click.option('-R', '--recursive', is_flag=True, default=False, help='Recursively list sub-paths encountered.')
@click.option('-l', '--long', 'as_table', is_flag=True, default=False, help='List as a table, with sub-group count.')
@click.option(
    '-d',
    '--with-description',
    'with_description',
    is_flag=True,
    default=False,
    help='Show also the group description.'
)
@click.option(
    '--no-virtual',
    'no_virtual',
    is_flag=True,
    default=False,
    help='Only show paths that fully correspond to an existing group.'
)
@click.option('--no-warn', is_flag=True, default=False, help='Do not issue a warning if any paths are invalid.')
@with_dbenv()
def group_path_ls(path, type_string, recursive, as_table, no_virtual, with_description, no_warn):
    # pylint: disable=too-many-arguments,too-many-branches
    """Show a list of existing group paths."""
    from aiida.plugins import GroupFactory
    from aiida.tools.groups.paths import GroupPath, InvalidPath

    try:
        path = GroupPath(path or '', cls=GroupFactory(type_string), warn_invalid_child=not no_warn)
    except InvalidPath as err:
        echo.echo_critical(str(err))

    if recursive:
        children = path.walk()
    else:
        children = path.children

    if as_table or with_description:
        from tabulate import tabulate
        headers = ['Path', 'Sub-Groups']
        if with_description:
            headers.append('Description')
        rows = []
        for child in sorted(children):
            if no_virtual and child.is_virtual:
                continue
            row = [
                child.path if child.is_virtual else click.style(child.path, bold=True),
                len([c for c in child.walk() if not c.is_virtual])
            ]
            if with_description:
                row.append('-' if child.is_virtual else child.get_group().description)
            rows.append(row)
        echo.echo(tabulate(rows, headers=headers))
    else:
        for child in sorted(children):
            if no_virtual and child.is_virtual:
                continue
            echo.echo(child.path, bold=not child.is_virtual)
