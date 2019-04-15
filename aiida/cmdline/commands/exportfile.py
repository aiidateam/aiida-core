# -*- coding: utf-8 -*-
import sys

from aiida.backends.utils import load_dbenv
from aiida.cmdline.baseclass import VerdiCommand

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0.1"
__authors__ = "The AiiDA team."


class Export(VerdiCommand):
    """
    Export nodes and group of nodes

    This command allows to export to file nodes and group of nodes, for backup
    purposes or to share data with collaborators.
    Call this command with the '-h' option for some documentation of its usage.
    """

    def run(self, *args):
        load_dbenv()

        import argparse

        from aiida.common.exceptions import NotExistent
        from aiida.backends.djsite.db import models
        from aiida.orm import Group
        from aiida.orm.importexport import export, export_zip

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Export data from the DB.')
        parser.add_argument('-c', '--computers', nargs='+', type=int, metavar="PK",
                            help="Export the given computers")
        parser.add_argument('-n', '--nodes', nargs='+', type=int, metavar="PK",
                            help="Export the given nodes")
        parser.add_argument('-g', '--groups', nargs='+', metavar="GROUPNAME",
                            help="Export all nodes in the given group(s), identified by name.",
                            type=str)
        parser.add_argument('-G', '--group_pks', nargs='+', metavar="PK",
                            help="Export all nodes in the given group(s), identified by pk.",
                            type=str)
        parser.add_argument('-P', '--no-parents',
                            dest='no_parents', action='store_true',
                            help="Store only the nodes that are explicitly given, without exporting the parents")
        parser.set_defaults(no_parents=False)
        parser.add_argument('-O', '--no-calc-outputs',
                            dest='no_calc_outputs', action='store_true',
                            help="If a calculation is included in the list of nodes to export, do not export its outputs")
        parser.set_defaults(no_calc_outputs=False)
        parser.add_argument('-y', '--overwrite',
                            dest='overwrite', action='store_true',
                            help="Overwrite the output file, if it exists")
        parser.set_defaults(overwrite=False)

        zipsubgroup = parser.add_mutually_exclusive_group()
        zipsubgroup.add_argument('-z', '--zipfile-compressed',
                            dest='zipfilec', action='store_true',
                            help="Store as zip file (experimental, should be faster")
        zipsubgroup.add_argument('-Z', '--zipfile-uncompressed',
                            dest='zipfileu', action='store_true',
                            help="Store as uncompressed zip file (experimental, should be faster")
        parser.set_defaults(zipfilec=False)
        parser.set_defaults(zipfileu=False)

        parser.add_argument('output_file', type=str,
                            help='The output file name for the export file')

        parsed_args = parser.parse_args(args)

        if parsed_args.nodes is None:
            node_pk_list = []
        else:
            node_pk_list = parsed_args.nodes

        groups_list = []

        if parsed_args.groups is not None:
            for group_name in parsed_args.groups:
                try:
                    group = Group.get_from_string(group_name)
                except (ValueError, NotExistent) as e:
                    print >> sys.stderr, e.message
                    sys.exit(1)
                node_pk_list += group.dbgroup.dbnodes.values_list('pk', flat=True)
                groups_list.append(group.dbgroup)
                
        if parsed_args.group_pks is not None:
            for group_pk in parsed_args.group_pks:
                try:
                    group = Group.get(pk=group_pk)
                except (ValueError, NotExistent) as e:
                    print >> sys.stderr, e.message
                    sys.exit(1)
                node_pk_list += group.dbgroup.dbnodes.values_list('pk', flat=True)
                groups_list.append(group.dbgroup)
        
        node_pk_list = set(node_pk_list)

        node_list = list(
            models.DbNode.objects.filter(pk__in=node_pk_list))
        missing_nodes = node_pk_list.difference(_.pk for _ in node_list)
        for pk in missing_nodes:
            print >> sys.stderr, ("WARNING! Node with pk= {} "
                                  "not found, skipping.".format(pk))
        if parsed_args.computers is not None:
            computer_list = list(models.DbComputer.objects.filter(
                pk__in=parsed_args.computers))
            missing_computers = set(parsed_args.computers).difference(
                _.pk for _ in computer_list)
            for pk in missing_computers:
                print >> sys.stderr, ("WARNING! Computer with pk= {} "
                                      "not found, skipping.".format(pk))
        else:
            computer_list = []

        what_list = node_list + computer_list + groups_list

        export_function = export
        additional_kwargs = {}
        if parsed_args.zipfileu:
            export_function = export_zip
            additional_kwargs.update({"use_compression": False})
        elif parsed_args.zipfilec:
            export_function = export_zip
            additional_kwargs.update({"use_compression": True})
        try:
            export_function(what=what_list,
                   also_parents=not parsed_args.no_parents,
                   also_calc_outputs=not parsed_args.no_calc_outputs,
                   outfile=parsed_args.output_file,
                   overwrite=parsed_args.overwrite,**additional_kwargs)
        except IOError as e:
            print >> sys.stderr, "IOError: {}".format(e.message)
            sys.exit(1)


    def complete(self, subargs_idx, subargs):
        return ""
