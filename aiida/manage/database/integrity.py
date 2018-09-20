# -*- coding: utf-8 -*-
"""Generic functions to verify the integrity of the database and optionally apply patches to fix problems."""
from __future__ import absolute_import
import uuid as UUID


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
    from aiida.orm.backend import construct_backend

    uuid_generator = getattr(UUID, 'uuid{}'.format(AIIDANODES_UUID_VERSION))

    backend = construct_backend()
    mapping = defaultdict(list)

    query = 'SELECT s.id, s.uuid FROM (SELECT *, COUNT(*) OVER(PARTITION BY uuid) AS c FROM db_dbnode) AS s WHERE c > 1'
    duplicates = backend.query_manager.raw(query)

    for pk, uuid in duplicates:
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
