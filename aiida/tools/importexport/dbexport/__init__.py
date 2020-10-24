# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=fixme,too-many-lines
"""Provides export functionalities."""
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field, asdict
import logging
import os
import tarfile
import time
from typing import (
    Any,
    Callable,
    ContextManager,
    DefaultDict,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)
import warnings

from aiida import get_version, orm
from aiida.common import json
from aiida.common.exceptions import LicensingException
from aiida.common.folders import Folder, RepositoryFolder, SandboxFolder
from aiida.common.links import GraphTraversalRules
from aiida.common.lang import type_check
from aiida.common.log import LOG_LEVEL_REPORT, override_log_formatter
from aiida.common.progress_reporter import get_progress_reporter
from aiida.common.warnings import AiidaDeprecationWarning
from aiida.orm.utils._repository import Repository
from aiida.tools.importexport.common import (
    exceptions,
)
from aiida.tools.importexport.common.config import (
    COMMENT_ENTITY_NAME,
    COMPUTER_ENTITY_NAME,
    EXPORT_VERSION,
    GROUP_ENTITY_NAME,
    LOG_ENTITY_NAME,
    NODE_ENTITY_NAME,
    NODES_EXPORT_SUBFOLDER,
    entity_names_to_entities,
    file_fields_to_model_fields,
    get_all_fields_info,
    model_fields_to_file_fields,
)
from aiida.tools.graph.graph_traversers import get_nodes_export, validate_traversal_rules
from aiida.tools.importexport.common.utils import export_shard_uuid
from aiida.tools.importexport.dbexport.utils import (
    EXPORT_LOGGER,
    ExportFileFormat,
    check_licenses,
    check_process_nodes_sealed,
    deprecated_parameters,
    fill_in_query,
    serialize_dict,
    summary,
)
from aiida.tools.importexport.dbexport.zip import ZipFolder

__all__ = ('export', 'EXPORT_LOGGER', 'ExportFileFormat', 'ArchiveWriterAbstract')


@dataclass
class ExportMetadata:
    """Class for storing metadata about an export."""
    graph_traversal_rules: Dict[str, bool]
    # Entity type -> UUID list
    entities_starting_set: Dict[str, Set[str]]
    include_comments: bool
    include_logs: bool
    # Entity type -> database ID key
    unique_identifiers: Dict[str, str] = field(repr=False)
    # Entity type -> database key -> meta parameters
    all_fields_info: Dict[str, Dict[str, Dict[str, str]]] = field(repr=False)
    aiida_version: str = field(default_factory=get_version)


@dataclass
class ArchiveData:
    """Class for storing data, to export to an AiiDA archive."""
    metadata: ExportMetadata
    node_uuids: Set[str]
    # UUID of the group -> UUIDs of the entities it contains
    group_uuids: Dict[str, Set[str]]
    # list of {'input': <UUID>, 'output': <UUID>, 'label': <LABEL>, 'type': <TYPE>}
    link_uuids: List[dict]
    # all entity data from the database, except Node extras and attributes
    # {'ENTITY_NAME': {<UUID>: {'db_key': 'value', ...}, ...}, ...}
    entity_data: Dict[str, Dict[int, dict]]
    # Iterable of Node (uuid, attributes, extras)
    node_data: Iterable[Tuple[str, dict, dict]]

    def __repr__(self) -> str:
        """Return string representation."""
        return f'ArchiveData(metadata={self.metadata},' + ','.join(
            f'#{k}={len(v)}' for k, v in self.entity_data.items()
        ) + ')'


@dataclass
class ExportReport:
    """Class for storing data about the export process."""
    # time in seconds
    time_collect_start: float
    time_collect_stop: float
    # skipped if no data to write
    time_write_start: Optional[float] = None
    time_write_stop: Optional[float] = None
    # additional data returned  by the writer
    writer_data: Optional[Dict[str, Any]] = None

    @property
    def total_time(self) -> float:
        """Return total time taken in seconds."""
        return (self.time_write_stop or self.time_collect_stop) - self.time_collect_start


class ArchiveWriterAbstract(ABC):
    """An abstract interface for AiiDA archive writers."""

    def __init__(self, filename: str, **kwargs: Any):
        """An archive writer

        :param filename: the filename (possibly including the absolute path)
            of the file on which to export.

        """
        # pylint: disable=unused-argument
        self._filename = filename

    @property
    def filename(self) -> str:
        """Return the filename to write to."""
        return self._filename

    @property
    @abstractmethod
    def file_format_verbose(self) -> str:
        """The file format name."""

    @property
    @abstractmethod
    def export_version(self) -> str:
        """The export version."""

    @abstractmethod
    def write(
        self,
        export_data: ArchiveData,
    ) -> dict:
        """write the archive.

        :param export_data: The data to export
        :returns: A dictionary of data about the write process

        """


