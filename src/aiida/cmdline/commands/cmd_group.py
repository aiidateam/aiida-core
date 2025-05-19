###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi group` commands"""

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options, types
from aiida.cmdline.utils import echo
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.exceptions import UniquenessError
from aiida.common.links import GraphTraversalRules


@verdi.group('group')
def verdi_group():
    """Create, inspect and manage groups of nodes."""


@verdi_group.command('add-nodes')
@options.GROUP(required=True)
@options.FORCE()
@arguments.NODES()
@with_dbenv()
def group_add_nodes(group, force, nodes):
    """Add nodes to a group."""
    if not force:
        click.confirm(f'Do you really want to add {len(nodes)} nodes to {group}?', abort=True)

    group.add_nodes(nodes)


@verdi_group.command('remove-nodes')
@options.GROUP(required=True)
@arguments.NODES()
@options.GROUP_CLEAR()
@options.FORCE()
@with_dbenv()
def group_remove_nodes(group, nodes, clear, force):
    """Remove nodes from a group."""
    from aiida.orm import Group, Node, QueryBuilder

    if nodes and clear:
        echo.echo_critical(
            'Specify either the `--clear` flag to remove all nodes or the identifiers of the nodes you want to remove.'
        )

    if not force:
        if nodes:
            node_pks = [node.pk for node in nodes]

            query = QueryBuilder()
            query.append(Group, filters={'id': group.pk}, tag='group')
            query.append(Node, with_group='group', filters={'id': {'in': node_pks}}, project='id')

            group_node_pks = query.all(flat=True)

            if not group_node_pks:
                echo.echo_critical(f'None of the specified nodes are in {group}.')

            if len(node_pks) > len(group_node_pks):
                node_pks = set(node_pks).difference(set(group_node_pks))
                echo.echo_warning(f'{len(node_pks)} nodes with PK {node_pks} are not in {group}.')

            message = f'Are you sure you want to remove {len(group_node_pks)} nodes from {group}?'

        elif clear:
            message = f'Are you sure you want to remove ALL the nodes from {group}?'
        else:
            echo.echo_critical(f'No nodes were provided for removal from {group}.')

        click.confirm(message, abort=True)

    if clear:
        group.clear()
    else:
        group.remove_nodes(nodes)


@verdi_group.command('move-nodes')
@arguments.NODES()
@click.option('-s', '--source-group', type=types.GroupParamType(), required=True, help='The group whose nodes to move.')
@click.option(
    '-t', '--target-group', type=types.GroupParamType(), required=True, help='The group to which the nodes are moved.'
)
@options.FORCE(help='Do not ask for confirmation and skip all checks.')
@options.ALL(help='Move all nodes from the source to the target group.')
@with_dbenv()
def group_move_nodes(source_group, target_group, force, nodes, all_entries):
    """Move the specified NODES from one group to another."""
    from aiida.orm import Group, Node, QueryBuilder

    if source_group.pk == target_group.pk:
        echo.echo_critical(f'Source and target group are the same: {source_group}.')

    if not nodes:
        if all_entries:
            nodes = list(source_group.nodes)
        else:
            echo.echo_critical('Neither NODES or the `-a, --all` option was specified.')

    node_pks = [node.pk for node in nodes]

    if not all_entries:
        query = QueryBuilder()
        query.append(Group, filters={'id': source_group.pk}, tag='group')
        query.append(Node, with_group='group', filters={'id': {'in': node_pks}}, project='id')

        source_group_node_pks = query.all(flat=True)

        if not source_group_node_pks:
            echo.echo_critical(f'None of the specified nodes are in {source_group}.')

        if len(node_pks) > len(source_group_node_pks):
            absent_node_pks = set(node_pks).difference(set(source_group_node_pks))
            echo.echo_warning(f'{len(absent_node_pks)} nodes with PK {absent_node_pks} are not in {source_group}.')
            nodes = [node for node in nodes if node.pk in source_group_node_pks]
            node_pks = set(node_pks).difference(absent_node_pks)

    query = QueryBuilder()
    query.append(Group, filters={'id': target_group.pk}, tag='group')
    query.append(Node, with_group='group', filters={'id': {'in': node_pks}}, project='id')

    target_group_node_pks = query.all(flat=True)

    if target_group_node_pks:
        echo.echo_warning(
            f'{len(target_group_node_pks)} nodes with PK {set(target_group_node_pks)} are already in '
            f'{target_group}. These will still be removed from {source_group}.'
        )

    if not force:
        click.confirm(
            f'Are you sure you want to move {len(nodes)} nodes from {source_group} ' f'to {target_group}?', abort=True
        )

    source_group.remove_nodes(nodes)
    target_group.add_nodes(nodes)


