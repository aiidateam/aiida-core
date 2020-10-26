# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Archive writer classes."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import time
import tarfile
from typing import Any, Callable, cast, Dict, Iterable, List, Set, Tuple, Type, Union

from aiida.common.folders import Folder, SandboxFolder
from aiida.common.progress_reporter import get_progress_reporter
from aiida.tools.importexport.archive.common import ArchiveMetadata
from aiida.tools.importexport.common.config import EXPORT_VERSION, NODES_EXPORT_SUBFOLDER, ExportFileFormat
from aiida.tools.importexport.common.utils import export_shard_uuid
from aiida.tools.importexport.common.zip_folder import ZipFolder

__all__ = ('ArchiveData', 'ArchiveWriterAbstract', 'get_writer', 'WriterJsonFolder', 'WriterJsonTar', 'WriterJsonZip')


def get_writer(file_format: str) -> Type['ArchiveWriterAbstract']:
    """Return the available writer classes."""
    writers = {
        ExportFileFormat.ZIP: WriterJsonZip,
        ExportFileFormat.TAR_GZIPPED: WriterJsonTar,
        'folder': WriterJsonFolder,
    }

    if file_format not in writers:
        raise ValueError(
            f'Can only write in the formats: {tuple(writers.keys())}, please specify one for "file_format".'
        )

    return cast(Type[ArchiveWriterAbstract], writers[file_format])


@dataclass
class ArchiveData:
    """Class for storing data, to export to an AiiDA archive."""
    metadata: ArchiveMetadata
    node_uuids: Set[str]
    # UUID of the group -> UUIDs of the entities it contains
    group_uuids: Dict[str, Set[str]]
    # list of {'input': <UUID>, 'output': <UUID>, 'label': <LABEL>, 'type': <TYPE>}
    link_uuids: List[dict]
    # all entity data from the database, except Node extras and attributes
    # {'ENTITY_NAME': {<Pk>: {'db_key': 'value', ...}, ...}, ...}
    entity_data: Dict[str, Dict[int, dict]]
    # Iterable of Node (uuid, attributes, extras)
    node_data: Iterable[Tuple[str, dict, dict]]
    # Iterable of Group (uuid, extras)
    group_data: Iterable[Tuple[str, dict]]

    def __repr__(self) -> str:
        """Return string representation."""
        return f'ArchiveData(metadata={self.metadata},' + ','.join(
            f'#{k}={len(v)}' for k, v in self.entity_data.items()
        ) + ')'


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
    def write(self, export_data: ArchiveData, get_node_repo: Callable[[str], Folder]) -> dict:
        """write the archive.

        :param export_data: The data to export
        :param get_node_repo: A callable: UUID -> to a folder of the node's repository
        :returns: A dictionary of data about the write process

        """


def _write_to_json_archive(
    folder: Union[Folder, ZipFolder], export_data: ArchiveData, export_version: str, get_node_repo: Callable[[str],
                                                                                                             Folder]
) -> None:
    """Write data to the archive."""
    # subfolder inside the export package
    nodesubfolder = folder.get_subfolder(NODES_EXPORT_SUBFOLDER, create=True, reset_limit=True)

    data: Dict[str, Any] = {
        'node_attributes': {},
        'node_extras': {},
        'export_data': export_data.entity_data,
        'links_uuid': export_data.link_uuids,
        'groups_uuid': {key: list(vals) for key, vals in export_data.group_uuids.items()},
        'group_extras': {},
    }

    for uuid, attributes, extras in export_data.node_data:
        data['node_attributes'][uuid] = attributes
        data['node_extras'][uuid] = extras

    for uuid, extras in export_data.group_data:
        data['group_extras'][uuid] = extras

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
        'conversion_info': export_data.metadata.conversion_info
    }

    with folder.open('metadata.json', 'w') as fhandle:
        fhandle.write(json.dumps(metadata))

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
            src_folder = get_node_repo(uuid)
            # In this way, I copy the content of the folder, and not the folder itself
            thisnodefolder.insert_path(src=src_folder.abspath, dest_name='.')


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

    def write(self, export_data: ArchiveData, get_node_repo: Callable[[str], Folder]) -> dict:
        """write the archive

        :param export_data: The data to export
        :returns: A dictionary of data about the write process

        """
        with ZipFolder(self.filename, mode='w', use_compression=self._use_compression) as folder:
            _write_to_json_archive(
                folder=folder,
                export_data=export_data,
                export_version=self.export_version,
                get_node_repo=get_node_repo,
            )

        return {}


class WriterJsonTar(ArchiveWriterAbstract):
    """An archive writer,
    which writes database data as a single JSON and repository data in a folder system.

    The entire containing folder is then compressed as a tar file.
    """

    def __init__(self, filename: str, sandbox_in_repo: bool = True, **kwargs: Any):
        """A writer for zipped archives.

        :param filename: the filename (possibly including the absolute path)
            of the file on which to export.
        :param sandbox_in_repo: Create the temporary uncompressed folder within the aiida repository

        """
        super().__init__(filename, **kwargs)
        self.sandbox_in_repo = sandbox_in_repo

    @property
    def file_format_verbose(self) -> str:
        return 'Gzipped tarball (compressed)'

    @property
    def export_version(self) -> str:
        return EXPORT_VERSION

    def write(self, export_data: ArchiveData, get_node_repo: Callable[[str], Folder]) -> dict:
        """write the archive

        :param export_data: The data to export
        :returns: A dictionary of data about the write process

        """
        with SandboxFolder(sandbox_in_repo=self.sandbox_in_repo) as folder:
            _write_to_json_archive(
                folder=folder,
                export_data=export_data,
                export_version=self.export_version,
                get_node_repo=get_node_repo,
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
        if not isinstance(folder, (Folder, ZipFolder)):
            raise TypeError('`folder` must be specified and given as an AiiDA Folder entity')
        self._folder = cast(Union[Folder, ZipFolder], folder)

    @property
    def file_format_verbose(self) -> str:
        return str(self._folder.__class__)

    @property
    def export_version(self) -> str:
        return EXPORT_VERSION

    def write(self, export_data: ArchiveData, get_node_repo: Callable[[str], Folder]) -> dict:
        """write the archive

        :param export_data: The data to export
        :returns: A dictionary of data about the write process

        """
        _write_to_json_archive(
            folder=self._folder,
            export_data=export_data,
            export_version=self.export_version,
            get_node_repo=get_node_repo,
        )

        return {}
