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


def _expand_ownership_for_deletion(
    backend: StorageBackend,
    pks_set_to_delete: set[int],
    *,
    dry_run: bool | Callable[[set[int]], bool],
    allow_ownership_expansion: bool,
) -> set[int]:
    """Expand a provenance deletion set to complete ownership units, with explicit approval.

    Follows stored owner references upward to the ownership root(s) and collects every owned
    descendant, so deleting a container includes its complete subtree (subject to ordinary
    provenance deletion safeguards) and owned children are never deleted independently.

    - If no expansion is needed, the set is returned unchanged.
    - If expansion is needed, the expanded set is presented for confirmation or explicit
      approval: ``dry_run=True`` (or a declining callback) returns the expanded set without
      deleting; ``dry_run=False`` requires ``allow_ownership_expansion`` and raises otherwise.
    - At execution, ``backend.delete_nodes_and_connections`` revalidates the approved set
      without enlarging it and fails if it became invalid.

    :raises aiida.common.exceptions.InvalidOperation: if expansion needs approval that was not given.
    """
    from aiida.common import exceptions
    from aiida.orm.nodes.data.container import expand_ownership_unit

    expanded = expand_ownership_unit(backend, pks_set_to_delete)
    if expanded == set(pks_set_to_delete):
        return pks_set_to_delete
    added = sorted(expanded - set(pks_set_to_delete))
    DELETE_LOGGER.report(
        'Ownership expansion: the deletion set targets container member(s); expanding to the complete '
        f'ownership unit(s), adding node(s): {added}'
    )
    if dry_run is True or not allow_ownership_expansion:
        if dry_run is False and not allow_ownership_expansion:
            msg = (
                'Cannot delete container member(s) without explicit ownership-expansion approval: '
                f'ownership expansion requires nodes {added}. Present the expanded set for '
                'confirmation (dry run) or pass `allow_ownership_expansion=True` (CLI `--force`); '
                '`dry_run=False` alone is not approval.'
            )
            raise exceptions.InvalidOperation(msg)
        return expanded
    return expanded


def delete_nodes(
    pks: Iterable[int],
    dry_run: bool | Callable[[set[int]], bool] = True,
    backend: StorageBackend | None = None,
    allow_ownership_expansion: bool = False,
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
    :param allow_ownership_expansion: explicitly approve expanding the deletion set to complete
        ownership units (ownership root plus full subtree) when an owned child or a container is
        targeted. ``dry_run=False`` alone is not approval: without this flag, targeting an
        ownership member raises instead of deleting. The CLI ``--force`` flag sets this.
    :param traversal_rules: graph traversal rules.
        See :const:`aiida.common.links.GraphTraversalRules` for what rule names
        are toggleable and what the defaults are.

    :returns: (pks to delete, whether they were deleted)

    """
    backend = backend or get_manager().get_profile_storage()

    def _missing_callback(_pks: Iterable[int]) -> None:
        for _pk in _pks:
            DELETE_LOGGER.warning(f'warning: node with pk<{_pk}> does not exist, skipping')

    # Ownership closure (spec §8) integrated into deletion planning: alternate ownership
    # expansion (child-targeted request -> ownership root + complete subtree) and ordinary
    # provenance deletion rules until a fixpoint, since provenance traversal of an expanded
    # set may pull in further ownership members. The final expanded set is presented for
    # confirmation or explicit approval; at execution it is revalidated without enlarging it.
    from aiida.orm.nodes.data.container import expand_ownership_unit

    pks_set_to_delete = expand_ownership_unit(backend, set(pks))
    while True:
        traversed = get_nodes_delete(
            pks_set_to_delete,
            get_links=False,
            missing_callback=_missing_callback,
            backend=backend,
            **traversal_rules,
        )['nodes']
        expanded = _expand_ownership_for_deletion(
            backend, traversed, dry_run=dry_run, allow_ownership_expansion=allow_ownership_expansion
        )
        if expanded == pks_set_to_delete:
            break
        pks_set_to_delete = expanded

    DELETE_LOGGER.report('%s Node(s) marked for deletion', len(pks_set_to_delete))

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
        backend.delete_nodes_and_connections(pks_set_to_delete)
    DELETE_LOGGER.report('Deletion of nodes completed.')

    return (pks_set_to_delete, True)


def delete_group_nodes(
    pks: Iterable[int],
    dry_run: bool | Callable[[set[int]], bool] = True,
    backend: StorageBackend | None = None,
    allow_ownership_expansion: bool = False,
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
    :param allow_ownership_expansion: explicitly approve expanding the deletion set to complete
        ownership units; ``dry_run=False`` alone is not approval (see :func:`delete_nodes`).
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
        allow_ownership_expansion=allow_ownership_expansion,
        **traversal_rules,
    )
