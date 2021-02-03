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
from copy import deepcopy
import os
from pathlib import Path
import shelve
import shutil
import time
import tempfile
from types import TracebackType
from typing import Any, cast, Dict, List, Optional, Type, Union
import zipfile

from archive_path import TarPath, ZipPath

from aiida.common import json
from aiida.common.exceptions import InvalidOperation
from aiida.common.folders import Folder
from aiida.tools.importexport.archive.common import ArchiveMetadata
from aiida.tools.importexport.common.config import (
    EXPORT_VERSION, NODE_ENTITY_NAME, NODES_EXPORT_SUBFOLDER, ExportFileFormat
)
from aiida.tools.importexport.common.utils import export_shard_uuid

__all__ = ('ArchiveWriterAbstract', 'get_writer', 'WriterJsonZip', 'WriterJsonTar', 'WriterJsonFolder')


def get_writer(file_format: str) -> Type['ArchiveWriterAbstract']:
    """Return the available writer classes."""
    writers = {
        ExportFileFormat.ZIP: WriterJsonZip,
        ExportFileFormat.TAR_GZIPPED: WriterJsonTar,
        'folder': WriterJsonFolder,
        'null': WriterNull,
    }

    if file_format not in writers:
        raise ValueError(
            f'Can only write in the formats: {tuple(writers.keys())}, not {file_format}, '
            'please specify one for "file_format".'
        )

    return cast(Type[ArchiveWriterAbstract], writers[file_format])


class ArchiveWriterAbstract(ABC):
    """An abstract interface for AiiDA archive writers."""

    def __init__(self, filepath: Union[str, Path], **kwargs: Any):
        """Initiate the writer.

        :param filepath: the path to the file to export to.
        :param kwargs: keyword arguments specific to the writer implementation.

        """
        # pylint: disable=unused-argument
        self._filepath = Path(filepath)
        self._info: Dict[str, Any] = {}
        self._in_context: bool = False

    @property
    def filepath(self) -> Path:
        """Return the filepath to write to."""
        return self._filepath

    @property
    def export_info(self) -> Dict[str, Any]:
        """Return information stored during the export process."""
        return deepcopy(self._info)

    @property
    @abstractmethod
    def file_format_verbose(self) -> str:
        """Return the file format name."""

    @property
    @abstractmethod
    def export_version(self) -> str:
        """Return the export version."""

    def __enter__(self) -> 'ArchiveWriterAbstract':
        """Open the contextmanager """
        self._in_context = True
        # reset the export information
        self._info = {'writer_entered': time.time()}
        self.open()
        return self

    def __exit__(
        self, exctype: Optional[Type[BaseException]], excinst: Optional[BaseException], exctb: Optional[TracebackType]
    ):
        """Open the contextmanager """
        self.close(exctype is not None)
        self._in_context = False
        self._info['writer_exited'] = time.time()
        return False

    def assert_within_context(self):
        """Assert that the method is called within a context.

        :raises: `~aiida.common.exceptions.InvalidOperation`: if not called within a context
        """
        if not self._in_context:
            raise InvalidOperation('the ArchiveReader method should be used within a context')

    def add_export_info(self, key: str, value: Any):
        """Record information about the export process.

        This information can be accessed by ``writer.export_info``,
        it is reset on entrance of the context manager.

        """
        self._info[key] = value

    def _remove_filepath(self):
        """To run before moving the final export from a temporary folder."""
        if self.filepath.exists():
            if self.filepath.is_file():
                self.filepath.unlink()
            else:
                shutil.rmtree(str(self.filepath))

    # initialise/finalise methods

    @abstractmethod
    def open(self):
        """Setup the export process.

        This method is called on entering a context manager.

        """

    @abstractmethod
    def close(self, excepted: bool):
        """Finalise the export.

        This method is called on exiting a context manager.

        :param excepted: Whether

        """

    # write methods

    @abstractmethod
    def write_metadata(self, data: ArchiveMetadata):
        """Write the metadata of the export process."""

    @abstractmethod
    def write_link(self, data: Dict[str, str]):
        """Write a dictionary of information for a single provenance link.

        :param data: ``{'input': <UUID_STR>, 'output': <UUID_STR>, 'label': <LABEL_STR>, 'type': <TYPE_STR>}``

        """

    @abstractmethod
    def write_group_nodes(self, uuid: str, node_uuids: List[str]):
        """Write a mapping of a group to the nodes it contains.

        :param uuid: the UUID of the group
        :param node_uuids: the list of node UUIDs the group contains

        """

    @abstractmethod
    def write_entity_data(self, name: str, pk: int, id_key: str, fields: Dict[str, Any]):
        """Write the data for a single DB entity.

        :param name: the name of the entity (e.g. 'NODE')
        :param pk: the primary key of the entity (unique for the current DB only)
        :param id_key: the key within ``fields`` that denotes the unique identifier of the entity (unique for all DBs)
        :param fields: mapping of DB fields to store -> values

        """

    @abstractmethod
    def write_node_repo_folder(self, uuid: str, path: Union[str, Path], overwrite: bool = True):
        """Write a node repository to the archive.

        :param uuid: The UUID of the node
        :param path: The path to the repository folder on disk
        :param overwrite: Allow to overwrite existing path in archive

        """


