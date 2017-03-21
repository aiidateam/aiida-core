# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import sys

from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.cmdline import delayed_load_node as load_node
from aiida.cmdline.baseclass import VerdiCommand
from aiida.cmdline.baseclass import (
    VerdiCommandRouter, VerdiCommandWithSubcommands)



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

    f = node.folder

    is_dir = False
    parts = path.split(os.path.sep)
    # except the last item
    for item in parts[:-1]:
        f = f.get_subfolder(item)
    if parts:
        if f.isdir(parts[-1]):
            f = f.get_subfolder(parts[-1])
            is_dir = True
        else:
            fname = parts[-1]
    else:
        is_dir = True

    if is_dir:
        if not f.isdir('.'):
            raise ValueError(
                "{}: No such file or directory in the repo".format(path))

        for elem, elem_is_file in sorted(f.get_content_list(only_paths=False)):
            if elem_is_file or not color:
                print elem
            else:
                # BOLD("1;") and color 34=blue
                outstr = "\x1b[1;{color_id}m{elem}\x1b[0m".format(color_id=34,
                                                                  elem=elem)
                print outstr
    else:
        if not f.isfile(fname):
            raise ValueError(
                "{}: No such file or directory in the repo".format(path))

        print fname


def cat_repo_files(node, path):
    """
    Given a Node and a relative path to a file in the Node repository directory,
    prints in output the content of the file.

    :param node: a Node instance
    :param path: a string with the relative path to list. Must be a file.
    :raise ValueError: if the file is not found, or is a directory.
    """
    import os

    f = node.folder

    is_dir = False
    parts = path.split(os.path.sep)
    # except the last item
    for item in parts[:-1]:
        f = f.get_subfolder(item)
    if parts:
        if f.isdir(parts[-1]):
            f = f.get_subfolder(parts[-1])
            is_dir = True
        else:
            fname = parts[-1]
    else:
        is_dir = True

    if is_dir:
        if not f.isdir('.'):
            raise ValueError(
                "{}: No such file or directory in the repo".format(path))
        else:
            raise ValueError("{}: is a directory".format(path))
    else:
        if not f.isfile(fname):
            raise ValueError(
                "{}: No such file or directory in the repo".format(path))

        absfname = f.get_abs_path(fname)
        with open(absfname) as f:
            for l in f:
                sys.stdout.write(l)


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
        ## Add here the classes to be supported.
        self.routed_subcommands = {
            'repo': _Repo,
            'show': _Show,
            'tree': _Tree
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
        self.valid_subcommands = {
            'ls': (self.ls, self.complete_none),
            'cat': (self.cat, self.complete_none),
        }

    def ls(self, *args):
        """
        List the files in the repository folder.
        """
        import argparse
        from aiida.common.exceptions import NotExistent

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='List files in the repository folder.')

        parser.add_argument('-c', '--color', action='store_true',
                            help="Color folders with a different color")
        parser.add_argument('-p', '--pk', type=int, required=True,
                            help='The pk of the node')
        parser.add_argument('path', type=str, default='.', nargs='?',
                            help='The relative path of the file you '
                                 'want to show')
        # parser.add_argument('-d', '--with-description',
        #                    dest='with_description',action='store_true',
        #                    help="Show also the description for the UPF family")
        # parser.set_defaults(with_description=False)

        args = list(args)
        parsed_args = parser.parse_args(args)

        if not is_dbenv_loaded():
            load_dbenv()

        try:
            n = load_node(parsed_args.pk)
        except NotExistent as e:
            print >> sys.stderr, e.message
            sys.exit(1)

        try:
            list_repo_files(n, parsed_args.path, parsed_args.color)
        except ValueError as e:
            print >> sys.stderr, e.message
            sys.exit(1)

    def cat(self, *args):
        """
        Output the content of a file in the repository folder.
        """
        import argparse
        from aiida.common.exceptions import NotExistent

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Output the content of a file in the repository folder.')
        parser.add_argument('-p', '--pk', type=int, required=True,
                            help='The pk of the node')
        parser.add_argument('path', type=str,
                            help='The relative path of the file you '
                                 'want to show')

        args = list(args)
        parsed_args = parser.parse_args(args)

        if not is_dbenv_loaded():
            load_dbenv()

        try:
            n = load_node(parsed_args.pk)
        except NotExistent as e:
            print >> sys.stderr, e.message
            sys.exit(1)

        try:
            cat_repo_files(n, parsed_args.path)
        except ValueError as e:
            print >> sys.stderr, e.message
            sys.exit(1)
        except IOError as e:
            import errno
            # Ignore Broken pipe errors, re-raise everything else
            if e.errno == errno.EPIPE:
                pass
            else:
                raise


