###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Functions to delete entities from the database, preserving provenance integrity."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable

from aiida.common.log import AIIDA_LOGGER
from aiida.manage import get_manager
from aiida.orm import Group, Node, QueryBuilder
from aiida.orm.implementation import StorageBackend
from aiida.tools.graph.graph_traversers import get_nodes_delete

__all__ = ('delete_group_nodes', 'delete_nodes')

DELETE_LOGGER = AIIDA_LOGGER.getChild('delete')


def delete_nodes(
    pks: Iterable[int],
    dry_run: bool | Callable[[set[int]], bool] = True,
    backend: StorageBackend | None = None,
    *,
    contains_forward: bool = True,
    **traversal_rules: bool,
) -> tuple[set[int], bool]:
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

    :param pks: a list of starting PKs of the nodes to delete
        (the full set will be based on the traversal rules)

    :param dry_run:
        If True, return the pks to delete without deleting anything.
        If False, delete the pks without confirmation
        If callable, a function that return True/False, based on the pks, e.g. ``dry_run=lambda pks: True``
    :param contains_forward: Follow ownership from containers to their descendants, never to their parents.
        If false, detach surviving owned members instead of deleting them.
    :param traversal_rules: graph traversal rules.
        See :const:`aiida.common.links.GraphTraversalRules` for what rule names
        are toggleable and what the defaults are.

    :returns: (pks to delete, whether they were deleted)

    """
    backend = backend or get_manager().get_profile_storage()

    def _missing_callback(_pks: Iterable[int]) -> None:
        for _pk in _pks:
            DELETE_LOGGER.warning(f'warning: node with pk<{_pk}> does not exist, skipping')

    from aiida.storage.ownership import expand_owned_members

    # Provenance can select additional containers; follow their owned members too.
    pks_set_to_delete = set(pks)
    while True:
        traversed = get_nodes_delete(
            pks_set_to_delete,
            get_links=False,
            missing_callback=_missing_callback,
            backend=backend,
            **traversal_rules,
        )['nodes']
        pks_set_to_delete = expand_owned_members(backend, traversed) if contains_forward else traversed
        if pks_set_to_delete == traversed:
            break

    membership = backend.get_membership_deletion(pks_set_to_delete)
    DELETE_LOGGER.report('%s Node(s) marked for deletion', len(pks_set_to_delete))
    if membership.detached or membership.edited_containers:
        if dry_run is True:
            DELETE_LOGGER.report('Nodes to delete: %s', sorted(pks_set_to_delete))
        if membership.detached:
            DELETE_LOGGER.report(
                'Owned members to detach and keep as standalone nodes: %s', sorted(membership.detached)
            )
        if membership.edited_containers:
            DELETE_LOGGER.report(
                'Surviving containers that will lose members: %s', sorted(membership.edited_containers)
            )

    if pks_set_to_delete and DELETE_LOGGER.level == logging.DEBUG:
        builder = QueryBuilder(backend=backend).append(
            Node, filters={'id': {'in': pks_set_to_delete}}, project=('uuid', 'id', 'node_type', 'label')
        )
        DELETE_LOGGER.debug('Node(s) to delete:')
        for uuid, pk, type_string, label in builder.iterall():
            try:
                short_type_string = type_string.split('.')[-2]
            except IndexError:
                short_type_string = type_string
            DELETE_LOGGER.debug(f'   {uuid} {pk} {short_type_string} {label}')

    if dry_run is True:
        DELETE_LOGGER.report('This was a dry run, exiting without deleting anything')
        return (pks_set_to_delete, False)

    # confirm deletion
    if callable(dry_run) and dry_run(pks_set_to_delete):
        DELETE_LOGGER.report('This was a dry run, exiting without deleting anything')
        return (pks_set_to_delete, False)

    if not pks_set_to_delete:
        return (pks_set_to_delete, True)

    DELETE_LOGGER.report('Starting node deletion...')
    with backend.transaction():
        if membership.detached or membership.edited_containers:
            backend.delete_nodes_and_connections(pks_set_to_delete, membership=membership)
        else:
            backend.delete_nodes_and_connections(pks_set_to_delete)
    DELETE_LOGGER.report('Deletion of nodes completed.')

    return (pks_set_to_delete, True)


def delete_group_nodes(
    pks: Iterable[int],
    dry_run: bool | Callable[[set[int]], bool] = True,
    backend: StorageBackend | None = None,
    *,
    contains_forward: bool = True,
    **traversal_rules: bool,
) -> tuple[set[int], bool]:
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
    :param contains_forward: If false, detach surviving owned members instead of deleting them.
    :param traversal_rules: graph traversal rules. See :const:`aiida.common.links.GraphTraversalRules` what rule names
        are toggleable and what the defaults are.

    :returns: (node pks to delete, whether they were deleted)

    """
    group_node_query = (
        QueryBuilder(backend=backend)
        .append(
            Group,
            filters={'id': {'in': list(pks)}},
            tag='groups',
        )
        .append(Node, project='id', with_group='groups')
    )
    group_node_query.distinct()
    node_pks = group_node_query.all(flat=True)
    return delete_nodes(
        node_pks,
        dry_run=dry_run,
        backend=backend,
        contains_forward=contains_forward,
        **traversal_rules,
    )