class WriterNull(ArchiveWriterAbstract):
    """A null archive writer, which does not do anything."""

    @property
    def file_format_verbose(self) -> str:
        return 'Null'

    @property
    def export_version(self) -> str:
        return EXPORT_VERSION

    def open(self):
        pass

    def close(self, excepted: bool):
        pass

    def write_metadata(self, data: ArchiveMetadata):
        pass

    def write_link(self, data: Dict[str, str]):
        pass

    def write_group_nodes(self, uuid: str, node_uuids: List[str]):
        pass

    def write_entity_data(self, name: str, pk: int, id_key: str, fields: Dict[str, Any]):
        pass

    def write_node_repo_folder(self, uuid: str, path: Union[str, Path], overwrite: bool = True):
        pass


class WriterJsonZip(ArchiveWriterAbstract):
    """An archive writer,
    which writes database data as a single JSON and repository data in a zipped folder system.
    """

    def __init__(
        self, filepath: Union[str, Path], *, use_compression: bool = True, cache_zipinfo: bool = False, **kwargs
    ):
        """Initiate the writer.

        :param filepath: the path to the file to export to.
        :param use_compression: Whether or not to deflate the objects inside the zip file.
        :param cache_zipinfo: Cache the zip file index on disk during the write.
            This reduces the RAM usage of the process, but will make the process slower.

        """
        super().__init__(filepath)
        self._compression = zipfile.ZIP_DEFLATED if use_compression else zipfile.ZIP_STORED
        self._cache_zipinfo = cache_zipinfo

    @property
    def file_format_verbose(self) -> str:
        return f'JSON Zip (compression={self._compression})'

    @property
    def export_version(self) -> str:
        return EXPORT_VERSION

    def open(self):
        # pylint: disable=attribute-defined-outside-init
        self.assert_within_context()
        # create a temporary folder in which to perform the write
        self._temp_path: Path = Path(tempfile.mkdtemp())
        # open a zipfile in in write mode to export to
        self._zipinfo_cache: Optional[dict]
        if self._cache_zipinfo:
            self._zipinfo_cache = shelve.open(str(self._temp_path / 'zipinfo_cache'))  # type: ignore
        else:
            self._zipinfo_cache = None
        self._archivepath: ZipPath = ZipPath(
            self._temp_path / 'export', mode='w', compression=self._compression, name_to_info=self._zipinfo_cache
        )
        # setup data to store
        self._data: Dict[str, Any] = {
            'node_attributes': {},
            'node_extras': {},
            'export_data': {},
            'links_uuid': [],
            'groups_uuid': {},
        }

    def close(self, excepted: bool):
        self.assert_within_context()
        if excepted:
            self._archivepath.close()
            shutil.rmtree(self._temp_path)
            return
        # write data.json
        with self._archivepath.joinpath('data.json').open('wb') as handle:
            json.dump(self._data, handle)
        # close the zipfile to finalise write
        self._archivepath.close()
        if getattr(self, '_zipinfo_cache', None) is not None:
            self._zipinfo_cache.close()  # type: ignore
            delattr(self, '_zipinfo_cache')
        # move the compressed file to the final path
        self._remove_filepath()
        shutil.move(str(self._archivepath.filepath), str(self.filepath))
        # remove the temporary folder
        shutil.rmtree(self._temp_path)

    def write_metadata(self, data: ArchiveMetadata):
        metadata = {
            'export_version': self.export_version,
            'aiida_version': data.aiida_version,
            'all_fields_info': data.all_fields_info,
            'unique_identifiers': data.unique_identifiers,
            'export_parameters': {
                'graph_traversal_rules': data.graph_traversal_rules,
                'entities_starting_set': data.entities_starting_set,
                'include_comments': data.include_comments,
                'include_logs': data.include_logs,
            },
            'conversion_info': data.conversion_info
        }
        with self._archivepath.joinpath('metadata.json').open('wb') as handle:
            json.dump(metadata, handle)

    def write_link(self, data: Dict[str, str]):
        self._data['links_uuid'].append(data)

    def write_group_nodes(self, uuid: str, node_uuids: List[str]):
        self._data['groups_uuid'][uuid] = node_uuids

    def write_entity_data(self, name: str, pk: int, id_key: str, fields: Dict[str, Any]):
        if name == NODE_ENTITY_NAME:
            # perform translation to current internal format
            self._data['node_attributes'][pk] = fields.pop('attributes')
            self._data['node_extras'][pk] = fields.pop('extras')
        self._data['export_data'].setdefault(name, {})[pk] = fields

    def write_node_repo_folder(self, uuid: str, path: Union[str, Path], overwrite: bool = True):
        self.assert_within_context()
        (self._archivepath / NODES_EXPORT_SUBFOLDER / export_shard_uuid(uuid)).puttree(path, check_exists=not overwrite)


