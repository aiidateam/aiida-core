# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi node` command."""
import pathlib
import shutil

import click
import tabulate

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.params.types.plugin import PluginParamType
from aiida.cmdline.utils import decorators, echo, multi_line_input
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common import exceptions, timezone
from aiida.common.links import GraphTraversalRules


@verdi.group('node')
def verdi_node():
    """Inspect, create and manage nodes."""


@verdi_node.group('repo')
def verdi_node_repo():
    """Inspect the content of a node repository folder."""


@verdi_node_repo.command('cat')
@arguments.NODE()
@click.argument('relative_path', type=str, required=False)
@with_dbenv()
def repo_cat(node, relative_path):
    """Output the content of a file in the node repository folder.

    For ``SinglefileData`` nodes, the `RELATIVE_PATH` does not have to be specified as it is determined automatically.
    """
    import errno
    import sys

    from aiida.orm import SinglefileData

    if not relative_path:
        if not isinstance(node, SinglefileData):
            raise click.BadArgumentUsage('Missing argument \'RELATIVE_PATH\'.')

        relative_path = node.filename

    try:
        with node.base.repository.open(relative_path, mode='rb') as fhandle:
            shutil.copyfileobj(fhandle, sys.stdout.buffer)
    except OSError as exception:
        # The sepcial case is breakon pipe error, which is usually OK.
        if exception.errno != errno.EPIPE:
            # Incorrect path or file not readable
            echo.echo_critical(f'failed to get the content of file `{relative_path}`: {exception}')


@verdi_node_repo.command('ls')
@arguments.NODE()
@click.argument('relative_path', type=str, required=False)
@click.option('-c', '--color', 'color', flag_value=True, help='Use different color for folders and files.')
@with_dbenv()
def repo_ls(node, relative_path, color):
    """List files in the node repository folder."""
    from aiida.cmdline.utils.repository import list_repository_contents

    try:
        list_repository_contents(node, relative_path, color)
    except FileNotFoundError:
        echo.echo_critical(f'the path `{relative_path}` does not exist for the given node')


@verdi_node_repo.command('dump')
@arguments.NODE()
@click.argument(
    'output_directory',
    type=click.Path(),
    required=True,
)
@with_dbenv()
def repo_dump(node, output_directory):
    """Copy the repository files of a node to an output directory.

    The output directory should not exist. If it does, the command
    will abort.
    """
    from aiida.repository import FileType

    output_directory = pathlib.Path(output_directory)

    try:
        output_directory.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        echo.echo_critical(f'Invalid value for "OUTPUT_DIRECTORY": Path "{output_directory}" exists.')

    def _copy_tree(key, output_dir):  # pylint: disable=too-many-branches
        """
        Recursively copy the content at the ``key`` path in the given node to
        the ``output_dir``.
        """
        for file in node.base.repository.list_objects(key):
            # Not using os.path.join here, because this is the "path"
            # in the AiiDA node, not an actual OS - level path.
            file_key = file.name if not key else f'{key}/{file.name}'
            if file.file_type == FileType.DIRECTORY:
                new_out_dir = output_dir / file.name
                assert not new_out_dir.exists()
                new_out_dir.mkdir()
                _copy_tree(key=file_key, output_dir=new_out_dir)

            else:
                assert file.file_type == FileType.FILE
                out_file_path = output_dir / file.name
                assert not out_file_path.exists()
                with node.base.repository.open(file_key, 'rb') as in_file:
                    with out_file_path.open('wb') as out_file:
                        shutil.copyfileobj(in_file, out_file)

    _copy_tree(key='', output_dir=output_directory)


@verdi_node.command('label')
@arguments.NODES()
@options.LABEL(help='Set LABEL as the new label for all NODES')
@options.RAW(help='Display only the labels, no extra information')
@options.FORCE()
@with_dbenv()
def node_label(nodes, label, raw, force):
    """View or set the label of one or more nodes."""
    table = []

    if label is None:
        for node in nodes:

            if raw:
                table.append([node.label])
            else:
                table.append([node.pk, node.label])

        if raw:
            echo.echo(tabulate.tabulate(table, tablefmt='plain'))
        else:
            echo.echo(tabulate.tabulate(table, headers=['ID', 'Label']))

    else:
        if not force:
            warning = f'Are you sure you want to set the label for {len(nodes)} nodes?'
            click.confirm(warning, abort=True)

        for node in nodes:
            node.label = label

        echo.echo_success(f"Set label '{label}' for {len(nodes)} nodes")


