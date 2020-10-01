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
import functools
import io
import os
import pathlib
import re
import typing

import numpy
from disk_objectstore import Container
from disk_objectstore.utils import LazyOpener

from aiida.common import exceptions, json
from aiida.repository.backend import AbstractRepositoryBackend
from aiida.repository.common import File, FileType
from aiida.repository.repository import Repository

ISOFORMAT_DATETIME_REGEX = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+(\+\d{2}:\d{2})?$')
REGEX_SHARD_SUB_LEVEL = re.compile(r'^[0-9a-f]{2}$')
REGEX_SHARD_FINAL_LEVEL = re.compile(r'^[0-9a-f-]{32}$')


class LazyFile(File):
    """Subclass of `File` where `key` also allows `LazyOpener` in addition to a string.

    This subclass is necessary because the migration will be storing instances of `LazyOpener` as the `key` which should
    normally only be a string. This subclass updates the `key` type check to allow this.
    """

    def __init__(
        self,
        name: str = '',
        file_type: FileType = FileType.DIRECTORY,
        key: typing.Union[str, None, LazyOpener] = None,
        objects: typing.Dict[str, 'File'] = None
    ):
        # pylint: disable=super-init-not-called
        if not isinstance(name, str):
            raise TypeError('name should be a string.')

        if not isinstance(file_type, FileType):
            raise TypeError('file_type should be an instance of `FileType`.')

        if key is not None and not isinstance(key, (str, LazyOpener)):
            raise TypeError('key should be `None` or a string.')

        if objects is not None and any([not isinstance(obj, self.__class__) for obj in objects.values()]):
            raise TypeError('objects should be `None` or a dictionary of `File` instances.')

        if file_type == FileType.DIRECTORY and key is not None:
            raise ValueError('an object of type `FileType.DIRECTORY` cannot define a key.')

        if file_type == FileType.FILE and objects is not None:
            raise ValueError('an object of type `FileType.FILE` cannot define any objects.')

        self._name = name
        self._file_type = file_type
        self._key = key
        self._objects = objects or {}


class MigrationRepository(Repository):
    """Subclass of `Repository` that uses `LazyFile` instead of `File` as its file class."""

    _file_cls = LazyFile


class NoopRepositoryBackend(AbstractRepositoryBackend):
    """Implementation of the ``AbstractRepositoryBackend`` where all write operations are no-ops.

    This repository backend is used to use the ``Repository`` interface to build repository metadata but instead of
    actually writing the content of the current repository to disk elsewhere, it will simply open a lazy file opener.
    In a subsequent step, all these streams are passed to the new Disk Object Store that will write their content
    directly to pack files for optimal efficiency.
    """

    def put_object_from_filelike(self, handle: io.BufferedIOBase) -> str:
        """Store the byte contents of a file in the repository.

        :param handle: filelike object with the byte content to be stored.
        :return: the generated fully qualified identifier for the object within the repository.
        :raises TypeError: if the handle is not a byte stream.
        """
        return LazyOpener(handle.name)

    def has_object(self, key: str) -> bool:
        """Return whether the repository has an object with the given key.

        :param key: fully qualified identifier for the object within the repository.
        :return: True if the object exists, False otherwise.
        """
        raise NotImplementedError()