class WriterJsonTar(ArchiveWriterAbstract):
    """An archive writer,
    which writes database data as a single JSON and repository data in a folder system.

    The entire containing folder is then compressed as a tar file.
    """

    @property
    def file_format_verbose(self) -> str:
        return 'Gzipped tarball (compressed)'

    @property
    def export_version(self) -> str:
        return EXPORT_VERSION

    def open(self):
        # pylint: disable=attribute-defined-outside-init
        self.assert_within_context()
        # create a temporary folder in which to perform the write
        self._temp_path: Path = Path(tempfile.mkdtemp())
        # open a zipfile in in write mode to export to
        self._archivepath: TarPath = TarPath(self._temp_path / 'export', mode='w:gz', dereference=True)
        # setup data to store
        self._data: Dict[str, Any] = {
            'node_attributes': {},
            'node_extras': {},
            'export_data': {},
            'links_uuid': [],
            'groups_uuid': {},
        }

    def close(self, excepted: bool):
        self.assert_within_context()
        if excepted:
            self._archivepath.close()
            shutil.rmtree(self._temp_path)
            return
        # write data.json
        with self._archivepath.joinpath('data.json').open('wb') as handle:
            json.dump(self._data, handle)
        # compress
        # close the zipfile to finalise write
        self._archivepath.close()
        # move the compressed file to the final path
        self._remove_filepath()
        shutil.move(str(self._archivepath.filepath), str(self.filepath))
        # remove the temporary folder
        shutil.rmtree(self._temp_path)

    def write_metadata(self, data: ArchiveMetadata):
        metadata = {
            'export_version': self.export_version,
            'aiida_version': data.aiida_version,
            'all_fields_info': data.all_fields_info,
            'unique_identifiers': data.unique_identifiers,
            'export_parameters': {
                'graph_traversal_rules': data.graph_traversal_rules,
                'entities_starting_set': data.entities_starting_set,
                'include_comments': data.include_comments,
                'include_logs': data.include_logs,
            },
            'conversion_info': data.conversion_info
        }
        with self._archivepath.joinpath('metadata.json').open('wb') as handle:
            json.dump(metadata, handle)

    def write_link(self, data: Dict[str, str]):
        self._data['links_uuid'].append(data)

    def write_group_nodes(self, uuid: str, node_uuids: List[str]):
        self._data['groups_uuid'][uuid] = node_uuids

    def write_entity_data(self, name: str, pk: int, id_key: str, fields: Dict[str, Any]):
        if name == NODE_ENTITY_NAME:
            # perform translation to current internal format
            self._data['node_attributes'][pk] = fields.pop('attributes')
            self._data['node_extras'][pk] = fields.pop('extras')
        self._data['export_data'].setdefault(name, {})[pk] = fields

    def write_node_repo_folder(self, uuid: str, path: Union[str, Path], overwrite: bool = True):
        self.assert_within_context()
        (self._archivepath / NODES_EXPORT_SUBFOLDER / export_shard_uuid(uuid)).puttree(path, check_exists=not overwrite)


