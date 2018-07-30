# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""""
Manipulating and printing information of nodes.
"""
import sys
import click
import tabulate

from aiida.cmdline.commands import verdi
from aiida.cmdline.params import options, arguments
from aiida.cmdline.utils import echo
from aiida.cmdline.utils.decorators import with_dbenv


@verdi.group('node')
def verdi_node():
    """Inspect, create and manage nodes."""
    pass


@verdi_node.group('repo')
def verdi_node_repo():
    pass


@verdi_node_repo.command('cat')
@arguments.NODE()
@click.argument('relative_path', type=str)
@with_dbenv()
def repo_cat(node, relative_path):
    """Output the content of a file in the repository folder."""
    try:
        cat_repo_files(node, relative_path)
    except ValueError as exc:
        echo.echo_critical(exc.message)
    except IOError as exc:
        import errno
        # Ignore Broken pipe errors, re-raise everything else
        if exc.errno == errno.EPIPE:
            pass
        else:
            echo.echo_critical(exc.message)


def cat_repo_files(node, path):
    """
    Given a Node and a relative path to a file in the Node repository directory,
    prints in output the content of the file.

    :param node: a Node instance
    :param path: a string with the relative path to list. Must be a file.
    :raise ValueError: if the file is not found, or is a directory.
    """
    import os

    fldr = node.folder

    is_dir = False
    parts = path.split(os.path.sep)
    # except the last item
    for item in parts[:-1]:
        fldr = fldr.get_subfolder(item)
    if parts:
        if fldr.isdir(parts[-1]):
            fldr = fldr.get_subfolder(parts[-1])
            is_dir = True
        else:
            fname = parts[-1]
    else:
        is_dir = True

    if is_dir:
        if not fldr.isdir('.'):
            raise ValueError("No directory '{}' in the repo".format(path))
        else:
            raise ValueError("'{}' is a directory".format(path))
    else:
        if not fldr.isfile(fname):
            raise ValueError("No file '{}' in the repo".format(path))

        absfname = fldr.get_abs_path(fname)
        with open(absfname) as repofile:
            for line in repofile:
                sys.stdout.write(line)


@verdi_node_repo.command('ls')
@arguments.NODE()
@click.argument('relative_path', type=str, default='.')
@click.option('-c', '--color', 'color', flag_value=True, help="Use different color for folders and files.")
@with_dbenv()
def repo_ls(node, relative_path, color):
    """List files in the repository folder."""

    try:
        list_repo_files(node, relative_path, color)
    except ValueError as exc:
        echo.echo_critical(exc.message)


def list_repo_files(node, path, color):
    """
    Given a Node and a relative path prints in output the list of files
    in the given path in the Node repository directory.

    :param node: a Node instance
    :param path: a string with the relative path to list. Can be a file.
    :param color: boolean, if True prints with the codes to show colors.
    :raise ValueError: if the file or directory is not found.
    """
    import os

    fldr = node.folder

    is_dir = False
    parts = path.split(os.path.sep)
    # except the last item
    for item in parts[:-1]:
        fldr = fldr.get_subfolder(item)
    if parts:
        if fldr.isdir(parts[-1]):
            fldr = fldr.get_subfolder(parts[-1])
            is_dir = True
        else:
            fname = parts[-1]
    else:
        is_dir = True

    if is_dir:
        if not fldr.isdir('.'):
            raise ValueError("{}: No such file or directory in the repo".format(path))

        for elem, elem_is_file in sorted(fldr.get_content_list(only_paths=False)):
            if elem_is_file or not color:
                print elem
            else:
                # BOLD("1;") and color 34=blue
                outstr = "\x1b[1;{color_id}m{elem}\x1b[0m".format(color_id=34, elem=elem)
                print outstr
    else:
        if not fldr.isfile(fname):
            raise ValueError("{}: No such file or directory in the repo".format(path))

        print fname


@verdi_node.command('label')
@arguments.NODES()
@options.LABEL(help='Set LABEL as the new label for all NODES')
@options.RAW(help='Display only the labels, no extra information')
@options.FORCE()
@with_dbenv()
def node_label(nodes, label, raw, force):
    """View or set the labels of one or more nodes."""
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
    """View or set the descriptions of one or more nodes."""
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

        echo.echo_success("Set description for {} nodes".format(len(nodes)))


@verdi_node.command('show')
@arguments.NODES()
@click.option('--print-groups', 'print_groups', flag_value=True, help="Show groups containing the nodes.")
@with_dbenv()
def show(nodes, print_groups):
    """Show generic information on node(s)."""
    from aiida.cmdline.utils.common import get_node_info

    for node in nodes:
        # pylint: disable=fixme
        #TODO: Add a check here on the node type, otherwise it might try to access
        # attributes such as code which are not necessarily there
        echo.echo(get_node_info(node))

        if print_groups:
            from aiida.orm.querybuilder import QueryBuilder
            from aiida.orm.group import Group
            from aiida.orm.node import Node  # pylint: disable=redefined-outer-name

            # pylint: disable=invalid-name
            qb = QueryBuilder()
            qb.append(Node, tag='node', filters={'id': {'==': node.pk}})
            qb.append(Group, tag='groups', group_of='node', project=['id', 'name'])

            echo.echo("#### GROUPS:")

            if qb.count() == 0:
                echo.echo("No groups found containing node {}".format(node.pk))
            else:
                res = qb.iterdict()
                for gr in res:
                    gr_specs = "{} {}".format(gr['groups']['name'], gr['groups']['id'])
                    echo.echo(gr_specs)


@verdi_node.command()
@arguments.NODES()
@click.option('-d', '--depth', 'depth', default=1, help="Show children of nodes up to given depth")
@with_dbenv()
def tree(nodes, depth):
    """
    Show trees of nodes.
    """
    for node in nodes:
        NodeTreePrinter.print_node_tree(node, depth)

        if len(nodes) > 1:
            echo.echo("")


class NodeTreePrinter(object):
    """Utility functions for printing node trees."""

    @classmethod
    def print_node_tree(cls, node, max_depth, follow_links=None):
        """Top-level function for printing node tree."""
        from ete3 import Tree
        from aiida.cmdline.utils.common import get_node_summary

        echo.echo(get_node_summary(node))

        tree_string = '({});'.format(cls._build_tree(node, max_depth=max_depth, follow_links=follow_links))
        tmp = Tree(tree_string, format=1)
        echo.echo(tmp.get_ascii(show_internal=True))

    @staticmethod
    def _ctime(nodelab):
        return nodelab[1].ctime

    @classmethod
    def _build_tree(cls, node, show_pk=True, max_depth=None, follow_links=None, depth=0):
        """Return string with tree."""
        if max_depth is not None and depth > max_depth:
            return None

        children = []
        # pylint: disable=unused-variable
        for label, child \
                in sorted(node.get_outputs(also_labels=True,
                                           link_type=follow_links),
                          key=cls._ctime):
            child_str = cls._build_tree(child, show_pk, follow_links=follow_links, max_depth=max_depth, depth=depth + 1)
            if child_str:
                children.append(child_str)

        out_values = []
        if children:
            out_values.append("(")
            out_values.append(", ".join(children))
            out_values.append(")")

        lab = node.__class__.__name__

        if show_pk:
            lab += " [{}]".format(node.pk)

        out_values.append(lab)

        return "".join(out_values)


@verdi_node.command('delete')
@arguments.NODES('nodes')
@click.option('-c', '--follow-calls', is_flag=True, help='follow call links downwards when deleting')
# Commenting also the option for follow returns. This is dangerous for the inexperienced user.
#@click.option('-r', '--follow-returns', is_flag=True, help='follow return links downwards when deleting')
@click.option(
    '-n', '--dry-run', is_flag=True, help='dry run, does not delete')
@click.option('-v', '--verbose', is_flag=True, help='print individual nodes marked for deletion.')
@options.NON_INTERACTIVE()
@with_dbenv()
def node_delete(nodes, follow_calls, dry_run, verbose, non_interactive):
    """
    Deletes a node and everything that originates from it.
    """
    from aiida.utils.delete_nodes import delete_nodes

    if not nodes:
        return

    verbosity = 1
    if non_interactive:
        verbosity = 0
    elif verbose:
        verbosity = 2

    node_pks_to_delete = [node.pk for node in nodes]

    delete_nodes(
        node_pks_to_delete, follow_calls=follow_calls, dry_run=dry_run, verbosity=verbosity, force=non_interactive)
