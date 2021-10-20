# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Generic functions to verify the integrity of the database and optionally apply patches to fix problems."""
import os

from aiida.common import exceptions

TABLES_UUID_DEDUPLICATION = ('db_dbcomment', 'db_dbcomputer', 'db_dbgroup', 'db_dbnode')


def _get_duplicate_uuids(table):
    """Retrieve rows with duplicate UUIDS.

    :param table: database table with uuid column, e.g. 'db_dbnode'
    :return: list of tuples of (id, uuid) of rows with duplicate UUIDs
    """
    from aiida.manage.manager import get_manager
    backend = get_manager().get_backend()
    query = f"""
        SELECT s.id, s.uuid FROM (SELECT *, COUNT(*) OVER(PARTITION BY uuid) AS c FROM {table})
        AS s WHERE c > 1
        """
    return backend.execute_raw(query)


def verify_uuid_uniqueness(table):
    """Check whether database table contains rows with duplicate UUIDS.

    :param table: Database table with uuid column, e.g. 'db_dbnode'
    :type str:

    :raises: IntegrityError if table contains rows with duplicate UUIDS.
    """
    duplicates = _get_duplicate_uuids(table=table)

    if duplicates:
        raise exceptions.IntegrityError(
            'Table {table:} contains rows with duplicate UUIDS: run '
            '`verdi database integrity detect-duplicate-uuid -t {table:}` to address the problem'.format(table=table)
        )


def _apply_new_uuid_mapping(table, mapping):
    """Take a mapping of pks to UUIDs and apply it to the given table.

    :param table: database table with uuid column, e.g. 'db_dbnode'
    :param mapping: dictionary of UUIDs mapped onto a pk
    """
    from aiida.manage.manager import get_manager
    backend = get_manager().get_backend()
    for pk, uuid in mapping.items():
        query = f"""UPDATE {table} SET uuid = '{uuid}' WHERE id = {pk}"""
        with backend.cursor() as cursor:
            cursor.execute(query)


def deduplicate_uuids(table=None, dry_run=True):
    """Detect and solve entities with duplicate UUIDs in a given database table.

    Before aiida-core v1.0.0, there was no uniqueness constraint on the UUID column of the node table in the database
    and a few other tables as well. This made it possible to store multiple entities with identical UUIDs in the same
    table without the database complaining. This bug was fixed in aiida-core=1.0.0 by putting an explicit uniqueness
    constraint on UUIDs on the database level. However, this would leave databases created before this patch with
    duplicate UUIDs in an inconsistent state. This command will run an analysis to detect duplicate UUIDs in a given
    table and solve it by generating new UUIDs. Note that it will not delete or merge any rows.

    :return: list of strings denoting the performed operations
    :raises ValueError: if the specified table is invalid
    """
    from collections import defaultdict
    import distutils.dir_util

    from aiida.common.utils import get_new_uuid

    from .utils import get_node_repository_sub_folder  # pylint: disable=no-name-in-module

    if table not in TABLES_UUID_DEDUPLICATION:
        raise ValueError(f"invalid table {table}: choose from {', '.join(TABLES_UUID_DEDUPLICATION)}")

    mapping = defaultdict(list)

    for pk, uuid in _get_duplicate_uuids(table=table):
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
                messages.append(f'would update UUID of {table} row<{pk}> from {uuid_ref} to {uuid_new}')
            else:
                messages.append(f'updated UUID of {table} row<{pk}> from {uuid_ref} to {uuid_new}')
                dirpath_repo_ref = get_node_repository_sub_folder(uuid_ref)
                dirpath_repo_new = get_node_repository_sub_folder(uuid_new)

                # First make sure the new repository exists, then copy the contents of the ref into the new. We use the
                # somewhat unknown `distuitils.dir_util` method since that does just contents as we want.
                os.makedirs(dirpath_repo_new, exist_ok=True)
                distutils.dir_util.copy_tree(dirpath_repo_ref, dirpath_repo_new)

    if not dry_run:
        _apply_new_uuid_mapping(table, mapping_new_uuid)

    if not messages:
        messages = ['no duplicate UUIDs found']

    return messages