class _Show(VerdiCommand):
    """
    Show node information (pk, uuid, class, inputs and outputs)
    """

    def run(self, *args):
        """
        Show node information.
        """
        import argparse
        from aiida.common.exceptions import NotExistent

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Show information of a node.')
        parser.add_argument('pk', type=int, default=None, nargs="+",
                            help="ID of the node.")
        parser.add_argument('--print-groups', action='store_true',
                            dest='print_groups', default=False,
                            help="Show groups containing the nodes.")
        parser.add_argument('--no-print-groups', '--dont-print-groups',
                            action='store_false', dest='print_groups',
                            default=False,
                            help="Do not show groups containing the nodes"
                                 "output. Default behaviour.")

        args = list(args)
        parsed_args = parser.parse_args(args)

        if not is_dbenv_loaded():
            load_dbenv()

        for pk in parsed_args.pk:
            try:
                n = load_node(pk)
                self.print_node_info(n, print_groups=parsed_args.print_groups)
            except NotExistent as e:
                print >> sys.stderr, e.message
                sys.exit(1)

            if len(parsed_args.pk) > 1:
                print ""

    def print_node_info(self, node, print_groups=False):
        from aiida.cmdline.common import print_node_info

###TODO
#Add a check here on the node type, otherwise it might try to access attributes such as code which are not necessarily there
#####
        print_node_info(node)

        if print_groups:
            from aiida.orm.querybuilder import QueryBuilder
            from aiida.orm.group import Group
            from aiida.orm.node import Node

            qb = QueryBuilder()
            qb.append(Node, tag='node', filters={'id': {'==': node.pk}})
            qb.append(Group, tag='groups', group_of='node',
                      project=['id', 'name'])

            print "#### GROUPS:"

            if qb.count() == 0:
                print "No groups found containing node {}".format(node.pk)
            else:
                res = qb.iterdict()
                for gr in res:
                    gr_specs = "{} {}".format(gr['groups']['name'],
                                              gr['groups']['id'])
                    print gr_specs


class _Tree(VerdiCommand):
    """
    Show a tree of the nodes.
    """

    def run(self, *args):
        """
        Show node information.
        """
        import argparse
        from aiida.common.exceptions import NotExistent

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Show information of a node.')
        parser.add_argument('pk', type=int, default=None, nargs="+",
                            help="ID of the node.")
        parser.add_argument('-d', '--depth', action='store', default=1,
                            metavar="N", type=int,
                            help="Add children of shown nodes up to Nth "
                                 "level. Default 0")

        args = list(args)
        parsed_args = parser.parse_args(args)

        if not is_dbenv_loaded():
            load_dbenv()

        for pk in parsed_args.pk:
            try:
                n = load_node(pk)
                self.print_node_tree(n, parsed_args.depth)
            except NotExistent as e:
                print >> sys.stderr, e.message
                sys.exit(1)

            if len(parsed_args.pk) > 1:
                print ""

    def print_node_tree(self, node, max_depth, follow_links=None):
        from aiida.cmdline.common import print_node_summary
        from ete3 import Tree
        print_node_summary(node)

        tree_string = \
            "({});".format(self._build_tree(node, max_depth=max_depth,
                                            follow_links=follow_links))
        t = Tree(tree_string, format=1)
        print(t.get_ascii(show_internal=True))

    def _ctime(self, nodelab):
        return nodelab[1].ctime

    def _build_tree(self, node, label_type=None, show_pk=True, max_depth=None,
                    follow_links=None, depth=0):
        if max_depth is not None and depth > max_depth:
            return

        children = []
        for label, child \
                in sorted(node.get_outputs(also_labels=True,
                                           link_type=follow_links),
                          key=self._ctime):
            child_str = self._build_tree(
                child, label, show_pk, follow_links=follow_links,
                max_depth=max_depth, depth=depth + 1)
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