def migrate_legacy_repository(node_count, shard=None):
    """Migrate the legacy file repository to the new disk object store and return mapping of repository metadata.

    The format of the return value will be a dictionary where the keys are the UUIDs of the nodes whose repository
    folder has contents have been migrated to the disk object store. The values are the repository metadata that contain
    the keys for the generated files with which the files in the disk object store can be retrieved. The format of the
    repository metadata follows exactly that of what is generated normally by the ORM.

    This implementation consciously uses the ``Repository`` interface in order to not have to rewrite the logic that
    builds the nested repository metadata based on the contents of a folder on disk. The advantage is that in this way
    it is guarantee that the exact same repository metadata is generated as it would have during normal operation.
    However, if the ``Repository`` interface or its implementation ever changes, it is possible that this solution will
    have to be adapted and the significant parts of the implementation will have to be copy pasted here.

    :return: mapping of node UUIDs onto the new repository metadata.
    :raises `~aiida.common.exceptions.DatabaseMigrationError`: in case the container of the migrated repository already
        exists or if the repository does not exist but the database contains at least one node.
    """
    # pylint: disable=too-many-locals
    from aiida.manage.configuration import get_profile

    profile = get_profile()
    backend = NoopRepositoryBackend()
    repository = MigrationRepository(backend=backend)

    # Initialize the new container: don't go through the profile, because that will not check if it already exists
    filepath = pathlib.Path(profile.repository_path) / 'container'
    basepath = pathlib.Path(profile.repository_path) / 'repository' / 'node'
    container = Container(filepath)

    if not basepath.is_dir():
        # If the database is empty, this is a new profile and so it is normal the repo folder doesn't exist. We simply
        # return as there is nothing to migrate
        if profile.is_test_profile or node_count == 0:
            return None, None

        raise exceptions.DatabaseMigrationError(
            f'the file repository `{basepath}` does not exist but the database is not empty, it contains {node_count} '
            'nodes. Aborting the migration.'
        )

    # When calling this function multiple times, once for each shard, we should only check whether the container has
    # already been initialized for the first shard.
    if shard is None or shard == '00':
        if container.is_initialised and not profile.is_test_profile:
            raise exceptions.DatabaseMigrationError(
                f'the container {filepath} already exists. If you ran this migration before and it failed simply '
                'delete this directory and restart the migration.'
            )

        container.init_container(clear=True, **profile.defaults['repository'])

    node_repository_dirpaths, missing_sub_repo_folder = get_node_repository_dirpaths(basepath, shard)

    filepaths = []
    streams = []
    mapping_metadata = {}

    # Loop over all the folders for each node that was found in the existing file repository and generate the repository
    # metadata that will have to be stored on the node. Calling `put_object_from_tree` will generate the virtual
    # hierarchy in memory, writing the files not actually to disk but opening lazy file handles, and then the call to
    # `serialize_repository` serializes the virtual hierarchy into JSON storable dictionary. This will later be stored
    # on the nodes in the database, and so it is added to the `mapping_metadata` which will be returned from this
    # function. After having constructed the virtual hierarchy, we walk over the contents and take just the files and
    # add the value (which is the `LazyOpener`) to the `streams` list as well as its relative path to `filepaths`.
    for node_uuid, node_dirpath in node_repository_dirpaths.items():
        repository.put_object_from_tree(node_dirpath)
        metadata = serialize_repository(repository)
        mapping_metadata[node_uuid] = metadata
        for root, _, filenames in repository.walk():
            for filename in filenames:
                parts = list(pathlib.Path(root / filename).parts)
                filepaths.append((node_uuid, parts))
                streams.append(functools.reduce(lambda objects, part: objects['o'].get(part), parts, metadata)['k'])

        # Reset the repository to a clean node repository, which removes the internal virtual file hierarchy
        repository.reset()

    # Free up the memory of this mapping that is no longer needed and can be big
    del node_repository_dirpaths

    hashkeys = container.add_streamed_objects_to_pack(streams, compress=False, open_streams=True)

    # Now all that remains is to go through all the generated repository metadata, stored for each node in the
    # `mapping_metadata` and replace the "values" for all the files, which are currently still the `LazyOpener`
    # instances, and replace them with the hashkey that was generated from its content by the DOS container.
    for hashkey, (node_uuid, parts) in zip(hashkeys, filepaths):
        repository_metadata = mapping_metadata[node_uuid]
        functools.reduce(lambda objects, part: objects['o'].get(part), parts, repository_metadata)['k'] = hashkey

    del filepaths
    del streams

    return mapping_metadata, missing_sub_repo_folder


