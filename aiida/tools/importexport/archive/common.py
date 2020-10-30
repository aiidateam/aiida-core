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
import dataclasses
import os
from pathlib import Path
import tarfile
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Union
import zipfile

from aiida.common.log import AIIDA_LOGGER
from aiida.tools.importexport.common.exceptions import CorruptArchive

__all__ = (
    'ArchiveMetadata', 'detect_archive_type', 'null_callback', 'read_file_in_zip', 'read_file_in_tar',
    'safe_extract_zip', 'safe_extract_tar'
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
    """Read a path from inside a zip file.

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
    """Read a path from inside a tar file.

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
    """Create filter for members to extract."""
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
                handle.extract(path=os.path.abspath(out_path), member=member.name)
    except tarfile.ReadError as error:
        raise CorruptArchive(f'The input file cannot be read: {error}')
