# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Generic functions to verify the integrity of the database and optionally apply patches to fix problems."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import uuid as UUID

from aiida.common.exceptions import IntegrityError


def verify_node_uuid_uniqueness():
    """Check whether the database contains nodes with duplicate UUIDS.

    :raises: IntegrityError if database contains nodes with duplicate UUIDS.
    """
    duplicates = get_duplicate_node_uuids()

    if duplicates:
        raise IntegrityError('your database contains nodes with duplicate UUIDS: '
                             'run `verdi database integrity duplicate-node-uuid` to return to a consistent state')


def get_duplicate_node_uuids():
    """Retrieve nodes with duplicate UUIDS.

    :return: list of tuples of (pk, uuid) of nodes with duplicate UUIDs
    """
    from aiida.orm.backends import construct_backend

    backend = construct_backend()
    duplicates = backend.query_manager.get_duplicate_node_uuids()

    return duplicates


def deduplicate_node_uuids(dry_run=True):
    """Detect and solve nodes with duplicate UUIDs.

    Before aiida-core v1.0.0, there was no uniqueness constraint on the UUID column of the Node table in the database.
    This made it possible to store multiple nodes with identical UUIDs without the database complaining. This was bug
    was fixed in aiida-core=1.0.0 by putting an explicit uniqueness constraint on node UUIDs on the database level.
    However, this would leave databases created before this patch with duplicate UUIDs in an inconsistent state. This
    command will run an analysis to detect duplicate UUIDs in the node table and solve it by generating new UUIDs. Note
    that it will not delete or merge any nodes.

    :param dry_run: when True, no actual changes will be made
    :return: list of strings denoting the performed operations, or those that would have been applied for dry_run=False
    """
    from collections import defaultdict

    from aiida.backends.settings import AIIDANODES_UUID_VERSION
    from aiida.orm import load_node

    uuid_generator = getattr(UUID, 'uuid{}'.format(AIIDANODES_UUID_VERSION))

    mapping = defaultdict(list)

    for pk, uuid in get_duplicate_node_uuids():
        mapping[uuid].append(int(pk))

    def copy_repo_folder(node_source, uuid):
        """
        Copy the repository folder from source node to a new location based on the given UUID.

        :param node_source: the node whose repository folder contents to copy
        :param uuid: the UUID that will be used to generate the sharded folder location for the copied folder
        """
        from aiida.common.folders import RepositoryFolder
        folder = RepositoryFolder('node', uuid)
        folder.replace_with_folder(node_source.folder.abspath)

    messages = []

    for uuid, nodes in mapping.items():

        uuid_old = None

        for pk in nodes:

            # We don't have to change all nodes that have the same UUID, the first one can keep the original
            if uuid_old is None:
                node_source = load_node(pk)
                uuid_old = uuid
                continue

            node = load_node(pk)
            uuid_new = str(uuid_generator())

            if dry_run:
                messages.append('would update UUID of Node<{}> from {} to {}'.format(pk, uuid_old, uuid_new))
            else:
                node._dbnode.uuid = uuid_new  # pylint: disable=protected-access
                node._dbnode.save()  # pylint: disable=protected-access
                copy_repo_folder(node_source, uuid_new)
                messages.append('updated UUID of Node<{}> from {} to {}'.format(pk, uuid_old, uuid_new))

    if not messages:
        messages = ['no duplicate UUIDs found']

    return messages
