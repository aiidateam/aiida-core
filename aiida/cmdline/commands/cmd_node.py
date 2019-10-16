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
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click
import tabulate

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options, arguments
from aiida.cmdline.params.types.plugin import PluginParamType
from aiida.cmdline.utils import decorators, echo, multi_line_input
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common import exceptions
from aiida.common import timezone
from aiida.common.links import GraphTraversalRules


@verdi.group('node')
def verdi_node():
    """Inspect, create and manage nodes."""


@verdi_node.group('repo')
def verdi_node_repo():
    """Inspect the content of a node repository folder."""


@verdi_node_repo.command('cat')
@arguments.NODE()
@click.argument('relative_path', type=str)
@with_dbenv()
def repo_cat(node, relative_path):
    """Output the content of a file in the node repository folder."""
    try:
        content = node.get_object_content(relative_path)
    except Exception as exception:  # pylint: disable=broad-except
        echo.echo_critical('failed to get the content of file `{}`: {}'.format(relative_path, exception))
    else:
        echo.echo(content)


@verdi_node_repo.command('ls')
@arguments.NODE()
@click.argument('relative_path', type=str, default='.')
@click.option('-c', '--color', 'color', flag_value=True, help='Use different color for folders and files.')
@with_dbenv()
def repo_ls(node, relative_path, color):
    """List files in the node repository folder."""
    from aiida.cmdline.utils.repository import list_repository_contents

    try:
        list_repository_contents(node, relative_path, color)
    except ValueError as exception:
        echo.echo_critical(exception)


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
            warning = 'Are you sure you want to set the label for {} nodes?'.format(len(nodes))
            click.confirm(warning, abort=True)

        for node in nodes:
            node.label = label

        echo.echo_success("Set label '{}' for {} nodes".format(label, len(nodes)))


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
            warning = 'Are you sure you want to set the description for  {} nodes?'.format(len(nodes))
            click.confirm(warning, abort=True)

        for node in nodes:
            node.description = description

        echo.echo_success('Set description for {} nodes'.format(len(nodes)))


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
            from aiida.orm.querybuilder import QueryBuilder
            from aiida.orm.groups import Group
            from aiida.orm import Node  # pylint: disable=redefined-outer-name

            # pylint: disable=invalid-name
            qb = QueryBuilder()
            qb.append(Node, tag='node', filters={'id': {'==': node.pk}})
            qb.append(Group, tag='groups', with_node='node', project=['id', 'name'])

            echo.echo('#### GROUPS:')

            if qb.count() == 0:
                echo.echo('No groups found containing node {}'.format(node.pk))
            else:
                res = qb.iterdict()
                for gr in res:
                    gr_specs = '{} {}'.format(gr['groups']['name'], gr['groups']['id'])
                    echo.echo(gr_specs)


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
            node_dict = node.attributes
            dict_name = 'attributes'
        else:
            node_dict = node.extras
            dict_name = 'extras'

        if keys is not None:
            node_dict = {k: v for k, v in node_dict.items() if k in keys}

        if raw:
            all_nodes.append({id_name: id_value, dict_name: node_dict})
        else:
            echo.echo('{}: {}'.format(id_name, id_value), bold=True)
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


@verdi_node.command()
@arguments.NODES()
@click.option('-d', '--depth', 'depth', default=1, help='Show children of nodes up to given depth')
@with_dbenv()
def tree(nodes, depth):
    """Show a tree of nodes starting from a given node."""
    from aiida.common import LinkType

    for node in nodes:
        NodeTreePrinter.print_node_tree(node, depth, tuple(LinkType.__members__.values()))

        if len(nodes) > 1:
            echo.echo('')


class NodeTreePrinter(object):
    """Utility functions for printing node trees."""

    @classmethod
    def print_node_tree(cls, node, max_depth, follow_links=()):
        """Top-level function for printing node tree."""
        from ete3 import Tree
        from aiida.cmdline.utils.common import get_node_summary

        echo.echo(get_node_summary(node))

        tree_string = '({});'.format(cls._build_tree(node, max_depth=max_depth, follow_links=follow_links))
        tmp = Tree(tree_string, format=1)
        echo.echo(tmp.get_ascii(show_internal=True))

    @staticmethod
    def _ctime(link_triple):
        return link_triple.node.ctime

    @classmethod
    def _build_tree(cls, node, show_pk=True, max_depth=None, follow_links=(), depth=0):
        """Return string with tree."""
        if max_depth is not None and depth > max_depth:
            return None

        children = []
        for entry in sorted(node.get_outgoing(link_type=follow_links).all(), key=cls._ctime):
            child_str = cls._build_tree(
                entry.node, show_pk, follow_links=follow_links, max_depth=max_depth, depth=depth + 1
            )
            if child_str:
                children.append(child_str)

        out_values = []
        if children:
            out_values.append('(')
            out_values.append(', '.join(children))
            out_values.append(')')

        lab = node.__class__.__name__

        if show_pk:
            lab += ' [{}]'.format(node.pk)

        out_values.append(lab)

        return ''.join(out_values)


