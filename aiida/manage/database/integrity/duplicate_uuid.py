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

from aiida.common import exceptions
from aiida.manage.manager import get_manager

__all__ = ('verify_uuid_uniqueness', 'get_duplicate_uuids', 'deduplicate_uuids', 'TABLES_UUID_DEDUPLICATION')

TABLES_UUID_DEDUPLICATION = ['db_dbcomment', 'db_dbcomputer', 'db_dbgroup', 'db_dbnode']


def get_duplicate_uuids(table):
    """Retrieve rows with duplicate UUIDS.

    :param table: Database table with uuid column, e.g. 'db_dbnode'
    :type str:

    :return: list of tuples of (id, uuid) of rows with duplicate UUIDs
    """
    backend = get_manager().get_backend()
    duplicates = backend.query_manager.get_duplicate_uuids(table=table)

    return duplicates


def verify_uuid_uniqueness(table):
    """Check whether database table contains rows with duplicate UUIDS.

    :param table: Database table with uuid column, e.g. 'db_dbnode'
    :type str:

    :raises: IntegrityError if table contains rows with duplicate UUIDS.
    """
    duplicates = get_duplicate_uuids(table=table)

    if duplicates:
        raise exceptions.IntegrityError(
            'Table {} contains rows with duplicate UUIDS: '
            'run `verdi database integrity duplicate-node-uuid` to return to a consistent state'.format(table))


def deduplicate_uuids(table=None, dry_run=True):
    """Detect and solve entities with duplicate UUIDs in a given database table.

    Before aiida-core v1.0.0, there was no uniqueness constraint on the UUID column of the node table in the database
    and a few other tables as well. This made it possible to store multiple entities with identical UUIDs in the same
    table without the database complaining. This bug was fixed in aiida-core=1.0.0 by putting an explicit uniqueness
    constraint on UUIDs on the database level. However, this would leave databases created before this patch with
    duplicate UUIDs in an inconsistent state. This command will run an analysis to detect duplicate UUIDs in a given
    table and solve it by generating new UUIDs. Note that it will not delete or merge any rows.

    :param dry_run: when True, no actual changes will be made
    :return: list of strings denoting the performed operations, or those that would have been applied for dry_run=False
    :raises ValueError: if the specified table is invalid
    """
    from collections import defaultdict

    from aiida.common.utils import get_new_uuid
    from aiida.orm import Node, load_computer, load_group, load_node
    from aiida.orm.utils.repository import Repository

    if table not in TABLES_UUID_DEDUPLICATION:
        raise ValueError('invalid table {}: choose from {}'.format(table, ', '.join(TABLES_UUID_DEDUPLICATION)))

    # A mapping of table to the corresponding entity loader, note that a loader for Comment is not implemented yet.
    loaders = {
        'db_dbcomputer': load_computer,
        'db_dbgroup': load_group,
        'db_dbnode': load_node,
    }

    mapping = defaultdict(list)

    for pk, uuid in get_duplicate_uuids(table=table):
        mapping[uuid].append(int(pk))

    messages = []

    try:
        load_entity = loaders[table]
    except KeyError:
        raise ValueError('no entity loader has been implemented yet for table {}'.format(table))

    for uuid, rows in mapping.items():

        uuid_old = None

        for pk in rows:

            # We don't have to change all rows that have the same UUID, the first one can keep the original
            if uuid_old is None:
                entity_reference = load_entity(pk)
                uuid_old = uuid
                continue

            entity = load_entity(pk)
            uuid_new = str(get_new_uuid())

            if dry_run:
                messages.append('would update UUID of {} row<{}> from {} to {}'.format(table, pk, uuid_old, uuid_new))
            else:

                entity.backend_entity._dbmodel.uuid = uuid_new  # pylint: disable=protected-access
                entity.backend_entity._dbmodel.save()  # pylint: disable=protected-access

                if isinstance(entity, Node):
                    entity._repository = Repository(entity.uuid, False, entity._repository_base_path)  # pylint: disable=protected-access
                    entity.put_object_from_tree(entity_reference._repository._get_base_folder().abspath)  # pylint: disable=protected-access
                    entity._repository.store()  # pylint: disable=protected-access

                messages.append('updated UUID of {} row<{}> from {} to {}'.format(table, pk, uuid_old, uuid_new))

    if not messages:
        messages = ['no duplicate UUIDs found']

    return messages
