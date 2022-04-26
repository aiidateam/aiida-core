# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migration from the "legacy" JSON format, to an sqlite database, and node uuid based repository to hash based."""
from contextlib import contextmanager
from datetime import datetime
from hashlib import sha256
from pathlib import Path, PurePosixPath
import shutil
import tarfile
from typing import Any, Callable, ContextManager, Dict, Iterator, List, Optional, Tuple, Union

from archive_path import ZipPath
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError

from aiida.common.exceptions import CorruptStorage, StorageMigrationError
from aiida.common.hashing import chunked_file_hash
from aiida.common.progress_reporter import get_progress_reporter
from aiida.repository.common import File, FileType
from aiida.storage.log import MIGRATE_LOGGER

from . import v1_db_schema as v1_schema
from ..utils import DB_FILENAME, REPO_FOLDER, create_sqla_engine
from .utils import update_metadata

_NODE_ENTITY_NAME = 'Node'
_GROUP_ENTITY_NAME = 'Group'
_COMPUTER_ENTITY_NAME = 'Computer'
_USER_ENTITY_NAME = 'User'
_LOG_ENTITY_NAME = 'Log'
_COMMENT_ENTITY_NAME = 'Comment'

file_fields_to_model_fields: Dict[str, Dict[str, str]] = {
    _NODE_ENTITY_NAME: {
        'dbcomputer': 'dbcomputer_id',
        'user': 'user_id'
    },
    _GROUP_ENTITY_NAME: {
        'user': 'user_id'
    },
    _COMPUTER_ENTITY_NAME: {},
    _LOG_ENTITY_NAME: {
        'dbnode': 'dbnode_id'
    },
    _COMMENT_ENTITY_NAME: {
        'dbnode': 'dbnode_id',
        'user': 'user_id'
    }
}

aiida_orm_to_backend = {
    _USER_ENTITY_NAME: v1_schema.DbUser,
    _GROUP_ENTITY_NAME: v1_schema.DbGroup,
    _NODE_ENTITY_NAME: v1_schema.DbNode,
    _COMMENT_ENTITY_NAME: v1_schema.DbComment,
    _COMPUTER_ENTITY_NAME: v1_schema.DbComputer,
    _LOG_ENTITY_NAME: v1_schema.DbLog,
}

LEGACY_TO_MAIN_REVISION = 'main_0000'


def perform_v1_migration(  # pylint: disable=too-many-locals
    inpath: Path,
    working: Path,
    new_zip: ZipPath,
    central_dir: Dict[str, Any],
    is_tar: bool,
    metadata: dict,
    data: dict,
) -> Path:
    """Perform the repository and JSON to SQLite migration.

    1. Iterate though the repository paths in the archive
    2. If a file, hash its contents and, if not already present, stream it to the new archive
    3. Store a mapping of the node UUIDs to a list of (path, hashkey or None if a directory) tuples

    :param inpath: the input path to the old archive
    :param metadata: the metadata to migrate
    :param data: the data to migrate

    :returns:the path to the sqlite database file
    """
    MIGRATE_LOGGER.report('Initialising new archive...')
    node_repos: Dict[str, List[Tuple[str, Optional[str]]]] = {}
    in_archive_context: Callable[[Path], ContextManager[Union[Path, ZipPath]]] = ZipPath
    if is_tar:
        # we cannot stream from a tar file performantly, so we extract it to disk first
        @contextmanager
        def _in_archive_context(_inpath):
            temp_folder = working / 'temp_unpack'
            with tarfile.open(_inpath, 'r') as tar:
                MIGRATE_LOGGER.report('Extracting tar archive...(may take a while)')
                tar.extractall(temp_folder)
            yield temp_folder
            MIGRATE_LOGGER.report('Removing extracted tar archive...')
            shutil.rmtree(temp_folder)

        in_archive_context = _in_archive_context

    with in_archive_context(inpath) as path:
        length = sum(1 for _ in path.glob('**/*'))
        base_parts = len(path.parts)
        with get_progress_reporter()(desc='Converting repo', total=length) as progress:
            for subpath in path.glob('**/*'):
                progress.update()
                parts = subpath.parts[base_parts:]
                # repository file are stored in the legacy archive as `nodes/uuid[0:2]/uuid[2:4]/uuid[4:]/path/...`
                if len(parts) < 6 or parts[0] != 'nodes' or parts[4] not in ('raw_input', 'path'):
                    continue
                uuid = ''.join(parts[1:4])
                posix_rel = PurePosixPath(*parts[5:])
                hashkey = None
                if subpath.is_file():
                    with subpath.open('rb') as handle:
                        hashkey = chunked_file_hash(handle, sha256)
                    if f'{REPO_FOLDER}/{hashkey}' not in central_dir:
                        (new_zip / f'{REPO_FOLDER}/{hashkey}').putfile(subpath)
                node_repos.setdefault(uuid, []).append((posix_rel.as_posix(), hashkey))
        MIGRATE_LOGGER.report(f'Unique repository files written: {len(central_dir)}')

    # convert the JSON database to SQLite
    _json_to_sqlite(working / DB_FILENAME, data, node_repos)

    # remove legacy keys from metadata and store
    metadata.pop('unique_identifiers', None)
    metadata.pop('all_fields_info', None)
    # remove legacy key nesting
    metadata['creation_parameters'] = metadata.pop('export_parameters', {})
    metadata['key_format'] = 'sha256'

    # update the version in the metadata
    update_metadata(metadata, LEGACY_TO_MAIN_REVISION)

    return working / DB_FILENAME