@verdi_node.command('delete')
@arguments.NODES('nodes', required=True)
@options.VERBOSE()
@options.DRY_RUN()
@options.FORCE()
@options.graph_traversal_rules(GraphTraversalRules.DELETE.value)
@with_dbenv()
def node_delete(nodes, dry_run, verbose, force, **kwargs):
    """Delete nodes from the database.

    Please note that this will not only delete the nodes explicitly provided via the command line, but will also include
    the nodes necessary to keep a consistent graph, according to the rules outlined in the documentation.
    """
    from aiida.manage.database.delete.nodes import delete_nodes

    verbosity = 1
    if force:
        verbosity = 0
    elif verbose:
        verbosity = 2

    node_pks_to_delete = [node.pk for node in nodes]

    delete_nodes(node_pks_to_delete, dry_run=dry_run, verbosity=verbosity, force=force, **kwargs)


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
            node.rehash()

    echo.echo_success('{} nodes re-hashed.'.format(num_nodes))


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
@options.VERBOSE(help='Print verbose information of the graph traversal.')
@click.option(
    '-e',
    '--engine',
    help="The graphviz engine, e.g. 'dot', 'circo', ... "
    '(see http://www.graphviz.org/doc/info/output.html)',
    default='dot'
)
@click.option('-f', '--output-format', help="The output format used for rendering ('pdf', 'png', etc.).", default='pdf')
@click.option('-s', '--show', is_flag=True, help='Open the rendered result with the default application.')
@decorators.with_dbenv()
def graph_generate(
    root_node, link_types, identifier, ancestor_depth, descendant_depth, process_out, process_in, engine, verbose,
    output_format, show
):
    """
    Generate a graph from a ROOT_NODE (specified by pk or uuid).
    """
    # pylint: disable=too-many-arguments
    from aiida.tools.visualization import Graph
    print_func = echo.echo_info if verbose else None
    link_types = {'all': (), 'logic': ('input_work', 'return'), 'data': ('input_calc', 'create')}[link_types]

    echo.echo_info('Initiating graphviz engine: {}'.format(engine))
    graph = Graph(engine=engine, node_id_type=identifier)
    echo.echo_info('Recursing ancestors, max depth={}'.format(ancestor_depth))
    graph.recurse_ancestors(
        root_node,
        depth=ancestor_depth,
        link_types=link_types,
        annotate_links='both',
        include_process_outputs=process_out,
        print_func=print_func
    )
    echo.echo_info('Recursing descendants, max depth={}'.format(descendant_depth))
    graph.recurse_descendants(
        root_node,
        depth=descendant_depth,
        link_types=link_types,
        annotate_links='both',
        include_process_inputs=process_in,
        print_func=print_func
    )
    output_file_name = graph.graphviz.render(
        filename='{}.{}'.format(root_node.pk, engine), format=output_format, view=show, cleanup=True
    )

    echo.echo_success('Output file: {}'.format(output_file_name))


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
        node.add_comment(content)

    echo.echo_success('comment added to {} nodes'.format(len(nodes)))


@verdi_comment.command('update')
@click.argument('comment_id', type=int, metavar='COMMENT_ID')
@click.argument('content', type=click.STRING, required=False)
@decorators.with_dbenv()
def comment_update(comment_id, content):
    """Update a comment of a node."""
    from aiida.orm.comments import Comment

    try:
        comment = Comment.objects.get(id=comment_id)
    except (exceptions.NotExistent, exceptions.MultipleObjectsError):
        echo.echo_critical('comment<{}> not found'.format(comment_id))

    if content is None:
        content = multi_line_input.edit_comment(comment.content)

    comment.set_content(content)

    echo.echo_success('comment<{}> updated'.format(comment_id))


@verdi_comment.command('show')
@options.USER()
@arguments.NODES()
@decorators.with_dbenv()
def comment_show(user, nodes):
    """Show the comments of one or multiple nodes."""
    for node in nodes:
        msg = '* Comments for Node<{}>'.format(node.pk)
        echo.echo('*' * len(msg))
        echo.echo(msg)
        echo.echo('*' * len(msg))

        all_comments = node.get_comments()

        if user is not None:
            comments = [comment for comment in all_comments if comment.user.email == user.email]

            if not comments:
                valid_users = ', '.join(set(comment.user.email for comment in all_comments))
                echo.echo_warning('no comments found for user {}'.format(user))
                echo.echo_info('valid users found for Node<{}>: {}'.format(node.pk, valid_users))

        else:
            comments = all_comments

        for comment in comments:
            comment_msg = [
                'Comment<{}> for Node<{}> by {}'.format(comment.id, node.pk, comment.user.email),
                'Created on {}'.format(timezone.localtime(comment.ctime).strftime('%Y-%m-%d %H:%M')),
                'Last modified on {}'.format(timezone.localtime(comment.mtime).strftime('%Y-%m-%d %H:%M')),
                '\n{}\n'.format(comment.content),
            ]
            echo.echo('\n'.join(comment_msg))

        if not comments:
            echo.echo_info('no comments found')


@verdi_comment.command('remove')
@options.FORCE()
@click.argument('comment', type=int, required=True, metavar='COMMENT_ID')
@decorators.with_dbenv()
def comment_remove(force, comment):
    """Remove a comment of a node."""
    from aiida.orm.comments import Comment

    if not force:
        click.confirm('Are you sure you want to remove comment<{}>'.format(comment), abort=True)

    try:
        Comment.objects.delete(comment)
    except exceptions.NotExistent as exception:
        echo.echo_critical('failed to remove comment<{}>: {}'.format(comment, exception))
    else:
        echo.echo_success('removed comment<{}>'.format(comment))