def _write_to_json_archive(folder: Union[Folder, ZipFolder], export_data: ArchiveData, export_version: str) -> None:
    """Write data to the archive."""
    # subfolder inside the export package
    nodesubfolder = folder.get_subfolder(NODES_EXPORT_SUBFOLDER, create=True, reset_limit=True)

    EXPORT_LOGGER.debug('ADDING DATA TO EXPORT ARCHIVE...')

    data: Dict[str, Any] = {
        'node_attributes': {},
        'node_extras': {},
        'export_data': export_data.entity_data,
        'links_uuid': export_data.link_uuids,
        'groups_uuid': {key: list(vals) for key, vals in export_data.group_uuids.items()},
    }

    for uuid, attributes, extras in export_data.node_data:
        data['node_attributes'][uuid] = attributes
        data['node_extras'][uuid] = extras

    # N.B. We're really calling zipfolder.open (if exporting a zipfile)
    with folder.open('data.json', mode='w') as fhandle:
        # fhandle.write(json.dumps(data, cls=UUIDEncoder))
        fhandle.write(json.dumps(data))

    metadata = {
        'export_version': export_version,
        'aiida_version': export_data.metadata.aiida_version,
        'all_fields_info': export_data.metadata.all_fields_info,
        'unique_identifiers': export_data.metadata.unique_identifiers,
        'export_parameters': {
            'graph_traversal_rules': export_data.metadata.graph_traversal_rules,
            'entities_starting_set': export_data.metadata.entities_starting_set,
            'include_comments': export_data.metadata.include_comments,
            'include_logs': export_data.metadata.include_logs,
        },
    }

    with folder.open('metadata.json', 'w') as fhandle:
        fhandle.write(json.dumps(metadata))

    EXPORT_LOGGER.debug('ADDING REPOSITORY FILES TO EXPORT ARCHIVE...')

    # If there are no nodes, there are no repository files to store
    if not export_data.node_uuids:
        return

    pbar_base_str = 'Exporting repository - '
    with get_progress_reporter()(total=len(export_data.node_uuids)) as progress:

        for uuid in export_data.node_uuids:
            sharded_uuid = export_shard_uuid(uuid)

            progress.set_description_str(f"{pbar_base_str}UUID={uuid.split('-')[0]}", refresh=False)
            progress.update()

            # Important to set create=False, otherwise creates twice a subfolder.
            # Maybe this is a bug of insert_path?
            thisnodefolder = nodesubfolder.get_subfolder(sharded_uuid, create=False, reset_limit=True)

            # Make sure the node's repository folder was not deleted
            src = RepositoryFolder(section=Repository._section_name, uuid=uuid)  # pylint: disable=protected-access
            if not src.exists():
                raise exceptions.ArchiveExportError(
                    f'Unable to find the repository folder for Node with UUID={uuid} '
                    'in the local repository'
                )

            # In this way, I copy the content of the folder, and not the folder itself
            thisnodefolder.insert_path(src=src.abspath, dest_name='.')


class WriterJsonZip(ArchiveWriterAbstract):
    """An archive writer,
    which writes database data as a single JSON and repository data in a zipped folder system.
    """

    def __init__(self, filename: str, use_compression: bool = True, **kwargs: Any):
        """A writer for zipped archives.

        :param filename: the filename (possibly including the absolute path)
            of the file on which to export.
        :param use_compression: Whether or not to compress the zip file.

        """
        super().__init__(filename, **kwargs)
        self._use_compression = use_compression

    @property
    def file_format_verbose(self) -> str:
        return 'Zip (compressed)' if self._use_compression else 'Zip (uncompressed)'

    @property
    def export_version(self) -> str:
        return EXPORT_VERSION

    def write(self, export_data: ArchiveData) -> dict:
        """write the archive

        :param export_data: The data to export
        :returns: A dictionary of data about the write process

        """
        with ZipFolder(self.filename, mode='w', use_compression=self._use_compression) as folder:
            _write_to_json_archive(
                folder=folder,
                export_data=export_data,
                export_version=self.export_version,
            )

        return {}


class WriterJsonTar(ArchiveWriterAbstract):
    """An archive writer,
    which writes database data as a single JSON and repository data in a folder system.

    The entire containing folder is then compressed as a tar file.
    """

    def __init__(self, filename: str, **kwargs: Any):
        """A writer for zipped archives.

        :param filename: the filename (possibly including the absolute path)
            of the file on which to export.
        :param sandbox_in_repo: Create the temporary uncompressed folder within the aiida repository

        """
        super().__init__(filename, **kwargs)
        self.sandbox_in_repo = kwargs.get('sandbox_in_repo', True)

    @property
    def file_format_verbose(self) -> str:
        return 'Gzipped tarball (compressed)'

    @property
    def export_version(self) -> str:
        return EXPORT_VERSION

    def write(self, export_data: ArchiveData) -> dict:
        """write the archive

        :param export_data: The data to export
        :returns: A dictionary of data about the write process

        """
        with SandboxFolder(sandbox_in_repo=self.sandbox_in_repo) as folder:
            _write_to_json_archive(
                folder=folder,
                export_data=export_data,
                export_version=self.export_version,
            )

            with tarfile.open(self.filename, 'w:gz', format=tarfile.PAX_FORMAT, dereference=True) as tar:
                time_compress_start = time.time()
                tar.add(folder.abspath, arcname='')
                time_compress_stop = time.time()

        return {'compression_time_start': time_compress_start, 'compression_time_stop': time_compress_stop}


