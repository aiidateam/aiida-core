# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Functions to delete entities from the database, preserving provenance integrity."""
import logging
from typing import Callable, Iterable, Optional, Set, Tuple, Union
import warnings

from aiida.backends.utils import delete_nodes_and_connections
from aiida.common.log import AIIDA_LOGGER
from aiida.common.warnings import AiidaDeprecationWarning
from aiida.orm import Group, Node, QueryBuilder, load_node
from aiida.tools.graph.graph_traversers import get_nodes_delete

__all__ = ('DELETE_LOGGER', 'delete_nodes', 'delete_group_nodes')

DELETE_LOGGER = AIIDA_LOGGER.getChild('delete')


def delete_nodes(
    pks: Iterable[int],
    verbosity: Optional[int] = None,
    dry_run: Union[bool, Callable[[Set[int]], bool]] = True,
    force: Optional[bool] = None,
    **traversal_rules: bool
) -> Tuple[Set[int], bool]:
    """Delete nodes given a list of "starting" PKs.

    This command will delete not only the specified nodes, but also the ones that are
    linked to these and should be also deleted in order to keep a consistent provenance
    according to the rules explained in the Topics - Provenance section of the documentation.
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

    .. deprecated:: 1.6.0
        The `verbosity` keyword will be removed in `v2.0.0`, set the level of `DELETE_LOGGER` instead.

    .. deprecated:: 1.6.0
        The `force` keyword will be removed in `v2.0.0`, use the `dry_run` option instead.

    :param pks: a list of starting PKs of the nodes to delete
        (the full set will be based on the traversal rules)

    :param dry_run:
        If True, return the pks to delete without deleting anything.
        If False, delete the pks without confirmation
        If callable, a function that return True/False, based on the pks, e.g. ``dry_run=lambda pks: True``

    :param traversal_rules: graph traversal rules.
        See :const:`aiida.common.links.GraphTraversalRules` for what rule names
        are toggleable and what the defaults are.

    :returns: (pks to delete, whether they were deleted)

    """
    # pylint: disable=too-many-arguments,too-many-branches,too-many-locals,too-many-statements

    if verbosity is not None:
        warnings.warn(
            'The verbosity option is deprecated and will be removed in `aiida-core==2.0.0`. '
            'Set the level of DELETE_LOGGER instead', AiidaDeprecationWarning
        )  # pylint: disable=no-member

    if force is not None:
        warnings.warn(
            'The force option is deprecated and will be removed in `aiida-core==2.0.0`. '
            'Use dry_run instead', AiidaDeprecationWarning
        )  # pylint: disable=no-member
        if force is True:
            dry_run = False

    def _missing_callback(_pks: Iterable[int]):
        for _pk in _pks:
            DELETE_LOGGER.warning(f'warning: node with pk<{_pk}> does not exist, skipping')

    pks_set_to_delete = get_nodes_delete(pks, get_links=False, missing_callback=_missing_callback,
                                         **traversal_rules)['nodes']

    DELETE_LOGGER.info('%s Node(s) marked for deletion', len(pks_set_to_delete))

    if pks_set_to_delete and DELETE_LOGGER.level == logging.DEBUG:
        builder = QueryBuilder().append(
            Node, filters={'id': {
                'in': pks_set_to_delete
            }}, project=('uuid', 'id', 'node_type', 'label')
        )
        DELETE_LOGGER.debug('Node(s) to delete:')
        for uuid, pk, type_string, label in builder.iterall():
            try:
                short_type_string = type_string.split('.')[-2]
            except IndexError:
                short_type_string = type_string
            DELETE_LOGGER.debug(f'   {uuid} {pk} {short_type_string} {label}')

    if dry_run is True:
        DELETE_LOGGER.info('This was a dry run, exiting without deleting anything')
        return (pks_set_to_delete, False)

    # confirm deletion
    if callable(dry_run) and dry_run(pks_set_to_delete):
        DELETE_LOGGER.info('This was a dry run, exiting without deleting anything')
        return (pks_set_to_delete, False)

    if not pks_set_to_delete:
        return (pks_set_to_delete, True)

    # Recover the list of folders to delete before actually deleting the nodes. I will delete the folders only later,
    # so that if there is a problem during the deletion of the nodes in the DB, I don't delete the folders
    repositories = [load_node(pk)._repository for pk in pks_set_to_delete]  # pylint: disable=protected-access

    DELETE_LOGGER.info('Starting node deletion...')
    delete_nodes_and_connections(pks_set_to_delete)

    DELETE_LOGGER.info('Nodes deleted from database, deleting files from the repository now...')

    # If we are here, we managed to delete the entries from the DB.
    # I can now delete the folders
    for repository in repositories:
        repository.erase(force=True)

    DELETE_LOGGER.info('Deletion of nodes completed.')

    return (pks_set_to_delete, True)


def delete_group_nodes(
    pks: Iterable[int],
    dry_run: Union[bool, Callable[[Set[int]], bool]] = True,
    **traversal_rules: bool
) -> Tuple[Set[int], bool]:
    """Delete nodes contained in a list of groups (not the groups themselves!).

    This command will delete not only the nodes, but also the ones that are
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

    :param pks: a list of the groups

    :param dry_run:
        If True, return the pks to delete without deleting anything.
        If False, delete the pks without confirmation
        If callable, a function that return True/False, based on the pks, e.g. ``dry_run=lambda pks: True``

    :param traversal_rules: graph traversal rules. See :const:`aiida.common.links.GraphTraversalRules` what rule names
        are toggleable and what the defaults are.

    :returns: (node pks to delete, whether they were deleted)

    """
    group_node_query = QueryBuilder().append(
        Group,
        filters={
            'id': {
                'in': list(pks)
            }
        },
        tag='groups',
    ).append(Node, project='id', with_group='groups')
    group_node_query.distinct()
    node_pks = group_node_query.all(flat=True)
    return delete_nodes(node_pks, dry_run=dry_run, **traversal_rules)
