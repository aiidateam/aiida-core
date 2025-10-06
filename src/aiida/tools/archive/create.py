###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Create an AiiDA archive.

The archive is a subset of the provenance graph,
stored in a single file.
"""

import shutil
import tempfile
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Union

from tabulate import tabulate

from aiida import orm
from aiida.common.datastructures import DEFAULT_BATCH_SIZE, DEFAULT_FILTER_SIZE, QueryParams
from aiida.common.lang import type_check
from aiida.common.links import GraphTraversalRules
from aiida.common.log import AIIDA_LOGGER
from aiida.common.progress_reporter import get_progress_reporter
from aiida.common.utils import batch_iter
from aiida.manage import get_manager
from aiida.orm.entities import EntityTypes
from aiida.orm.implementation import StorageBackend
from aiida.orm.utils.links import LinkQuadruple
from aiida.tools.graph.graph_traversers import get_nodes_export, validate_traversal_rules

from .abstract import ArchiveFormatAbstract, ArchiveWriterAbstract
from .common import entity_type_to_orm
from .exceptions import ArchiveExportError, ExportValidationError
from .implementations.sqlite_zip import ArchiveFormatSqlZip

__all__ = ('EXPORT_LOGGER', 'create_archive')

EXPORT_LOGGER = AIIDA_LOGGER.getChild('export')
QbType = Callable[[], orm.QueryBuilder]


def create_archive(
    entities: Optional[Iterable[Union[orm.Computer, orm.Node, orm.Group, orm.User]]],
    filename: Union[None, str, Path] = None,
    *,
    archive_format: Optional[ArchiveFormatAbstract] = None,
    overwrite: bool = False,
    include_comments: bool = True,
    include_logs: bool = True,
    include_authinfos: bool = False,
    allowed_licenses: Optional[Union[list, Callable]] = None,
    forbidden_licenses: Optional[Union[list, Callable]] = None,
    strip_checkpoints: bool = True,
    batch_size: int = DEFAULT_BATCH_SIZE,
    filter_size: int = DEFAULT_FILTER_SIZE,
    compression: int = 6,
    test_run: bool = False,
    backend: Optional[StorageBackend] = None,
    **traversal_rules: bool,
) -> Path:
    """Export AiiDA data to an archive file.

    The export follows the following logic:

    First gather all entity primary keys (per type) that needs to be exported.
    This need to proceed in the "reverse" order of relationships:

    - groups: input groups
    - group_to_nodes: from nodes in groups
    - nodes & links: from graph_traversal(input nodes & group_to_nodes)
    - computers: from input computers & computers of nodes
    - authinfos: from authinfos of computers
    - comments: from comments of nodes
    - logs: from logs of nodes
    - users: from users of nodes, groups, comments & authinfos

    Now stream the full entities (per type) to the archive writer,
    in the order of relationships:

    - users
    - computers
    - authinfos
    - groups
    - nodes
    - comments
    - logs
    - group_to_nodes
    - links

    Finally stream the repository files,
    for the exported nodes, to the archive writer.

    Note, the logging level and progress reporter should be set externally, for example::

        from aiida.common.progress_reporter import set_progress_bar_tqdm

        EXPORT_LOGGER.setLevel('DEBUG')
        set_progress_bar_tqdm(leave=True)
        create_archive(...)

    :param entities: If ``None``, import all entities,
        or a list of entity instances that can include Computers, Groups, and Nodes.

    :param filename: the filename (possibly including the absolute path)
        of the file on which to export.

    :param overwrite: if True, overwrite the output file without asking, if it exists.
        If False, raise an
        :py:class:`~aiida.tools.archive.exceptions.ArchiveExportError`
        if the output file already exists.

    :param allowed_licenses: List or function.
        If a list, then checks whether all licenses of Data nodes are in the list. If a function,
        then calls function for licenses of Data nodes expecting True if license is allowed, False
        otherwise.

    :param forbidden_licenses: List or function. If a list,
        then checks whether all licenses of Data nodes are in the list. If a function,
        then calls function for licenses of Data nodes expecting True if license is allowed, False
        otherwise.

    :param include_comments: In-/exclude export of comments for given node(s) in ``entities``.
        Default: True, *include* comments in export (as well as relevant users).

    :param include_logs: In-/exclude export of logs for given node(s) in ``entities``.
        Default: True, *include* logs in export.

    :param strip_checkpoints: Remove checkpoint keys from process node attributes.
        These contain serialized code and can cause security issues.

    :param compression: level of compression to use (integer from 0 to 9)

    :param batch_size: batch database query results in sub-collections to reduce memory usage

    :param filter_size: batch database query filters to avoid database parameter limits (e.g., psql-psycopg 65535 limit)

    :param test_run: if True, do not write to file

    :param backend: the backend to export from. If not specified, the default backend is used.

    :param traversal_rules: graph traversal rules. See :const:`aiida.common.links.GraphTraversalRules`
        what rule names are toggleable and what the defaults are.

    :raises `~aiida.tools.archive.exceptions.ArchiveExportError`:
        if there are any internal errors when exporting.
    :raises `~aiida.common.exceptions.LicensingException`:
        if any node is licensed under forbidden license.

    """
    # check the backend
    backend = backend or get_manager().get_profile_storage()
    type_check(backend, StorageBackend)

    # create a function to get a query builder instance for the backend
    def querybuilder():
        return orm.QueryBuilder(backend=backend)

    # check/set archive file path
    type_check(filename, (str, Path), allow_none=True)
    if filename is None:
        filename = Path.cwd() / 'export_data.aiida'
    filename = Path(filename)
    if not overwrite and filename.exists():
        raise ArchiveExportError(f"The output file '{filename}' already exists")
    if filename.exists() and not filename.is_file():
        raise ArchiveExportError(f"The output file '{filename}' exists as a directory")

    if compression not in range(10):
        raise ArchiveExportError('compression must be an integer between 0 and 9')

    # check file format
    archive_format = archive_format or ArchiveFormatSqlZip()
    type_check(archive_format, ArchiveFormatAbstract)

    # check traversal rules
    validate_traversal_rules(GraphTraversalRules.EXPORT, **traversal_rules)
    full_traversal_rules = {
        name: traversal_rules.get(name, rule.default) for name, rule in GraphTraversalRules.EXPORT.value.items()
    }

    initial_summary = get_init_summary(
        archive_version=archive_format.latest_version,
        outfile=filename,
        collect_all=entities is None,
        include_authinfos=include_authinfos,
        include_comments=include_comments,
        include_logs=include_logs,
        traversal_rules=full_traversal_rules,
        compression=compression,
    )
    EXPORT_LOGGER.report(initial_summary)

    # Store starting UUIDs, to write to metadata
    starting_uuids: dict[EntityTypes, set[str]] = {
        EntityTypes.USER: set(),
        EntityTypes.COMPUTER: set(),
        EntityTypes.GROUP: set(),
        EntityTypes.NODE: set(),
    }

    # Store all entity IDs to be written to the archive
    # Note, this is the order they will be written to the archive
    entity_ids: dict[EntityTypes, set[int]] = {
        ent: set()
        for ent in [
            EntityTypes.USER,
            EntityTypes.COMPUTER,
            EntityTypes.AUTHINFO,
            EntityTypes.GROUP,
            EntityTypes.NODE,
            EntityTypes.COMMENT,
            EntityTypes.LOG,
        ]
    }
    query_params = QueryParams(batch_size=batch_size, filter_size=filter_size)

    # extract ids/uuid from initial entities
    type_check(entities, Iterable, allow_none=True)
    if entities is None:
        group_nodes, link_data = _collect_all_entities(
            querybuilder, entity_ids, include_authinfos, include_comments, include_logs, query_params.batch_size
        )
    else:
        for entry in entities:
            if entry.pk is None or entry.uuid is None:
                continue

            if isinstance(entry, orm.Group):
                starting_uuids[EntityTypes.GROUP].add(entry.uuid)
                entity_ids[EntityTypes.GROUP].add(entry.pk)
            elif isinstance(entry, orm.Node):
                starting_uuids[EntityTypes.NODE].add(entry.uuid)
                entity_ids[EntityTypes.NODE].add(entry.pk)
            elif isinstance(entry, orm.Computer):
                starting_uuids[EntityTypes.COMPUTER].add(entry.uuid)
                entity_ids[EntityTypes.COMPUTER].add(entry.pk)
            elif isinstance(entry, orm.User):
                starting_uuids[EntityTypes.USER].add(entry.email)
                entity_ids[EntityTypes.USER].add(entry.pk)
            else:
                raise ArchiveExportError(
                    f'I was given {entry} ({type(entry)}), which is not a User, Node, Computer, or Group instance'
                )
        group_nodes, link_data = _collect_required_entities(
            querybuilder,
            entity_ids,
            traversal_rules,
            include_authinfos,
            include_comments,
            include_logs,
            backend,
            query_params,
        )

    # now all the nodes have been retrieved, perform some checks
    if entity_ids[EntityTypes.NODE]:
        EXPORT_LOGGER.report('Validating Nodes')
        _check_unsealed_nodes(querybuilder, entity_ids[EntityTypes.NODE], batch_size, filter_size)
        _check_node_licenses(
            querybuilder, entity_ids[EntityTypes.NODE], allowed_licenses, forbidden_licenses, batch_size, filter_size
        )

    # get a count of entities, to report
    entity_counts = {etype.value: len(ids) for etype, ids in entity_ids.items()}
    entity_counts[EntityTypes.LINK.value] = len(link_data)
    entity_counts[EntityTypes.GROUP_NODE.value] = len(group_nodes)
    count_summary = [[(name + 's'), num] for name, num in entity_counts.items() if num]

    if test_run:
        EXPORT_LOGGER.report('Test Run: Stopping before archive creation')
        if node_ids := entity_ids[EntityTypes.NODE]:
            # Batch the node IDs to avoid parameter limits in dry run as well
            all_keys = set()
            for _, node_batch_ids in batch_iter(node_ids, filter_size):
                batch_keys = set(
                    orm.Node.get_collection(backend).iter_repo_keys(
                        filters={'id': {'in': node_batch_ids}}, batch_size=batch_size
                    )
                )
                all_keys.update(batch_keys)
            count_summary.append(['Repository Files', len(all_keys)])
        else:
            count_summary.append(['Repository Files', 0])
        EXPORT_LOGGER.report(f'Archive would be created with:\n{tabulate(count_summary)}')
        return filename

    EXPORT_LOGGER.report(f'Creating archive with:\n{tabulate(count_summary)}')

    # Create and open the archive for writing.
    # We create in a temp dir then move to final place at end,
    # so that the user cannot end up with a half written archive on errors
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_filename = Path(tmpdir) / 'export.zip'
        with archive_format.open(tmp_filename, mode='x', compression=compression) as writer:
            # add metadata
            writer.update_metadata(
                {
                    'ctime': datetime.now().isoformat(),
                    'creation_parameters': {
                        'entities_starting_set': None
                        if entities is None
                        else {etype.value: list(unique) for etype, unique in starting_uuids.items() if unique},
                        'include_authinfos': include_authinfos,
                        'include_comments': include_comments,
                        'include_logs': include_logs,
                        'graph_traversal_rules': full_traversal_rules,
                    },
                }
            )
            # stream entity data to the archive
            with get_progress_reporter()(desc='Archiving database: ', total=sum(entity_counts.values())) as progress:
                for etype, ids in entity_ids.items():
                    if etype == EntityTypes.NODE and strip_checkpoints:

                        def transform(row):
                            data = row['entity']
                            if data.get('node_type', '').startswith('process.'):
                                data['attributes'].pop(orm.ProcessNode.CHECKPOINT_KEY, None)
                            return data
                    else:

                        def transform(row):
                            return row['entity']

                    progress.set_description_str(f'Archiving database: {etype.value}s')
                    if ids:
                        # Batch also the IDs to avoid query filter parameter limits
                        for _, batch_ids in batch_iter(ids, filter_size):
                            # Build the query for this batch of IDs
                            query = querybuilder().append(
                                entity_type_to_orm[etype],
                                filters={'id': {'in': batch_ids}},
                                tag='entity',
                                project=['**'],
                            )

                            # Process the query results in batches
                            query_results = query.iterdict(batch_size=batch_size)

                            for nrows, rows in batch_iter(query_results, batch_size, transform):
                                writer.bulk_insert(etype, rows)
                                progress.update(nrows)

                # stream links
                progress.set_description_str(f'Archiving database: {EntityTypes.LINK.value}s')

                def transform(d):
                    return {
                        'input_id': d.source_id,
                        'output_id': d.target_id,
                        'label': d.link_label,
                        'type': d.link_type,
                    }

                for nrows, rows in batch_iter(link_data, batch_size, transform):
                    writer.bulk_insert(EntityTypes.LINK, rows, allow_defaults=True)
                    progress.update(nrows)
                del link_data  # release memory

                # stream group_nodes
                progress.set_description_str(f'Archiving database: {EntityTypes.GROUP_NODE.value}s')

                def transform(d):
                    return {'dbgroup_id': d[0], 'dbnode_id': d[1]}

                for nrows, rows in batch_iter(group_nodes, batch_size, transform):
                    writer.bulk_insert(EntityTypes.GROUP_NODE, rows, allow_defaults=True)
                    progress.update(nrows)
                del group_nodes  # release memory

            # stream node repository files to the archive
            if entity_ids[EntityTypes.NODE]:
                _stream_repo_files(
                    archive_format.key_format, writer, entity_ids[EntityTypes.NODE], backend, batch_size, filter_size
                )

            EXPORT_LOGGER.report('Finalizing archive creation...')

        if filename.exists():
            filename.unlink()

        filename.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(tmp_filename, filename)

    EXPORT_LOGGER.report('Archive created successfully')

    return filename


def _collect_all_entities(
    querybuilder: QbType,
    entity_ids: dict[EntityTypes, set[int]],
    include_authinfos: bool,
    include_comments: bool,
    include_logs: bool,
    batch_size: int,
) -> tuple[list[list[int]], set[LinkQuadruple]]:
    """Collect all entities.

    :returns: (group_id_to_node_id, link_data) and updates entity_ids
    """

    def progress_str(name):
        return f'Collecting entities: {name}'

    with get_progress_reporter()(desc=progress_str(''), total=9) as progress:
        progress.set_description_str(progress_str('Nodes'))
        entity_ids[EntityTypes.NODE].update(
            querybuilder().append(orm.Node, project='id').all(batch_size=batch_size, flat=True)
        )
        progress.update()

        progress.set_description_str(progress_str('Links'))
        progress.update()
        qbuilder = (
            querybuilder()
            .append(orm.Node, tag='incoming', project=['id'])
            .append(orm.Node, with_incoming='incoming', project=['id'], edge_project=['type', 'label'])
            .distinct()
        )
        link_data = {LinkQuadruple(*row) for row in qbuilder.all(batch_size=batch_size)}

        progress.set_description_str(progress_str('Groups'))
        progress.update()
        entity_ids[EntityTypes.GROUP].update(
            querybuilder()
            .append(
                orm.Group,
                project='id',
            )
            .all(batch_size=batch_size, flat=True)
        )
        progress.set_description_str(progress_str('Nodes-Groups'))
        progress.update()
        qbuilder = (
            querybuilder()
            .append(orm.Group, project='id', tag='group')
            .append(orm.Node, with_group='group', project='id')
            .distinct()
        )
        group_nodes: list[list[int]] = qbuilder.all(batch_size=batch_size)

        progress.set_description_str(progress_str('Computers'))
        progress.update()
        entity_ids[EntityTypes.COMPUTER].update(
            querybuilder()
            .append(
                orm.Computer,
                project='id',
            )
            .all(batch_size=batch_size, flat=True)
        )

        progress.set_description_str(progress_str('AuthInfos'))
        progress.update()
        if include_authinfos:
            entity_ids[EntityTypes.AUTHINFO].update(
                querybuilder()
                .append(
                    orm.AuthInfo,
                    project='id',
                )
                .all(batch_size=batch_size, flat=True)
            )

        progress.set_description_str(progress_str('Logs'))
        progress.update()
        if include_logs:
            entity_ids[EntityTypes.LOG].update(
                querybuilder()
                .append(
                    orm.Log,
                    project='id',
                )
                .all(batch_size=batch_size, flat=True)
            )

        progress.set_description_str(progress_str('Comments'))
        progress.update()
        if include_comments:
            entity_ids[EntityTypes.COMMENT].update(
                querybuilder()
                .append(
                    orm.Comment,
                    project='id',
                )
                .all(batch_size=batch_size, flat=True)
            )

        progress.set_description_str(progress_str('Users'))
        progress.update()
        entity_ids[EntityTypes.USER].update(
            querybuilder()
            .append(
                orm.User,
                project='id',
            )
            .all(batch_size=batch_size, flat=True)
        )

    return group_nodes, link_data


def _collect_required_entities(
    querybuilder: QbType,
    entity_ids: dict[EntityTypes, set[int]],
    traversal_rules: dict[str, bool],
    include_authinfos: bool,
    include_comments: bool,
    include_logs: bool,
    backend: StorageBackend,
    query_params: QueryParams,
) -> tuple[list[list[int]], set[LinkQuadruple]]:
    """Collect required entities, given a set of starting entities and provenance graph traversal rules.

    :returns: (group_id_to_node_id, link_data) and updates entity_ids
    """

    filter_size = query_params.filter_size
    batch_size = query_params.batch_size

    def progress_str(name):
        return f'Collecting entities: {name}'

    with get_progress_reporter()(desc=progress_str(''), total=7) as progress:
        # get all nodes from groups
        progress.set_description_str(progress_str('Nodes (groups)'))
        group_nodes: list[list[int]] = []
        if ids := entity_ids[EntityTypes.GROUP]:
            for _, group_batch_ids in batch_iter(ids, filter_size):
                qbuilder = querybuilder()
                qbuilder.append(orm.Group, filters={'id': {'in': group_batch_ids}}, project='id', tag='group')
                qbuilder.append(orm.Node, with_group='group', project='id')
                qbuilder.distinct()
                batch_group_nodes = qbuilder.all(batch_size=batch_size)
                group_nodes.extend(batch_group_nodes)
                entity_ids[EntityTypes.NODE].update(nid for _, nid in batch_group_nodes)

        # get full set of nodes & links, following traversal rules
        progress.set_description_str(progress_str('Nodes (traversal)'))
        progress.update()
        traverse_output = get_nodes_export(
            starting_pks=entity_ids[EntityTypes.NODE], get_links=True, backend=backend, **traversal_rules
        )
        entity_ids[EntityTypes.NODE].update(traverse_output.pop('nodes'))
        link_data = traverse_output.pop('links') or set()  # possible memory hog?

        progress.set_description_str(progress_str('Computers'))
        progress.update()

        # get full set of computers
        if ids := entity_ids[EntityTypes.NODE]:
            for _, node_batch_ids in batch_iter(ids, filter_size):
                entity_ids[EntityTypes.COMPUTER].update(
                    pk
                    for (pk,) in querybuilder()
                    .append(orm.Node, filters={'id': {'in': node_batch_ids}}, tag='node')
                    .append(orm.Computer, with_node='node', project='id')
                    .distinct()
                    .iterall(batch_size=batch_size)
                )

        # get full set of authinfos
        progress.set_description_str(progress_str('AuthInfos'))
        progress.update()
        if include_authinfos and (ids := entity_ids[EntityTypes.COMPUTER]):
            for _, computer_batch_ids in batch_iter(ids, filter_size):
                entity_ids[EntityTypes.AUTHINFO].update(
                    pk
                    for (pk,) in querybuilder()
                    .append(orm.Computer, filters={'id': {'in': computer_batch_ids}}, tag='comp')
                    .append(orm.AuthInfo, with_computer='comp', project='id')
                    .distinct()
                    .iterall(batch_size=batch_size)
                )

        # get full set of logs
        progress.set_description_str(progress_str('Logs'))
        progress.update()
        if include_logs and (ids := entity_ids[EntityTypes.NODE]):
            for _, node_batch_ids in batch_iter(ids, filter_size):
                entity_ids[EntityTypes.LOG].update(
                    pk
                    for (pk,) in querybuilder()
                    .append(orm.Node, filters={'id': {'in': node_batch_ids}}, tag='node')
                    .append(orm.Log, with_node='node', project='id')
                    .distinct()
                    .iterall(batch_size=batch_size)
                )

        # get full set of comments
        progress.set_description_str(progress_str('Comments'))
        progress.update()
        if include_comments and (ids := entity_ids[EntityTypes.NODE]):
            for _, node_batch_ids in batch_iter(ids, filter_size):
                entity_ids[EntityTypes.COMMENT].update(
                    pk
                    for (pk,) in querybuilder()
                    .append(orm.Node, filters={'id': {'in': node_batch_ids}}, tag='node')
                    .append(orm.Comment, with_node='node', project='id')
                    .distinct()
                    .iterall(batch_size=batch_size)
                )

        # get full set of users
        progress.set_description_str(progress_str('Users'))
        progress.update()
        if ids := entity_ids[EntityTypes.NODE]:
            for _, node_batch_ids in batch_iter(ids, filter_size):
                entity_ids[EntityTypes.USER].update(
                    pk
                    for (pk,) in querybuilder()
                    .append(orm.Node, filters={'id': {'in': node_batch_ids}}, tag='node')
                    .append(orm.User, with_node='node', project='id')
                    .distinct()
                    .iterall(batch_size=batch_size)
                )
        if ids := entity_ids[EntityTypes.GROUP]:
            for _, group_batch_ids in batch_iter(ids, filter_size):
                entity_ids[EntityTypes.USER].update(
                    pk
                    for (pk,) in querybuilder()
                    .append(orm.Group, filters={'id': {'in': group_batch_ids}}, tag='group')
                    .append(orm.User, with_group='group', project='id')
                    .distinct()
                    .iterall(batch_size=batch_size)
                )
        if ids := entity_ids[EntityTypes.COMMENT]:
            for _, comment_batch_ids in batch_iter(ids, filter_size):
                entity_ids[EntityTypes.USER].update(
                    pk
                    for (pk,) in querybuilder()
                    .append(orm.Comment, filters={'id': {'in': comment_batch_ids}}, tag='comment')
                    .append(orm.User, with_comment='comment', project='id')
                    .distinct()
                    .iterall(batch_size=batch_size)
                )
        if ids := entity_ids[EntityTypes.AUTHINFO]:
            for _, authinfo_batch_ids in batch_iter(ids, filter_size):
                entity_ids[EntityTypes.USER].update(
                    pk
                    for (pk,) in querybuilder()
                    .append(orm.AuthInfo, filters={'id': {'in': authinfo_batch_ids}}, tag='auth')
                    .append(orm.User, with_authinfo='auth', project='id')
                    .distinct()
                    .iterall(batch_size=batch_size)
                )

        progress.update()

    return group_nodes, link_data


def _stream_repo_files(
    key_format: str,
    writer: ArchiveWriterAbstract,
    node_ids: set[int],
    backend: StorageBackend,
    batch_size: int,
    filter_size: int,
) -> None:
    """Collect all repository object keys from the nodes, then stream the files to the archive."""

    # Batch the node IDs to avoid parameter limits when getting repo keys
    all_keys = set()

    for _, node_batch_ids in batch_iter(node_ids, filter_size):
        batch_keys = set(
            orm.Node.get_collection(backend).iter_repo_keys(
                filters={'id': {'in': node_batch_ids}}, batch_size=batch_size
            )
        )
        all_keys.update(batch_keys)

    repository = backend.get_repository()
    if not repository.key_format == key_format:
        # Here we would have to go back and replace all the keys in the `BackendNode.repository_metadata`s
        raise NotImplementedError(
            f'Backend repository key format incompatible: {repository.key_format!r} != {key_format!r}'
        )
    with get_progress_reporter()(desc='Archiving files: ', total=len(all_keys)) as progress:
        for key, stream in repository.iter_object_streams(all_keys):  # type: ignore[arg-type]
            # to-do should we use assume the key here is correct, or always re-compute and check?
            writer.put_object(stream, key=key)
            progress.update()


def _check_unsealed_nodes(querybuilder: QbType, node_ids: set[int], batch_size: int, filter_size: int) -> None:
    """Check no process nodes are unsealed, i.e. all processes have completed."""
    if not node_ids:
        return

    all_unsealed_pks = []

    for _, node_batch_ids in batch_iter(node_ids, filter_size):
        qbuilder = (
            querybuilder()
            .append(
                orm.ProcessNode,
                filters={
                    'id': {'in': node_batch_ids},
                    'attributes.sealed': {
                        '!in': [True]  # better operator?
                    },
                },
                project='id',
            )
            .distinct()
        )
        batch_unsealed_pks = qbuilder.all(batch_size=batch_size, flat=True)
        all_unsealed_pks.extend(batch_unsealed_pks)

    if all_unsealed_pks:
        raise ExportValidationError(
            'All ProcessNodes must be sealed before they can be exported. '
            f'Node(s) with PK(s): {", ".join(str(pk) for pk in all_unsealed_pks)} is/are not sealed.'
        )


def _check_node_licenses(
    querybuilder: QbType,
    node_ids: set[int],
    allowed_licenses: Optional[Union[Sequence[str], Callable]],
    forbidden_licenses: Optional[Union[Sequence[str], Callable]],
    batch_size: int,
    filter_size: int,
) -> None:
    """Check the nodes to be archived for disallowed licences."""

    from aiida.common.exceptions import LicensingException

    if allowed_licenses is None and forbidden_licenses is None:
        return None

    # set allowed function
    if allowed_licenses is None:

        def check_allowed(_):
            return True
    elif callable(allowed_licenses):

        def _check_allowed(name):
            try:
                return allowed_licenses(name)
            except Exception as exc:
                raise LicensingException('allowed_licenses function error') from exc

        check_allowed = _check_allowed
    elif isinstance(allowed_licenses, Sequence):

        def check_allowed(lic):
            return lic in allowed_licenses
    else:
        raise TypeError('allowed_licenses not a list or function')

    # set forbidden function
    if forbidden_licenses is None:

        def check_forbidden(_):
            return False
    elif callable(forbidden_licenses):

        def _check_forbidden(name):
            try:
                return forbidden_licenses(name)
            except Exception as exc:
                raise LicensingException('forbidden_licenses function error') from exc

        check_forbidden = _check_forbidden
    elif isinstance(forbidden_licenses, Sequence):

        def check_forbidden(lic):
            return lic in forbidden_licenses
    else:
        raise TypeError('forbidden_licenses not a list or function')

    for _, node_batch_ids in batch_iter(node_ids, filter_size):
        # create query for this batch
        qbuilder = querybuilder().append(
            orm.Node,
            project=['id', 'attributes.source.license'],
            filters={'id': {'in': node_batch_ids}},
        )

        for node_id, name in qbuilder.iterall(batch_size=batch_size):
            if name is None:
                continue
            if not check_allowed(name):
                raise LicensingException(
                    f"Node {node_id} is licensed under '{name}' license, which is not in the list of allowed licenses"
                )
            if check_forbidden(name):
                raise LicensingException(
                    f"Node {node_id} is licensed under '{name}' license, which is in the list of forbidden licenses"
                )


def get_init_summary(
    *,
    archive_version: str,
    outfile: Path,
    collect_all: bool,
    include_authinfos: bool,
    include_comments: bool,
    include_logs: bool,
    traversal_rules: dict,
    compression: int,
) -> str:
    """Get summary for archive initialisation"""
    parameters: list[list[Any]] = [['Path', str(outfile)], ['Version', archive_version], ['Compression', compression]]

    result = f'\n{tabulate(parameters, headers=["Archive Parameters", ""])}'

    inclusions: list[list[Any]] = [
        ['Computers/Nodes/Groups/Users', 'All' if collect_all else 'Selected'],
        ['Computer Authinfos', include_authinfos],
        ['Node Comments', include_comments],
        ['Node Logs', include_logs],
    ]
    result += f'\n\n{tabulate(inclusions, headers=["Inclusion rules", ""])}'

    if not collect_all:
        rules_table = [[f'Follow links {" ".join(name.split("_"))}s', value] for name, value in traversal_rules.items()]
        result += f'\n\n{tabulate(rules_table, headers=["Traversal rules", ""])}'

    return result + '\n'
