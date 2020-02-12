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
    return os.path.join(get_node_repository_sub_folder(uuid), name + '.npy')


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