class WriterJsonFolder(ArchiveWriterAbstract):
    """An archive writer,
    which writes database data as a single JSON and repository data in a folder system.

    This writer is mainly intended for backward compatibility with `export_tree`.
    """

    def __init__(self, filename: str, folder: Union[Folder, ZipFolder] = None, **kwargs: Any):
        """A writer for zipped archives.

        :param filename: the filename (possibly including the absolute path)
            of the file on which to export.
        :param folder: a folder to write the archive to.

        """
        super().__init__(filename, **kwargs)
        type_check(folder, (Folder, ZipFolder), msg='`folder` must be specified and given as an AiiDA Folder entity')
        self._folder = cast(Union[Folder, ZipFolder], folder)

    @property
    def file_format_verbose(self) -> str:
        return str(self._folder.__class__)

    @property
    def export_version(self) -> str:
        return EXPORT_VERSION

    def write(self, export_data: ArchiveData) -> dict:
        """write the archive

        :param export_data: The data to export
        :returns: A dictionary of data about the write process

        """
        _write_to_json_archive(
            folder=self._folder,
            export_data=export_data,
            export_version=self.export_version,
        )

        return {}


def get_writer(file_format: str) -> Type[ArchiveWriterAbstract]:
    """Return the available writer classes."""
    # TODO this could be made an entrypoint
    writers = {
        ExportFileFormat.ZIP: WriterJsonZip,
        ExportFileFormat.TAR_GZIPPED: WriterJsonTar,
        'folder': WriterJsonFolder,
    }

    if file_format not in writers:
        raise exceptions.ArchiveExportError(
            f'Can only export in the formats: {tuple(writers.keys())}, please specify one for "file_format".'
        )

    return cast(Type[ArchiveWriterAbstract], writers[file_format])


def export(
    entities: Optional[Iterable[Any]] = None,
    filename: Optional[str] = None,
    file_format: str = ExportFileFormat.ZIP,
    overwrite: bool = False,
    silent: bool = False,
    use_compression: bool = True,
    include_comments: bool = True,
    include_logs: bool = True,
    allowed_licenses: Optional[Union[list, Callable]] = None,
    forbidden_licenses: Optional[Union[list, Callable]] = None,
    writer_init: Optional[Dict[str, Any]] = None,
    **traversal_rules: bool,
) -> ExportReport:
    """Export AiiDA data to an archive file.

    .. deprecated:: 1.2.1
        Support for the parameters `what` and `outfile` will be removed in `v2.0.0`.
        Please use `entities` and `filename` instead, respectively.

    :param entities: a list of entity instances;
        they can belong to different models/entities.

    :param filename: the filename (possibly including the absolute path)
        of the file on which to export.

    :param file_format: See `ExportFileFormat` for complete list of valid values (default: 'zip').

    :param overwrite: if True, overwrite the output file without asking, if it exists.
        If False, raise an
        :py:class:`~aiida.tools.importexport.common.exceptions.ArchiveExportError`
        if the output file already exists.

    :param silent: suppress console prints and progress bar.

    :param use_compression: Whether or not to compress the archive file
        (only valid for the zip file format).

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

    :param writer_init: Additional key-word arguments to pass to the writer class init

    :param traversal_rules: graph traversal rules. See :const:`aiida.common.links.GraphTraversalRules`
        what rule names are toggleable and what the defaults are.

    :returns: a dictionary of data regarding the export process (timings, etc)

    :raises `~aiida.tools.importexport.common.exceptions.ArchiveExportError`:
        if there are any internal errors when exporting.
    :raises `~aiida.common.exceptions.LicensingException`:
        if any node is licensed under forbidden license.
    """
    # Backwards-compatibility
    entities = cast(
        Iterable[Any],
        deprecated_parameters(
            old={
                'name': 'what',
                'value': traversal_rules.pop('what', None)
            },
            new={
                'name': 'entities',
                'value': entities
            },
        ),
    )
    filename = cast(
        str,
        deprecated_parameters(
            old={
                'name': 'outfile',
                'value': traversal_rules.pop('outfile', None)
            },
            new={
                'name': 'filename',
                'value': filename
            },
        ),
    )

    type_check(
        entities,
        (list, tuple, set),
        msg='`entities` must be specified and given as a list of AiiDA entities',
    )
    entities = list(entities)
    if type_check(filename, str, allow_none=True) is None:
        filename = 'export_data.aiida'

    if not overwrite and os.path.exists(filename):
        raise exceptions.ArchiveExportError(f"The output file '{filename}' already exists")

    # validate the traversal rules and generate a full set for reporting
    validate_traversal_rules(GraphTraversalRules.EXPORT, **traversal_rules)
    full_traversal_rules = {
        name: traversal_rules.get(name, rule.default) for name, rule in GraphTraversalRules.EXPORT.value.items()
    }

    writer = get_writer(file_format)(filename=filename, use_compression=use_compression, **(writer_init or {}))

    if silent:
        logging.disable(logging.CRITICAL)

    try:
        summary(
            file_format=writer.file_format_verbose,
            export_version=writer.export_version,
            outfile=filename,
            include_comments=include_comments,
            include_logs=include_logs,
            traversal_rules=full_traversal_rules
        )

        report_data: Dict[str, Any] = {'time_write_start': None, 'time_write_stop': None, 'writer_data': None}

        report_data['time_collect_start'] = time.time()
        export_data = _collect_archive_data(
            entities=entities,
            allowed_licenses=allowed_licenses,
            forbidden_licenses=forbidden_licenses,
            include_comments=include_comments,
            include_logs=include_logs,
            **traversal_rules
        )
        report_data['time_collect_stop'] = time.time()

        extract_time = report_data['time_collect_stop'] - report_data['time_collect_start']
        EXPORT_LOGGER.debug(f'Data extracted in {extract_time:6.2g} s.')

        if export_data is not None:
            try:
                report_data['time_write_start'] = time.time()
                report_data['writer_data'] = writer.write(export_data=export_data)  # type: ignore
                report_data['time_write_stop'] = time.time()
            except (exceptions.ArchiveExportError, LicensingException) as exc:
                if os.path.exists(filename):
                    os.remove(filename)
                raise exc

            write_time = report_data['time_write_stop'] - report_data['time_write_start']
            EXPORT_LOGGER.debug(f'Data written in {write_time:6.2g} s.')

        else:
            EXPORT_LOGGER.debug('No data to write.')

    finally:
        # Reset logging level
        if silent:
            logging.disable(logging.NOTSET)

    return ExportReport(**report_data)