def _json_to_sqlite(  # pylint: disable=too-many-branches,too-many-locals
    outpath: Path, data: dict, node_repos: Dict[str, List[Tuple[str, Optional[str]]]], batch_size: int = 100
) -> None:
    """Convert a JSON archive format to SQLite."""
    from aiida.tools.archive.common import batch_iter

    MIGRATE_LOGGER.report('Converting DB to SQLite')

    engine = create_sqla_engine(outpath)
    v1_schema.ArchiveV1Base.metadata.create_all(engine)

    with engine.begin() as connection:
        # proceed in order of relationships
        for entity_type in (
            _USER_ENTITY_NAME, _COMPUTER_ENTITY_NAME, _GROUP_ENTITY_NAME, _NODE_ENTITY_NAME, _LOG_ENTITY_NAME,
            _COMMENT_ENTITY_NAME
        ):
            if not data['export_data'].get(entity_type, {}):
                continue
            length = len(data['export_data'].get(entity_type, {}))
            backend_cls = aiida_orm_to_backend[entity_type]
            with get_progress_reporter()(desc=f'Adding {entity_type}s', total=length) as progress:
                for nrows, rows in batch_iter(_iter_entity_fields(data, entity_type, node_repos), batch_size):
                    # to-do check for unused keys?
                    # to-do handle null values?
                    try:
                        connection.execute(insert(backend_cls.__table__), rows)  # type: ignore
                    except IntegrityError as exc:
                        raise StorageMigrationError(f'Database integrity error: {exc}') from exc
                    progress.update(nrows)

    if not (data['groups_uuid'] or data['links_uuid']):
        return None

    with engine.begin() as connection:

        # get mapping of node IDs to node UUIDs
        node_uuid_map = {
            uuid: pk for uuid, pk in connection.execute(select(v1_schema.DbNode.uuid, v1_schema.DbNode.id))  # pylint: disable=unnecessary-comprehension
        }

        # links
        if data['links_uuid']:

            def _transform_link(link_row):
                try:
                    input_id = node_uuid_map[link_row['input']]
                except KeyError:
                    raise StorageMigrationError(f'Database contains link with unknown input node: {link_row}')
                try:
                    output_id = node_uuid_map[link_row['output']]
                except KeyError:
                    raise StorageMigrationError(f'Database contains link with unknown output node: {link_row}')
                return {
                    'input_id': input_id,
                    'output_id': output_id,
                    'label': link_row['label'],
                    'type': link_row['type']
                }

            with get_progress_reporter()(desc='Adding Links', total=len(data['links_uuid'])) as progress:
                for nrows, rows in batch_iter(data['links_uuid'], batch_size, transform=_transform_link):
                    connection.execute(insert(v1_schema.DbLink.__table__), rows)
                    progress.update(nrows)

        # groups to nodes
        if data['groups_uuid']:
            # get mapping of node IDs to node UUIDs
            group_uuid_map = {
                uuid: pk for uuid, pk in connection.execute(select(v1_schema.DbGroup.uuid, v1_schema.DbGroup.id))  # pylint: disable=unnecessary-comprehension
            }
            length = sum(len(uuids) for uuids in data['groups_uuid'].values())
            unknown_nodes: Dict[str, set] = {}
            with get_progress_reporter()(desc='Adding Group-Nodes', total=length) as progress:
                for group_uuid, node_uuids in data['groups_uuid'].items():
                    group_id = group_uuid_map[group_uuid]
                    rows = []
                    for uuid in node_uuids:
                        if uuid in node_uuid_map:
                            rows.append({'dbnode_id': node_uuid_map[uuid], 'dbgroup_id': group_id})
                        else:
                            unknown_nodes.setdefault(group_uuid, set()).add(uuid)
                    connection.execute(insert(v1_schema.DbGroupNodes.__table__), rows)
                    progress.update(len(node_uuids))
            if unknown_nodes:
                MIGRATE_LOGGER.warning(f'Dropped unknown nodes in groups: {unknown_nodes}')


