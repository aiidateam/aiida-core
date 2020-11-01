# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Shared resources for the archive."""
from collections import OrderedDict
import copy
import dataclasses
import os
from pathlib import Path
import tarfile
from types import TracebackType
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Type, Union
import zipfile

from aiida.common import json  # handles byte dumps
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.importexport.common.exceptions import CorruptArchive

__all__ = (
    'ArchiveMetadata', 'detect_archive_type', 'null_callback', 'read_file_in_zip', 'read_file_in_tar',
    'safe_extract_zip', 'safe_extract_tar', 'CacheFolder'
)

ARCHIVE_LOGGER = AIIDA_LOGGER.getChild('archive')


@dataclasses.dataclass
class ArchiveMetadata:
    """Class for storing metadata about this archive.

    Required fields are necessary for importing the data back into AiiDA,
    whereas optional fields capture information about the export/migration process(es)
    """
    export_version: str
    aiida_version: str
    # Entity type -> database ID key
    unique_identifiers: Dict[str, str] = dataclasses.field(repr=False)
    # Entity type -> database key -> meta parameters
    all_fields_info: Dict[str, Dict[str, Dict[str, str]]] = dataclasses.field(repr=False)

    # optional data
    graph_traversal_rules: Optional[Dict[str, bool]] = dataclasses.field(default=None)
    # Entity type -> UUID list
    entities_starting_set: Optional[Dict[str, Set[str]]] = dataclasses.field(default=None)
    include_comments: Optional[bool] = dataclasses.field(default=None)
    include_logs: Optional[bool] = dataclasses.field(default=None)
    # list of migration event notifications
    conversion_info: List[str] = dataclasses.field(default_factory=list, repr=False)


def null_callback(action: str, value: Any):  # pylint: disable=unused-argument
    """A null callback function."""


def detect_archive_type(in_path: str) -> str:
    """For back-compatibility, but should be replaced with direct comparison of classes.

    :param in_path: the path to the file
    :returns: the archive type identifier (currently one of 'zip', 'tar.gz', 'folder')

    """
    from aiida.tools.importexport.common.config import ExportFileFormat
    from aiida.tools.importexport.common.exceptions import ImportValidationError

    if os.path.isdir(in_path):
        return 'folder'
    if tarfile.is_tarfile(in_path):
        return ExportFileFormat.TAR_GZIPPED
    if zipfile.is_zipfile(in_path):
        return ExportFileFormat.ZIP
    raise ImportValidationError(
        'Unable to detect the input file format, it is neither a '
        'folder, tar file, nor a (possibly compressed) zip file.'
    )


def read_file_in_zip(filepath: str, path: str) -> str:
    """Read a text based file from inside a zip file and return its content.

    :param filepath: the path to the zip file
    :param path: the relative path within the zip file

    """
    try:
        return zipfile.ZipFile(filepath, 'r', allowZip64=True).read(path).decode('utf8')
    except zipfile.BadZipfile as error:
        raise CorruptArchive(f'The input file cannot be read: {error}')
    except KeyError:
        raise CorruptArchive(f'required file {path} is not included')


def read_file_in_tar(filepath: str, path: str) -> str:
    """Read a text based file from inside a tar file and return its content.

    :param filepath: the path to the tar file
    :param path: the relative path within the tar file

    """
    try:
        with tarfile.open(filepath, 'r:*', format=tarfile.PAX_FORMAT) as handle:
            result = handle.extractfile(path)
            if result is None:
                raise CorruptArchive(f'required file `{path}` is not included')
            output = result.read()
            if isinstance(output, bytes):
                return output.decode('utf8')
    except tarfile.ReadError:
        raise ValueError('The input file format is not valid (not a tar file)')
    except (KeyError, AttributeError):
        raise CorruptArchive(f'required file `{path}` is not included')


