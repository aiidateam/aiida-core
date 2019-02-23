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

    :param table: database table with uuid column, e.g. 'db_dbnode'
    :return: list of tuples of (id, uuid) of rows with duplicate UUIDs
    """
    backend = get_manager().get_backend()
    return backend.query_manager.get_duplicate_uuids(table=table)


def verify_uuid_uniqueness(table):
    """Check whether database table contains rows with duplicate UUIDS.

    :param table: Database table with uuid column, e.g. 'db_dbnode'
    :type str:

    :raises: IntegrityError if table contains rows with duplicate UUIDS.
    """
    duplicates = get_duplicate_uuids(table=table)

    if duplicates:
        raise exceptions.IntegrityError(
            'Table {table:} contains rows with duplicate UUIDS: run '
            '`verdi database integrity detect-duplicate-uuid -t {table:}` to address the problem'.format(table=table))


def apply_new_uuid_mapping(table, mapping):
    """Take a mapping of pks to UUIDs and apply it to the given table.

    :param table: database table with uuid column, e.g. 'db_dbnode'
    :param mapping: dictionary of UUIDs mapped onto a pk
    """
    backend = get_manager().get_backend()
    backend.query_manager.apply_new_uuid_mapping(table, mapping)


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
    from aiida.orm.utils.repository import Repository

    if table not in TABLES_UUID_DEDUPLICATION:
        raise ValueError('invalid table {}: choose from {}'.format(table, ', '.join(TABLES_UUID_DEDUPLICATION)))

    mapping = defaultdict(list)

    for pk, uuid in get_duplicate_uuids(table=table):
        mapping[uuid].append(int(pk))

    messages = []
    mapping_new_uuid = {}

    for uuid, rows in mapping.items():

        uuid_ref = None

        for pk in rows:

            # We don't have to change all rows that have the same UUID, the first one can keep the original
            if uuid_ref is None:
                uuid_ref = uuid
                continue

            uuid_new = str(get_new_uuid())
            mapping_new_uuid[pk] = uuid_new

            if dry_run:
                messages.append('would update UUID of {} row<{}> from {} to {}'.format(table, pk, uuid_ref, uuid_new))
            else:
                messages.append('updated UUID of {} row<{}> from {} to {}'.format(table, pk, uuid_ref, uuid_new))
                repo_ref = Repository(uuid_ref, True, 'path')
                repo_new = Repository(uuid_new, False, 'path')
                repo_new.put_object_from_tree(repo_ref._get_base_folder().abspath)  # pylint: disable=protected-access
                repo_new.store()

    if not dry_run:
        apply_new_uuid_mapping(table, mapping_new_uuid)

    if not messages:
        messages = ['no duplicate UUIDs found']

    return messages