@verdi_node.command('description')
@arguments.NODES()
@options.DESCRIPTION(help='Set DESCRIPTION as the new description for all NODES', default=None)
@options.RAW(help='Display only descriptions, no extra information')
@options.FORCE()
@with_dbenv()
def node_description(nodes, description, force, raw):
    """View or set the description of one or more nodes."""
    table = []

    if description is None:
        for node in nodes:

            if raw:
                table.append([node.description])
            else:
                table.append([node.pk, node.description])

        if raw:
            echo.echo(tabulate.tabulate(table, tablefmt='plain'))
        else:
            echo.echo(tabulate.tabulate(table, headers=['ID', 'Description']))

    else:
        if not force:
            warning = f'Are you sure you want to set the description for  {len(nodes)} nodes?'
            click.confirm(warning, abort=True)

        for node in nodes:
            node.description = description

        echo.echo_success(f'Set description for {len(nodes)} nodes')


@verdi_node.command('show')
@arguments.NODES()
@click.option('--print-groups', 'print_groups', flag_value=True, help='Show groups containing the nodes.')
@with_dbenv()
def node_show(nodes, print_groups):
    """Show generic information on one or more nodes."""
    from aiida.cmdline.utils.common import get_node_info

    for node in nodes:
        # pylint: disable=fixme
        # TODO: Add a check here on the node type, otherwise it might try to access
        # attributes such as code which are not necessarily there
        echo.echo(get_node_info(node))

        if print_groups:
            from aiida.orm import Node  # pylint: disable=redefined-outer-name
            from aiida.orm.groups import Group
            from aiida.orm.querybuilder import QueryBuilder

            # pylint: disable=invalid-name
            qb = QueryBuilder()
            qb.append(Node, tag='node', filters={'id': {'==': node.pk}})
            qb.append(Group, tag='groups', with_node='node', project=['id', 'label', 'type_string'])

            echo.echo('#### GROUPS:')

            if qb.count() == 0:
                echo.echo(f'Node {node.pk} does not belong to any group')
            else:
                echo.echo(f'Node {node.pk} belongs to the following groups:')
                res = qb.iterdict()
                table = [(gr['groups']['id'], gr['groups']['label'], gr['groups']['type_string']) for gr in res]
                table.sort()

                echo.echo(tabulate.tabulate(table, headers=['PK', 'Label', 'Group type']))


def echo_node_dict(nodes, keys, fmt, identifier, raw, use_attrs=True):
    """Show the attributes or extras of one or more nodes."""
    all_nodes = []
    for node in nodes:
        if identifier == 'pk':
            id_name = 'PK'
            id_value = node.pk
        else:
            id_name = 'UUID'
            id_value = node.uuid

        if use_attrs:
            node_dict = node.base.attributes.all
            dict_name = 'attributes'
        else:
            node_dict = node.base.extras.all
            dict_name = 'extras'

        if keys is not None:
            node_dict = {k: v for k, v in node_dict.items() if k in keys}

        if raw:
            all_nodes.append({id_name: id_value, dict_name: node_dict})
        else:
            echo.echo(f'{id_name}: {id_value}', bold=True)
            echo.echo_dictionary(node_dict, fmt=fmt)
    if raw:
        echo.echo_dictionary(all_nodes, fmt=fmt)


@verdi_node.command('attributes')
@arguments.NODES()
@options.DICT_KEYS()
@options.DICT_FORMAT()
@options.IDENTIFIER()
@options.RAW(help='Print the results as a single dictionary.')
@with_dbenv()
def attributes(nodes, keys, fmt, identifier, raw):
    """Show the attributes of one or more nodes."""
    echo_node_dict(nodes, keys, fmt, identifier, raw)


@verdi_node.command('extras')
@arguments.NODES()
@options.DICT_KEYS()
@options.DICT_FORMAT()
@options.IDENTIFIER()
@options.RAW(help='Print the results as a single dictionary.')
@with_dbenv()
def extras(nodes, keys, fmt, identifier, raw):
    """Show the extras of one or more nodes."""
    echo_node_dict(nodes, keys, fmt, identifier, raw, use_attrs=False)


