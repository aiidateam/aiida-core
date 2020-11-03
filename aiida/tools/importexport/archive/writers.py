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
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import time
import tarfile
import tempfile
from types import TracebackType
from typing import Any, Callable, cast, Dict, Iterable, List, Optional, Set, Tuple, Type, Union
import zipfile

from aiida.common import json
from aiida.common.exceptions import InvalidOperation
from aiida.common.folders import Folder, SandboxFolder
from aiida.common.progress_reporter import get_progress_reporter
from aiida.tools.importexport.archive.common import ArchiveMetadata
from aiida.tools.importexport.common.config import EXPORT_VERSION, NODE_ENTITY_NAME, NODES_EXPORT_SUBFOLDER, ExportFileFormat
from aiida.tools.importexport.common.utils import export_shard_uuid
from aiida.tools.importexport.archive.zip_path import ZipPath

__all__ = ('ArchiveWriterAbstract', 'get_writer', 'WriterJsonZip', )#'WriterJsonTar', 'WriterJsonFolder')


def get_writer(file_format: str) -> Type['ArchiveWriterAbstract']:
    """Return the available writer classes."""
    writers = {
        ExportFileFormat.ZIP: WriterJsonZip,
        # ExportFileFormat.TAR_GZIPPED: WriterJsonTar,
        # 'folder': WriterJsonFolder,
    }

    if file_format not in writers:
        raise ValueError(
            f'Can only write in the formats: {tuple(writers.keys())}, please specify one for "file_format".'
        )

    return cast(Type[ArchiveWriterAbstract], writers[file_format])


class ArchiveWriterAbstract(ABC):
    """An abstract interface for AiiDA archive writers."""

    def __init__(self, filepath: Union[str, Path], **kwargs: Any):
        """An archive writer

        :param filepath: the path to the file to export to.
        :param kwargs: keyword arguments specific to the writer implementation.

        """
        # pylint: disable=unused-argument
        self._filepath = Path(filepath)
        self._info: Dict[str, Any] = {}

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
        self._info = {}
        self.open()
        return self

    def __exit__(
        self, exctype: Optional[Type[BaseException]], excinst: Optional[BaseException], exctb: Optional[TracebackType]
    ):
        """Open the contextmanager """
        self.close(exctype is not None)
        self._in_context = False
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
    def write_node_repo_folder(self, uuid: str, path: Union[str, Path]):
        """Write a node repository to the archive.
        
        :param uuid: The UUID of the node
        :param path: The path to the repository folder

        """

class WriterJsonZip(ArchiveWriterAbstract):
    
    def __init__(self, filepath: Union[str, Path], *, use_compression: bool = True):
        """An archive writer.

        :param filepath: the path to the file to export to.
        :param use_compression: Whether or not to deflate the objects inside the zip file.

        """
        super().__init__(filepath)
        self._compression = zipfile.ZIP_DEFLATED if use_compression else zipfile.ZIP_STORED

    @property
    def file_format_verbose(self) -> str:
        return f'Zip (compression={self._compression})'

    @property
    def export_version(self) -> str:
        return EXPORT_VERSION

    def open(self):
        self.assert_within_context()
        # create the zipfile in which to write the export
        self._temp_path: Path = Path(tempfile.mkdtemp())
        self._zippath: ZipPath = ZipPath(self._temp_path / 'export', mode='w', compression=self._compression)
        # setup data to store
        self._data: Dict[str, Any] = {
            'node_attributes': {},
            'node_extras': {},
            'export_data': {},
            'links_uuid': [],
            'groups_uuid': {},
        }

    def close(self, excepted: bool):
        # TODO this doubles memory
        self._zippath.joinpath('data.json').write_text(json.dumps(self._data))
        self._zippath.close() 
        shutil.move(self._zippath.filepath, self.filepath)
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
        self._zippath.joinpath('metadata.json').write_text(json.dumps(metadata))

    def write_link(self, data: Dict[str, str]):
        self._data['links_uuid'].append(data)

    def write_group_nodes(self, uuid: str, node_uuids: List[str]):
        self._data['groups_uuid'][uuid] = node_uuids

    def write_entity_data(self, name: str, pk: int, id_key: str, fields: Dict[str, Any]):
        if name == NODE_ENTITY_NAME:
            self._data['node_attributes'][pk] = fields.pop('attributes')
            self._data['node_extras'][pk] = fields.pop('extras')
        self._data['export_data'].setdefault(name, {})[pk] = fields
    
    def write_node_repo_folder(self, uuid: str, path: Path):
        self.assert_within_context()
        (self._zippath / export_shard_uuid(uuid)).copytree(path)