@override_log_formatter('%(message)s')
def _collect_archive_data(
    entities: Optional[Iterable[Any]] = None,
    allowed_licenses: Optional[Union[list, Callable]] = None,
    forbidden_licenses: Optional[Union[list, Callable]] = None,
    include_comments: bool = True,
    include_logs: bool = True,
    **traversal_rules: bool,
) -> Optional[ArchiveData]:
    """Collect data to be exported

    .. deprecated:: 1.2.1
        Support for the parameter `what` will be removed in `v2.0.0`. Please use `entities` instead.

    :param entities: a list of entity instances; they can belong to different models/entities.

    :param allowed_licenses: List or function.
        If a list, then checks whether all licenses of Data nodes are in the list.
        If a function, then calls function for licenses of Data nodes,
        expecting True if license is allowed, False otherwise.

    :param forbidden_licenses: List or function.
        If a list, then checks whether all licenses of Data nodes are in the list.
        If a function, then calls function for licenses of Data nodes,
        expecting True if license is allowed, False otherwise.

    :param include_comments: In-/exclude export of comments for given node(s) in ``entities``.
        Default: True, *include* comments in export (as well as relevant users).

    :param include_logs: In-/exclude export of logs for given node(s) in ``entities``.
        Default: True, *include* logs in export.

    :param traversal_rules: graph traversal rules.
        See :const:`aiida.common.links.GraphTraversalRules`
        what rule names are toggleable and what the defaults are.

    :raises `~aiida.tools.importexport.common.exceptions.ArchiveExportError`:
        if there are any internal errors when exporting.
    :raises `~aiida.common.exceptions.LicensingException`:
        if any node is licensed under forbidden license.
    """
    # pylint: disable=too-many-locals
    EXPORT_LOGGER.debug('STARTING EXPORT...')

    # Backwards-compatibility
    entities = cast(
        Iterable[Any],
        deprecated_parameters(
            old={
                'name': 'what',
                'value': traversal_rules.pop('what', None)
            },
            new={
                'name': 'entities',
                'value': entities
            },
        ),
    )

    type_check(
        entities,
        (list, tuple, set),
        msg='`entities` must be specified and given as a list of AiiDA entities',
    )
    entities = list(entities)

    all_fields_info, unique_identifiers = get_all_fields_info()

    entities_starting_set, given_node_entry_ids = _get_starting_node_ids(entities)

    (
        node_ids_to_be_exported,
        node_pk_2_uuid_mapping,
        links_uuid,
        traversal_rules,
    ) = _collect_node_ids(given_node_entry_ids, **traversal_rules)

    _check_node_licenses(node_ids_to_be_exported, allowed_licenses, forbidden_licenses)

    entries_queries = _collect_entity_queries(
        node_ids_to_be_exported,
        entities_starting_set,
        node_pk_2_uuid_mapping,
        include_comments,
        include_logs,
    )

    export_data = _perform_export_queries(entries_queries)

    # note this was originally below the attributes and group_uuid gather
    check_process_nodes_sealed({
        node_pk for node_pk, content in export_data.get(NODE_ENTITY_NAME, {}).items()
        if content['node_type'].startswith('process.')
    })

    model_data = sum(len(model_data) for model_data in export_data.values())
    if not model_data:
        EXPORT_LOGGER.log(msg='Nothing to store, exiting...', level=LOG_LEVEL_REPORT)
        return None
    EXPORT_LOGGER.log(
        msg=(
            f'Exporting a total of {model_data} database entries, '
            f'of which {len(node_ids_to_be_exported)} are Nodes.'
        ),
        level=LOG_LEVEL_REPORT,
    )

    groups_uuid = _get_groups_uuid(export_data)

    # Turn sets into lists to be able to export them as JSON metadata.
    for entity, entity_set in entities_starting_set.items():
        entities_starting_set[entity] = list(entity_set)  # type: ignore

    metadata = ExportMetadata(
        graph_traversal_rules=traversal_rules,
        entities_starting_set=entities_starting_set,
        include_comments=include_comments,
        include_logs=include_logs,
        unique_identifiers=unique_identifiers,
        all_fields_info=all_fields_info
    )

    all_node_uuids = {node_pk_2_uuid_mapping[_] for _ in node_ids_to_be_exported}

    # we get the node data last, because it is generally the largest data source
    # and later we may look to stream this data in chunks
    node_data = _collect_node_data(node_ids_to_be_exported)

    return ArchiveData(
        metadata,
        all_node_uuids,
        groups_uuid,
        links_uuid,
        export_data,
        node_data,
    )


