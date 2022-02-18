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
from typing import TYPE_CHECKING, Optional, Set

from aiida.common.log import AIIDA_LOGGER
from aiida.manage import get_manager

if TYPE_CHECKING:
    from aiida.orm.implementation import Backend

__all__ = ('MAINTAIN_LOGGER',)

MAINTAIN_LOGGER = AIIDA_LOGGER.getChild('maintain')


def repository_maintain(
    full: bool = False,
    dry_run: bool = False,
    backend: Optional['Backend'] = None,
    **kwargs,
) -> None:
    """Performs maintenance tasks on the repository.

        :param full:
            flag to perform operations that require to stop using the maintained profile.

        :param dry_run:
            flag to only print the actions that would be taken without actually executing them.

        :param backend:
            specific backend in which to apply the maintenance (defaults to current profile).
    """

    if backend is None:
        backend = get_manager().get_profile_storage()
    repository = backend.get_repository()

    unreferenced_objects = get_unreferenced_keyset(aiida_backend=backend)
    MAINTAIN_LOGGER.info(f'Deleting {len(unreferenced_objects)} unreferenced objects ...')
    if not dry_run:
        repository.delete_objects(list(unreferenced_objects))

    MAINTAIN_LOGGER.info('Starting repository-specific operations ...')
    repository.maintain(live=not full, dry_run=dry_run, **kwargs)


def get_unreferenced_keyset(check_consistency: bool = True, aiida_backend: Optional['Backend'] = None) -> Set[str]:
    """Returns the keyset of objects that exist in the repository but are not tracked by AiiDA.

    This should be all the soft-deleted files.

        :param check_consistency:
            toggle for a check that raises if there are references in the database with no actual object in the
            underlying repository.

        :param aiida_backend:
            specific backend in which to apply the operation (defaults to current profile).

        :return:
            a set with all the objects in the underlying repository that are not referenced in the database.
    """
    from aiida import orm
    MAINTAIN_LOGGER.info('Obtaining unreferenced object keys ...')

    if aiida_backend is None:
        aiida_backend = get_manager().get_profile_storage()

    repository = aiida_backend.get_repository()

    keyset_repository = set(repository.list_objects())
    keyset_database = set(orm.Node.objects(aiida_backend).iter_repo_keys())

    if check_consistency:
        keyset_missing = keyset_database - keyset_repository
        if len(keyset_missing) > 0:
            raise RuntimeError(
                'There are objects referenced in the database that are not present in the repository. Aborting!'
            )

    return keyset_repository - keyset_database


def get_repository_info(statistics: bool = False, backend: Optional['Backend'] = None) -> dict:
    """Returns general information on the repository."""
    if backend is None:
        backend = get_manager().get_profile_storage()
    repository = backend.get_repository()
    return repository.get_info(statistics)