@verdi_group.command('delete')
@arguments.GROUPS()
@options.ALL_USERS(help='Filter and delete groups for all users, rather than only for the current user.')
@options.USER(help='Add a filter to delete groups belonging to a specific user.')
@options.TYPE_STRING(help='Filter to only include groups of this type string.')
@options.PAST_DAYS(help='Add a filter to delete only groups created in the past N days.', default=None)
@click.option(
    '-s',
    '--startswith',
    type=click.STRING,
    default=None,
    help='Add a filter to delete only groups for which the label begins with STRING.',
)
@click.option(
    '-e',
    '--endswith',
    type=click.STRING,
    default=None,
    help='Add a filter to delete only groups for which the label ends with STRING.',
)
@click.option(
    '-c',
    '--contains',
    type=click.STRING,
    default=None,
    help='Add a filter to delete only groups for which the label contains STRING.',
)
@options.NODE(help='Delete only the groups that contain a node.')
@options.FORCE()
@click.option(
    '--delete-nodes', is_flag=True, default=False, help='Delete all nodes in the group along with the group itself.'
)
@options.graph_traversal_rules(GraphTraversalRules.DELETE.value)
@options.DRY_RUN()
@with_dbenv()
def group_delete(
    groups,
    delete_nodes,
    dry_run,
    force,
    all_users,
    user,
    type_string,
    past_days,
    startswith,
    endswith,
    contains,
    node,
    **traversal_rules,
):
    """Delete groups and (optionally) the nodes they contain."""
    from tabulate import tabulate

    from aiida import orm
    from aiida.tools import delete_group_nodes

    filters_provided = any(
        [all_users or user or past_days or startswith or endswith or contains or node or type_string]
    )

    if groups and filters_provided:
        echo.echo_critical('Cannot specify both GROUPS and any of the other filters.')

    if not groups and filters_provided:
        import datetime

        from aiida.common import timezone
        from aiida.common.escaping import escape_for_sql_like

        builder = orm.QueryBuilder()
        filters = {}

        # Note: we could have set 'core' as a default value for type_string,
        # but for the sake of uniform interface, we decided to keep the default value of None.
        # Otherwise `verdi group delete 123 -T core` would have worked, but we say
        #  'Cannot specify both GROUPS and any of the other filters'.
        if type_string is None:
            type_string = 'core'

        if '%' in type_string or '_' in type_string:
            filters['type_string'] = {'like': type_string}
        else:
            filters['type_string'] = type_string

        # Creation time
        if past_days:
            filters['time'] = {'>': timezone.now() - datetime.timedelta(days=past_days)}

        # Query for specific group labels
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
            user_email = orm.User.collection.get_default().email

        # Query groups that belong to all users
        if not all_users:
            builder.append(orm.User, filters={'email': user_email}, with_group='group')

        # Query groups that contain a particular node
        if node:
            builder.append(orm.Node, filters={'id': node.pk}, with_group='group')

        groups = builder.all(flat=True)
        if not groups:
            echo.echo_report('No groups found matching the specified criteria.')
            return

    elif not groups and not filters_provided:
        echo.echo_report('Nothing happened. Please specify at least one group or provide filters to query groups.')
        return

    projection_lambdas = {
        'pk': lambda group: str(group.pk),
        'label': lambda group: group.label,
        'type_string': lambda group: group.type_string,
        'count': lambda group: group.count(),
        'user': lambda group: group.user.email.strip(),
        'description': lambda group: group.description,
    }

    table = []
    projection_header = ['PK', 'Label', 'Type string', 'User']
    projection_fields = ['pk', 'label', 'type_string', 'user']
    for group in groups:
        table.append([projection_lambdas[field](group) for field in projection_fields])

    if not (force or dry_run):
        echo.echo_report('The following groups will be deleted:')
        echo.echo(tabulate(table, headers=projection_header))
        click.confirm('Are you sure you want to continue?', abort=True)
    elif dry_run:
        echo.echo_report('Would have deleted:')
        echo.echo(tabulate(table, headers=projection_header))

    for group in groups:
        group_str = str(group)

        if delete_nodes:

            def _dry_run_callback(pks):
                if not pks or force:
                    return False
                echo.echo_warning(
                    f'YOU ARE ABOUT TO DELETE {len(pks)} NODES ASSOCIATED WITH {group_str}! THIS CANNOT BE UNDONE!'
                )
                return not click.confirm('Do you want to continue?', abort=True)

            _, nodes_deleted = delete_group_nodes([group.pk], dry_run=dry_run or _dry_run_callback, **traversal_rules)
            if not nodes_deleted:
                # don't delete the group if the nodes were not deleted
                return

        if not dry_run:
            orm.Group.collection.delete(group.pk)
            echo.echo_success(f'{group_str} deleted.')


