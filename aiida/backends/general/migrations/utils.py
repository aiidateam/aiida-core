# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name
"""Various utils that should be used during migrations and migrations tests because the AiiDA ORM cannot be used."""
import datetime
import errno
import os
import re

import numpy

from aiida.common import json

ISOFORMAT_DATETIME_REGEX = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+(\+\d{2}:\d{2})?$')


def ensure_repository_folder_created(uuid):
    """Make sure that the repository sub folder for the node with the given UUID exists or create it.

    :param uuid: UUID of the node
    """
    dirpath = get_node_repository_sub_folder(uuid)

    try:
        os.makedirs(dirpath)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def put_object_from_string(uuid, name, content):
    """Write a file with the given content in the repository sub folder of the given node.

    :param uuid: UUID of the node
    :param name: name to use for the file
    :param content: the content to write to the file
    """
    ensure_repository_folder_created(uuid)
    filepath = os.path.join(get_node_repository_sub_folder(uuid), name)

    with open(filepath, 'w', encoding='utf-8') as handle:
        handle.write(content)


def get_object_from_repository(uuid, name):
    """Return the content of a file with the given name in the repository sub folder of the given node.

    :param uuid: UUID of the node
    :param name: name to use for the file
    """
    filepath = os.path.join(get_node_repository_sub_folder(uuid), name)

    with open(filepath) as handle:
        return handle.read()


def get_node_repository_sub_folder(uuid):
    """Return the absolute path to the sub folder `path` within the repository of the node with the given UUID.

    :param uuid: UUID of the node
    :return: absolute path to node repository folder, i.e `/some/path/repository/node/12/ab/c123134-a123/path`
    """
    from aiida.manage.configuration import get_profile

    uuid = str(uuid)

    repo_dirpath = os.path.join(get_profile().repository_path, 'repository')
    node_dirpath = os.path.join(repo_dirpath, 'node', uuid[:2], uuid[2:4], uuid[4:], 'path')

    return node_dirpath


def get_numpy_array_absolute_path(uuid, name):
    """Return the absolute path of a numpy array with the given name in the repository of the node with the given uuid.

    :param uuid: the UUID of the node
    :param name: the name of the numpy array
    :return: the absolute path of the numpy array file
    """
    return os.path.join(get_node_repository_sub_folder(uuid), f'{name}.npy')


def store_numpy_array_in_repository(uuid, name, array):
    """Store a numpy array in the repository folder of a node.

    :param uuid: the node UUID
    :param name: the name under which to store the array
    :param array: the numpy array to store
    """
    ensure_repository_folder_created(uuid)
    filepath = get_numpy_array_absolute_path(uuid, name)

    with open(filepath, 'wb') as handle:
        numpy.save(handle, array)


def delete_numpy_array_from_repository(uuid, name):
    """Delete the numpy array with a given name from the repository corresponding to a node with a given uuid.

    :param uuid: the UUID of the node
    :param name: the name of the numpy array
    """
    filepath = get_numpy_array_absolute_path(uuid, name)

    try:
        os.remove(filepath)
    except (IOError, OSError):
        pass


def load_numpy_array_from_repository(uuid, name):
    """Load and return a numpy array from the repository folder of a node.

    :param uuid: the node UUID
    :param name: the name under which to store the array
    :return: the numpy array
    """
    filepath = get_numpy_array_absolute_path(uuid, name)
    return numpy.load(filepath)


def recursive_datetime_to_isoformat(value):
    """Convert all datetime objects in the given value to string representations in ISO format.

    :param value: a mapping, sequence or single value optionally containing datetime objects
    """
    if isinstance(value, list):
        return [recursive_datetime_to_isoformat(_) for _ in value]

    if isinstance(value, dict):
        return dict((key, recursive_datetime_to_isoformat(val)) for key, val in value.items())

    if isinstance(value, datetime.datetime):
        return value.isoformat()

    return value


def dumps_json(dictionary):
    """Transforms all datetime object into isoformat and then returns the JSON."""
    return json.dumps(recursive_datetime_to_isoformat(dictionary))


def get_duplicate_uuids(table):
    """Retrieve rows with duplicate UUIDS.

    :param table: database table with uuid column, e.g. 'db_dbnode'
    :return: list of tuples of (id, uuid) of rows with duplicate UUIDs
    """
    from aiida.manage.manager import get_manager
    backend = get_manager().get_backend()
    return backend.query_manager.get_duplicate_uuids(table=table)


def verify_uuid_uniqueness(table):
    """Check whether database table contains rows with duplicate UUIDS.

    :param table: Database table with uuid column, e.g. 'db_dbnode'
    :type str:

    :raises: IntegrityError if table contains rows with duplicate UUIDS.
    """
    from aiida.common import exceptions
    duplicates = get_duplicate_uuids(table=table)

    if duplicates:
        raise exceptions.IntegrityError(
            'Table {table:} contains rows with duplicate UUIDS: run '
            '`verdi database integrity detect-duplicate-uuid -t {table:}` to address the problem'.format(table=table)
        )


def apply_new_uuid_mapping(table, mapping):
    """Take a mapping of pks to UUIDs and apply it to the given table.

    :param table: database table with uuid column, e.g. 'db_dbnode'
    :param mapping: dictionary of UUIDs mapped onto a pk
    """
    from aiida.manage.manager import get_manager
    backend = get_manager().get_backend()
    backend.query_manager.apply_new_uuid_mapping(table, mapping)


def deduplicate_uuids(table=None):
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
    import distutils.dir_util
    from collections import defaultdict

    from aiida.common.utils import get_new_uuid

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

            messages.append(f'updated UUID of {table} row<{pk}> from {uuid_ref} to {uuid_new}')
            dirpath_repo_ref = get_node_repository_sub_folder(uuid_ref)
            dirpath_repo_new = get_node_repository_sub_folder(uuid_new)

            # First make sure the new repository exists, then copy the contents of the ref into the new. We use the
            # somewhat unknown `distuitils.dir_util` method since that does just contents as we want.
            os.makedirs(dirpath_repo_new, exist_ok=True)
            distutils.dir_util.copy_tree(dirpath_repo_ref, dirpath_repo_new)

    apply_new_uuid_mapping(table, mapping_new_uuid)

    if not messages:
        messages = ['no duplicate UUIDs found']

    return messages