def get_node_repository_dirpaths(basepath, shard=None):
    """Return a mapping of node UUIDs onto the path to their current repository folder in the old repository.

    :param basepath: the absolute path of the base folder of the old file repository.
    :param shard: optional shard to define which first shard level to check. If `None`, all shard levels are checked.
    :return: dictionary of node UUID onto absolute filepath and list of node repo missing one of the two known sub
        folders, ``path`` or ``raw_input``, which is unexpected.
    :raises `~aiida.common.exceptions.DatabaseMigrationError`: if the repository contains node folders that contain both
        the `path` and `raw_input` subdirectories, which should never happen.
    """
    # pylint: disable=too-many-branches
    from aiida.manage.configuration import get_profile

    profile = get_profile()
    mapping = {}
    missing_sub_repo_folder = []
    contains_both = []

    if shard is not None:

        # If the shard is not present in the basepath, there is nothing to do
        if shard not in os.listdir(basepath):
            return mapping, missing_sub_repo_folder

        shards = [pathlib.Path(basepath) / shard]
    else:
        shards = basepath.iterdir()

    for shard_one in shards:

        if not REGEX_SHARD_SUB_LEVEL.match(shard_one.name):
            continue

        for shard_two in shard_one.iterdir():

            if not REGEX_SHARD_SUB_LEVEL.match(shard_two.name):
                continue

            for shard_three in shard_two.iterdir():

                if not REGEX_SHARD_FINAL_LEVEL.match(shard_three.name):
                    continue

                uuid = shard_one.name + shard_two.name + shard_three.name
                dirpath = basepath / shard_one / shard_two / shard_three
                subdirs = [path.name for path in dirpath.iterdir()]

                path = None

                if 'path' in subdirs and 'raw_input' in subdirs:
                    # If the `path` is empty, we simply ignore and set `raw_input` to be migrated, otherwise we add
                    # the entry to `contains_both` which will cause the migration to fail.
                    if os.listdir(dirpath / 'path'):
                        contains_both.append(str(dirpath))
                    else:
                        path = dirpath / 'raw_input'
                elif 'path' in subdirs:
                    path = dirpath / 'path'
                elif 'raw_input' in subdirs:
                    path = dirpath / 'raw_input'
                else:
                    missing_sub_repo_folder.append(str(dirpath))

                if path is not None:
                    mapping[uuid] = path

    if contains_both and not profile.is_test_profile:
        raise exceptions.DatabaseMigrationError(
            f'The file repository `{basepath}` contained node repository folders that contained both the `path` as well'
            ' as the `raw_input` subfolders. This should not have happened, as the latter is used for calculation job '
            'nodes, and the former for all other nodes. The migration will be aborted and the paths of the offending '
            'node folders will be printed below. If you know which of the subpaths is incorrect, you can manually '
            'delete it and then restart the migration. Here is the list of offending node folders:\n' +
            '\n'.join(contains_both)
        )

    return mapping, missing_sub_repo_folder


def serialize_repository(repository: Repository) -> dict:
    """Serialize the metadata into a JSON-serializable format.

    .. note:: the serialization format is optimized to reduce the size in bytes.

    :return: dictionary with the content metadata.
    """
    file_object = repository._directory  # pylint: disable=protected-access
    if file_object.file_type == FileType.DIRECTORY:
        if file_object.objects:
            return {'o': {key: obj.serialize() for key, obj in file_object.objects.items()}}
        return {}
    return {'k': file_object.key}


def ensure_repository_folder_created(uuid):
    """Make sure that the repository sub folder for the node with the given UUID exists or create it.

    :param uuid: UUID of the node
    """
    dirpath = get_node_repository_sub_folder(uuid)
    os.makedirs(dirpath, exist_ok=True)


def put_object_from_string(uuid, name, content):
    """Write a file with the given content in the repository sub folder of the given node.

    :param uuid: UUID of the node
    :param name: name to use for the file
    :param content: the content to write to the file
    """
    ensure_repository_folder_created(uuid)
    basepath = get_node_repository_sub_folder(uuid)
    dirname = os.path.dirname(name)

    if dirname:
        os.makedirs(os.path.join(basepath, dirname), exist_ok=True)

    filepath = os.path.join(basepath, name)

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


def get_node_repository_sub_folder(uuid, subfolder='path'):
    """Return the absolute path to the sub folder `path` within the repository of the node with the given UUID.

    :param uuid: UUID of the node
    :return: absolute path to node repository folder, i.e `/some/path/repository/node/12/ab/c123134-a123/path`
    """
    from aiida.manage.configuration import get_profile

    uuid = str(uuid)

    repo_dirpath = os.path.join(get_profile().repository_path, 'repository')
    node_dirpath = os.path.join(repo_dirpath, 'node', uuid[:2], uuid[2:4], uuid[4:], subfolder)

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


def get_repository_object(hashkey):
    """Return the content of an object stored in the disk object store repository for the given hashkey."""
    from aiida.manage.configuration import get_profile

    dirpath_container = os.path.join(get_profile().repository_path, 'container')
    container = Container(dirpath_container)
    return container.get_object_content(hashkey)


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