@verdi_node.command('delete')
@click.argument('identifier', nargs=-1, metavar='NODES')
@options.DRY_RUN()
@options.FORCE()
@options.graph_traversal_rules(GraphTraversalRules.DELETE.value)
@with_dbenv()
def node_delete(identifier, dry_run, force, **traversal_rules):
    """Delete nodes from the provenance graph.

    This will not only delete the nodes explicitly provided via the command line, but will also include
    the nodes necessary to keep a consistent graph, according to the rules outlined in the documentation.
    You can modify some of those rules using options of this command.
    """
    from aiida.orm.utils.loaders import NodeEntityLoader
    from aiida.tools import delete_nodes

    pks = []

    for obj in identifier:
        # we only load the node if we need to convert from a uuid/label
        try:
            pks.append(int(obj))
        except ValueError:
            pks.append(NodeEntityLoader.load_entity(obj).pk)

    def _dry_run_callback(pks):
        if not pks or force:
            return False
        echo.echo_warning(f'YOU ARE ABOUT TO DELETE {len(pks)} NODES! THIS CANNOT BE UNDONE!')
        return not click.confirm('Shall I continue?', abort=True)

    _, was_deleted = delete_nodes(pks, dry_run=dry_run or _dry_run_callback, **traversal_rules)

    if was_deleted:
        echo.echo_success('Finished deletion.')


@verdi_node.command('rehash')
@arguments.NODES()
@click.option(
    '-e',
    '--entry-point',
    type=PluginParamType(group=('aiida.calculations', 'aiida.data', 'aiida.workflows'), load=True),
    default=None,
    help='Only include nodes that are class or sub class of the class identified by this entry point.'
)
@options.FORCE()
@with_dbenv()
def rehash(nodes, entry_point, force):
    """Recompute the hash for nodes in the database.

    The set of nodes that will be rehashed can be filtered by their identifier and/or based on their class.
    """
    from aiida.orm import Data, ProcessNode, QueryBuilder

    if not force:
        echo.echo_warning('This command will recompute and overwrite the hashes of all nodes.')
        echo.echo_warning('Note that this can take a lot of time for big databases.')
        echo.echo_warning('')
        echo.echo_warning('', nl=False)

        confirm_message = 'Do you want to continue?'

        try:
            click.confirm(text=confirm_message, abort=True)
        except click.Abort:
            echo.echo('\n')
            echo.echo_critical('Migration aborted, the data has not been affected.')

    # If no explicit entry point is defined, rehash all nodes, which are either Data nodes or ProcessNodes
    if entry_point is None:
        entry_point = (Data, ProcessNode)

    if nodes:
        to_hash = [(node,) for node in nodes if isinstance(node, entry_point)]
        num_nodes = len(to_hash)
    else:
        builder = QueryBuilder()
        builder.append(entry_point, tag='node')
        to_hash = builder.all()
        num_nodes = builder.count()

    if not to_hash:
        echo.echo_critical('no matching nodes found')

    with click.progressbar(to_hash, label='Rehashing Nodes:') as iter_hash:
        for node, in iter_hash:
            node.base.caching.rehash()

    echo.echo_success(f'{num_nodes} nodes re-hashed.')


@verdi_node.group('graph')
def verdi_graph():
    """Create visual representations of the provenance graph."""


@verdi_graph.command('generate')
@arguments.NODE('root_node')
@click.option(
    '-l',
    '--link-types',
    help=(
        'The link types to include: '
        "'data' includes only 'input_calc' and 'create' links (data provenance only), "
        "'logic' includes only 'input_work' and 'return' links (logical provenance only)."
    ),
    default='all',
    type=click.Choice(['all', 'data', 'logic'])
)
@click.option(
    '--identifier',
    help='the type of identifier to use within the node text',
    default='uuid',
    type=click.Choice(['pk', 'uuid', 'label'])
)
@click.option(
    '-a',
    '--ancestor-depth',
    help='The maximum depth when recursing upwards, if not set it will recurse to the end.',
    type=click.IntRange(min=0)
)
@click.option(
    '-d',
    '--descendant-depth',
    help='The maximum depth when recursing through the descendants. If not set it will recurse to the end.',
    type=click.IntRange(min=0)
)
@click.option('-o', '--process-out', is_flag=True, help='Show outgoing links for all processes.')
@click.option('-i', '--process-in', is_flag=True, help='Show incoming links for all processes.')
@click.option(
    '-e',
    '--engine',
    help="The graphviz engine, e.g. 'dot', 'circo', ... "
    '(see http://www.graphviz.org/doc/info/output.html)',
    default='dot'
)
@click.option('-f', '--output-format', help="The output format used for rendering ('pdf', 'png', etc.).", default='pdf')
@click.option(
    '-c',
    '--highlight-classes',
    help=
    "Only color nodes of specific class label (as displayed in the graph, e.g. 'StructureData', 'FolderData', etc.).",
    type=click.STRING,
    default=None,
    multiple=True
)
@click.option('-s', '--show', is_flag=True, help='Open the rendered result with the default application.')
@decorators.with_dbenv()
def graph_generate(
    root_node, link_types, identifier, ancestor_depth, descendant_depth, process_out, process_in, engine, output_format,
    highlight_classes, show
):
    """
    Generate a graph from a ROOT_NODE (specified by pk or uuid).
    """
    # pylint: disable=too-many-arguments
    from aiida.tools.visualization import Graph
    link_types = {'all': (), 'logic': ('input_work', 'return'), 'data': ('input_calc', 'create')}[link_types]

    echo.echo_info(f'Initiating graphviz engine: {engine}')
    graph = Graph(engine=engine, node_id_type=identifier)
    echo.echo_info(f'Recursing ancestors, max depth={ancestor_depth}')

    graph.recurse_ancestors(
        root_node,
        depth=ancestor_depth,
        link_types=link_types,
        annotate_links='both',
        include_process_outputs=process_out,
        highlight_classes=highlight_classes,
    )
    echo.echo_info(f'Recursing descendants, max depth={descendant_depth}')
    graph.recurse_descendants(
        root_node,
        depth=descendant_depth,
        link_types=link_types,
        annotate_links='both',
        include_process_inputs=process_in,
        highlight_classes=highlight_classes,
    )
    output_file_name = graph.graphviz.render(
        filename=f'{root_node.pk}.{engine}', format=output_format, view=show, cleanup=True
    )

    echo.echo_success(f'Output file: {output_file_name}')