def _get_filter(only_prefix: Iterable[str], ignore_prefix: Iterable[str]) -> Callable[[str], bool]:
    """Create filter for members to extract.

    :param only_prefix: Extract only internal paths starting with these prefixes
    :param ignore_prefix: Ignore internal paths starting with these prefixes

    """
    if only_prefix:

        def _filter(name):
            return any(name.startswith(prefix) for prefix in only_prefix
                       ) and all(not name.startswith(prefix) for prefix in ignore_prefix)
    else:

        def _filter(name):
            return all(not name.startswith(prefix) for prefix in ignore_prefix)

    return _filter


def safe_extract_zip(
    in_path: Union[str, Path],
    out_path: Union[str, Path],
    *,
    only_prefix: Iterable[str] = (),
    ignore_prefix: Iterable[str] = ('..', '/'),
    callback: Callable[[str, Any], None] = null_callback,
    callback_description: str = 'Extracting zip files'
):
    """Safely extract a zip file

    :param in_path: Path to extract from
    :param out_path: Path to extract to
    :param only_prefix: Extract only internal paths starting with these prefixes
    :param ignore_prefix: Ignore internal paths starting with these prefixes
    :param callback: a callback to report on the process, ``callback(action, value)``,
        with the following callback signatures:

        - ``callback('init', {'total': <int>, 'description': <str>})``,
            to signal the start of a process, its total iterations and description
        - ``callback('update', <int>)``,
            to signal an update to the process and the number of iterations to progress

    :param callback_description: the description to return in the callback

    :raises `~aiida.tools.importexport.common.exceptions.CorruptArchive`: if the file cannot be read

    """
    _filter = _get_filter(only_prefix, ignore_prefix)
    try:
        with zipfile.ZipFile(in_path, 'r', allowZip64=True) as handle:
            callback('init', {'total': 1, 'description': "Computing zip files to extract"})
            members = [name for name in handle.namelist() if _filter(name)]
            callback('init', {'total': len(members), 'description': callback_description})
            for membername in members:
                callback('update', 1)
                handle.extract(path=os.path.abspath(out_path), member=membername)
    except zipfile.BadZipfile as error:
        raise CorruptArchive(f'The input file cannot be read: {error}')


def safe_extract_tar(
    in_path: Union[str, Path],
    out_path: Union[str, Path],
    *,
    only_prefix: Iterable[str] = (),
    ignore_prefix: Iterable[str] = ('..', '/'),
    callback: Callable[[str, Any], None] = null_callback,
    callback_description: str = 'Extracting tar files'
):
    """Safely extract a tar file

    :param in_path: Path to extract from
    :param out_path: Path to extract to
    :param only_prefix: Extract only internal paths starting with these prefixes
    :param ignore_prefix: Ignore internal paths starting with these prefixes
    :param callback: a callback to report on the process, ``callback(action, value)``,
        with the following callback signatures:

        - ``callback('init', {'total': <int>, 'description': <str>})``,
            to signal the start of a process, its total iterations and description
        - ``callback('update', <int>)``,
            to signal an update to the process and the number of iterations to progress

    :param callback_description: the description to return in the callback

    :raises `~aiida.tools.importexport.common.exceptions.CorruptArchive`: if the file cannot be read

    """
    _filter = _get_filter(only_prefix, ignore_prefix)
    try:
        with tarfile.open(in_path, 'r:*', format=tarfile.PAX_FORMAT) as handle:
            callback('init', {'total': 1, 'description': "Computing tar files to extract"})
            members = [m for m in handle.getmembers() if _filter(m.name)]
            callback('init', {'total': len(members), 'description': callback_description})
            for member in members:
                callback('update', 1)
                if member.isdev():
                    # safety: skip if character device, block device or FIFO
                    msg = f'WARNING, device found inside the tar file: {member.name}'
                    ARCHIVE_LOGGER.warning(msg)
                    continue
                if member.issym() or member.islnk():
                    # safety: skip symlinks
                    msg = f'WARNING, symlink found inside the tar file: {member.name}'
                    ARCHIVE_LOGGER.warning(msg)
                    continue
                handle.extract(path=os.path.abspath(out_path), member=member)
    except tarfile.ReadError as error:
        raise CorruptArchive(f'The input file cannot be read: {error}')


