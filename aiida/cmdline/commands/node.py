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

from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.cmdline import delayed_load_node as load_node
from aiida.cmdline.baseclass import (VerdiCommandRouter, VerdiCommandWithSubcommands)
from aiida.cmdline.commands import verdi, verdi_node, verdi_node_repo

from aiida.cmdline.utils import echo
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.cmdline.params import options, arguments


class Node(VerdiCommandRouter):
    """
    Manage operations on AiiDA nodes

    There is a list of subcommands for managing specific types of data.
    For instance, 'node repo' manages the files in the local repository.
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        super(Node, self).__init__()
        self.routed_subcommands = {
            'repo': _Repo,
            'show': verdi,
            'tree': verdi,
            'delete': verdi,
            'label': verdi,
            'description': verdi,
        }


# Note: this class should not be exposed directly in the main module,
# otherwise it becomes a command of 'verdi'. Instead, we want it to be a
# subcommand of verdi data.
class _Repo(VerdiCommandWithSubcommands):
    """
    Show files and their contents in the local repository
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        super(_Repo, self).__init__()
        self.valid_subcommands = {
            'ls': (verdi, self.complete_none),
            'cat': (verdi, self.complete_none),
        }


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
@options.DESCRIPTION(help='Set DESCRIPTION as the new description for all NODES')
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


# the classes _Label and _Description are written here,
# but in fact they are called by the verdi calculation or verdi data
# in fact, I don't want to allow the possibility of changing labels or
# descriptions of codes, for that there is a separate command


class _Label(VerdiCommandWithSubcommands):
    """
    See or modify the label of one or more set of nodes
    """

    def __init__(self, node_subclass='data'):
        super(_Label, self).__init__()
        self._node_subclass = node_subclass
        if self._node_subclass not in ['calculation', 'data']:
            raise ValueError("Class must be loaded with a valid node_subclass")

    def _node_class_ok(self, node):
        """Check whether node class is recognized."""
        from aiida.orm import Calculation as OrmCalculation
        from aiida.orm import Data as OrmData

        if self._node_subclass == 'calculation':
            return isinstance(node, OrmCalculation)
        elif self._node_subclass == 'data':
            return isinstance(node, OrmData)
        else:
            raise ValueError("node_subclass not recognized")

    # pylint: disable=too-many-branches
    def run(self, *args):
        if not is_dbenv_loaded():
            load_dbenv()
        import argparse
        from aiida.cmdline import wait_for_confirmation

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(), description="See/modify the labels of Nodes.")
        # display parameters
        parser.add_argument(
            '-r', '--raw', action='store_true', default=False, help="Display only the labels, without the pk.")
        # pks
        parser.add_argument('pks', type=int, nargs='+', help="a list of nodes to show.")
        # parameters for label modification
        parser.add_argument(
            '-s',
            '--set',
            action='store_true',
            default=False,
            help="If present, set a new label, otherwise only "
            "show the labels.")
        parser.add_argument('-f', '--force', action='store_true', default=False, help="Force the reset of the label.")
        parser.add_argument(
            '-l',
            '--label',
            type=str,
            default=None,
            help="The new label to be set on the node. Note: "
            "pass it between quotes.")

        parsed_args = parser.parse_args(args)
        raw = parsed_args.raw
        # pylint: disable=invalid-name
        pks = parsed_args.pks

        if not parsed_args.set:
            for pk in pks:
                node = load_node(pk)
                if not self._node_class_ok(node):
                    print "Node {} is not a subclass of {}. Exiting...".format(pk, self._node_subclass)
                    sys.exit(1)
                if raw:
                    print '"{}"'.format(node.label)
                else:
                    if not node.label:
                        print 'Node {}, label: n.a.'.format(pk)
                    else:
                        print 'Node {}, label: "{}"'.format(pk, node.label)
        else:
            if len(pks) > 1:
                sys.stderr.write("More than one node found to set one label" ". Exiting...\n")
                sys.exit(1)
            else:
                pk = pks[0]

            new_label = parsed_args.label
            if new_label is None:
                sys.stderr.write("A new label is required" ". Exiting...\n")
                sys.exit(1)

            node = load_node(pk)

            if not self._node_class_ok(node):
                print "Node {} is not a subclass of {}. Exiting...".format(pk, self._node_subclass)
                sys.exit(1)

            old_label = node.label
            if not parsed_args.force:
                sys.stderr.write("Current label is: {}\n".format(old_label))
                sys.stderr.write("New label is: {}\n".format(new_label))
                sys.stderr.write("Are you sure you want to reset the label? " "[Y/N] ")
                if not wait_for_confirmation():
                    sys.exit(0)

            node.label = new_label


