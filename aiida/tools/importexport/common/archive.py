# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-branches
"""Utility functions and classes to interact with AiiDA export archives."""
import os
import sys
import tarfile
import zipfile
import warnings

from aiida.common.progress_reporter import get_progress_reporter, set_progress_bar_tqdm, set_progress_reporter
from aiida.common.warnings import AiidaDeprecationWarning
from aiida.tools.importexport.common.config import NODES_EXPORT_SUBFOLDER
from aiida.tools.importexport.common.exceptions import CorruptArchive

__all__ = ('extract_zip', 'extract_tar', 'extract_tree')


def _update_description(path, progress_bar, refresh: bool = False):
    """Update description for a progress bar given path

    :param path: path of file or directory
    :type path: str
    :param refresh: Whether or not to refresh the progress bar with the new description. Default: False.
    :type refresh: bool
    """
    (path, description) = os.path.split(path)
    while description == '':
        (path, description) = os.path.split(path)
    description = f'EXTRACTING: {description}'

    progress_bar.set_description_str(description, refresh=refresh)


def extract_zip(infile, folder, nodes_export_subfolder=None, check_files=('data.json', 'metadata.json'), **kwargs):
    """Extract the nodes to be imported from a zip file.

    :param infile: file path
    :type infile: str

    :param folder: a temporary folder used to extract the file tree
    :type folder: :py:class:`~aiida.common.folders.SandboxFolder`

    :param nodes_export_subfolder: name of the subfolder for AiiDA nodes
    :type nodes_export_subfolder: str

    :param check_files: list of files to check are present

    :param silent: suppress progress bar
    :type silent: bool

    :raises TypeError: if parameter types are not respected
    :raises `~aiida.tools.importexport.common.exceptions.CorruptArchive`: if the archive misses files or files have
        incorrect formats
    """
    warnings.warn(
        'extract_zip function is deprecated and will be removed in AiiDA v2.0.0, '
        'use extract_tree in the archive-path package instead', AiidaDeprecationWarning
    )  # pylint: disable=no-member

    if nodes_export_subfolder:
        if not isinstance(nodes_export_subfolder, str):
            raise TypeError('nodes_export_subfolder must be a string')
    else:
        nodes_export_subfolder = NODES_EXPORT_SUBFOLDER

    if not kwargs.get('silent', False):
        set_progress_bar_tqdm(unit='files')
    else:
        set_progress_reporter(None)

    data_files = set()

    try:
        with zipfile.ZipFile(infile, 'r', allowZip64=True) as handle:

            members = handle.namelist()

            if not members:
                raise CorruptArchive('no files detected in archive')

            with get_progress_reporter()(total=len(members)) as progress:

                for membername in members:

                    progress.update()

                    # Check that we are only exporting nodes within the subfolder!
                    # better check such that there are no .. in the
                    # path; use probably the folder limit checks
                    if membername in check_files:
                        data_files.add(membername)
                    elif not membername.startswith(nodes_export_subfolder + os.sep):
                        continue

                    _update_description(membername, progress)

                    handle.extract(path=folder.abspath, member=membername)

    except zipfile.BadZipfile:
        raise ValueError('The input file format for import is not valid (not a zip file)')

    for name in check_files:
        if name not in data_files:
            raise CorruptArchive('Archive missing required file:f {name}')


def extract_tar(infile, folder, nodes_export_subfolder=None, check_files=('data.json', 'metadata.json'), **kwargs):
    """
    Extract the nodes to be imported from a (possibly zipped) tar file.

    :param infile: file path
    :type infile: str

    :param folder: a temporary fodler used to extract the file tree
    :type folder: :py:class:`~aiida.common.folders.SandboxFolder`

    :param nodes_export_subfolder: name of the subfolder for AiiDA nodes
    :type nodes_export_subfolder: str

    :param check_files: list of files to check are present

    :param silent: suppress progress bar
    :type silent: bool

    :raises TypeError: if parameter types are not respected
    :raises `~aiida.tools.importexport.common.exceptions.CorruptArchive`: if the archive misses files or files have
        incorrect formats
    """
    warnings.warn(
        'extract_tar function is deprecated and will be removed in AiiDA v2.0.0, '
        'use extract_tree in the archive-path package instead', AiidaDeprecationWarning
    )  # pylint: disable=no-member

    if nodes_export_subfolder:
        if not isinstance(nodes_export_subfolder, str):
            raise TypeError('nodes_export_subfolder must be a string')
    else:
        nodes_export_subfolder = NODES_EXPORT_SUBFOLDER

    if not kwargs.get('silent', False):
        set_progress_bar_tqdm(unit='files')
    else:
        set_progress_reporter(None)

    data_files = set()

    try:
        with tarfile.open(infile, 'r:*', format=tarfile.PAX_FORMAT) as handle:

            members = handle.getmembers()

            if len(members) == 1 and members[0].size == 0:
                raise CorruptArchive('no files detected in archive')

            with get_progress_reporter()(total=len(members)) as progress:

                for member in members:

                    progress.update()

                    if member.isdev():
                        # safety: skip if character device, block device or FIFO
                        print(f'WARNING, device found inside the import file: {member.name}', file=sys.stderr)
                        continue
                    if member.issym() or member.islnk():
                        # safety: in export, I set dereference=True therefore
                        # there should be no symbolic or hard links.
                        print(f'WARNING, symlink found inside the import file: {member.name}', file=sys.stderr)
                        continue
                    # Check that we are only exporting nodes within the subfolder!
                    # better check such that there are no .. in the
                    # path; use probably the folder limit checks
                    if member.name in check_files:
                        data_files.add(member.name)
                    elif not member.name.startswith(nodes_export_subfolder + os.sep):
                        continue

                    _update_description(member.name, progress)

                    handle.extract(path=folder.abspath, member=member)
    except tarfile.ReadError:
        raise ValueError('The input file format for import is not valid (not a tar file)')

    for name in check_files:
        if name not in data_files:
            raise CorruptArchive('Archive missing required file:f {name}')


def extract_tree(infile, folder):
    """Prepare to import nodes from plain file system tree by copying in the given sandbox folder.

    .. note:: the contents of the unpacked archive directory are copied into the sandbox folder, because the files will
        anyway haven to be copied to the repository at some point. By copying the contents of the source directory now
        and continuing operation only on the sandbox folder, we do not risk to modify the source files accidentally.
        During import then, the node files from the sandbox can be moved to the repository, so they won't have to be
        copied again in any case.

    :param infile: absolute filepath point to the unpacked archive directory
    :type infile: str

    :param folder: a temporary folder to which the archive contents are copied
    :type folder: :py:class:`~aiida.common.folders.SandboxFolder`
    """
    folder.replace_with_folder(infile, move=False, overwrite=True)
