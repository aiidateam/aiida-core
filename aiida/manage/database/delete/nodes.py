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

# OBS: keep_dataprov only affects if follow_calls is True: should it default
#      to False and delete everything or to True and be more carefull without
#      further specifications?
#      Are we REALLY going to use this in another case? Or should I just have
#      follow_callcalc and follow_callwork?


def delete_nodes(
    pks, verbosity=0, dry_run=False, force=False, follow_create=True, follow_calls=False, keep_dataprov=False
):
    """
    Delete nodes by a list of pks

    This command will delete not only the specified nodes, but also the ones that
    are linked to them and should be also deleted in order to keep a provenance
    that makes sense. The general rules for this are:

    (1) If a DATA node is deleted, all procedures that are conected to it must
        be deleted as well (it doesn't make sense to keep procedures without
        its inputs or outputs).

    (2) If a CALC node is deleted, any WORK node that is linked will also be deleted
        and (by default) any OUT-DATA nodes will be deleted as well.
        INP-DATA nodes are kept.

    (3) If a WORK node is deleted, any WORK node that is upwards-connected will be
        deleted as well, but by default it wont delete any WORK or CALC node that
        are called by it (downwards-connected).
        All DATA nodes are kept (either inputs or outputs).

    These rules are 'recursive', so if a CALC node is deleted, then its output
    DATA nodes will be deleted as well, and then any CALC node that may have
    those as inputs, and so on.

    :param pks: a list of the PKs of the nodes to delete
    :param bool force: do not ask for confirmation to delete nodes.
    :param int verbosity: 0 prints nothing,
                          1 prints just sums and total,
                          2 prints individual nodes.
    :param bool follow_create (True):
        This will delete all output data created by any deleted calculation.
    :param bool follow_calls (False):
        This will delete all procedures called by the deleted workflow and also by all the
        controling workflows upstream (not that this may delete workflow sections that are
        'unrelated' to what has been chosen to delete just because they are connected at some
        point of the upwards provenance). Use with care, and it is advisable to never combine
        with force.
    :param bool keep_dataprov (False):
        Only used when follow_calls=True, this will keep all the data provenance from all
        deleted nodes, only propagating deletion to the logical provenance (i.e., the
        follow_calls will only follow CALL_WORK but not CALL_CALC).
    :param bool dry_run:
        Do not delete, a dry run, with statistics printed according to verbosity levels.
    :param bool force:
        Do not ask for confirmation to delete nodes.
    """
    # pylint: disable=too-many-arguments,too-many-branches,too-many-locals,too-many-statements
    from aiida.backends.utils import delete_nodes_and_connections
    from aiida.common import exceptions
    from aiida.common.links import LinkType
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

    follow_upwards = []
    follow_upwards.append(LinkType.CREATE.value)
    follow_upwards.append(LinkType.RETURN.value)
    follow_upwards.append(LinkType.CALL_CALC.value)
    follow_upwards.append(LinkType.CALL_WORK.value)

    follow_downwards = []
    follow_downwards.append(LinkType.INPUT_CALC.value)
    follow_downwards.append(LinkType.INPUT_WORK.value)

    if follow_calls:
        follow_downwards.append(LinkType.CALL_WORK.value)
        if not keep_dataprov:
            follow_downwards.append(LinkType.CALL_CALC.value)

    if follow_create:
        follow_downwards.append(LinkType.CREATE.value)

    links_upwards = {'type': {'in': follow_upwards}}
    links_downwards = {'type': {'in': follow_downwards}}

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
            edge_filters=links_downwards,
            with_incoming='sources',
            project='id'
        )
        new_pks_set = new_pks_set.union(set(i for i, in query_nodes.iterall()))

        query_nodes = QueryBuilder()
        query_nodes.append(Node, filters={'id': {'in': operational_set}}, tag='sources')
        query_nodes.append(
            Node,
            filters={'id': {
                '!in': accumulator_set
            }},
            edge_filters=links_upwards,
            with_outgoing='sources',
            project='id'
        )
        new_pks_set = new_pks_set.union(set(i for i, in query_nodes.iterall()))

        operational_set = new_pks_set.difference(accumulator_set)
        accumulator_set = new_pks_set.union(accumulator_set)

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
        echo.echo('I am starting node deletion.')
    delete_nodes_and_connections(pks_set_to_delete)

    if verbosity > 0:
        echo.echo('I have finished node deletion and I am starting folder deletion.')

    # If we are here, we managed to delete the entries from the DB.
    # I can now delete the folders
    for repository in repositories:
        repository.erase(force=True)

    if verbosity > 0:
        echo.echo('I have finished folder deletion. Deletion completed.')