def _get_starting_node_ids(entities: List[Any]) -> Tuple[DefaultDict[str, Set[str]], Set[int]]:
    """Get the starting node UUIDs and PKs

    :param entities: a list of entity instances

    :raises exceptions.ArchiveExportError:
    :return: entities_starting_set, given_node_entry_ids
    """
    entities_starting_set: DefaultDict[str, Set[str]] = defaultdict(set)
    given_node_entry_ids: Set[int] = set()

    # store a list of the actual dbnodes
    total = len(entities) + (1 if GROUP_ENTITY_NAME in entities_starting_set else 0)
    if not total:
        return entities_starting_set, given_node_entry_ids

    with get_progress_reporter()(desc='Collecting chosen entities', total=total) as progress:
        for entry in entities:

            if issubclass(entry.__class__, orm.Group):
                entities_starting_set[GROUP_ENTITY_NAME].add(entry.uuid)
            elif issubclass(entry.__class__, orm.Node):
                entities_starting_set[NODE_ENTITY_NAME].add(entry.uuid)
                given_node_entry_ids.add(entry.pk)
            elif issubclass(entry.__class__, orm.Computer):
                entities_starting_set[COMPUTER_ENTITY_NAME].add(entry.uuid)
            else:
                raise exceptions.ArchiveExportError(
                    f'I was given {entry} ({type(entry)}),'
                    ' which is not a Node, Computer, or Group instance'
                )

            progress.update()

        # Add all the nodes contained within the specified groups
        if GROUP_ENTITY_NAME in entities_starting_set:

            progress.set_description_str('Retrieving Nodes from Groups ...', refresh=False)

            # Use single query instead of given_group.nodes iterator for performance.
            qh_groups = (
                orm.QueryBuilder().append(
                    orm.Group,
                    filters={
                        'uuid': {
                            'in': entities_starting_set[GROUP_ENTITY_NAME]
                        }
                    },
                    tag='groups',
                ).queryhelp
            )

            # Delete this import once the dbexport.zip module has been renamed
            from builtins import zip  # pylint: disable=redefined-builtin

            node_results = (
                orm.QueryBuilder(**qh_groups).append(orm.Node, project=['id', 'uuid'], with_group='groups').all()
            )
            if node_results:
                pks, uuids = map(list, zip(*node_results))
                entities_starting_set[NODE_ENTITY_NAME].update(uuids)  # type: ignore
                given_node_entry_ids.update(pks)  # type: ignore
                del node_results, pks, uuids

    return entities_starting_set, given_node_entry_ids


