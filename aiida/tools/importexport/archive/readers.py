# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Archive reader classes."""
from abc import ABC, abstractmethod
import json
import os
from pathlib import Path
import tarfile
from types import TracebackType
from typing import Any, Callable, cast, Dict, Iterable, Iterator, List, Optional, Set, Tuple, Type
import zipfile

from distutils.version import StrictVersion
from archive_path import TarPath, ZipPath, read_file_in_tar, read_file_in_zip

from aiida.common.log import AIIDA_LOGGER
from aiida.common.exceptions import InvalidOperation
from aiida.common.folders import Folder, SandboxFolder
from aiida.tools.importexport.common.config import EXPORT_VERSION, ExportFileFormat, NODES_EXPORT_SUBFOLDER
from aiida.tools.importexport.common.exceptions import (CorruptArchive, IncompatibleArchiveVersionError)
from aiida.tools.importexport.archive.common import (ArchiveMetadata, null_callback)
from aiida.tools.importexport.common.config import NODE_ENTITY_NAME, GROUP_ENTITY_NAME
from aiida.tools.importexport.common.utils import export_shard_uuid

__all__ = (
    'ArchiveReaderAbstract',
    'ARCHIVE_READER_LOGGER',
    'ReaderJsonBase',
    'ReaderJsonFolder',
    'ReaderJsonTar',
    'ReaderJsonZip',
    'get_reader',
)

ARCHIVE_READER_LOGGER = AIIDA_LOGGER.getChild('archive.reader')


def get_reader(file_format: str) -> Type['ArchiveReaderAbstract']:
    """Return the available writer classes."""
    readers = {
        ExportFileFormat.ZIP: ReaderJsonZip,
        ExportFileFormat.TAR_GZIPPED: ReaderJsonTar,
        'folder': ReaderJsonFolder,
    }

    if file_format not in readers:
        raise ValueError(
            f'Can only read in the formats: {tuple(readers.keys())}, please specify one for "file_format".'
        )

    return cast(Type[ArchiveReaderAbstract], readers[file_format])