class WriterJsonFolder(ArchiveWriterAbstract):
    """An archive writer,
    which writes database data as a single JSON and repository data in a folder system.

    This writer is mainly intended for backward compatibility with `export_tree`.
    """

    def __init__(self, filepath: str, folder: Folder = None, **kwargs: Any):
        """Initiate the writer.

        :param folder: a folder to write the archive to.
        :param filepath: dummy value not used

        """
        super().__init__(filepath, **kwargs)
        if not isinstance(folder, Folder):
            raise TypeError('`folder` must be specified and given as an AiiDA Folder entity')
        self._folder = cast(Folder, folder)

    @property
    def file_format_verbose(self) -> str:
        return 'JSON Folder'

    @property
    def export_version(self) -> str:
        return EXPORT_VERSION

    def open(self):
        # pylint: disable=attribute-defined-outside-init
        self.assert_within_context()
        # setup data to store
        self._data: Dict[str, Any] = {
            'node_attributes': {},
            'node_extras': {},
            'export_data': {},
            'links_uuid': [],
            'groups_uuid': {},
        }
        # ensure folder is created
        self._folder.create()

    def close(self, excepted: bool):
        self.assert_within_context()
        if excepted:
            return
        with self._folder.open('data.json', 'wb') as handle:
            json.dump(self._data, handle)

    def write_metadata(self, data: ArchiveMetadata):
        metadata = {
            'export_version': self.export_version,
            'aiida_version': data.aiida_version,
            'all_fields_info': data.all_fields_info,
            'unique_identifiers': data.unique_identifiers,
            'export_parameters': {
                'graph_traversal_rules': data.graph_traversal_rules,
                'entities_starting_set': data.entities_starting_set,
                'include_comments': data.include_comments,
                'include_logs': data.include_logs,
            },
            'conversion_info': data.conversion_info
        }
        with self._folder.open('metadata.json', 'wb') as handle:
            json.dump(metadata, handle)

    def write_link(self, data: Dict[str, str]):
        self._data['links_uuid'].append(data)

    def write_group_nodes(self, uuid: str, node_uuids: List[str]):
        self._data['groups_uuid'][uuid] = node_uuids

    def write_entity_data(self, name: str, pk: int, id_key: str, fields: Dict[str, Any]):
        if name == NODE_ENTITY_NAME:
            # perform translation to current internal format
            self._data['node_attributes'][pk] = fields.pop('attributes')
            self._data['node_extras'][pk] = fields.pop('extras')
        self._data['export_data'].setdefault(name, {})[pk] = fields

    def write_node_repo_folder(self, uuid: str, path: Union[str, Path], overwrite: bool = True):
        self.assert_within_context()
        repo_folder = self._folder.get_subfolder(NODES_EXPORT_SUBFOLDER).get_subfolder(export_shard_uuid(uuid))
        repo_folder.insert_path(src=os.path.abspath(path), dest_name='.', overwrite=overwrite)