def _collect_node_ids(given_node_entry_ids: Set[int],
                      **traversal_rules: bool) -> Tuple[Set[int], Dict[int, str], List[dict], Dict[str, bool]]:
    """Iteratively explore the AiiDA graph to find further nodes that should also be exported

    At the same time, we will create the links_uuid list of dicts to be exported

    """
    with get_progress_reporter()(desc='Traversing provenance via links ...', total=1) as progress:
        traverse_output = get_nodes_export(starting_pks=given_node_entry_ids, get_links=True, **traversal_rules)
        progress.update()

    node_ids_to_be_exported = traverse_output['nodes']
    graph_traversal_rules = traverse_output['rules']

    # A utility dictionary for mapping PK to UUID.
    if node_ids_to_be_exported:
        qbuilder = orm.QueryBuilder().append(
            orm.Node,
            project=('id', 'uuid'),
            filters={'id': {
                'in': node_ids_to_be_exported
            }},
        )
        node_pk_2_uuid_mapping = dict(qbuilder.all())
    else:
        node_pk_2_uuid_mapping = {}

    # The set of tuples now has to be transformed to a list of dicts
    links_uuid = [{
        'input': node_pk_2_uuid_mapping[link.source_id],
        'output': node_pk_2_uuid_mapping[link.target_id],
        'label': link.link_label,
        'type': link.link_type,
    } for link in traverse_output['links']]

    return (
        node_ids_to_be_exported,
        node_pk_2_uuid_mapping,
        links_uuid,
        graph_traversal_rules,
    )


def _check_node_licenses(
    node_ids_to_be_exported: Set[int],
    allowed_licenses: Optional[Union[list, Callable]],
    forbidden_licenses: Optional[Union[list, Callable]],
) -> None:
    """Check the nodes to be archived for disallowed licences."""
    # TODO (Spyros) To see better! Especially for functional licenses
    # Check the licenses of exported data.
    if allowed_licenses is not None or forbidden_licenses is not None:
        builder = orm.QueryBuilder()
        builder.append(
            orm.Node,
            project=['id', 'attributes.source.license'],
            filters={'id': {
                'in': node_ids_to_be_exported
            }},
        )
        # Skip those nodes where the license is not set (this is the standard behavior with Django)
        node_licenses = [(a, b) for [a, b] in builder.all() if b is not None]
        check_licenses(node_licenses, allowed_licenses, forbidden_licenses)


def _collect_entity_queries(
    node_ids_to_be_exported: Set[int],
    entities_starting_set: DefaultDict[str, Set[str]],
    node_pk_2_uuid_mapping: Dict[int, str],
    include_comments: bool = True,
    include_logs: bool = True,
) -> Dict[str, orm.QueryBuilder]:
    """Gather partial queries for all entities to export."""
    # pylint: disable=too-many-locals
    given_log_entry_ids = set()
    given_comment_entry_ids = set()
    all_fields_info, _ = get_all_fields_info()

    total = 1 + ((1 if include_logs else 0) + (1 if include_logs else 0) if node_ids_to_be_exported else 0)
    with get_progress_reporter()(desc='Initializing export of all entities', total=total) as progress:

        # Universal "entities" attributed to all types of nodes
        # Logs
        if include_logs and node_ids_to_be_exported:
            # Get related log(s) - universal for all nodes
            builder = orm.QueryBuilder()
            builder.append(
                orm.Log,
                filters={'dbnode_id': {
                    'in': node_ids_to_be_exported
                }},
                project='uuid',
            )
            res = set(builder.all(flat=True))
            given_log_entry_ids.update(res)

            progress.update()

        # Comments
        if include_comments and node_ids_to_be_exported:
            # Get related log(s) - universal for all nodes
            builder = orm.QueryBuilder()
            builder.append(
                orm.Comment,
                filters={'dbnode_id': {
                    'in': node_ids_to_be_exported
                }},
                project='uuid',
            )
            res = set(builder.all(flat=True))
            given_comment_entry_ids.update(res)

            progress.update()

        # Here we get all the columns that we plan to project per entity that we would like to extract
        given_entities = set(entities_starting_set.keys())
        if node_ids_to_be_exported:
            given_entities.add(NODE_ENTITY_NAME)
        if given_log_entry_ids:
            given_entities.add(LOG_ENTITY_NAME)
        if given_comment_entry_ids:
            given_entities.add(COMMENT_ENTITY_NAME)

        progress.update()

    entities_to_add: Dict[str, orm.QueryBuilder] = {}
    if not given_entities:
        return entities_to_add

    with get_progress_reporter()(total=len(given_entities)) as progress:

        pbar_base_str = 'Preparing entities'

        for given_entity in given_entities:
            progress.set_description_str(f'{pbar_base_str} - {given_entity}s', refresh=False)
            progress.update()

            project_cols = ['id']
            # The following gets a list of fields that we need,
            # e.g. user, mtime, uuid, computer
            entity_prop = all_fields_info[given_entity].keys()

            # Here we do the necessary renaming of properties
            for prop in entity_prop:
                # nprop contains the list of projections
                nprop = (
                    file_fields_to_model_fields[given_entity][prop]
                    if prop in file_fields_to_model_fields[given_entity] else prop
                )
                project_cols.append(nprop)

            # Getting the ids that correspond to the right entity
            entry_uuids_to_add = entities_starting_set.get(given_entity, set())
            if not entry_uuids_to_add:
                if given_entity == LOG_ENTITY_NAME:
                    entry_uuids_to_add = given_log_entry_ids
                elif given_entity == COMMENT_ENTITY_NAME:
                    entry_uuids_to_add = given_comment_entry_ids
            elif given_entity == NODE_ENTITY_NAME:
                entry_uuids_to_add.update({node_pk_2_uuid_mapping[_] for _ in node_ids_to_be_exported})

            builder = orm.QueryBuilder()
            builder.append(
                entity_names_to_entities[given_entity],
                filters={'uuid': {
                    'in': entry_uuids_to_add
                }},
                project=project_cols,
                tag=given_entity,
                outerjoin=True,
            )
            entities_to_add[given_entity] = builder

    return entities_to_add