def _convert_datetime(key, value):
    if key in ('time', 'ctime', 'mtime') and value is not None:
        return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')
    return value


def _iter_entity_fields(
    data,
    name: str,
    node_repos: Dict[str, List[Tuple[str, Optional[str]]]],
) -> Iterator[Dict[str, Any]]:
    """Iterate through entity fields."""
    keys = file_fields_to_model_fields.get(name, {})
    if name == _NODE_ENTITY_NAME:
        # here we merge in the attributes and extras before yielding
        attributes = data.get('node_attributes', {})
        extras = data.get('node_extras', {})
        for pk, all_fields in data['export_data'].get(name, {}).items():
            if pk not in attributes:
                raise CorruptStorage(f'Unable to find attributes info for Node with Pk={pk}')
            if pk not in extras:
                raise CorruptStorage(f'Unable to find extra info for Node with Pk={pk}')
            uuid = all_fields['uuid']
            repository_metadata = _create_repo_metadata(node_repos[uuid]) if uuid in node_repos else {}
            yield {
                **{keys.get(key, key): _convert_datetime(key, val) for key, val in all_fields.items()},
                **{
                    'id': pk,
                    'attributes': attributes[pk],
                    'extras': extras[pk],
                    'repository_metadata': repository_metadata
                }
            }
    else:
        for pk, all_fields in data['export_data'].get(name, {}).items():
            yield {**{keys.get(key, key): _convert_datetime(key, val) for key, val in all_fields.items()}, **{'id': pk}}


def _create_repo_metadata(paths: List[Tuple[str, Optional[str]]]) -> Dict[str, Any]:
    """Create the repository metadata.

    :param paths: list of (path, hashkey) tuples
    :return: the repository metadata
    """
    top_level = File()
    for _path, hashkey in paths:
        path = PurePosixPath(_path)
        if hashkey is None:
            _create_directory(top_level, path)
        else:
            directory = _create_directory(top_level, path.parent)
            directory.objects[path.name] = File(path.name, FileType.FILE, hashkey)
    return top_level.serialize()


def _create_directory(top_level: File, path: PurePosixPath) -> File:
    """Create a new directory with the given path.

    :param path: the relative path of the directory.
    :return: the created directory.
    """
    directory = top_level

    for part in path.parts:
        if part not in directory.objects:
            directory.objects[part] = File(part)

        directory = directory.objects[part]

    return directory
