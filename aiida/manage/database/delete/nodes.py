# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Function to delete nodes from the database."""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import click

from aiida.cmdline.utils import echo
from aiida.common import InternalError


def delete_nodes(pks, verbosity=0, dry_run=False, force=False, **kwargs):
    """Delete nodes by a list of pks.

    This command will delete not only the specified nodes, but also the ones that are
    linked to these and should be also deleted in order to keep a consistent provenance
    according to the rules explained in the concepts section of the documentation.
    In summary:

    1. If a DATA node is deleted, any process nodes linked to it will also be deleted.

    2. If a CALC node is deleted, any incoming WORK node (callers) will be deleted as
    well whereas any incoming DATA node (inputs) will be kept. Outgoing DATA nodes
    (outputs) will be deleted by default but this can be disabled.

    3. If a WORK node is deleted, any incoming WORK node (callers) will be deleted as
    well, but all DATA nodes will be kept. Outgoing WORK or CALC nodes will be kept by
    default, but deletion of either of both kind of connected nodes can be enabled.

    These rules are 'recursive', so if a CALC node is deleted, then its output DATA
    nodes will be deleted as well, and then any CALC node that may have those as
    inputs, and so on.

    :param pks: a list of the PKs of the nodes to delete
    :param bool force: do not ask for confirmation to delete nodes.
    :param int verbosity: 0 prints nothing,
                          1 prints just sums and total,
                          2 prints individual nodes.

    :param kwargs: graph traversal rules. See :const:`aiida.common.links.GraphTraversalRules` what rule names
        are toggleable and what the defaults are.
    :param bool dry_run:
        Just perform a dry run and do not delete anything. Print statistics according
        to the verbosity level set.
    :param bool force:
        Do not ask for confirmation to delete nodes.
    """
    # pylint: disable=too-many-arguments,too-many-branches,too-many-locals,too-many-statements
    from aiida.backends.utils import delete_nodes_and_connections
    from aiida.common import exceptions
    from aiida.common.links import GraphTraversalRules
    from aiida.orm import Node, QueryBuilder, load_node

    starting_pks = []
    for pk in pks:
        try:
            load_node(pk)
        except exceptions.NotExistent:
            echo.echo_warning('warning: node with pk<{}> does not exist, skipping'.format(pk))
        else:
            starting_pks.append(pk)

    # An empty set might be problematic for the queries done below.
    if not starting_pks:
        if verbosity:
            echo.echo('Nothing to delete')
        return

    follow_forwards = []
    follow_backwards = []

    # Create the dictionary with graph traversal rules to be used in determing complete node set to be exported
    for name, rule in GraphTraversalRules.DELETE.value.items():

        # Check that rules that are not toggleable are not specified in the keyword arguments
        if not rule.toggleable and name in kwargs:
            raise exceptions.ExportValidationError('traversal rule {} is not toggleable'.format(name))

        follow = kwargs.pop(name, rule.default)

        if follow:
            if rule.direction == 'forward':
                follow_forwards.append(rule.link_type.value)
            elif rule.direction == 'backward':
                follow_backwards.append(rule.link_type.value)
            else:
                raise InternalError('unrecognized direction `{}` for graph traversal rule'.format(rule.direction))

    links_backwards = {'type': {'in': follow_backwards}}
    links_forwards = {'type': {'in': follow_forwards}}

    operational_set = set().union(set(starting_pks))
    accumulator_set = set().union(set(starting_pks))

    while operational_set:
        new_pks_set = set()

        query_nodes = QueryBuilder()
        query_nodes.append(Node, filters={'id': {'in': operational_set}}, tag='sources')
        query_nodes.append(
            Node,
            filters={'id': {
                '!in': accumulator_set
            }},
            edge_filters=links_forwards,
            with_incoming='sources',
            project='id'
        )
        new_pks_set.update(i for i, in query_nodes.iterall())

        query_nodes = QueryBuilder()
        query_nodes.append(Node, filters={'id': {'in': operational_set}}, tag='sources')
        query_nodes.append(
            Node,
            filters={'id': {
                '!in': accumulator_set
            }},
            edge_filters=links_backwards,
            with_outgoing='sources',
            project='id'
        )
        new_pks_set.update(i for i, in query_nodes.iterall())

        operational_set = new_pks_set.difference(accumulator_set)
        accumulator_set.update(new_pks_set)

    pks_set_to_delete = accumulator_set

    if verbosity > 0:
        echo.echo(
            'I {} delete {} node{}'.format(
                'would' if dry_run else 'will', len(pks_set_to_delete), 's' if len(pks_set_to_delete) > 1 else ''
            )
        )
        if verbosity > 1:
            builder = QueryBuilder().append(
                Node, filters={'id': {
                    'in': pks_set_to_delete
                }}, project=('uuid', 'id', 'node_type', 'label')
            )
            echo.echo('The nodes I {} delete:'.format('would' if dry_run else 'will'))
            for uuid, pk, type_string, label in builder.iterall():
                try:
                    short_type_string = type_string.split('.')[-2]
                except IndexError:
                    short_type_string = type_string
                echo.echo('   {} {} {} {}'.format(uuid, pk, short_type_string, label))

    if dry_run:
        if verbosity > 0:
            echo.echo('\nThis was a dry run, exiting without deleting anything')
        return

    # Asking for user confirmation here
    if force:
        pass
    else:
        echo.echo_warning('YOU ARE ABOUT TO DELETE {} NODES! THIS CANNOT BE UNDONE!'.format(len(pks_set_to_delete)))
        if not click.confirm('Shall I continue?'):
            echo.echo('Exiting without deleting')
            return

    # Recover the list of folders to delete before actually deleting the nodes. I will delete the folders only later,
    # so that if there is a problem during the deletion of the nodes in the DB, I don't delete the folders
    repositories = [load_node(pk)._repository for pk in pks_set_to_delete]  # pylint: disable=protected-access

    if verbosity > 0:
        echo.echo('Starting node deletion...')
    delete_nodes_and_connections(pks_set_to_delete)

    if verbosity > 0:
        echo.echo('Nodes deleted from database, deleting files from the repository now...')

    # If we are here, we managed to delete the entries from the DB.
    # I can now delete the folders
    for repository in repositories:
        repository.erase(force=True)

    if verbosity > 0:
        echo.echo('Deletion completed.')
