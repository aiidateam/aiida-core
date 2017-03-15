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

from aiida.backends.utils import load_dbenv
from aiida.cmdline.baseclass import VerdiCommand



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

        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm import Group, Node, Computer
        from aiida.orm.importexport import export, export_zip

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Export data from the DB.')
        parser.add_argument('-c', '--computers', nargs='+', type=int,
                            metavar="PK", help="Export the given computers")
        parser.add_argument('-n', '--nodes', nargs='+', type=int, metavar="PK",
                            help="Export the given nodes")
        parser.add_argument('-g', '--groups', nargs='+', metavar="GROUPNAME",
                            help="Export all nodes in the given group(s), "
                                 "identified by name.",
                            type=str)
        parser.add_argument('-G', '--group_pks', nargs='+', metavar="PK",
                            help="Export all nodes in the given group(s), "
                                 "identified by pk.",
                            type=str)
        parser.add_argument('-P', '--no-parents',
                            dest='no_parents', action='store_true',
                            help="Store only the nodes that are explicitly "
                                 "given, without exporting the parents")
        parser.set_defaults(no_parents=False)
        parser.add_argument('-O', '--no-calc-outputs',
                            dest='no_calc_outputs', action='store_true',
                            help="If a calculation is included in the list of "
                                 "nodes to export, do not export its outputs")
        parser.set_defaults(no_calc_outputs=False)
        parser.add_argument('-y', '--overwrite',
                            dest='overwrite', action='store_true',
                            help="Overwrite the output file, if it exists")
        parser.set_defaults(overwrite=False)

        zipsubgroup = parser.add_mutually_exclusive_group()
        zipsubgroup.add_argument('-z', '--zipfile-compressed',
                            dest='zipfilec', action='store_true',
                            help="Store as zip file (experimental, should be "
                                 "faster")
        zipsubgroup.add_argument('-Z', '--zipfile-uncompressed',
                            dest='zipfileu', action='store_true',
                            help="Store as uncompressed zip file "
                                 "(experimental, should be faster")
        parser.set_defaults(zipfilec=False)
        parser.set_defaults(zipfileu=False)

        parser.add_argument('output_file', type=str,
                            help='The output file name for the export file')

        parsed_args = parser.parse_args(args)

        if parsed_args.nodes is None:
            node_id_set = set()
        else:
            node_id_set = set(parsed_args.nodes)

        group_dict = dict()

        if parsed_args.groups is not None:
            qb = QueryBuilder()
            qb.append(Group, tag='group', project=['*'],
                      filters={'name': {'in': parsed_args.groups}})
            qb.append(Node, tag='node', member_of='group', project=['id'])
            res = qb.dict()

            group_dict.update({_['group']['*'].name: _['group']['*'].dbgroup
                               for _ in res})
            node_id_set.update([_['node']['id'] for _ in res])

        if parsed_args.group_pks is not None:
            qb = QueryBuilder()
            qb.append(Group, tag='group', project=['*'],
                      filters={'id': {'in': parsed_args.group_pks}})
            qb.append(Node, tag='node', member_of='group', project=['id'])
            res = qb.dict()

            group_dict.update({_['group']['*'].name: _['group']['*'].dbgroup
                               for _ in res})
            node_id_set.update([_['node']['id'] for _ in res])

        # The db_groups that correspond to what was searched above
        dbgroups_list = group_dict.values()

        # Getting the nodes that correspond to the ids that were found above
        if len(node_id_set) > 0:
            qb = QueryBuilder()
            qb.append(Node, tag='node', project=['*'],
                      filters={'id': {'in': node_id_set}})
            node_list = [_[0] for _ in qb.all()]
        else:
            node_list = list()

        # Check if any of the nodes wasn't found in the database.
        missing_nodes = node_id_set.difference(_.id for _ in node_list)
        for id in missing_nodes:
            print >> sys.stderr, ("WARNING! Node with pk= {} "
                                  "not found, skipping.".format(id))

        # The dbnodes of the above node list
        dbnode_list = [_.dbnode for _ in node_list]

        if parsed_args.computers is not None:
            qb = QueryBuilder()
            qb.append(Computer, tag='comp', project=['*'],
                      filters={'id': {'in': set(parsed_args.computers)}})
            computer_list = [_[0] for _ in qb.all()]
            missing_computers = set(parsed_args.computers).difference(
                _.id for _ in computer_list)
            for id in missing_computers:
                print >> sys.stderr, ("WARNING! Computer with pk= {} "
                                      "not found, skipping.".format(id))
        else:
            computer_list = []

        # The dbcomputers of the above computer list
        dbcomputer_list = [_.dbcomputer for _ in computer_list]

        what_list = dbnode_list + dbcomputer_list + dbgroups_list

        export_function = export
        additional_kwargs = {}
        if parsed_args.zipfileu:
            export_function = export_zip
            additional_kwargs.update({"use_compression": False})
        elif parsed_args.zipfilec:
            export_function = export_zip
            additional_kwargs.update({"use_compression": True})
        try:
            export_function(
                what=what_list, also_parents=not parsed_args.no_parents,
                also_calc_outputs=not parsed_args.no_calc_outputs,
                outfile=parsed_args.output_file,
                overwrite=parsed_args.overwrite,**additional_kwargs)
        except IOError as e:
            print >> sys.stderr, "IOError: {}".format(e.message)
            sys.exit(1)

    def complete(self, subargs_idx, subargs):
        return ""