class ArchiveReaderAbstract(ABC):
    """An abstract interface for AiiDA archive readers.

    An ``ArchiveReader`` implementation is intended to be used with a context::

        with ArchiveReader(filename) as reader:
            reader.entity_count('Node')

    """

    def __init__(self, filename: str, **kwargs: Any):
        """An archive reader

        :param filename: the filename (possibly including the absolute path)
            of the file to import.

        """
        # pylint: disable=unused-argument
        self._filename = filename
        self._in_context = False

    @property
    def filename(self) -> str:
        """Return the name of the file that is being read from."""
        return self._filename

    @property
    @abstractmethod
    def file_format_verbose(self) -> str:
        """The file format name."""

    @property
    @abstractmethod
    def compatible_export_version(self) -> str:
        """Return the export version that this reader is compatible with."""

    def __enter__(self) -> 'ArchiveReaderAbstract':
        self._in_context = True
        return self

    def __exit__(
        self, exctype: Optional[Type[BaseException]], excinst: Optional[BaseException], exctb: Optional[TracebackType]
    ):
        self._in_context = False

    def assert_within_context(self):
        """Assert that the method is called within a context.

        :raises: `~aiida.common.exceptions.InvalidOperation`: if not called within a context
        """
        if not self._in_context:
            raise InvalidOperation('the ArchiveReader method should be used within a context')

    @property
    @abstractmethod
    def export_version(self) -> str:
        """Return the export version.

        :raises `~aiida.tools.importexport.common.exceptions.CorruptArchive`: If the version cannot be retrieved.
        """
        # this should be able to be returned independent of any metadata validation

    def check_version(self):
        """Check the version compatibility of the archive.

        :raises: `~aiida.tools.importexport.common.exceptions.IncompatibleArchiveVersionError`:
            If the version is not compatible

        """
        file_version = StrictVersion(self.export_version)
        expected_version = StrictVersion(self.compatible_export_version)

        try:
            if file_version != expected_version:
                msg = f'Archive file version is {file_version}, can read only version {expected_version}'
                if file_version < expected_version:
                    msg += "\nUse 'verdi export migrate' to update this archive file."
                else:
                    msg += '\nUpdate your AiiDA version in order to import this file.'

                raise IncompatibleArchiveVersionError(msg)
        except AttributeError:
            msg = (
                f'Archive file version is {self.export_version}, '
                f'can read only version {self.compatible_export_version}'
            )
            raise IncompatibleArchiveVersionError(msg)

    @property
    @abstractmethod
    def metadata(self) -> ArchiveMetadata:
        """Return the full (validated) archive metadata."""

    @property
    def entity_names(self) -> List[str]:
        """Return list of all entity names."""
        return list(self.metadata.all_fields_info.keys())

    @abstractmethod
    def entity_count(self, name: str) -> int:
        """Return the count of an entity or None if not contained in the archive."""

    @property
    @abstractmethod
    def link_count(self) -> int:
        """Return the count of links."""

    @abstractmethod
    def iter_entity_fields(self,
                           name: str,
                           fields: Optional[Tuple[str, ...]] = None) -> Iterator[Tuple[int, Dict[str, Any]]]:
        """Iterate over entities and yield their pk and database fields."""

    @abstractmethod
    def iter_node_uuids(self) -> Iterator[str]:
        """Iterate over node UUIDs."""

    @abstractmethod
    def iter_group_uuids(self) -> Iterator[Tuple[str, Set[str]]]:
        """Iterate over group UUIDs and the a set of node UUIDs they contain."""

    @abstractmethod
    def iter_link_data(self) -> Iterator[dict]:
        """Iterate over links: {'input': <UUID>, 'output': <UUID>, 'label': <LABEL>, 'type': <TYPE>}"""

    @abstractmethod
    def iter_node_repos(
        self,
        uuids: Iterable[str],
        callback: Callable[[str, Any], None] = null_callback,
    ) -> Iterator[Folder]:
        """Yield temporary folders containing the contents of the repository for each node.

        :param uuids: UUIDs of the nodes over whose repository folders to iterate
        :param callback: a callback to report on the process, ``callback(action, value)``,
            with the following callback signatures:

            - ``callback('init', {'total': <int>, 'description': <str>})``,
               to signal the start of a process, its total iterations and description
            - ``callback('update', <int>)``,
               to signal an update to the process and the number of iterations to progress

        :raises `~aiida.tools.importexport.common.exceptions.CorruptArchive`: If the repository does not exist.
        """

    def node_repository(self, uuid: str) -> Folder:
        """Return a temporary folder with the contents of the repository for a single node.

        :param uuid: The UUID of the node

        :raises `~aiida.tools.importexport.common.exceptions.CorruptArchive`: If the repository does not exist.
        """
        return next(self.iter_node_repos([uuid]))


