###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Import an archive."""

from pathlib import Path
from typing import Any, Callable, Dict, Literal, Optional, Set, Tuple, Union

from tabulate import tabulate

from aiida import orm
from aiida.common import timezone
from aiida.common.exceptions import IncompatibleStorageSchema
from aiida.common.lang import type_check
from aiida.common.links import LinkType
from aiida.common.log import AIIDA_LOGGER
from aiida.common.progress_reporter import get_progress_reporter
from aiida.common.utils import DEFAULT_BATCH_SIZE, DEFAULT_FILTER_SIZE, batch_iter
from aiida.manage import get_manager
from aiida.orm.entities import EntityTypes
from aiida.orm.implementation import StorageBackend
from aiida.orm.querybuilder import QueryBuilder
from aiida.repository import Repository

from .abstract import ArchiveFormatAbstract
from .common import entity_type_to_orm
from .exceptions import ImportTestRun, ImportUniquenessError, ImportValidationError
from .implementations.sqlite_zip import ArchiveFormatSqlZip

__all__ = ('IMPORT_LOGGER', 'import_archive')

IMPORT_LOGGER = AIIDA_LOGGER.getChild('export')

MergeExtrasType = Tuple[Literal['k', 'n'], Literal['c', 'n'], Literal['l', 'u', 'd']]
MergeExtraDescs = (
    {'k': '(k)eep', 'n': 'do (n)ot keep'},
    {'c': '(c)reate', 'n': 'do (n)ot create'},
    {'l': '(l)eave existing', 'u': '(u)pdate with new', 'd': '(d)elete'},
)
MergeCommentsType = Literal['leave', 'newest', 'overwrite']

DUPLICATE_LABEL_MAX = 100
DUPLICATE_LABEL_TEMPLATE = '{0} (Imported #{1})'