@verdi_group.command('relabel')
@arguments.GROUP()
@click.argument('label', type=click.STRING)
@with_dbenv()
def group_relabel(group, label):
    """Change the label of a group."""
    try:
        group.label = label
    except UniquenessError as exception:
        echo.echo_critical(str(exception))
    else:
        echo.echo_success(f"Label changed to '{label}'")
        msg = (
            'Note that if you are dumping your profile data to disk, to reflect the relabeling of the group, '
            'run your `verdi profile dump` command again.'
        )
        echo.echo_report(msg)


@verdi_group.command('description')
@arguments.GROUP()
@click.argument('description', type=click.STRING, required=False)
@with_dbenv()
def group_description(group, description):
    """Change the description of a group.

    If no description is defined, the current description will simply be echoed.
    """
    if description:
        group.description = description
        echo.echo_success(f'Changed the description of {group}.')
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
    help='Show UUIDs together with PKs. Note: if the --raw option is also passed, PKs are not printed, but only UUIDs.',
)
@arguments.GROUP()
@with_dbenv()
def group_show(group, raw, limit, uuid):
    """Show information for a given group."""
    from tabulate import tabulate

    from aiida.common import timezone
    from aiida.common.utils import str_timedelta

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
@options.USER(help='Add a filter to show only groups belonging to a specific user.')
@options.ALL(help='Show groups of all types.')
@options.TYPE_STRING(default='core', help='Filter to only include groups of this type string.')
@click.option(
    '-d', '--with-description', 'with_description', is_flag=True, default=False, help='Show also the group description.'
)
@click.option('-C', '--count', is_flag=True, default=False, help='Show also the number of nodes in the group.')
@options.PAST_DAYS(help='Add a filter to show only groups created in the past N days.', default=None)
@click.option(
    '-s',
    '--startswith',
    type=click.STRING,
    default=None,
    help='Add a filter to show only groups for which the label begins with STRING.',
)
@click.option(
    '-e',
    '--endswith',
    type=click.STRING,
    default=None,
    help='Add a filter to show only groups for which the label ends with STRING.',
)
@click.option(
    '-c',
    '--contains',
    type=click.STRING,
    default=None,
    help='Add a filter to show only groups for which the label contains STRING.',
)
@options.ORDER_BY(type=click.Choice(['id', 'label', 'ctime']), default='label')
@options.ORDER_DIRECTION()
@options.NODE(help='Show only the groups that contain this node.')
@with_dbenv()
def group_list(
    all_users,
    user,
    all_entries,
    type_string,
    with_description,
    count,
    past_days,
    startswith,
    endswith,
    contains,
    order_by,
    order_dir,
    node,
):
    """Show a list of existing groups."""
    import datetime

    from tabulate import tabulate

    from aiida import orm
    from aiida.common import timezone
    from aiida.common.escaping import escape_for_sql_like

    builder = orm.QueryBuilder()
    filters = {}

    if not all_entries:
        if '%' in type_string or '_' in type_string:
            filters['type_string'] = {'like': type_string}
        else:
            filters['type_string'] = type_string

    # Creation time
    if past_days:
        filters['time'] = {'>': timezone.now() - datetime.timedelta(days=past_days)}

    # Query for specific group labels
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
        user_email = orm.User.collection.get_default().email

    # Query groups that belong to all users
    if not all_users:
        builder.append(orm.User, filters={'email': user_email}, with_group='group')

    # Query groups that contain a particular node
    if node:
        builder.append(orm.Node, filters={'id': node.pk}, with_group='group')

    builder.order_by({orm.Group: {order_by: order_dir}})

    projection_lambdas = {
        'pk': lambda group: str(group.pk),
        'label': lambda group: group.label,
        'type_string': lambda group: group.type_string,
        'count': lambda group: group.count(),
        'user': lambda group: group.user.email.strip(),
        'description': lambda group: group.description,
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

    for group in builder.iterall():
        table.append([projection_lambdas[field](group[0]) for field in projection_fields])

    if not all_entries:
        echo.echo_report('To show groups of all types, use the `-a/--all` option.')

    if not table:
        echo.echo_report('No groups found matching the specified criteria.')
    else:
        echo.echo(tabulate(table, headers=projection_header))


@verdi_group.command('create')
@click.argument('group_label', nargs=1, type=click.STRING)
@with_dbenv()
def group_create(group_label):
    """Create an empty group with a given label."""
    from aiida import orm

    group, created = orm.Group.collection.get_or_create(label=group_label)

    if created:
        echo.echo_success(f"Group created with PK = {group.pk} and label '{group.label}'.")
    else:
        echo.echo_report(f"Group with label '{group.label}' already exists: {group}.")


@verdi_group.command('copy')
@arguments.GROUP('source_group')
@click.argument('destination_group', nargs=1, type=click.STRING)
@with_dbenv()
def group_copy(source_group, destination_group):
    """Duplicate a group.

    More in detail, add all nodes from the source group to the destination group.
    Note that the destination group may not exist.
    """
    from aiida import orm

    dest_group, created = orm.Group.collection.get_or_create(label=destination_group)

    # Issue warning if destination group is not empty and get user confirmation to continue
    if not created and not dest_group.is_empty:
        echo.echo_warning(f'Destination {dest_group} already exists and is not empty.')
        click.confirm('Do you wish to continue anyway?', abort=True)

    # Copy nodes
    dest_group.add_nodes(list(source_group.nodes))
    echo.echo_success(f'Nodes copied from {source_group} to {dest_group}.')


@verdi_group.group('path')
def verdi_group_path():
    """Inspect groups of nodes, with delimited label paths."""


@verdi_group_path.command('ls')
@click.argument('path', type=click.STRING, required=False)
@options.TYPE_STRING(default='core', help='Filter to only include groups of this type string.')
@click.option('-R', '--recursive', is_flag=True, default=False, help='Recursively list sub-paths encountered.')
@click.option('-l', '--long', 'as_table', is_flag=True, default=False, help='List as a table, with sub-group count.')
@click.option(
    '-d', '--with-description', 'with_description', is_flag=True, default=False, help='Show also the group description.'
)
@click.option(
    '--no-virtual',
    'no_virtual',
    is_flag=True,
    default=False,
    help='Only show paths that fully correspond to an existing group.',
)
@click.option('--no-warn', is_flag=True, default=False, help='Do not issue a warning if any paths are invalid.')
@with_dbenv()
def group_path_ls(path, type_string, recursive, as_table, no_virtual, with_description, no_warn):
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
                len([c for c in child.walk() if not c.is_virtual]),
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


@verdi_group.command('dump')
@arguments.GROUP()
@options.PATH()
@options.DRY_RUN()
@options.OVERWRITE()
@options.PAST_DAYS()
@options.START_DATE()
@options.END_DATE()
@options.FILTER_BY_LAST_DUMP_TIME()
@options.DUMP_PROCESSES()
@options.DUMP_DATA()
@options.ONLY_TOP_LEVEL_CALCS()
@options.ONLY_TOP_LEVEL_WORKFLOWS()
@options.DELETE_MISSING()
@options.SYMLINK_CALCS()
@options.INCLUDE_INPUTS()
@options.INCLUDE_OUTPUTS()
@options.INCLUDE_ATTRIBUTES()
@options.INCLUDE_EXTRAS()
@options.FLAT()
@options.DUMP_UNSEALED()
@click.pass_context
@with_dbenv()
def group_dump(
    ctx,
    group,
    path,
    dry_run,
    overwrite,
    past_days,
    start_date,
    end_date,
    filter_by_last_dump_time,
    dump_processes,
    dump_data,
    delete_missing,
    only_top_level_calcs,
    only_top_level_workflows,
    symlink_calcs,
    include_inputs,
    include_outputs,
    include_attributes,
    include_extras,
    flat,
    dump_unsealed,
):
    """Dump data of an AiiDA group to disk.

    If 'aiida_dump_config.yaml' exists in the target directory, it will be used
    as the sole source of configuration settings, ignoring other CLI flags.
    Otherwise, CLI flags will be used.
    """
    import traceback
    from pathlib import Path

    from pydantic import ValidationError

    from aiida.cmdline.utils import echo
    from aiida.common import NotExistent
    from aiida.tools.dumping import GroupDumper
    from aiida.tools.dumping.config import DumpConfig, DumpMode

    warning_msg = (
        'This is a new feature which is still in its testing phase. '
        'If you encounter unexpected behavior or bugs, please report them via Discourse or GitHub.'
    )
    echo.echo_warning(warning_msg)

    # --- Initial Setup ---
    final_dump_config = None
    resolved_base_output_path: Path  # Will be set

    try:
        if path is None:
            resolved_base_output_path = Path.cwd() / group.label
            echo.echo_report(f"No output path specified. Using default: './{group.label}'")
        else:
            resolved_base_output_path = Path(path).resolve()
            echo.echo_report(f"Using specified output path: '{resolved_base_output_path}'")

        config_file_path = resolved_base_output_path / 'aiida_dump_config.yaml'

        if config_file_path.is_file() and not overwrite:
            # --- Config File Exists: Load ONLY from file ---
            try:
                config_path_rel = config_file_path.relative_to(Path.cwd())
            except ValueError:
                config_path_rel = config_file_path
            echo.echo_report(f"Config file found at '{config_path_rel}'.")
            echo.echo_report('Using config file settings ONLY (ignoring other CLI flags).')
            try:
                final_dump_config = DumpConfig.parse_yaml_file(config_file_path)
                if final_dump_config.groups not in ([group.uuid], [group.label]):
                    msg = (
                        f"Config file specifies groups '{final_dump_config.groups}', "
                        f"Overriding to dump only group '{group.label}'."
                    )
                    echo.echo_warning(msg)
                    final_dump_config.groups = [group.uuid]

            except (ValidationError, FileNotFoundError, ValueError) as e:
                echo.echo_critical(f'Error loading or validating config file {config_file_path}: {e}')
                return
        else:
            # --- Config File Does NOT Exist: Use ONLY CLI args ---
            echo.echo_report('No config file found. Using command-line arguments.')
            try:
                # Gather relevant CLI args for group dump
                config_input_data = {
                    'dry_run': dry_run,
                    'overwrite': overwrite,
                    'groups': [group.uuid],  # Set group explicitly here
                    'past_days': past_days,
                    'start_date': start_date,
                    'end_date': end_date,
                    'filter_by_last_dump_time': filter_by_last_dump_time,
                    'dump_processes': dump_processes,
                    'dump_data': dump_data,
                    'only_top_level_calcs': only_top_level_calcs,
                    'only_top_level_workflows': only_top_level_workflows,
                    'delete_missing': delete_missing,
                    'symlink_calcs': symlink_calcs,
                    'include_inputs': include_inputs,
                    'include_outputs': include_outputs,
                    'include_attributes': include_attributes,
                    'include_extras': include_extras,
                    'flat': flat,
                    'dump_unsealed': dump_unsealed,
                }
                final_dump_config = DumpConfig.model_validate(config_input_data)
            except ValidationError as e:
                echo.echo_critical(f'Invalid command-line arguments provided:\n{e}')
                return

        # --- Logical Checks ---
        if final_dump_config.dump_mode == DumpMode.DRY_RUN and overwrite:
            msg = (
                '`--dry-run` and `--overwrite` selected (or set in config). Overwrite operation will NOT be performed.'
            )
            echo.echo_warning(msg)

        # --- Instantiate and Run GroupDumper ---
        group_dumper = GroupDumper(group=group, config=final_dump_config, output_path=resolved_base_output_path)
        group_dumper.dump()

        if final_dump_config.dump_mode != DumpMode.DRY_RUN:
            msg = f'Raw files for group `{group.label}` dumped into folder `{resolved_base_output_path}`.'
            echo.echo_success(msg)
        else:
            echo.echo_success('Dry run completed.')

    except NotExistent as e:
        echo.echo_critical(f'Error: Required AiiDA entity not found: {e!s}')
    except Exception as e:
        msg = f'Unexpected error during dump of group {group.label}:\n ({e!s}).\n'
        echo.echo_critical(msg + traceback.format_exc())
