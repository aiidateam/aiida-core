###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for operations on files on remote computers."""

from __future__ import annotations

import os
import typing as t

from aiida import orm
from aiida.cmdline.utils import echo
from aiida.orm.nodes.data.remote.base import RemoteData

if t.TYPE_CHECKING:
    from collections.abc import Sequence

    from aiida.orm.implementation import StorageBackend
    from aiida.transports import Transport


def clean_remote(transport: Transport, path: str) -> None:
    """Recursively remove a remote folder, with the given absolute path, and all its contents. The path should be
    made accessible through the transport channel, which should already be open

    :param transport: an open Transport channel
    :param path: an absolute path on the remote made available through the transport
    """
    if not isinstance(path, str):
        raise ValueError('the path has to be a string type')

    if not os.path.isabs(path):
        raise ValueError('the path should be absolute')

    if not transport.is_open:
        raise ValueError('the transport should already be open')

    try:
        transport.rmtree(path)
    except OSError:
        pass


def clean_mapping_remote_paths(path_mapping, silent=False):
    """Clean the remote folders for a given mapping of computer UUIDs to a list of remote folders.

    :param path_mapping: a dictionary where the keys are the computer UUIDs and the values are lists of remote folders
        It's designed to accept the output of `get_calcjob_remote_paths`
    :param transport: the transport to use to clean the remote folders
    :param silent: if True, the `echo` output will be suppressed
    """

    user = orm.User.collection.get_default()

    if not user:
        raise ValueError('No default user found')

    for computer_uuid, paths in path_mapping.items():
        counter = 0
        computer = orm.load_computer(uuid=computer_uuid)
        transport = orm.AuthInfo.collection.get(dbcomputer_id=computer.pk, aiidauser_id=user.pk).get_transport()

        with transport:
            for remote_folder in paths:
                remote_folder._clean(transport=transport)
                counter += 1

        if not silent:
            echo.echo_success(f'{counter} remote folders cleaned on {computer.label}')


def clean_mapping_stashed_paths(path_mapping, silent=False):
    """Clean the stashed folders for a given mapping of computer UUIDs to a list of stashed folders.

    :param path_mapping: a dictionary where the keys are the computer UUIDs and the values are lists of stashed folders
        It's designed to accept the output of `get_calcjob_stashed_paths`
    :param silent: if True, the `echo` output will be suppressed
    :raises NotImplementedError: if a RemoteStashCustomData node is encountered
    """
    from aiida.orm.nodes.data.remote.stash import RemoteStashCustomData

    user = orm.User.collection.get_default()

    if not user:
        raise ValueError('No default user found')

    for computer_uuid, paths in path_mapping.items():
        counter = 0
        computer = orm.load_computer(uuid=computer_uuid)
        transport = orm.AuthInfo.collection.get(dbcomputer_id=computer.pk, aiidauser_id=user.pk).get_transport()

        with transport:
            for stashed_folder in paths:
                if isinstance(stashed_folder, RemoteStashCustomData):
                    raise NotImplementedError(
                        "I don't know how to delete remote files of RemoteStashCustomData. "
                        f'Please manually clean the stashed data for node {stashed_folder.pk}.'
                    )
                stashed_folder._clean(transport=transport)
                counter += 1

        if not silent:
            echo.echo_success(f'{counter} stashed folders cleaned on {computer.label}')