@verdi_node.group('comment')
def verdi_comment():
    """Inspect, create and manage node comments."""


@verdi_comment.command('add')
@options.NODES(required=True)
@click.argument('content', type=click.STRING, required=False)
@decorators.with_dbenv()
def comment_add(nodes, content):
    """Add a comment to one or more nodes."""
    if not content:
        content = multi_line_input.edit_comment()

    for node in nodes:
        node.base.comments.add(content)

    echo.echo_success(f'comment added to {len(nodes)} nodes')


@verdi_comment.command('update')
@click.argument('comment_id', type=int, metavar='COMMENT_ID')
@click.argument('content', type=click.STRING, required=False)
@decorators.with_dbenv()
def comment_update(comment_id, content):
    """Update a comment of a node."""
    from aiida.orm.comments import Comment

    try:
        comment = Comment.collection.get(id=comment_id)
    except (exceptions.NotExistent, exceptions.MultipleObjectsError):
        echo.echo_critical(f'comment<{comment_id}> not found')

    if content is None:
        content = multi_line_input.edit_comment(comment.content)

    comment.set_content(content)

    echo.echo_success(f'comment<{comment_id}> updated')


@verdi_comment.command('show')
@options.USER()
@arguments.NODES()
@decorators.with_dbenv()
def comment_show(user, nodes):
    """Show the comments of one or multiple nodes."""
    for node in nodes:
        msg = f'* Comments for Node<{node.pk}>'
        echo.echo('*' * len(msg))
        echo.echo(msg)
        echo.echo('*' * len(msg))

        all_comments = node.base.comments.all()

        if user is not None:
            comments = [comment for comment in all_comments if comment.user.email == user.email]

            if not comments:
                valid_users = ', '.join(set(comment.user.email for comment in all_comments))
                echo.echo_warning(f'no comments found for user {user}')
                echo.echo_report(f'valid users found for Node<{node.pk}>: {valid_users}')

        else:
            comments = all_comments

        for comment in comments:
            comment_msg = [
                f'Comment<{comment.pk}> for Node<{node.pk}> by {comment.user.email}',
                f"Created on {timezone.localtime(comment.ctime).strftime('%Y-%m-%d %H:%M')}",
                f"Last modified on {timezone.localtime(comment.mtime).strftime('%Y-%m-%d %H:%M')}",
                f'\n{comment.content}\n',
            ]
            echo.echo('\n'.join(comment_msg))

        if not comments:
            echo.echo_report('no comments found')


@verdi_comment.command('remove')
@options.FORCE()
@click.argument('comment', type=int, required=True, metavar='COMMENT_ID')
@decorators.with_dbenv()
def comment_remove(force, comment):
    """Remove a comment of a node."""
    from aiida.orm.comments import Comment

    if not force:
        click.confirm(f'Are you sure you want to remove comment<{comment}>', abort=True)

    try:
        Comment.collection.delete(comment)
    except exceptions.NotExistent as exception:
        echo.echo_critical(f'failed to remove comment<{comment}>: {exception}')
    else:
        echo.echo_success(f'removed comment<{comment}>')
