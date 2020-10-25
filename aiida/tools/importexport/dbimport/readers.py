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
import dataclasses
import json
import os
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
import zipfile
import tarfile

from wrapt import decorator

from aiida.common.exceptions import InvalidOperation
from aiida.common.folders import Folder, SandboxFolder
from aiida.tools.importexport.common.config import EXPORT_VERSION, NODES_EXPORT_SUBFOLDER
from aiida.tools.importexport.common.exceptions import CorruptArchive, ImportValidationError
from aiida.tools.importexport.common.utils import export_shard_uuid


def detect_file_type(in_path):
    """For back-compatibility."""
    if os.path.isdir(in_path):
        return 'folder'
    if tarfile.is_tarfile(in_path):
        return 'tar'
    if zipfile.is_zipfile(in_path):
        return 'zip'
    raise ImportValidationError(
        'Unable to detect the input file format, it is neither a '
        'tar file, nor a (possibly compressed) zip file.'
    )


@dataclasses.dataclass
class ExportMetadata:
    """Class for storing metadata about an export."""
    graph_traversal_rules: Dict[str, bool]
    # Entity type -> UUID list
    entities_starting_set: Dict[str, Set[str]]
    include_comments: bool
    include_logs: bool
    # Entity type -> database ID key
    unique_identifiers: Dict[str, str] = dataclasses.field(repr=False)
    # Entity type -> database key -> meta parameters
    all_fields_info: Dict[str, Dict[str, Dict[str, str]]] = dataclasses.field(repr=False)
    aiida_version: str
    export_version: str


@decorator
def ensure_within_context(wrapped, instance, args, kwargs):
    """Ensure that the method is called within a context manager.

    Note, this decorator is not compatible with @property (https://github.com/GrahamDumpleton/wrapt/issues/44)
    """
    if instance is not None and not instance._in_context:  # pylint: disable=protected-access
        raise InvalidOperation('the ArchiveReader method should be used within a context')
    return wrapped(*args, **kwargs)


class ArchiveReaderAbstract(ABC):
    """An abstract interface for AiiDA archive readers."""

    def __init__(self, filename: str, **kwargs: Any):
        """An archive writer

        :param filename: the filename (possibly including the absolute path)
            of the file on which to import.

        """
        # pylint: disable=unused-argument
        self._filename = filename
        self._in_context = False

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
    def compatible_export_version(self) -> str:
        """Return the export version that this reader is compatible with."""

    def __enter__(self):
        self._in_context = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._in_context = False

    @property
    @abstractmethod
    def metadata(self) -> ExportMetadata:
        """Return the export metadata."""

    @property
    def entity_names(self) -> List[str]:
        """Return list of all entity names."""
        return list(self.metadata.all_fields_info.keys())

    @abstractmethod
    def entity_count(self, name: str) -> Optional[int]:
        """Return the count of an entity or None if not contained in the archive."""

    @property
    @abstractmethod
    def link_count(self) -> int:
        """Return the count of links."""

    @abstractmethod
    def iter_entity_fields(self,
                           name: str,
                           fields: Optional[Tuple[str, ...]] = None) -> Iterable[Tuple[int, str, Dict[str, Any]]]:
        """Iterate over entities and yield their pk, unique identifier, and database fields."""

    @abstractmethod
    def iter_group_uuids(self) -> Iterable[Tuple[str, Set[str]]]:
        """Iterate groups and the nodes they contain."""

    @abstractmethod
    def iter_link_uuids(self) -> Iterable[dict]:
        """Iterate links: {'input': <UUID>, 'output': <UUID>, 'label': <LABEL>, 'type': <TYPE>}"""

    @abstractmethod
    def node_repository(self, uuid: str) -> Folder:
        """Return a temporary folder containing the contents of the repository for a single node.

        :raises `~aiida.tools.importexport.common.exceptions.CorruptArchive`: If the repository does not exist.
        """