def get_calcjob_remote_paths(
    pks: list[int] | None = None,
    past_days: int | None = None,
    older_than: int | None = None,
    computers: Sequence[orm.Computer] | None = None,
    user: orm.User | None = None,
    backend: StorageBackend | None = None,
    exit_status: int | None = None,
    only_not_cleaned: bool = False,
) -> dict[str, list[RemoteData]] | None:
    """Return a mapping of computer uuids to a list of remote paths, for a given set of calcjobs. The set of
    calcjobs will be determined by a query with filters based on the pks, past_days, older_than,
    computers and user arguments.

    :param pks: only include calcjobs with a pk in this list
    :param past_days: only include calcjobs created since past_days
    :param older_than: only include calcjobs older than
    :param computers: only include calcjobs that were ran on these computers
    :param user: only include calcjobs of this user
    :param exit_status: only select calcjob with this exit_status
    :param only_not_cleaned: only include calcjobs whose workdir have not been cleaned
    :return: mapping of computer uuid and list of remote folder
    """
    from datetime import timedelta

    from aiida.common import timezone
    from aiida.orm import CalcJobNode

    filters_calc: dict[str, t.Any] = {}
    filters_computer = {}
    filters_remote = {}

    if user is None:
        if backend:
            user = orm.User.get_collection(backend).get_default()
        else:
            user = orm.User.collection.get_default()

    if computers is not None:
        filters_computer['id'] = {'in': [computer.pk for computer in computers]}

    if past_days is not None:
        filters_calc['mtime'] = {'>': timezone.now() - timedelta(days=past_days)}

    if older_than is not None:
        older_filter = {'<': timezone.now() - timedelta(days=older_than)}
        # Check if we need to apply the AND condition
        if 'mtime' not in filters_calc:
            filters_calc['mtime'] = older_filter
        else:
            past_filter = filters_calc['mtime']
            filters_calc['mtime'] = {'and': [past_filter, older_filter]}

    if exit_status is not None:
        filters_calc['attributes.exit_status'] = exit_status

    if pks:
        filters_calc['id'] = {'in': pks}

    if only_not_cleaned is True:
        filters_remote['or'] = [
            {f'extras.{RemoteData.KEY_EXTRA_CLEANED}': {'!==': True}},
            {'extras': {'!has_key': RemoteData.KEY_EXTRA_CLEANED}},
        ]

    query = orm.QueryBuilder(backend=backend)
    query.append(CalcJobNode, tag='calc', filters=filters_calc)
    query.append(
        RemoteData, tag='remote', project=['*'], edge_filters={'label': 'remote_folder'}, filters=filters_remote
    )
    query.append(orm.Computer, with_node='calc', tag='computer', project=['uuid'], filters=filters_computer)
    query.append(orm.User, with_node='calc', filters={'email': user.email})  # type: ignore[union-attr]

    if query.count() == 0:
        return None

    path_mapping: dict[str, list[RemoteData]] = {}

    for remote_data, computer_uuid in query.iterall():
        path_mapping.setdefault(computer_uuid, []).append(remote_data)

    return path_mapping


def get_calcjob_stashed_paths(
    pks: list[int] | None = None,
    past_days: int | None = None,
    older_than: int | None = None,
    computers: Sequence[orm.Computer] | None = None,
    user: orm.User | None = None,
    backend: StorageBackend | None = None,
    exit_status: int | None = None,
    only_not_cleaned: bool = False,
):
    """Return a mapping of computer uuids to a list of stashed remote paths, for a given set of calcjobs.

    :param pks: only include calcjobs with a pk in this list
    :param past_days: only include calcjobs created since past_days
    :param older_than: only include calcjobs older than
    :param computers: only include calcjobs that were ran on these computers
    :param user: only include calcjobs of this user
    :param exit_status: only select calcjob with this exit_status
    :param only_not_cleaned: only include calcjobs whose stashed directories have not been cleaned
    :return: mapping of computer uuid and list of remote stash nodes
    """
    from datetime import timedelta

    from aiida.common import timezone
    from aiida.orm import CalcJobNode
    from aiida.orm.nodes.data.remote.stash import RemoteStashData

    filters_calc: dict[str, t.Any] = {}
    filters_computer = {}
    filters_stash = {}

    if user is None:
        if backend:
            user = orm.User.get_collection(backend).get_default()
        else:
            user = orm.User.collection.get_default()

    if computers is not None:
        filters_computer['id'] = {'in': [computer.pk for computer in computers]}

    if past_days is not None:
        filters_calc['mtime'] = {'>': timezone.now() - timedelta(days=past_days)}

    if older_than is not None:
        older_filter = {'<': timezone.now() - timedelta(days=older_than)}
        if 'mtime' not in filters_calc:
            filters_calc['mtime'] = older_filter
        else:
            past_filter = filters_calc['mtime']
            filters_calc['mtime'] = {'and': [past_filter, older_filter]}

    if exit_status is not None:
        filters_calc['attributes.exit_status'] = exit_status

    if pks:
        filters_calc['id'] = {'in': pks}

    if only_not_cleaned is True:
        filters_stash['or'] = [
            {f'extras.{RemoteData.KEY_EXTRA_CLEANED}': {'!==': True}},
            {'extras': {'!has_key': RemoteData.KEY_EXTRA_CLEANED}},
        ]

    query = orm.QueryBuilder(backend=backend)
    query.append(CalcJobNode, tag='calc', filters=filters_calc)
    query.append(
        RemoteStashData, tag='stash', project=['*'], edge_filters={'label': 'remote_stash'}, filters=filters_stash
    )
    query.append(orm.Computer, with_node='calc', tag='computer', project=['uuid'], filters=filters_computer)
    query.append(orm.User, with_node='calc', filters={'email': user.email})  # type: ignore[union-attr]

    if query.count() == 0:
        return None

    path_mapping: dict[str, list] = {}

    for stash_data, computer_uuid in query.iterall():
        path_mapping.setdefault(computer_uuid, []).append(stash_data)

    return path_mapping