# the classes _Label and _Description are written here,
# but in fact they are called by the verdi calculation or verdi data
# in fact, I don't want to allow the possibility of changing labels or
# descriptions of codes, for that there is a separate command

class _Label(VerdiCommandWithSubcommands):
    """
    See or modify the label of one or more set of nodes
    """

    def __init__(self, node_subclass='data'):
        self._node_subclass = node_subclass
        if self._node_subclass not in ['calculation', 'data']:
            raise ValueError("Class must be loaded with a valid node_subclass")

    def _node_class_ok(self, n):
        from aiida.orm import Calculation as OrmCalculation
        from aiida.orm import Data as OrmData

        if self._node_subclass == 'calculation':
            return isinstance(n, OrmCalculation)
        elif self._node_subclass == 'data':
            return isinstance(n, OrmData)
        else:
            raise ValueError("node_subclass not recognized")

    def run(self, *args):
        if not is_dbenv_loaded():
            load_dbenv()
        import argparse
        from aiida.cmdline import wait_for_confirmation

        parser = argparse.ArgumentParser(prog=self.get_full_command_name(),
                                         description="See/modify the labels of Nodes.")
        # display parameters
        parser.add_argument('-r', '--raw', action='store_true', default=False,
                            help="Display only the labels, without the pk.")
        # pks
        parser.add_argument('pks', type=int, nargs='+',
                            help="a list of nodes to show.")
        # parameters for label modification
        parser.add_argument('-s', '--set', action='store_true', default=False,
                            help="If present, set a new label, otherwise only "
                                 "show the labels.")
        parser.add_argument('-f', '--force', action='store_true',
                            default=False,
                            help="Force the reset of the label.")
        parser.add_argument('-l', '--label', type=str, default=None,
                            help="The new label to be set on the node. Note: "
                                 "pass it between quotes.")

        parsed_args = parser.parse_args(args)
        raw = parsed_args.raw
        pks = parsed_args.pks

        if not parsed_args.set:
            for pk in pks:
                n = load_node(pk)
                if not self._node_class_ok(n):
                    print "Node {} is not a subclass of {}. Exiting...".format(
                        pk,
                        self._node_subclass)
                    sys.exit(1)
                if raw:
                    print '"{}"'.format(n.label)
                else:
                    if not n.label:
                        print 'Node {}, label: n.a.'.format(pk)
                    else:
                        print 'Node {}, label: "{}"'.format(pk, n.label)
        else:
            if len(pks) > 1:
                sys.stderr.write("More than one node found to set one label"
                                 ". Exiting...\n")
                sys.exit(1)
            else:
                pk = pks[0]

            new_label = parsed_args.label
            if new_label is None:
                sys.stderr.write("A new label is required"
                                 ". Exiting...\n")
                sys.exit(1)

            n = load_node(pk)

            if not self._node_class_ok(n):
                print "Node {} is not a subclass of {}. Exiting...".format(pk,
                                                                           self._node_subclass)
                sys.exit(1)

            old_label = n.label
            if not parsed_args.force:
                sys.stderr.write("Current label is: {}\n".format(old_label))
                sys.stderr.write("New label is: {}\n".format(new_label))
                sys.stderr.write("Are you sure you want to reset the label? "
                                 "[Y/N] ")
                if not wait_for_confirmation():
                    sys.exit(0)

            n.label = new_label