class ReaderJsonBase(ArchiveReaderAbstract):
    """A reader base for the JSON compressed formats."""

    FILENAME_DATA = 'data.json'
    FILENAME_METADATA = 'metadata.json'
    REPO_FOLDER = NODES_EXPORT_SUBFOLDER

    def __init__(self, filename: str, sandbox_in_repo: bool = False, **kwargs: Any):
        """A reader for JSON compressed archives.

        :param filename: the filename (possibly including the absolute path)
            of the file on which to export.
        :param sandbox_in_repo: Create the temporary uncompressed folder within the aiida repository

        """
        super().__init__(filename, **kwargs)
        self._metadata = None
        self._data = None
        # a temporary folder used to extract the file tree
        self._sandbox: Optional[SandboxFolder] = None
        self._sandbox_in_repo = sandbox_in_repo

    @property
    def file_format_verbose(self) -> str:
        raise NotImplementedError()

    @property
    def compatible_export_version(self) -> str:
        return EXPORT_VERSION

    def __enter__(self):
        super().__enter__()
        self._sandbox = SandboxFolder(self._sandbox_in_repo)
        return self

    def __exit__(
        self, exctype: Optional[Type[BaseException]], excinst: Optional[BaseException], exctb: Optional[TracebackType]
    ):
        self._sandbox.erase()  # type: ignore
        self._sandbox = None
        self._metadata = None
        self._data = None
        super().__exit__(exctype, excinst, exctb)

    def _get_metadata(self):
        """Retrieve the metadata JSON."""
        raise NotImplementedError()

    def _get_data(self):
        """Retrieve the data JSON."""
        raise NotImplementedError()

    def _extract(self, *, path_prefix: str, callback: Callable[[str, Any], None]):
        """Extract repository data to a temporary folder.

        :param path_prefix: Only extract paths starting with this prefix.
        :param callback: a callback to report on the process, ``callback(action, value)``,
            with the following callback signatures:

            - ``callback('init', {'total': <int>, 'description': <str>})``,
               to signal the start of a process, its total iterations and description
            - ``callback('update', <int>)``,
               to signal an update to the process and the number of iterations to progress

        :raises TypeError: if parameter types are not respected
        """
        raise NotImplementedError()

    @property
    def export_version(self) -> str:
        metadata = self._get_metadata()
        if 'export_version' not in metadata:
            raise CorruptArchive('export_version missing from metadata.json')
        return metadata['export_version']

    @property
    def metadata(self) -> ArchiveMetadata:
        metadata = self._get_metadata()
        export_parameters = metadata.get('export_parameters', {})
        output = {
            'export_version': metadata['export_version'],
            'aiida_version': metadata['aiida_version'],
            'all_fields_info': metadata['all_fields_info'],
            'unique_identifiers': metadata['unique_identifiers'],
            'graph_traversal_rules': export_parameters.get('graph_traversal_rules', None),
            'entities_starting_set': export_parameters.get('entities_starting_set', None),
            'include_comments': export_parameters.get('include_comments', None),
            'include_logs': export_parameters.get('include_logs', None),
            'conversion_info': metadata.get('conversion_info', [])
        }
        try:
            return ArchiveMetadata(**output)
        except TypeError as error:
            raise CorruptArchive(f'Metadata invalid: {error}')

    def entity_count(self, name: str) -> int:
        data = self._get_data().get('export_data', {}).get(name, {})
        return len(data)

    @property
    def link_count(self) -> int:
        return len(self._get_data()['links_uuid'])

    def iter_entity_fields(self,
                           name: str,
                           fields: Optional[Tuple[str, ...]] = None) -> Iterator[Tuple[int, Dict[str, Any]]]:
        if name not in self.entity_names:
            raise ValueError(f'Unknown entity name: {name}')
        data = self._get_data()['export_data'].get(name, {})
        if name == NODE_ENTITY_NAME:
            # here we merge in the attributes and extras before yielding
            attributes = self._get_data().get('node_attributes', {})
            extras = self._get_data().get('node_extras', {})
            for pk, all_fields in data.items():
                if pk not in attributes:
                    raise CorruptArchive(f'Unable to find attributes info for Node with Pk={pk}')
                if pk not in extras:
                    raise CorruptArchive(f'Unable to find extra info for Node with Pk={pk}')
                all_fields = {**all_fields, **{'attributes': attributes[pk], 'extras': extras[pk]}}
                if fields is not None:
                    all_fields = {k: v for k, v in all_fields.items() if k in fields}
                yield int(pk), all_fields
        else:
            for pk, all_fields in data.items():
                if fields is not None:
                    all_fields = {k: v for k, v in all_fields.items() if k in fields}
                yield int(pk), all_fields

    def iter_node_uuids(self) -> Iterator[str]:
        for _, fields in self.iter_entity_fields(NODE_ENTITY_NAME, fields=('uuid',)):
            yield fields['uuid']

    def iter_group_uuids(self) -> Iterator[Tuple[str, Set[str]]]:
        group_uuids = self._get_data()['groups_uuid']
        for _, fields in self.iter_entity_fields(GROUP_ENTITY_NAME, fields=('uuid',)):
            key = fields['uuid']
            yield key, set(group_uuids.get(key, set()))

    def iter_link_data(self) -> Iterator[dict]:
        for value in self._get_data()['links_uuid']:
            yield value

    def iter_node_repos(
        self,
        uuids: Iterable[str],
        callback: Callable[[str, Any], None] = null_callback,
    ) -> Iterator[Folder]:
        path_prefixes = [os.path.join(self.REPO_FOLDER, export_shard_uuid(uuid)) for uuid in uuids]

        if not path_prefixes:
            return
        self.assert_within_context()
        assert self._sandbox is not None  # required by mypy

        # unarchive the common folder if it does not exist
        common_prefix = os.path.commonpath(path_prefixes)
        if not self._sandbox.get_subfolder(common_prefix).exists():
            self._extract(path_prefix=common_prefix, callback=callback)

        callback('init', {'total': len(path_prefixes), 'description': 'Iterating node repositories'})
        for uuid, path_prefix in zip(uuids, path_prefixes):
            callback('update', 1)
            subfolder = self._sandbox.get_subfolder(path_prefix)
            if not subfolder.exists():
                raise CorruptArchive(
                    f'Unable to find the repository folder for Node with UUID={uuid} in the exported file'
                )
            yield subfolder