def _perform_export_queries(entries_queries: Dict[str, orm.QueryBuilder]) -> Dict[str, Dict[int, dict]]:
    """Start automatic recursive export data generation

    :param entries_queries: partial queries for all entities to export

    :return: export data mappings by entity type -> pk -> db_columns, e.g.
        {'ENTITY_NAME': {<pk>: {'uuid': 'abc', ...}, ...}, ...}
        Note: this data does not yet contain attributes and extras

    """
    EXPORT_LOGGER.debug('GATHERING DATABASE ENTRIES...')

    all_fields_info, _ = get_all_fields_info()

    export_data = defaultdict(dict)  # type: dict
    if not entries_queries:
        return export_data

    entity_separator = '_'
    counts = [p_query.count() for p_query in entries_queries.values()]
    with get_progress_reporter()(total=sum(counts)) as progress:

        for entity_name, partial_query in entries_queries.items():

            progress.set_description_str(f'Exporting {entity_name} fields', refresh=False)

            foreign_fields = {k: v for k, v in all_fields_info[entity_name].items() if 'requires' in v}

            for value in foreign_fields.values():
                ref_model_name = value['requires']
                fill_in_query(
                    partial_query,
                    entity_name,
                    ref_model_name,
                    [entity_name],
                    entity_separator,
                )

            for temp_d in partial_query.iterdict():

                progress.update()

                for key in temp_d:
                    # Get current entity
                    current_entity = key.split(entity_separator)[-1]

                    # This is a empty result of an outer join.
                    # It should not be taken into account.
                    if temp_d[key]['id'] is None:
                        continue

                    export_data[current_entity].update({
                        temp_d[key]['id']:
                        serialize_dict(
                            temp_d[key],
                            remove_fields=['id'],
                            rename_fields=model_fields_to_file_fields[current_entity],
                        )
                    })

    return export_data


def _collect_node_data(all_node_pks: Set[int]) -> Iterable[Tuple[str, dict, dict]]:
    """Gather attributes and extras for nodes

    :param export_data:  mappings by entity type -> pk -> db_columns
    :param all_node_pks: set of pks

    :return: iterable of (uuid, attributes, extras)

    """
    # ATTRIBUTES and EXTRAS
    EXPORT_LOGGER.debug('GATHERING NODE ATTRIBUTES AND EXTRAS...')
    node_data = []

    # Another QueryBuilder query to get the attributes and extras.
    if all_node_pks:
        all_nodes_query = orm.QueryBuilder().append(
            orm.Node,
            filters={'id': {
                'in': all_node_pks
            }},
            project=['id', 'attributes', 'extras'],
        )

        with get_progress_reporter()(total=all_nodes_query.count()) as progress:
            progress.set_description_str('Exporting Attributes and Extras', refresh=False)

            for node_pk, attributes, extras in all_nodes_query.iterall():
                progress.update()

                node_data.append((str(node_pk), attributes, extras))

    return node_data


def _get_groups_uuid(export_data: Dict[str, Dict[int, dict]]) -> Dict[str, Set[str]]:
    """Get node UUIDs per group."""
    EXPORT_LOGGER.debug('GATHERING GROUP ELEMENTS...')
    groups_uuid: Dict[str, Set[str]] = defaultdict(set)
    # If a group is in the exported data, we export the group/node correlation
    if GROUP_ENTITY_NAME not in export_data:
        return groups_uuid

    group_uuids_with_node_uuids = (
        orm.QueryBuilder().append(
            orm.Group,
            filters={
                'id': {
                    'in': export_data[GROUP_ENTITY_NAME]
                }
            },
            project='uuid',
            tag='groups',
        ).append(orm.Node, project='uuid', with_group='groups')
    )

    total_node_uuids_for_groups = group_uuids_with_node_uuids.count()

    if not total_node_uuids_for_groups:
        return groups_uuid

    with get_progress_reporter()(desc='Exporting Groups ...', total=total_node_uuids_for_groups) as progress:

        for group_uuid, node_uuid in group_uuids_with_node_uuids.iterall():
            progress.update()

            groups_uuid[group_uuid].add(node_uuid)

    return groups_uuid


