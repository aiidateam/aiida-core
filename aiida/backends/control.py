# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for overall repository control commands."""
# Note: these functions are not methods of `AbstractRepositoryBackend` because they need access to the orm.
# This is because they have to go through all the nodes to gather the list of keys that AiiDA is keeping
# track of (since they are descentralized in each node entry).
# See the get_unreferenced_keyset function
from typing import Optional, Set

from aiida.common.log import AIIDA_LOGGER
from aiida.manage.manager import get_manager
from aiida.orm.implementation import Backend

__all__ = ('MAINTAIN_LOGGER',)

MAINTAIN_LOGGER = AIIDA_LOGGER.getChild('maintain')


def repository_maintain(
    full: bool = False,
    dry_run: bool = False,
    backend: Optional[Backend] = None,
    **kwargs,
) -> dict:
    """Performs maintenance tasks on the repository."""

    if backend is None:
        backend = get_manager().get_backend()
    repository = backend.get_repository()

    unreferenced_objects = get_unreferenced_keyset(aiida_backend=backend)
    if dry_run:
        MAINTAIN_LOGGER.info(f'Would delete {len(unreferenced_objects)} unreferenced objects ...')
    else:
        MAINTAIN_LOGGER.info(f'Deleting {len(unreferenced_objects)} unreferenced objects ...')
        repository.delete_objects(list(unreferenced_objects))

    MAINTAIN_LOGGER.info('Starting repository-specific operations ...')
    repository.maintain(live=not full, dry_run=dry_run, **kwargs)


def get_unreferenced_keyset(check_consistency: bool = True, aiida_backend: Optional[Backend] = None) -> Set[str]:
    """Returns the keyset of objects that exist in the repository but are not tracked by AiiDA.

    This should be all the soft-deleted files.
    """
    from aiida import orm
    MAINTAIN_LOGGER.info('Obtaining unreferenced object keys ...')

    if aiida_backend is None:
        aiida_backend = get_manager().get_backend()

    repository = aiida_backend.get_repository()

    keyset_backend = set(repository.list_objects())
    keyset_aiidadb = set(orm.Node.objects(aiida_backend).iter_repo_keys())

    if check_consistency:
        keyset_missing = keyset_aiidadb - keyset_backend
        if len(keyset_missing) > 0:
            raise RuntimeError(
                'There are objects referenced in the database that are not present in the repository. Aborting!'
            )

    return keyset_backend - keyset_aiidadb


def get_repository_info(statistics: bool = False, backend: Optional[Backend] = None) -> dict:
    """Returns general information on the repository."""
    if backend is None:
        backend = get_manager().get_backend()
    repository = backend.get_repository()
    return repository.get_info(statistics)