class _Description(VerdiCommandWithSubcommands):
    """
    See or modify the label of one or more set of nodes
    """

    def __init__(self, node_subclass='data'):
        self._node_subclass = node_subclass
        if self._node_subclass not in ['calculation', 'data']:
            raise ValueError("Class must be loaded with a valid node_subclass")

    def _node_class_ok(self, n):
        from aiida.orm import Calculation as OrmCalculation
        from aiida.orm import Data as OrmData

        if self._node_subclass == 'calculation':
            return isinstance(n, OrmCalculation)
        elif self._node_subclass == 'data':
            return isinstance(n, OrmData)
        else:
            raise ValueError("node_subclass not recognized")

    def run(self, *args):
        if not is_dbenv_loaded():
            load_dbenv()
        import argparse
        from aiida.cmdline import wait_for_confirmation

        parser = argparse.ArgumentParser(prog=self.get_full_command_name(),
                                         description="See description of Nodes. If no node "
                                                     "description or label is found, prints n.a.")

        # parameters for display
        parser.add_argument('-n', '--no-labels', action='store_false',
                            default=True,
                            help="Don't show the labels.")
        parser.add_argument('-r', '--raw', action='store_true', default=False,
                            help="If set, prints only the description without "
                                 "pks or labels.")
        # pks
        parser.add_argument('pks', type=int, nargs='+',
                            help="a list of node pks to show.")
        # parameters for description modifications
        parser.add_argument('-s', '--set', action='store_true', default=False,
                            help="If present, set a new label, otherwise only "
                                 "show the labels.")
        parser.add_argument('-a', '--add-to-description', action='store_true',
                            default=False,
                            help="If -s, the string passed in -d is appended "
                                 "to the current description.")
        parser.add_argument('-f', '--force', action='store_true',
                            default=False,
                            help="Force the reset of the description.")
        parser.add_argument('-d', '--description', type=str,
                            help="The new description to be set on the node. "
                                 "Note: pass it between quotes.")

        parsed_args = parser.parse_args(args)

        pks = parsed_args.pks

        if not parsed_args.set:
            also_labels = parsed_args.no_labels
            for pk in pks:
                n = load_node(pk)

                if not self._node_class_ok(n):
                    print "Node {} is not a subclass of {}. Exiting...".format(
                        pk,
                        self._node_subclass)
                    sys.exit(1)

                label = n.label
                description = n.description

                if parsed_args.raw:
                    print '"{}"'.format(n.description)
                    print ""

                else:
                    print "Node pk: {}".format(pk)
                    if also_labels:
                        if label:
                            print 'Label: "{}"'.format(label)
                        else:
                            print 'Label: n.a.'
                    if description:
                        print 'Description: "{}"'.format(description)
                    else:
                        print 'Description: n.a.'
                    print ""
        else:
            # check that only one pk is present
            if len(pks) > 1:
                sys.stderr.write(
                    "More than one node found to set one description"
                    ". Exiting...\n")
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
                    print "Node {} is not a subclass of {}. Exiting...".format(
                        pk,
                        self._node_subclass)
                    sys.exit(1)

                old_description = n.description
                if not parsed_args.force:
                    sys.stderr.write(
                        "Current description is: {}\n".format(old_description))
                    sys.stderr.write(
                        "New description is: {}\n".format(new_description))
                    sys.stderr.write(
                        "Are you sure you want to reset the description? "
                        "[Y/N] ")
                    if not wait_for_confirmation():
                        sys.exit(0)

                n.description = new_description

            else:
                n = load_node(pk)
                if not self._node_class_ok(n):
                    print "Node {} is not a subclass of {}. Exiting...".format(
                        pk,
                        self._node_subclass)
                    sys.exit(1)

                old_description = n.description
                new_description = old_description + "\n" + new_description
                n.description = new_description