class _Description(VerdiCommandWithSubcommands):
    """
    See or modify the label of one or more set of nodes
    """

    def __init__(self, node_subclass='data'):
        super(_Description, self).__init__()
        self._node_subclass = node_subclass
        if self._node_subclass not in ['calculation', 'data']:
            raise ValueError("Class must be loaded with a valid node_subclass")

    def _node_class_ok(self, node):
        """Check whether node class is recognized."""
        from aiida.orm import Calculation as OrmCalculation
        from aiida.orm import Data as OrmData

        if self._node_subclass == 'calculation':
            return isinstance(node, OrmCalculation)
        elif self._node_subclass == 'data':
            return isinstance(node, OrmData)
        else:
            raise ValueError("node_subclass not recognized")

    # pylint: disable=too-many-statements,too-many-branches
    def run(self, *args):
        if not is_dbenv_loaded():
            load_dbenv()
        import argparse
        from aiida.cmdline import wait_for_confirmation

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description="See description of Nodes. If no node "
            "description or label is found, prints n.a.")

        # parameters for display
        parser.add_argument('-n', '--no-labels', action='store_false', default=True, help="Don't show the labels.")
        parser.add_argument(
            '-r',
            '--raw',
            action='store_true',
            default=False,
            help="If set, prints only the description without "
            "pks or labels.")
        # pks
        parser.add_argument('pks', type=int, nargs='+', help="a list of node pks to show.")
        # parameters for description modifications
        parser.add_argument(
            '-s',
            '--set',
            action='store_true',
            default=False,
            help="If present, set a new label, otherwise only "
            "show the labels.")
        parser.add_argument(
            '-a',
            '--add-to-description',
            action='store_true',
            default=False,
            help="If -s, the string passed in -d is appended "
            "to the current description.")
        parser.add_argument(
            '-f', '--force', action='store_true', default=False, help="Force the reset of the description.")
        parser.add_argument(
            '-d',
            '--description',
            type=str,
            help="The new description to be set on the node. "
            "Note: pass it between quotes.")

        parsed_args = parser.parse_args(args)

        # pylint: disable=invalid-name
        pks = parsed_args.pks

        if not parsed_args.set:
            also_labels = parsed_args.no_labels
            for pk in pks:
                n = load_node(pk)

                if not self._node_class_ok(n):
                    echo.echo_critical("Node {} is not a subclass of {}. Exiting...".format(pk, self._node_subclass))

                label = n.label
                description = n.description

                if parsed_args.raw:
                    echo.echo('"{}"'.format(n.description))
                    echo.echo("")

                else:
                    echo.echo("Node pk: {}".format(pk))
                    if also_labels:
                        if label:
                            echo.echo('Label: "{}"'.format(label))
                        else:
                            echo.echo('Label: n.a.')
                    if description:
                        echo.echo('Description: "{}"'.format(description))
                    else:
                        echo.echo('Description: n.a.')
                    echo.echo("")
        else:
            # check that only one pk is present
            if len(pks) > 1:
                sys.stderr.write("More than one node found to set one description" ". Exiting...\n")
                sys.exit(1)
            else:
                pk = pks[0]

            new_description = parsed_args.description
            if new_description is None:
                sys.stderr.write("No description was found. Exiting...\n")
                sys.exit(1)

            if not parsed_args.add_to_description:
                n = load_node(pk)
                if not self._node_class_ok(n):
                    echo.echo_critical("Node {} is not a subclass of {}. Exiting...".format(pk, self._node_subclass))

                old_description = n.description
                if not parsed_args.force:
                    sys.stderr.write("Current description is: {}\n".format(old_description))
                    sys.stderr.write("New description is: {}\n".format(new_description))
                    sys.stderr.write("Are you sure you want to reset the description? " "[Y/N] ")
                    if not wait_for_confirmation():
                        sys.exit(0)

                n.description = new_description

            else:
                n = load_node(pk)
                if not self._node_class_ok(n):
                    echo.echo_critical("Node {} is not a subclass of {}. Exiting...".format(pk, self._node_subclass))

                old_description = n.description
                new_description = old_description + "\n" + new_description
                n.description = new_description