# class WriterJsonBase(ArchiveWriterAbstract):

#     def open(self):
#         self.assert_within_context()
#         self._metadata: dict = {}
#         self._entity_data: Dict[str, Dict[str, Dict[str, Any]]] = {}
#         self._link_uuids: List[Dict[str, str]] = []
#         self._group_uuids: Dict[str, List[str]] = {}
#         self._temp_path: Path = Path(tempfile.mkdtemp())
#         self._repo_path: Path = (self._temp_path / NODES_EXPORT_SUBFOLDER)
#         self._repo_path.mkdir()

#     def close(self, excepted: bool):
#         self.assert_within_context()
#         shutil.rmtree(self._temp_path)

#     def export(self):
#         self.assert_within_context()

#         (self._temp_path / 'metadata.json').write_text(json.dumps(self._metadata), encoding='utf8')

#         node_attributes: Dict[str, dict] = {}
#         node_extras: Dict[str, dict] = {}
#         for pk, fields in self._entity_data.get(NODE_ENTITY_NAME, {}).items():
#             node_attributes[pk] = fields.pop('attributes')
#             node_extras[pk] = fields.pop('extras')

#         data: Dict[str, Any] = {
#             'node_attributes': node_attributes,
#             'node_extras': node_extras,
#             'export_data': self._entity_data,
#             'links_uuid': self._link_uuids,
#             'groups_uuid': self._group_uuids,
#         }
#         (self._temp_path / 'data.json').write_text(json.dumps(data), encoding='utf8')

#         self._write_to_output(self._temp_path)

#     def _write_to_output(self, path: Path):
#         raise NotImplementedError('must be subclassed')

#     def write_metadata(self, metadata: ArchiveMetadata):
#         self._metadata = {
#             'export_version': self.export_version,
#             'aiida_version': metadata.aiida_version,
#             'all_fields_info': metadata.all_fields_info,
#             'unique_identifiers': metadata.unique_identifiers,
#             'export_parameters': {
#                 'graph_traversal_rules': metadata.graph_traversal_rules,
#                 'entities_starting_set': metadata.entities_starting_set,
#                 'include_comments': metadata.include_comments,
#                 'include_logs': metadata.include_logs,
#             },
#             'conversion_info': metadata.conversion_info
#         }

#     def write_link(self, data: Dict[str, str]):
#         # input: str, output: str, label: str, type: str
#         self._link_uuids.append(data)

#     def write_group_uuids(self, uuid: str, node_uuids: List[str]):
#         self._group_uuids[uuid] = node_uuids

#     def write_entity_data(self, name: str, pk: str, fields: Dict[str, Any]):
#         self._entity_data.setdefault(name, {})[pk] = fields

#     def copy_node_repository(self, uuid: str, path: Path):
#         self.assert_within_context()
#         repo_path = self._repo_path / export_shard_uuid(uuid)
#         shutil.copytree(path, repo_path)


# class WriterJsonZip(WriterJsonBase):
#     """An archive writer,
#     which writes database data as a single JSON and repository data in a zipped folder system.
#     """

#     def __init__(self, filename: str, use_compression: bool = True, **kwargs: Any):
#         """A writer for zipped archives.

#         :param filename: the filename (possibly including the absolute path)
#             of the file on which to export.
#         :param use_compression: Whether or not to compress the zip file.

#         """
#         super().__init__(filename, **kwargs)
#         self._use_compression = use_compression

#     @property
#     def file_format_verbose(self) -> str:
#         return 'Zip (compressed)' if self._use_compression else 'Zip (uncompressed)'

#     @property
#     def export_version(self) -> str:
#         return EXPORT_VERSION

