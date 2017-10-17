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
import click

from aiida.backends.utils import load_dbenv
from aiida.cmdline.commands import verdi, export
from aiida.cmdline.baseclass import VerdiCommand, VerdiCommandWithSubcommands

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

class Export(VerdiCommandWithSubcommands):
    """
    Create and manage AiiDA export archives
    """
    def __init__(self):
        self.valid_subcommands = {
            'create': (self.cli, self.complete_none)
        }

    def cli(self, *args):
        verdi()


@export.command('create', context_settings=CONTEXT_SETTINGS)
@click.argument('outfile', type=click.Path())
@click.option('-n', '--nodes', multiple=True, type=int,
    help='Export the given nodes by pk')
@click.option('-c', '--computers', multiple=True, type=int,
    help='Export the given computers by pk')
@click.option('-g', '--groups', multiple=True, type=int,
    help='Export the given groups by pk')
@click.option('-G', '--group_names', multiple=True, type=str,
    help='Export the given groups by group name')
@click.option('-P', '--no-parents', is_flag=True, default=False,
    help='Store only the nodes that are explicitly given, without exporting the parents')
@click.option('-O', '--no-calc-outputs', is_flag=True, default=False,
    help='If a calculation is included in the list of nodes to export, do not export its outputs')
@click.option('-y', '--overwrite', is_flag=True, default=False,
    help='Overwrite the output file, if it exists')
@click.option('-z', '--zipfile-compressed', is_flag=True, default=False,
    help='tore as zip file (experimental, should be faster')
@click.option('-Z', '--zipfile-uncompressed', is_flag=True, default=False,
    help='Store as uncompressed zip file (experimental, should be faster')
def create(outfile, computers, groups, nodes, group_names, no_parents, no_calc_outputs,
    overwrite, zipfile_compressed, zipfile_uncompressed):
    """
    Export nodes and groups of nodes to an archive file for backup or sharing purposes
    """
    load_dbenv()
    from aiida.orm import Group, Node, Computer
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.importexport import export, export_zip

    node_id_set = set(nodes)
    group_dict = dict()

    if group_names:
        qb = QueryBuilder()
        qb.append(Group, tag='group', project=['*'], filters={'name': {'in': group_names}})
        qb.append(Node, tag='node', member_of='group', project=['id'])
        res = qb.dict()

        group_dict.update({group['group']['*'].name: group['group']['*'].dbgroup for group in res})
        node_id_set.update([node['node']['id'] for node in res])

    if groups:
        qb = QueryBuilder()
        qb.append(Group, tag='group', project=['*'], filters={'id': {'in': groups}})
        qb.append(Node, tag='node', member_of='group', project=['id'])
        res = qb.dict()

        group_dict.update({group['group']['*'].name: group['group']['*'].dbgroup for group in res})
        node_id_set.update([node['node']['id'] for node in res])

    # The db_groups that correspond to what was searched above
    dbgroups_list = group_dict.values()

    # Getting the nodes that correspond to the ids that were found above
    if len(node_id_set) > 0:
        qb = QueryBuilder()
        qb.append(Node, tag='node', project=['*'], filters={'id': {'in': node_id_set}})
        node_list = [node[0] for node in qb.all()]
    else:
        node_list = list()

    # Check if any of the nodes wasn't found in the database.
    missing_nodes = node_id_set.difference(node.id for node in node_list)
    for node_id in missing_nodes:
        print >> sys.stderr, ('WARNING! Node with pk={} not found, skipping'.format(node_id))

    # The dbnodes of the above node list
    dbnode_list = [node.dbnode for node in node_list]

    if computers:
        qb = QueryBuilder()
        qb.append(Computer, tag='comp', project=['*'], filters={'id': {'in': set(computers)}})
        computer_list = [computer[0] for computer in qb.all()]
        missing_computers = set(computers).difference(computer.id for computer in computer_list)

        for computer_id in missing_computers:
            print >> sys.stderr, ('WARNING! Computer with pk={} not found, skipping'.format(computer_id))
    else:
        computer_list = []

    # The dbcomputers of the above computer list
    dbcomputer_list = [computer.dbcomputer for computer in computer_list]

    what_list = dbnode_list + dbcomputer_list + dbgroups_list

    export_function = export
    additional_kwargs = {}

    if zipfile_uncompressed:
        export_function = export_zip
        additional_kwargs.update({'use_compression': False})
    elif zipfile_compressed:
        export_function = export_zip
        additional_kwargs.update({'use_compression': True})

    try:
        export_function(
            what=what_list, also_parents=not no_parents,
            also_calc_outputs=not no_calc_outputs,
            outfile=outfile, overwrite=overwrite,
            **additional_kwargs
        )
    except IOError as e:
        print >> sys.stderr, 'IOError: {}'.format(e.message)
        sys.exit(1)