class ReaderJsonZip(ReaderJsonBase):
    """A reader for a JSON zip compressed format."""

    @property
    def file_format_verbose(self) -> str:
        return 'JSON (zip compressed)'

    def _get_metadata(self):
        if self._metadata is None:
            try:
                self._metadata = json.loads(read_file_in_zip(self.filename, self.FILENAME_METADATA))
            except (IOError, FileNotFoundError) as error:
                raise CorruptArchive(str(error))
        return self._metadata

    def _get_data(self):
        if self._data is None:
            try:
                self._data = json.loads(read_file_in_zip(self.filename, self.FILENAME_DATA))
            except (IOError, FileNotFoundError) as error:
                raise CorruptArchive(str(error))
        return self._data

    def _extract(self, *, path_prefix: str, callback: Callable[[str, Any], None] = null_callback):
        self.assert_within_context()
        assert self._sandbox is not None  # required by mypy
        try:
            ZipPath(self.filename, mode='r', allow_zip64=True).joinpath(path_prefix).extract_tree(
                self._sandbox.abspath, callback=callback, cb_descript='Extracting repository files'
            )
        except zipfile.BadZipfile as error:
            raise CorruptArchive(f'The input file cannot be read: {error}')
        except NotADirectoryError as error:
            raise CorruptArchive(f'Unable to find required folder in archive: {error}')


class ReaderJsonTar(ReaderJsonBase):
    """A reader for a JSON tar compressed format."""

    @property
    def file_format_verbose(self) -> str:
        return 'JSON (tar.gz compressed)'

    def _get_metadata(self):
        if self._metadata is None:
            try:
                self._metadata = json.loads(read_file_in_tar(self.filename, self.FILENAME_METADATA))
            except (IOError, FileNotFoundError) as error:
                raise CorruptArchive(str(error))
        return self._metadata

    def _get_data(self):
        if self._data is None:
            try:
                self._data = json.loads(read_file_in_tar(self.filename, self.FILENAME_DATA))
            except (IOError, FileNotFoundError) as error:
                raise CorruptArchive(str(error))
        return self._data

    def _extract(self, *, path_prefix: str, callback: Callable[[str, Any], None] = null_callback):
        self.assert_within_context()
        assert self._sandbox is not None  # required by mypy
        try:
            TarPath(self.filename, mode='r:*').joinpath(path_prefix).extract_tree(
                self._sandbox.abspath,
                allow_dev=False,
                allow_symlink=False,
                callback=callback,
                cb_descript='Extracting repository files'
            )
        except tarfile.ReadError as error:
            raise CorruptArchive(f'The input file cannot be read: {error}')
        except NotADirectoryError as error:
            raise CorruptArchive(f'Unable to find required folder in archive: {error}')


class ReaderJsonFolder(ReaderJsonBase):
    """A reader for a JSON plain folder format."""

    @property
    def file_format_verbose(self) -> str:
        return 'JSON (folder)'

    def _get_metadata(self):
        if self._metadata is None:
            path = Path(self.filename) / self.FILENAME_METADATA
            if not path.exists():
                raise CorruptArchive(f'required file `{self.FILENAME_METADATA}` is not included')
            self._metadata = json.loads(path.read_text(encoding='utf8'))
        return self._metadata

    def _get_data(self):
        if self._data is None:
            path = Path(self.filename) / self.FILENAME_DATA
            if not path.exists():
                raise CorruptArchive(f'required file `{self.FILENAME_DATA}` is not included')
            self._data = json.loads(path.read_text(encoding='utf8'))
        return self._data

    def _extract(self, *, path_prefix: str, callback: Callable[[str, Any], None] = null_callback):
        # pylint: disable=unused-argument
        self.assert_within_context()
        assert self._sandbox is not None  # required by mypy
        # By copying the contents of the source directory, we do not risk to modify the source files accidentally
        # Use path_prefix? or is this quick enough to not worry
        self._sandbox.replace_with_folder(self.filename, overwrite=True)