#     def open(self):
#         self.assert_within_context()
#         self._metadata: dict = {}
#         self._entity_data: Dict[str, Dict[str, Dict[str, Any]]] = {}
#         self._link_uuids: List[Dict[str, str]] = []
#         self._group_uuids: Dict[str, List[str]] = {}
#         self._temp_path: Path = Path(tempfile.mkdtemp())
#         self._temp_file: Path = self._temp_path / 'out.aiida'
#         self._zip_path: ZipFolder = ZipFolder(self._temp_file, mode='w', use_compression=self._use_compression)
#         self._repo_path: ZipFolder = self._zip_path / NODES_EXPORT_SUBFOLDER

#     def export(self):
#         self.assert_within_context()

#         (self._zip_path / 'metadata.json').write_text(json.dumps(self._metadata))

#         node_attributes: Dict[str, dict] = {}
#         node_extras: Dict[str, dict] = {}
#         for pk, fields in self._entity_data.get(NODE_ENTITY_NAME, {}).items():
#             node_attributes[pk] = fields.pop('attributes')
#             node_extras[pk] = fields.pop('extras')

#         data: Dict[str, Any] = {
#             'node_attributes': node_attributes,
#             'node_extras': node_extras,
#             'export_data': self._entity_data,
#             'links_uuid': self._link_uuids,
#             'groups_uuid': self._group_uuids,
#         }
#         (self._zip_path / 'data.json').write_text(json.dumps(data))

#         shutil.move(self._temp_file, self.filepath)

#     def copy_node_repository(self, uuid: str, path: Path):
#         self.assert_within_context()
#         folder = self._repo_path.get_subfolder(export_shard_uuid(uuid), create=False, reset_limit=True)
#         folder.insert_path(src=os.path.abspath(path), dest_name='.')

#     # def _write_to_output(self, path: Path):
#     #     if self._use_compression:
#     #         compression = zipfile.ZIP_DEFLATED
#     #     else:
#     #         compression = zipfile.ZIP_STORED

#     #     self.add_info('compression_time_start', time.time())
#     #     with zipfile.ZipFile(self.filepath, mode='w', compression=compression, allowZip64=True) as archive:
#     #         for dirpath, dirnames, filenames in os.walk(path):
#     #             relpath = os.path.relpath(dirpath, path)
#     #             for filename in dirnames + filenames:
#     #                 real_src = os.path.join(dirpath, filename)
#     #                 real_dest = os.path.join(relpath, filename)
#     #                 archive.write(real_src, real_dest)
#     #     self.add_info('compression_time_stop', time.time())


# class WriterJsonTar(WriterJsonBase):
#     """An archive writer,
#     which writes database data as a single JSON and repository data in a folder system.

#     The entire containing folder is then compressed as a tar file.
#     """

#     @property
#     def file_format_verbose(self) -> str:
#         return 'Gzipped tarball (compressed)'

#     @property
#     def export_version(self) -> str:
#         return EXPORT_VERSION

#     def _write_to_output(self, path: Path):
#         self.add_info('compression_time_start', time.time())
#         with tarfile.open(self.filepath, 'w:gz', format=tarfile.PAX_FORMAT, dereference=True) as archive:
#             archive.add(os.path.abspath(path), arcname='')
#         self.add_info('compression_time_stop', time.time())


# class WriterJsonFolder(ArchiveWriterAbstract):
#     """An archive writer,
#     which writes database data as a single JSON and repository data in a folder system.

#     This writer is mainly intended for backward compatibility with `export_tree`.
#     """

#     def __init__(self, filename: str, folder: Union[Folder, ZipFolder] = None, **kwargs: Any):
#         """A writer for zipped archives.

#         :param filename: the filename (possibly including the absolute path)
#             of the file on which to export.
#         :param folder: a folder to write the archive to.

#         """
#         super().__init__(filename, **kwargs)
#         if not isinstance(folder, (Folder, ZipFolder)):
#             raise TypeError('`folder` must be specified and given as an AiiDA Folder entity')
#         self._folder = cast(Union[Folder, ZipFolder], folder)

#     @property
#     def file_format_verbose(self) -> str:
#         return str(self._folder.__class__)

#     @property
#     def export_version(self) -> str:
#         return EXPORT_VERSION

#     def _write_to_output(self, path: Path):
#         if self.filepath.exists():
#             if self.filepath.is_file():
#                 self.filepath.unlink()
#             else:
#                 shutil.rmtree(self.filepath)
#         shutil.move(path, self.filepath)