class CacheFolder:
    """A class to encapsulate a folder path with cached read/writes.

    The class can be used as a context manager, and will flush the cache on exit::

        with CacheFolder(path) as folder:
            # these are stored in memory (no disk write)
            folder.write_text('path/to/file.txt', 'content')
            folder.write_json('path/to/data.json', {'a': 1})
            # these will be read from memory
            text = folder.read_text('path/to/file.txt')
            text = folder.load_json('path/to/data.json')

        # all files will now have been written to disk

    """

    def __init__(self, path: Union[Path, str], *, encoding: str = 'utf8'):
        """Initialise cached folder.

        :param path: folder path to cache
        :param encoding: encoding of text to read/write

        """
        self._path = Path(path)
        # dict mapping path -> (type, content)
        self._cache = OrderedDict()  # type: ignore
        self._encoding = encoding
        self._max_items = 100  # maximum limit of files to store in memory

    def _write_object(self, path: str, ctype: str, content: Any):
        """Write an object from the cache to disk.

        :param path: relative path of file
        :param ctype: the type of the content
        :param content: the content to write

        """
        if ctype == 'text':
            text = content
        elif ctype == 'json':
            text = json.dumps(content)
        else:
            raise TypeError(f'Unknown content type: {ctype}')

        (self._path / path).write_text(text, encoding=self._encoding)

    def flush(self):
        """Flush the cache."""
        for path, (ctype, content) in self._cache.items():
            self._write_object(path, ctype, content)

    def _limit_cache(self):
        """Ensure the cache does not exceed a set limit.

        Content is uncached on a First-In-First-Out basis.

        """
        while len(self._cache) > self._max_items:
            path, (ctype, content) = self._cache.popitem(last=False)
            self._write_object(path, ctype, content)

    def get_path(self, flush=True) -> Path:
        """Return the path.

        :param flush: flush the cache before returning

        """
        if flush:
            self.flush()
        return self._path

    def write_text(self, path: str, content: str):
        """write text to the cache.

        :param path: path relative to base folder

        """
        assert isinstance(content, str)
        self._cache[path] = ('text', content)
        self._limit_cache()

    def read_text(self, path) -> str:
        """write text from the cache or base folder.

        :param path: path relative to base folder

        """
        if path not in self._cache:
            return (self._path / path).read_text(self._encoding)
        ctype, content = self._cache[path]
        if ctype == 'text':
            return content
        if ctype == 'json':
            return json.dumps(content)

        raise TypeError(f"content of type '{ctype}' could not be converted to text")

    def write_json(self, path: str, data: dict):
        """Write dict to the folder, to be serialized as json.

        The dictionary is stored in memory, until the cache is flushed,
        at which point the dictionary is serialized to json and written to disk.

        :param path: path relative to base folder

        """
        json.dumps(data)  # make sure that the data can be converted to json
        self._cache[path] = ('json', data)
        self._limit_cache()

    def load_json(self, path: str, ensure_copy: bool = False) -> Tuple[bool, dict]:
        """Load a json file from the cache folder.

        Important: if the dict is returned directly from the cache, any mutations will affect the cached dict.

        :param path: path relative to base folder
        :param ensure_copy: ensure the dict is a copy of that from the cache

        :returns: (from cache, the content)
            If from cache, mutations will directly affect the cache

        """
        if path not in self._cache:
            return False, json.loads((self._path / path).read_text(self._encoding))

        ctype, content = self._cache[path]
        if ctype == 'text':
            return False, json.loads(content)
        if ctype == 'json':
            if ensure_copy:
                return False, copy.deepcopy(content)
            return True, content

        raise TypeError(f"content of type '{ctype}' could not be converted to a dict")

    def remove_file(self, path):
        """Remove a file from both the cache and base folder (if present).

        :param path: path relative to base folder

        """
        self._cache.pop(path, None)
        if (self._path / path).exists():
            (self._path / path).unlink()

    def __enter__(self):
        """Enter the contextmanager."""
        return self

    def __exit__(
        self, exctype: Optional[Type[BaseException]], excinst: Optional[BaseException], exctb: Optional[TracebackType]
    ):
        """Exit the contextmanager."""
        self.flush()
        return False