# THESE FUNCTIONS ARE ONLY ADDED FOR BACK-COMPATIBILITY


def export_tree(
    entities: Optional[Iterable[Any]] = None,
    folder: Optional[Union[Folder, ZipFolder]] = None,
    allowed_licenses: Optional[Union[list, Callable]] = None,
    forbidden_licenses: Optional[Union[list, Callable]] = None,
    silent: bool = False,
    include_comments: bool = True,
    include_logs: bool = True,
    **traversal_rules: bool,
) -> None:
    """Export the entries passed in the 'entities' list to a file tree.
    .. deprecated:: 1.2.1
        Support for the parameter `what` will be removed in `v2.0.0`. Please use `entities` instead.
    :param entities: a list of entity instances; they can belong to different models/entities.

    :param folder: a temporary folder to build the archive before compression.

    :param allowed_licenses: List or function. If a list, then checks whether all licenses of Data nodes are in the
        list. If a function, then calls function for licenses of Data nodes expecting True if license is allowed, False
        otherwise.

    :param forbidden_licenses: List or function. If a list, then checks whether all licenses of Data nodes are in the
        list. If a function, then calls function for licenses of Data nodes expecting True if license is allowed, False
        otherwise.

    :param silent: suppress console prints and progress bar.

    :param include_comments: In-/exclude export of comments for given node(s) in ``entities``.
        Default: True, *include* comments in export (as well as relevant users).

    :param include_logs: In-/exclude export of logs for given node(s) in ``entities``.
        Default: True, *include* logs in export.

    :param traversal_rules: graph traversal rules. See :const:`aiida.common.links.GraphTraversalRules` what rule names
        are toggleable and what the defaults are.

    :raises `~aiida.tools.importexport.common.exceptions.ArchiveExportError`: if there are any internal errors when
        exporting.
    :raises `~aiida.common.exceptions.LicensingException`: if any node is licensed under forbidden license.
    """
    warnings.warn(
        'function is deprecated and will be removed in AiiDA v2.0.0, use `export` instead', AiidaDeprecationWarning
    )  # pylint: disable=no-member
    export(
        entities=entities,
        filename='none',
        overwrite=True,
        file_format='folder',
        allowed_licenses=allowed_licenses,
        forbidden_licenses=forbidden_licenses,
        silent=silent,
        include_comments=include_comments,
        include_logs=include_logs,
        writer_init={'folder': folder},
        **traversal_rules,
    )


def export_zip(
    entities: Optional[Iterable[Any]] = None,
    filename: Optional[str] = None,
    use_compression: bool = True,
    **kwargs: Any,
) -> Tuple[float, float]:
    """Export in a zipped folder

    .. deprecated:: 1.2.1
        Support for the parameters `what` and `outfile` will be removed in `v2.0.0`.
        Please use `entities` and `filename` instead, respectively.

    :param entities: a list of entity instances; they can belong to different models/entities.

    :param filename: the filename
        (possibly including the absolute path) of the file on which to export.

    :param use_compression: Whether or not to compress the zip file.

    """
    warnings.warn(
        'function is deprecated and will be removed in AiiDA v2.0.0, use `export` instead', AiidaDeprecationWarning
    )  # pylint: disable=no-member
    report = export(
        entities=entities,
        filename=filename,
        file_format=ExportFileFormat.ZIP,
        use_compression=use_compression,
        **kwargs,
    )
    if report.time_write_stop is not None:
        return (report.time_collect_start, report.time_write_stop)

    # there was no data to write
    return (report.time_collect_start, report.time_collect_stop)


def export_tar(
    entities: Optional[Iterable[Any]] = None,
    filename: Optional[str] = None,
    **kwargs: Any,
) -> Tuple[float, float, float, float]:
    """Export the entries passed in the 'entities' list to a gzipped tar file.

    .. deprecated:: 1.2.1
        Support for the parameters `what` and `outfile` will be removed in `v2.0.0`.
        Please use `entities` and `filename` instead, respectively.

    :param entities: a list of entity instances; they can belong to different models/entities.

    :param filename: the filename (possibly including the absolute path)
        of the file on which to export.
    """
    warnings.warn(
        'function is deprecated and will be removed in AiiDA v2.0.0, use `export` instead', AiidaDeprecationWarning
    )  # pylint: disable=no-member
    report = export(
        entities=entities,
        filename=filename,
        file_format=ExportFileFormat.TAR_GZIPPED,
        **kwargs,
    )

    if report.writer_data is not None:
        return (
            report.time_collect_start, report.time_write_stop, report.writer_data['compression_time_start'],
            report.writer_data['compression_time_stop']
        )  # type: ignore

    # there was no data to write
    return (report.time_collect_start, report.time_collect_stop, report.time_collect_stop, report.time_collect_stop)