class ReaderJsonZip(ArchiveReaderAbstract):
    """A reader for a Json zip compressed format."""

    def __init__(self, filename: str, sandbox_in_repo: bool = True, **kwargs: Any):
        """A writer for zipped archives.

        :param filename: the filename (possibly including the absolute path)
            of the file on which to export.

        """
        super().__init__(filename, **kwargs)
        self._metadata = None
        self._data = None
        # a temporary folder used to extract the file tree
        self._sandbox: Optional[SandboxFolder] = None
        self._sandbox_in_repo = sandbox_in_repo
        self._nodes_export_subfolder = NODES_EXPORT_SUBFOLDER
        self._extracted = False

    @property
    def file_format_verbose(self) -> str:
        return 'Zip'

    @property
    def compatible_export_version(self) -> str:
        """Return the export version that this reader is compatible with."""
        return EXPORT_VERSION

    @ensure_within_context
    def _get_metadata(self):
        """Retrieve the metadata JSON."""
        if self._metadata is None:
            try:
                self._metadata = json.loads(
                    zipfile.ZipFile(self.filename, 'r', allowZip64=True).read('metadata.json').decode('utf8')
                )
            except zipfile.BadZipfile:
                raise ValueError('The input file format is not valid (not a zip file)')
            except KeyError:
                raise CorruptArchive('required file `metadata.json` is not included')
        return self._metadata

    @ensure_within_context
    def _get_data(self):
        """Retrieve the data JSON."""
        if self._data is None:
            try:
                self._data = json.loads(
                    zipfile.ZipFile(self.filename, 'r', allowZip64=True).read('data.json').decode('utf8')
                )
            except zipfile.BadZipfile:
                raise ValueError('The input file format is not valid (not a zip file)')
            except KeyError:
                raise CorruptArchive('required file `data.json` is not included')
        return self._data

    @ensure_within_context
    def _extract(self, path_prefix: str = ''):
        """Extract repository data to a temporary folder.

        :param path_prefix: Only extract paths starting with this prefix.

        :raises TypeError: if parameter types are not respected
        """
        try:
            with zipfile.ZipFile(self.filename, 'r', allowZip64=True) as handle:
                for membername in handle.namelist():
                    if not membername.startswith(path_prefix):
                        continue
                    handle.extract(path=self._sandbox.abspath, member=membername)
        except zipfile.BadZipfile:
            raise TypeError('The input file format is not valid (not a zip file)')
        self._extracted = True

    def __enter__(self):
        super().__enter__()
        self._sandbox = SandboxFolder(self._sandbox_in_repo)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._sandbox.erase()
        self._sandbox = None
        self._extracted = False
        self._metadata = None
        self._data = None
        super().__exit__(exc_type, exc_val, exc_tb)

    @property
    def metadata(self) -> ExportMetadata:
        """Return the export metadata."""
        metadata = self._get_metadata()
        output = {
            'export_version': metadata['export_version'],
            'aiida_version': metadata['aiida_version'],
            'all_fields_info': metadata['all_fields_info'],
            'unique_identifiers': metadata['unique_identifiers'],
            'graph_traversal_rules': metadata['export_parameters']['graph_traversal_rules'],
            'entities_starting_set': metadata['export_parameters']['entities_starting_set'],
            'include_comments': metadata['export_parameters']['include_comments'],
            'include_logs': metadata['export_parameters']['include_logs'],
        }
        return ExportMetadata(**output)

    def entity_count(self, name: str) -> Optional[int]:
        data = self._get_data().get('export_data', {}).get(name, None)
        return len(data) if data is not None else None

    @property
    def link_count(self) -> int:
        return len(self._get_data()['links_uuid'])

    def iter_entity_fields(self,
                           name: str,
                           fields: Optional[Tuple[str, ...]] = None) -> Iterable[Tuple[int, str, Dict[str, Any]]]:
        identifiers = self.metadata.unique_identifiers
        try:
            identifier = identifiers[name]
        except KeyError:
            raise ValueError(f'Unknown entity name: {name}')
        data = self._get_data()['export_data'].get(name, {})
        if name == 'Node':
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
                yield int(pk), identifier, all_fields
        else:
            for pk, all_fields in data.items():
                if fields is not None:
                    all_fields = {k: v for k, v in all_fields.items() if k in fields}
                yield int(pk), identifier, all_fields

    def iter_group_uuids(self) -> Iterable[Tuple[str, Set[str]]]:
        for key, values in self._get_data()['groups_uuid'].items():
            yield key, set(values)

    def iter_link_uuids(self) -> Iterable[dict]:
        for value in self._get_data()['links_uuid']:
            yield value

    def node_repository(self, uuid: str) -> Folder:
        path_prefix = os.path.join(self._nodes_export_subfolder, export_shard_uuid(uuid)) + os.sep
        subfolder = self._sandbox.get_subfolder(path_prefix)
        if not subfolder.exists():
            self._extract(path_prefix=path_prefix)
        if not subfolder.exists():
            raise CorruptArchive(f'Unable to find the repository folder for Node with UUID={uuid} in the exported file')
        return subfolder