def import_archive(
    path: Union[str, Path],
    *,
    archive_format: Optional[ArchiveFormatAbstract] = None,
    import_new_extras: bool = True,
    merge_extras: MergeExtrasType = ('k', 'n', 'l'),
    merge_comments: MergeCommentsType = 'leave',
    include_authinfos: bool = False,
    create_group: bool = True,
    group: Optional[orm.Group] = None,
    test_run: bool = False,
    backend: Optional[StorageBackend] = None,
    filter_size: int = DEFAULT_FILTER_SIZE,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> Optional[int]:
    """Import an archive into the AiiDA backend.

    :param path: the path to the archive
    :param archive_format: The class for interacting with the archive
    :param import_new_extras: Keep extras on new nodes (except private aiida keys), else strip
    :param merge_extras: Rules for merging extras into existing nodes.
        The first letter acts on extras that are present in the original node and not present in the imported node.
        Can be either:
        'k' (keep it) or
        'n' (do not keep it).
        The second letter acts on the imported extras that are not present in the original node.
        Can be either:
        'c' (create it) or
        'n' (do not create it).
        The third letter defines what to do in case of a name collision.
        Can be either:
        'l' (leave the old value),
        'u' (update with a new value),
        'd' (delete the extra)
    :param create_group: Add all imported nodes to the specified group, or an automatically created one
    :param group: Group wherein all imported Nodes will be placed.
        If None, one will be auto-generated.
    :param test_run: if True, do not write to file
    :param backend: the backend to import to. If not specified, the default backend is used.
    :param filter_size: query filters are batched by this number to avoid database parameter limits. Try reducing
        this value in case you run into related errors.
    :param batch_size: Batch size for streaming database rows

    :returns: Primary Key of the import Group

    :raises `~aiida.common.exceptions.CorruptStorage`: if the provided archive cannot be read.
    :raises `~aiida.common.exceptions.IncompatibleStorageSchema`: if the archive version is not at head.
    :raises `~aiida.tools.archive.exceptions.ImportValidationError`: if invalid entities are found in the archive.
    :raises `~aiida.tools.archive.exceptions.ImportUniquenessError`: if a new unique entity can not be created.
    """
    archive_format = archive_format or ArchiveFormatSqlZip()
    type_check(path, (str, Path))
    type_check(archive_format, ArchiveFormatAbstract)
    type_check(batch_size, int)
    type_check(import_new_extras, bool)
    type_check(merge_extras, tuple)
    if len(merge_extras) != 3:
        raise ValueError('merge_extras not of length 3')
    if not (merge_extras[0] in ['k', 'n'] and merge_extras[1] in ['c', 'n'] and merge_extras[2] in ['l', 'u', 'd']):
        raise ValueError('merge_extras contains invalid values')
    if merge_comments not in ('leave', 'newest', 'overwrite'):
        raise ValueError(f"merge_comments not in {('leave', 'newest', 'overwrite')!r}")
    type_check(group, orm.Group, allow_none=True)
    type_check(test_run, bool)
    backend = backend or get_manager().get_profile_storage()
    type_check(backend, StorageBackend)

    if group and not group.is_stored:
        group.store()

    # check the version is latest
    # to-do we should have a way to check the version against aiida-core
    # i.e. its not whether the version is the latest that matters, it is that it is compatible with the backend version
    # its a bit weird at the moment because django/sqlalchemy have different versioning
    if not archive_format.read_version(path) == archive_format.latest_version:
        raise IncompatibleStorageSchema(
            f'The archive version {archive_format.read_version(path)!r} '
            f'is not the latest version {archive_format.latest_version!r}'
        )

    IMPORT_LOGGER.report(
        str(
            tabulate(
                [
                    ['Archive', Path(path).name],
                    ['New Node Extras', 'keep' if import_new_extras else 'strip'],
                    ['Merge Node Extras (in database)', MergeExtraDescs[0][merge_extras[0]]],
                    ['Merge Node Extras (in archive)', MergeExtraDescs[1][merge_extras[1]]],
                    ['Merge Node Extras (in both)', MergeExtraDescs[2][merge_extras[2]]],
                    ['Merge Comments', merge_comments],
                    ['Computer Authinfos', 'include' if include_authinfos else 'exclude'],
                ],
                headers=['Parameters', ''],
            )
        )
        + '\n'
    )

    if test_run:
        IMPORT_LOGGER.report('Test run: nothing will be added to the profile')

    with archive_format.open(path, mode='r') as reader:
        backend_from = reader.get_backend()

        # To ensure we do not corrupt the backend database on a faulty import,
        # Every addition/update is made in a single transaction, which is commited on exit
        with backend.transaction():
            user_ids_archive_backend = _import_users(backend_from, backend, batch_size, filter_size)
            computer_ids_archive_backend = _import_computers(backend_from, backend, batch_size, filter_size)
            if include_authinfos:
                _import_authinfos(
                    backend_from,
                    backend,
                    batch_size,
                    user_ids_archive_backend,
                    computer_ids_archive_backend,
                )
            node_ids_archive_backend = _import_nodes(
                backend_from,
                backend,
                batch_size,
                filter_size,
                user_ids_archive_backend,
                computer_ids_archive_backend,
                import_new_extras,
                merge_extras,
            )
            _import_logs(backend_from, backend, batch_size, filter_size, node_ids_archive_backend)
            _import_comments(
                backend_from,
                backend,
                batch_size,
                filter_size,
                user_ids_archive_backend,
                node_ids_archive_backend,
                merge_comments,
            )
            _import_links(backend_from, backend, batch_size, node_ids_archive_backend)
            group_labels = _import_groups(
                backend_from, backend, batch_size, filter_size, user_ids_archive_backend, node_ids_archive_backend
            )
            import_group_id = None
            if create_group:
                import_group_id = _make_import_group(group, group_labels, node_ids_archive_backend, backend, batch_size)
            new_repo_keys = _get_new_object_keys(
                archive_format.key_format,
                backend_from,
                backend,
                batch_size,
            )

            if test_run:
                # exit before we write anything to the database or repository
                raise ImportTestRun('test run complete')

            # now the transaction has been successfully populated, but not committed, we add the repository files
            # if the commit fails, this is not so much an issue, since the files can be removed on repo maintenance
            _add_files_to_repo(backend_from, backend, new_repo_keys)

            IMPORT_LOGGER.report('Committing transaction to database...')

    return import_group_id


def _add_new_entities(
    etype: EntityTypes,
    total: int,
    unique_field: str,
    backend_unique_id: dict,
    backend_from: StorageBackend,
    backend_to: StorageBackend,
    batch_size: int,
    filter_size: int,
    transform: Callable[[dict], dict],
) -> None:
    """Add new entities to the output backend and update the mapping of unique field -> id."""
    IMPORT_LOGGER.report(f'Adding {total} new {etype.value}(s)')

    # collect the unique entities from the input backend to be added to the output backend
    ufields = []
    query = QueryBuilder(backend=backend_from).append(entity_type_to_orm[etype], project=unique_field)
    for (ufield,) in query.distinct().iterall(batch_size=batch_size):
        if ufield not in backend_unique_id:
            ufields.append(ufield)

    with get_progress_reporter()(desc=f'Adding new {etype.value}(s)', total=total) as progress:
        # batch the filtering of rows by filter size, to limit the number of query variables used in any one query,
        # since certain backends have a limit on the number of variables in a query (such as SQLITE_MAX_VARIABLE_NUMBER)
        for nrows, ufields_batch in batch_iter(ufields, filter_size):
            rows = [
                transform(row)
                for row in QueryBuilder(backend=backend_from)
                .append(
                    entity_type_to_orm[etype],
                    filters={unique_field: {'in': ufields_batch}},
                    project=['**'],
                    tag='entity',
                )
                .dict(batch_size=batch_size)
            ]
            new_ids = backend_to.bulk_insert(etype, rows)
            backend_unique_id.update({row[unique_field]: pk for pk, row in zip(new_ids, rows)})
            progress.update(nrows)


def _import_users(
    backend_from: StorageBackend, backend_to: StorageBackend, batch_size: int, filter_size: int
) -> Dict[int, int]:
    """Import users from one backend to another.

    :returns: mapping of input backend id to output backend id
    """
    # get the records from the input backend
    qbuilder = QueryBuilder(backend=backend_from)
    input_id_email = dict(qbuilder.append(orm.User, project=['id', 'email']).all(batch_size=batch_size))

    # get matching emails from the backend
    output_email_id: Dict[str, int] = {}
    if input_id_email:
        output_email_id = {
            key: value
            for query_results in [
                dict(
                    orm.QueryBuilder(backend=backend_to)
                    .append(orm.User, filters={'email': {'in': chunk}}, project=['email', 'id'])
                    .all(batch_size=batch_size)
                )
                for _, chunk in batch_iter(set(input_id_email.values()), filter_size)
            ]
            for key, value in query_results.items()
        }

    new_users = len(input_id_email) - len(output_email_id)
    existing_users = len(output_email_id)

    if existing_users:
        IMPORT_LOGGER.report(f'Skipping {existing_users} existing User(s)')
    if new_users:
        # add new users and update output_email_id with their email -> id mapping
        def transform(row):
            return {k: v for k, v in row['entity'].items() if k != 'id'}

        _add_new_entities(
            EntityTypes.USER,
            new_users,
            'email',
            output_email_id,
            backend_from,
            backend_to,
            batch_size,
            filter_size,
            transform,
        )

    # generate mapping of input backend id to output backend id
    return {int(i): output_email_id[email] for i, email in input_id_email.items()}


def _import_computers(
    backend_from: StorageBackend, backend_to: StorageBackend, batch_size: int, filter_size: int
) -> Dict[int, int]:
    """Import computers from one backend to another.

    :returns: mapping of input backend id to output backend id
    """
    # get the records from the input backend
    qbuilder = QueryBuilder(backend=backend_from)
    input_id_uuid = dict(qbuilder.append(orm.Computer, project=['id', 'uuid']).all(batch_size=batch_size))

    # get matching uuids from the backend
    backend_uuid_id: Dict[str, int] = {}
    if input_id_uuid:
        backend_uuid_id = {
            key: value
            for query_results in [
                dict(
                    orm.QueryBuilder(backend=backend_to)
                    .append(orm.Computer, filters={'uuid': {'in': chunk}}, project=['uuid', 'id'])
                    .all(batch_size=batch_size)
                )
                for _, chunk in batch_iter(set(input_id_uuid.values()), filter_size)
            ]
            for key, value in query_results.items()
        }

    new_computers = len(input_id_uuid) - len(backend_uuid_id)
    existing_computers = len(backend_uuid_id)

    if existing_computers:
        IMPORT_LOGGER.report(f'Skipping {existing_computers} existing Computer(s)')
    if new_computers:
        # add new computers and update backend_uuid_id with their uuid -> id mapping

        # Labels should be unique, so we create new labels on clashes
        labels = {
            label
            for (label,) in orm.QueryBuilder(backend=backend_to)
            .append(orm.Computer, project='label')
            .iterall(batch_size=batch_size)
        }
        relabelled = 0

        def transform(row: dict) -> dict:
            data = row['entity']
            pk = data.pop('id')
            nonlocal labels
            if data['label'] in labels:
                for i in range(DUPLICATE_LABEL_MAX):
                    new_label = DUPLICATE_LABEL_TEMPLATE.format(data['label'], i)
                    if new_label not in labels:
                        data['label'] = new_label
                        break
                else:
                    raise ImportUniquenessError(
                        f'Archive Computer {pk} has existing label {data["label"]!r} and re-labelling failed'
                    )
                nonlocal relabelled
                relabelled += 1
            labels.add(data['label'])
            return data

        _add_new_entities(
            EntityTypes.COMPUTER,
            new_computers,
            'uuid',
            backend_uuid_id,
            backend_from,
            backend_to,
            batch_size,
            filter_size,
            transform,
        )

        if relabelled:
            IMPORT_LOGGER.report(f'Re-labelled {relabelled} new Computer(s)')

    # generate mapping of input backend id to output backend id
    return {int(i): backend_uuid_id[uuid] for i, uuid in input_id_uuid.items()}


def _import_authinfos(
    backend_from: StorageBackend,
    backend_to: StorageBackend,
    batch_size: int,
    user_ids_archive_backend: Dict[int, int],
    computer_ids_archive_backend: Dict[int, int],
) -> None:
    """Import logs from one backend to another.

    :returns: mapping of input backend id to output backend id
    """
    # get the records from the input backend
    qbuilder = QueryBuilder(backend=backend_from)
    input_id_user_comp = qbuilder.append(
        orm.AuthInfo,
        project=['id', 'aiidauser_id', 'dbcomputer_id'],
    ).all(batch_size=batch_size)

    # translate user_id / computer_id, from -> to
    try:
        to_user_id_comp_id = [
            (user_ids_archive_backend[_user_id], computer_ids_archive_backend[_comp_id])
            for _, _user_id, _comp_id in input_id_user_comp
        ]
    except KeyError as exception:
        raise ImportValidationError(f'Archive AuthInfo has unknown User/Computer: {exception}')

    # retrieve existing user_id / computer_id
    backend_id_user_comp = []
    if to_user_id_comp_id:
        qbuilder = orm.QueryBuilder(backend=backend_to)
        qbuilder.append(
            orm.AuthInfo,
            filters={
                'aiidauser_id': {'in': [_user_id for _user_id, _ in to_user_id_comp_id]},
                'dbcomputer_id': {'in': [_comp_id for _, _comp_id in to_user_id_comp_id]},
            },
            project=['id', 'aiidauser_id', 'dbcomputer_id'],
        )
        backend_id_user_comp = [
            (user_id, comp_id)
            for _, user_id, comp_id in qbuilder.all(batch_size=batch_size)
            if (user_id, comp_id) in to_user_id_comp_id
        ]

    new_authinfos = len(input_id_user_comp) - len(backend_id_user_comp)
    existing_authinfos = len(backend_id_user_comp)

    if existing_authinfos:
        IMPORT_LOGGER.report(f'Skipping {existing_authinfos} existing AuthInfo(s)')
    if not new_authinfos:
        return

    # import new authinfos
    IMPORT_LOGGER.report(f'Adding {new_authinfos} new {EntityTypes.AUTHINFO.value}(s)')
    new_ids = [
        _id
        for _id, _user_id, _comp_id in input_id_user_comp
        if (user_ids_archive_backend[_user_id], computer_ids_archive_backend[_comp_id]) not in backend_id_user_comp
    ]
    qbuilder = QueryBuilder(backend=backend_from).append(
        orm.AuthInfo, filters={'id': {'in': new_ids}}, project=['**'], tag='entity'
    )
    iterator = qbuilder.iterdict()

    def transform(row: dict) -> dict:
        data = row['entity']
        data.pop('id')
        data['aiidauser_id'] = user_ids_archive_backend[data['aiidauser_id']]
        data['dbcomputer_id'] = computer_ids_archive_backend[data['dbcomputer_id']]
        return data

    with get_progress_reporter()(
        desc=f'Adding new {EntityTypes.AUTHINFO.value}(s)', total=qbuilder.count()
    ) as progress:
        for nrows, rows in batch_iter(iterator, batch_size, transform):
            backend_to.bulk_insert(EntityTypes.AUTHINFO, rows)
            progress.update(nrows)


def _import_nodes(
    backend_from: StorageBackend,
    backend_to: StorageBackend,
    batch_size: int,
    filter_size: int,
    user_ids_archive_backend: Dict[int, int],
    computer_ids_archive_backend: Dict[int, int],
    import_new_extras: bool,
    merge_extras: MergeExtrasType,
) -> Dict[int, int]:
    """Import nodes from one backend to another.

    :returns: mapping of input backend id to output backend id
    """
    IMPORT_LOGGER.report('Collecting Node(s) ...')
    # get the records from the input backend
    qbuilder = QueryBuilder(backend=backend_from)
    input_id_uuid = dict(qbuilder.append(orm.Node, project=['id', 'uuid']).all(batch_size=batch_size))

    # get matching uuids from the backend
    backend_uuid_id: Dict[str, int] = {}

    if input_id_uuid:
        backend_uuid_id = {
            key: value
            for query_results in [
                dict(
                    orm.QueryBuilder(backend=backend_to)
                    .append(orm.Node, filters={'uuid': {'in': chunk}}, project=['uuid', 'id'])
                    .all(batch_size=batch_size)
                )
                for _, chunk in batch_iter(set(input_id_uuid.values()), filter_size)
            ]
            for key, value in query_results.items()
        }

    new_nodes = len(input_id_uuid) - len(backend_uuid_id)

    if backend_uuid_id:
        _merge_node_extras(backend_from, backend_to, batch_size, backend_uuid_id, merge_extras)

    if new_nodes:
        # add new nodes and update backend_uuid_id with their uuid -> id mapping
        transform = NodeTransform(user_ids_archive_backend, computer_ids_archive_backend, import_new_extras)
        _add_new_entities(
            EntityTypes.NODE,
            new_nodes,
            'uuid',
            backend_uuid_id,
            backend_from,
            backend_to,
            batch_size,
            filter_size,
            transform,
        )

    # generate mapping of input backend id to output backend id
    return {int(i): backend_uuid_id[uuid] for i, uuid in input_id_uuid.items()}


class NodeTransform:
    """Callable to transform a Node DB row, between the source archive and target backend."""

    def __init__(
        self,
        user_ids_archive_backend: Dict[int, int],
        computer_ids_archive_backend: Dict[int, int],
        import_new_extras: bool,
    ):
        """Construct a new instance."""
        self.user_ids_archive_backend = user_ids_archive_backend
        self.computer_ids_archive_backend = computer_ids_archive_backend
        self.import_new_extras = import_new_extras

    def __call__(self, row: dict) -> dict:
        """Perform the transform."""
        data = row['entity']
        pk = data.pop('id')
        try:
            data['user_id'] = self.user_ids_archive_backend[data['user_id']]
        except KeyError as exc:
            raise ImportValidationError(f'Archive Node {pk} has unknown User: {exc}')
        if data['dbcomputer_id'] is not None:
            try:
                data['dbcomputer_id'] = self.computer_ids_archive_backend[data['dbcomputer_id']]
            except KeyError as exc:
                raise ImportValidationError(f'Archive Node {pk} has unknown Computer: {exc}')
        if self.import_new_extras:
            # Remove node hashing and other aiida "private" extras
            data['extras'] = {k: v for k, v in data['extras'].items() if not k.startswith('_aiida_')}
            if data.get('node_type', '').endswith('code.Code.'):
                data['extras'].pop('hidden', None)
        else:
            data['extras'] = {}
        if data.get('node_type', '').startswith('process.'):
            # remove checkpoint from attributes of process nodes
            data['attributes'].pop(orm.ProcessNode.CHECKPOINT_KEY, None)
        return data


def _import_logs(
    backend_from: StorageBackend,
    backend_to: StorageBackend,
    batch_size: int,
    filter_size: int,
    node_ids_archive_backend: Dict[int, int],
) -> Dict[int, int]:
    """Import logs from one backend to another.

    :returns: mapping of input backend id to output backend id
    """
    # get the records from the input backend
    qbuilder = QueryBuilder(backend=backend_from)
    input_id_uuid = dict(qbuilder.append(orm.Log, project=['id', 'uuid']).all(batch_size=batch_size))

    # get matching uuids from the backend
    backend_uuid_id: Dict[str, int] = {}

    if input_id_uuid:
        backend_uuid_id = {
            key: value
            for query_results in [
                dict(
                    orm.QueryBuilder(backend=backend_to)
                    .append(orm.Log, filters={'uuid': {'in': chunk}}, project=['uuid', 'id'])
                    .all(batch_size=batch_size)
                )
                for _, chunk in batch_iter(set(input_id_uuid.values()), filter_size)
            ]
            for key, value in query_results.items()
        }

    new_logs = len(input_id_uuid) - len(backend_uuid_id)
    existing_logs = len(backend_uuid_id)

    if existing_logs:
        IMPORT_LOGGER.report(f'Skipping {existing_logs} existing Log(s)')
    if new_logs:
        # add new logs and update backend_uuid_id with their uuid -> id mapping
        def transform(row: dict) -> dict:
            data = row['entity']
            pk = data.pop('id')
            try:
                data['dbnode_id'] = node_ids_archive_backend[data['dbnode_id']]
            except KeyError as exc:
                raise ImportValidationError(f'Archive Log {pk} has unknown Node: {exc}')
            return data

        _add_new_entities(
            EntityTypes.LOG,
            new_logs,
            'uuid',
            backend_uuid_id,
            backend_from,
            backend_to,
            batch_size,
            filter_size,
            transform,
        )

    # generate mapping of input backend id to output backend id
    return {int(i): backend_uuid_id[uuid] for i, uuid in input_id_uuid.items()}


def _merge_node_extras(
    backend_from: StorageBackend,
    backend_to: StorageBackend,
    batch_size: int,
    backend_uuid_id: Dict[str, int],
    mode: MergeExtrasType,
) -> None:
    """Merge extras from the input backend with the ones in the output backend.

    :param backend_uuid_id: mapping of uuid to output backend id
    :param mode: tuple of merge modes for extras
    """
    num_existing = len(backend_uuid_id)

    if mode == ('k', 'n', 'l'):
        # 'none': keep old extras, do not add imported ones
        IMPORT_LOGGER.report(f'Skipping {num_existing} existing Node(s)')
        return

    input_extras = (
        QueryBuilder(backend=backend_from)
        .append(
            orm.Node, tag='node', filters={'uuid': {'in': list(backend_uuid_id.keys())}}, project=['uuid', 'extras']
        )
        .order_by([{'node': 'uuid'}])
    )

    if mode == ('n', 'c', 'u'):
        # 'mirror' operation: remove old extras, put only the new ones
        IMPORT_LOGGER.report(f'Replacing {num_existing} existing Node extras')

        def transform(row):
            return {'id': backend_uuid_id[row[0]], 'extras': row[1]}

        with get_progress_reporter()(desc='Replacing extras', total=input_extras.count()) as progress:
            for nrows, rows in batch_iter(input_extras.iterall(batch_size=batch_size), batch_size, transform):
                backend_to.bulk_update(EntityTypes.NODE, rows)
                progress.update(nrows)
        return

    # run (slower) generic merge operation
    backend_extras = (
        QueryBuilder(backend=backend_to)
        .append(
            orm.Node, tag='node', filters={'uuid': {'in': list(backend_uuid_id.keys())}}, project=['uuid', 'extras']
        )
        .order_by([{'node': 'uuid'}])
    )

    IMPORT_LOGGER.report(f'Merging {num_existing} existing Node extras')

    if not input_extras.count() == backend_extras.count():
        raise ImportValidationError(
            f'Number of Nodes in archive ({input_extras.count()}) and backend ({backend_extras.count()}) do not match'
        )

    def _transform(data: tuple[Any, Any]) -> dict:
        """Transform the new and existing extras into a dict that can be passed to bulk_update."""
        new_uuid, new_extras = data[0]
        old_uuid, old_extras = data[1]
        if new_uuid != old_uuid:
            raise ImportValidationError(f'UUID mismatch when merging node extras: {new_uuid} != {old_uuid}')
        backend_id = backend_uuid_id[new_uuid]
        old_keys = set(old_extras.keys())
        new_keys = set(new_extras.keys())
        collided_keys = old_keys.intersection(new_keys)
        old_keys_only = old_keys.difference(collided_keys)
        new_keys_only = new_keys.difference(collided_keys)

        final_extras = {}

        if mode == ('k', 'c', 'u'):
            # 'update_existing' operation: if an extra already exists,
            # overwrite its new value with a new one
            final_extras = new_extras
            for key in old_keys_only:
                final_extras[key] = old_extras[key]
            return {'id': backend_id, 'extras': final_extras}

        if mode == ('k', 'c', 'l'):
            # 'keep_existing': if an extra already exists, keep its original value
            final_extras = old_extras
            for key in new_keys_only:
                final_extras[key] = new_extras[key]
            return {'id': backend_id, 'extras': final_extras}

        if mode[0] == 'k':
            for key in old_keys_only:
                final_extras[key] = old_extras[key]
        elif mode[0] != 'n':
            raise ImportValidationError(
                f"Unknown first letter of the update extras mode: '{mode}'. Should be either 'k' or 'n'"
            )
        if mode[1] == 'c':
            for key in new_keys_only:
                final_extras[key] = new_extras[key]
        elif mode[1] != 'n':
            raise ImportValidationError(
                f"Unknown second letter of the update extras mode: '{mode}'. Should be either 'c' or 'n'"
            )
        if mode[2] == 'u':
            for key in collided_keys:
                final_extras[key] = new_extras[key]
        elif mode[2] == 'l':
            for key in collided_keys:
                final_extras[key] = old_extras[key]
        elif mode[2] != 'd':
            raise ImportValidationError(
                f"Unknown third letter of the update extras mode: '{mode}'. Should be one of 'u'/'l'/'a'/'d'"
            )
        return {'id': backend_id, 'extras': final_extras}

    with get_progress_reporter()(desc='Merging extras', total=input_extras.count()) as progress:
        for nrows, rows in batch_iter(
            zip(
                input_extras.iterall(batch_size=batch_size),
                backend_extras.iterall(batch_size=batch_size),
            ),
            batch_size,
            _transform,
        ):
            backend_to.bulk_update(EntityTypes.NODE, rows)
            progress.update(nrows)


class CommentTransform:
    """Callable to transform a Comment DB row, between the source archive and target backend."""

    def __init__(
        self,
        user_ids_archive_backend: Dict[int, int],
        node_ids_archive_backend: Dict[int, int],
    ):
        """Construct a new instance."""
        self.user_ids_archive_backend = user_ids_archive_backend
        self.node_ids_archive_backend = node_ids_archive_backend

    def __call__(self, row: dict) -> dict:
        """Perform the transform."""
        data = row['entity']
        pk = data.pop('id')
        try:
            data['user_id'] = self.user_ids_archive_backend[data['user_id']]
        except KeyError as exc:
            raise ImportValidationError(f'Archive Comment {pk} has unknown User: {exc}')
        try:
            data['dbnode_id'] = self.node_ids_archive_backend[data['dbnode_id']]
        except KeyError as exc:
            raise ImportValidationError(f'Archive Comment {pk} has unknown Node: {exc}')
        return data


def _import_comments(
    backend_from: StorageBackend,
    backend: StorageBackend,
    batch_size: int,
    filter_size: int,
    user_ids_archive_backend: Dict[int, int],
    node_ids_archive_backend: Dict[int, int],
    merge_comments: MergeCommentsType,
) -> Dict[int, int]:
    """Import comments from one backend to another.

    :returns: mapping of archive id to backend id
    """
    # get the records from the input backend
    qbuilder = QueryBuilder(backend=backend_from)
    input_id_uuid = dict(qbuilder.append(orm.Comment, project=['id', 'uuid']).all(batch_size=batch_size))

    # get matching uuids from the backend
    backend_uuid_id: Dict[str, int] = {}
    if input_id_uuid:
        backend_uuid_id = dict(
            orm.QueryBuilder(backend=backend)
            .append(orm.Comment, filters={'uuid': {'in': list(input_id_uuid.values())}}, project=['uuid', 'id'])
            .all(batch_size=batch_size)
        )

    new_comments = len(input_id_uuid) - len(backend_uuid_id)
    existing_comments = len(backend_uuid_id)

    archive_comments = QueryBuilder(backend=backend_from).append(
        orm.Comment, filters={'uuid': {'in': list(backend_uuid_id.keys())}}, project=['uuid', 'mtime', 'content']
    )

    if existing_comments:
        if merge_comments == 'leave':
            IMPORT_LOGGER.report(f'Skipping {existing_comments} existing Comment(s)')
        elif merge_comments == 'overwrite':
            IMPORT_LOGGER.report(f'Overwriting {existing_comments} existing Comment(s)')

            def _transform(row):
                data = {'id': backend_uuid_id[row[0]], 'mtime': row[1], 'content': row[2]}
                return data

            with get_progress_reporter()(desc='Overwriting comments', total=archive_comments.count()) as progress:
                for nrows, rows in batch_iter(archive_comments.iterall(batch_size=batch_size), batch_size, _transform):
                    backend.bulk_update(EntityTypes.COMMENT, rows)
                    progress.update(nrows)

        elif merge_comments == 'newest':
            IMPORT_LOGGER.report(f'Updating {existing_comments} existing Comment(s)')

            def _transform(row):
                # to-do this is probably not the most efficient way to do this
                uuid, new_mtime, new_comment = row
                cmt = orm.comments.CommentCollection(orm.Comment, backend).get(uuid=uuid)
                if cmt.mtime < new_mtime:
                    cmt.set_mtime(new_mtime)
                    cmt.set_content(new_comment)

            with get_progress_reporter()(desc='Updating comments', total=archive_comments.count()) as progress:
                for nrows, rows in batch_iter(archive_comments.iterall(batch_size=batch_size), batch_size, _transform):
                    progress.update(nrows)

        else:
            raise ImportValidationError(f'Unknown merge_comments value: {merge_comments}.')
    if new_comments:
        # add new comments and update backend_uuid_id with their uuid -> id mapping
        _add_new_entities(
            EntityTypes.COMMENT,
            new_comments,
            'uuid',
            backend_uuid_id,
            backend_from,
            backend,
            batch_size,
            filter_size,
            CommentTransform(user_ids_archive_backend, node_ids_archive_backend),
        )

    # generate mapping of input backend id to output backend id
    return {int(i): backend_uuid_id[uuid] for i, uuid in input_id_uuid.items()}


def _import_links(
    backend_from: StorageBackend,
    backend_to: StorageBackend,
    batch_size: int,
    node_ids_archive_backend: Dict[int, int],
) -> None:
    """Import links from one backend to another."""
    # initial variables
    calculation_node_types = 'process.calculation.'
    workflow_node_types = 'process.workflow.'
    data_node_types = 'data.'
    allowed_link_nodes = {
        LinkType.CALL_CALC: (workflow_node_types, calculation_node_types),
        LinkType.CALL_WORK: (workflow_node_types, workflow_node_types),
        LinkType.CREATE: (calculation_node_types, data_node_types),
        LinkType.INPUT_CALC: (data_node_types, calculation_node_types),
        LinkType.INPUT_WORK: (data_node_types, workflow_node_types),
        LinkType.RETURN: (workflow_node_types, data_node_types),
    }
    link_type_uniqueness = {
        LinkType.CALL_CALC: ('out_id',),
        LinkType.CALL_WORK: ('out_id',),
        LinkType.CREATE: (
            'in_id_label',
            'out_id',
        ),
        LinkType.INPUT_CALC: ('out_id_label',),
        LinkType.INPUT_WORK: ('out_id_label',),
        LinkType.RETURN: ('in_id_label',),
    }

    # Batch by type, to reduce memory load
    # to-do check no extra types in archive?
    for link_type in LinkType:
        # get validation parameters
        allowed_in_type, allowed_out_type = allowed_link_nodes[link_type]
        link_uniqueness = link_type_uniqueness[link_type]

        # count links of this type in archive
        archive_query = (
            QueryBuilder(backend=backend_from)
            .append(orm.Node, tag='incoming', project=['id', 'node_type'])
            .append(
                orm.Node,
                with_incoming='incoming',
                project=['id', 'node_type'],
                edge_filters={'type': link_type.value},
                edge_project=['id', 'label'],
            )
        )
        total = archive_query.count()

        if not total:
            continue  # nothing to add

        # get existing links set, to check existing
        IMPORT_LOGGER.report(f'Gathering existing {link_type.value!r} Link(s)')
        existing_links = {
            tuple(link)
            for link in orm.QueryBuilder(backend=backend_to)
            .append(entity_type='link', filters={'type': link_type.value}, project=['input_id', 'output_id', 'label'])
            .iterall(batch_size=batch_size)
        }
        # create additional validators
        # note, we only populate them when required, to reduce memory usage
        existing_in_id_label = (
            {(link[0], link[2]) for link in existing_links} if 'in_id_label' in link_uniqueness else set()
        )
        existing_out_id = {link[1] for link in existing_links} if 'out_id' in link_uniqueness else set()
        existing_out_id_label = (
            {(link[1], link[2]) for link in existing_links} if 'out_id_label' in link_uniqueness else set()
        )

        # loop through archive links; validate and add new
        new_count = existing_count = 0
        insert_rows = []
        with get_progress_reporter()(desc=f'Processing {link_type.value!r} Link(s)', total=total) as progress:
            for in_id, in_type, out_id, out_type, link_id, link_label in archive_query.iterall(batch_size=batch_size):
                progress.update()

                # convert ids: archive -> profile
                try:
                    in_id = node_ids_archive_backend[in_id]  # noqa: PLW2901
                except KeyError as exc:
                    raise ImportValidationError(f'Archive Link {link_id} has unknown input Node: {exc}')
                try:
                    out_id = node_ids_archive_backend[out_id]  # noqa: PLW2901
                except KeyError as exc:
                    raise ImportValidationError(f'Archive Link {link_id} has unknown output Node: {exc}')

                # skip existing links
                if (in_id, out_id, link_label) in existing_links:
                    existing_count += 1
                    continue

                # validation
                if in_id == out_id:
                    raise ImportValidationError(f'Cannot add a link to oneself: {in_id}')
                if not in_type.startswith(allowed_in_type):
                    raise ImportValidationError(
                        f'Cannot add a {link_type.value!r} link from {in_type} (link {link_id})'
                    )
                if not out_type.startswith(allowed_out_type):
                    raise ImportValidationError(f'Cannot add a {link_type.value!r} link to {out_type} (link {link_id})')
                if 'in_id_label' in link_uniqueness and (in_id, link_label) in existing_in_id_label:
                    raise ImportUniquenessError(
                        f'Node {in_id} already has an outgoing {link_type.value!r} link with label {link_label!r}'
                    )
                if 'out_id' in link_uniqueness and out_id in existing_out_id:
                    raise ImportUniquenessError(f'Node {out_id} already has an incoming {link_type.value!r} link')
                if 'out_id_label' in link_uniqueness and (out_id, link_label) in existing_out_id_label:
                    raise ImportUniquenessError(
                        f'Node {out_id} already has an incoming {link_type.value!r} link with label {link_label!r}'
                    )

                # update variables
                new_count += 1
                insert_rows.append(
                    {
                        'input_id': in_id,
                        'output_id': out_id,
                        'type': link_type.value,
                        'label': link_label,
                    }
                )
                existing_links.add((in_id, out_id, link_label))
                existing_in_id_label.add((in_id, link_label))
                existing_out_id.add(out_id)
                existing_out_id_label.add((out_id, link_label))

                # flush new rows, once batch size is reached
                if (new_count % batch_size) == 0:
                    backend_to.bulk_insert(EntityTypes.LINK, insert_rows)
                    insert_rows = []

            # flush remaining new rows
            if insert_rows:
                backend_to.bulk_insert(EntityTypes.LINK, insert_rows)

        # report counts
        if existing_count:
            IMPORT_LOGGER.report(f'Skipped {existing_count} existing {link_type.value!r} Link(s)')
        if new_count:
            IMPORT_LOGGER.report(f'Added {new_count} new {link_type.value!r} Link(s)')


class GroupTransform:
    """Callable to transform a Group DB row, between the source archive and target backend."""

    def __init__(self, user_ids_archive_backend: Dict[int, int], labels: Set[str]):
        self.user_ids_archive_backend = user_ids_archive_backend
        self.labels = labels
        self.relabelled = 0

    def __call__(self, row: dict) -> dict:
        """Perform the transform."""
        data = row['entity']
        pk = data.pop('id')
        try:
            data['user_id'] = self.user_ids_archive_backend[data['user_id']]
        except KeyError as exc:
            raise ImportValidationError(f'Archive Group {pk} has unknown User: {exc}')
        # Labels should be unique, so we create new labels on clashes
        if data['label'] in self.labels:
            for i in range(DUPLICATE_LABEL_MAX):
                new_label = DUPLICATE_LABEL_TEMPLATE.format(data['label'], i)
                if new_label not in self.labels:
                    data['label'] = new_label
                    break
            else:
                raise ImportUniquenessError(
                    f'Archive Group {pk} has existing label {data["label"]!r} and re-labelling failed'
                )
            self.relabelled += 1
        self.labels.add(data['label'])
        return data


def _import_groups(
    backend_from: StorageBackend,
    backend_to: StorageBackend,
    batch_size: int,
    filter_size: int,
    user_ids_archive_backend: Dict[int, int],
    node_ids_archive_backend: Dict[int, int],
) -> Set[str]:
    """Import groups from the input backend, and add group -> node records.

    :returns: Set of labels
    """
    # get the records from the input backend
    qbuilder = QueryBuilder(backend=backend_from)
    input_id_uuid = dict(qbuilder.append(orm.Group, project=['id', 'uuid']).all(batch_size=batch_size))

    # get matching uuids from the backend
    backend_uuid_id: Dict[str, int] = {}
    if input_id_uuid:
        backend_uuid_id = dict(
            orm.QueryBuilder(backend=backend_to)
            .append(orm.Group, filters={'uuid': {'in': list(input_id_uuid.values())}}, project=['uuid', 'id'])
            .all(batch_size=batch_size)
        )

    # get all labels
    labels = {
        label
        for (label,) in orm.QueryBuilder(backend=backend_to)
        .append(orm.Group, project='label')
        .iterall(batch_size=batch_size)
    }

    new_groups = len(input_id_uuid) - len(backend_uuid_id)
    new_uuids = set(input_id_uuid.values()).difference(backend_uuid_id.keys())
    existing_groups = len(backend_uuid_id)

    if existing_groups:
        IMPORT_LOGGER.report(f'Skipping {existing_groups} existing Group(s)')
    if new_groups:
        # add new groups and update backend_uuid_id with their uuid -> id mapping

        transform = GroupTransform(user_ids_archive_backend, labels)

        _add_new_entities(
            EntityTypes.GROUP,
            new_groups,
            'uuid',
            backend_uuid_id,
            backend_from,
            backend_to,
            batch_size,
            filter_size,
            transform,
        )

        if transform.relabelled:
            IMPORT_LOGGER.report(f'Re-labelled {transform.relabelled} new Group(s)')

        # generate mapping of input backend id to output backend id
        group_id_archive_backend = {i: backend_uuid_id[uuid] for i, uuid in input_id_uuid.items()}
        # Add nodes to new groups
        iterator = (
            QueryBuilder(backend=backend_from)
            .append(orm.Group, project='id', filters={'uuid': {'in': new_uuids}}, tag='group')
            .append(orm.Node, project='id', with_group='group')
        )
        total = iterator.count()
        if total:
            IMPORT_LOGGER.report(f'Adding {total} Node(s) to new Group(s)')

            def group_node_transform(row):
                group_id = group_id_archive_backend[row[0]]
                try:
                    node_id = node_ids_archive_backend[row[1]]
                except KeyError as exc:
                    raise ImportValidationError(f'Archive Group {group_id} has unknown Node: {exc}')
                return {'dbgroup_id': group_id, 'dbnode_id': node_id}

            with get_progress_reporter()(desc=f'Adding new {EntityTypes.GROUP_NODE.value}(s)', total=total) as progress:
                for nrows, rows in batch_iter(
                    iterator.iterall(batch_size=batch_size), batch_size, group_node_transform
                ):
                    backend_to.bulk_insert(EntityTypes.GROUP_NODE, rows)
                    progress.update(nrows)

    return labels


def _make_import_group(
    group: Optional[orm.Group],
    labels: Set[str],
    node_ids_archive_backend: Dict[int, int],
    backend_to: StorageBackend,
    batch_size: int,
) -> Optional[int]:
    """Make an import group containing all imported nodes.

    :param group: Use an existing group
    :param labels: All existing group labels on the backend
    :param node_ids_archive_backend: node pks to add to the group

    :returns: The id of the group

    """
    # Do not create an empty group
    if not node_ids_archive_backend:
        IMPORT_LOGGER.debug('No nodes to import, so no import group created')
        return None

    # Get the Group id
    if group is None:
        # Get an unique name for the import group, based on the current (local) time
        label = timezone.localtime(timezone.now()).strftime('%Y%m%d-%H%M%S')
        if label in labels:
            for i in range(DUPLICATE_LABEL_MAX):
                new_label = DUPLICATE_LABEL_TEMPLATE.format(label, i)
                if new_label not in labels:
                    label = new_label
                    break
            else:
                raise ImportUniquenessError(f'New import Group has existing label {label!r} and re-labelling failed')
        dummy_orm = orm.ImportGroup(label, backend=backend_to)
        row = {
            'label': label,
            'description': 'Group generated by archive import',
            'type_string': dummy_orm.type_string,
            'user_id': dummy_orm.user.pk,
        }
        (group_id,) = backend_to.bulk_insert(EntityTypes.GROUP, [row], allow_defaults=True)
        IMPORT_LOGGER.report(f'Created new import Group: PK={group_id}, label={label}')
        group_node_ids = set()
    else:
        group_id = group.pk  # type: ignore[assignment]
        IMPORT_LOGGER.report(f'Using existing import Group: PK={group_id}, label={group.label}')
        group_node_ids = {
            pk
            for (pk,) in orm.QueryBuilder(backend=backend_to)
            .append(orm.Group, filters={'id': group_id}, tag='group')
            .append(orm.Node, with_group='group', project='id')
            .iterall(batch_size=batch_size)
        }

    # Add all the nodes to the Group
    with get_progress_reporter()(
        desc='Adding all Node(s) to the import Group', total=len(node_ids_archive_backend)
    ) as progress:
        iterator = (
            {'dbgroup_id': group_id, 'dbnode_id': node_id}
            for node_id in node_ids_archive_backend.values()
            if node_id not in group_node_ids
        )
        for nrows, rows in batch_iter(iterator, batch_size):
            backend_to.bulk_insert(EntityTypes.GROUP_NODE, rows)
            progress.update(nrows)

    return group_id


def _get_new_object_keys(
    key_format: str,
    backend_from: StorageBackend,
    backend_to: StorageBackend,
    batch_size: int,
) -> Set[str]:
    """Return the object keys that need to be added to the backend."""
    archive_hashkeys: Set[str] = set()
    query = QueryBuilder(backend=backend_from).append(orm.Node, project='repository_metadata')
    with get_progress_reporter()(desc='Collecting archive Node file keys', total=query.count()) as progress:
        for (repository_metadata,) in query.iterall(batch_size=batch_size):
            archive_hashkeys.update(key for key in Repository.flatten(repository_metadata).values() if key is not None)
            progress.update()

    IMPORT_LOGGER.report('Checking keys against repository ...')

    repository = backend_to.get_repository()
    if not repository.key_format == key_format:
        raise NotImplementedError(
            f'Backend repository key format incompatible: {repository.key_format!r} != {key_format!r}'
        )
    new_hashkeys = archive_hashkeys.difference(repository.list_objects())

    existing_count = len(archive_hashkeys) - len(new_hashkeys)
    if existing_count:
        IMPORT_LOGGER.report(f'Skipping {existing_count} existing repository files')
    if new_hashkeys:
        IMPORT_LOGGER.report(f'Adding {len(new_hashkeys)} new repository files')

    return new_hashkeys


def _add_files_to_repo(backend_from: StorageBackend, backend_to: StorageBackend, new_keys: Set[str]) -> None:
    """Add the new files to the repository."""
    if not new_keys:
        return None

    repository_to = backend_to.get_repository()
    repository_from = backend_from.get_repository()
    with get_progress_reporter()(desc='Adding archive files to repository', total=len(new_keys)) as progress:
        for key, handle in repository_from.iter_object_streams(new_keys):  # type: ignore[arg-type]
            backend_key = repository_to.put_object_from_filelike(handle)
            if backend_key != key:
                raise ImportValidationError(
                    f'Archive repository key is different to backend key: {key!r} != {backend_key!r}'
                )
            progress.update()
