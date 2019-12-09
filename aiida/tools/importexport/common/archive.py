# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions and classes to interact with AiiDA export archives."""

import os
import sys
import tarfile
import zipfile

from wrapt import decorator

from aiida.common import json
from aiida.common.exceptions import ContentNotExistent, InvalidOperation
from aiida.common.folders import SandboxFolder
from aiida.tools.importexport.common.config import NODES_EXPORT_SUBFOLDER
from aiida.tools.importexport.common.exceptions import CorruptArchive

__all__ = ('Archive', 'extract_zip', 'extract_tar', 'extract_tree')


class Archive:
    """Utility class to operate on exported archive files or directories.

    The main usage should be to construct the class with the filepath of the export archive as an argument.
    The contents will be lazily unpacked into a sand box folder which is constructed upon entering the instance
    within a context and which will be automatically cleaned upon leaving that context. Example::

        with Archive('/some/path/archive.aiida') as archive:
            archive.version

    """

    FILENAME_DATA = 'data.json'
    FILENAME_METADATA = 'metadata.json'

    def __init__(self, filepath):
        self._filepath = filepath
        self._folder = None
        self._unpacked = False
        self._data = None
        self._meta_data = None

    def __enter__(self):
        """Instantiate a SandboxFolder into which the archive can be lazily unpacked."""
        self._folder = SandboxFolder()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Clean the sandbox folder if it was instatiated."""
        if self.folder:
            self.folder.erase()

    @decorator
    def ensure_within_context(wrapped, instance, args, kwargs):  # pylint: disable=no-self-argument
        """Decorator to ensure that the instance is called within a context manager."""
        if instance and not instance.folder:
            raise InvalidOperation('the Archive class should be used within a context')

        return wrapped(*args, **kwargs)  # pylint: disable=not-callable

    @decorator
    def ensure_unpacked(wrapped, instance, args, kwargs):  # pylint: disable=no-self-argument
        """Decorator to ensure that the archive is unpacked before entering the decorated function."""
        if instance and not instance.unpacked:
            instance.unpack()

        return wrapped(*args, **kwargs)  # pylint: disable=not-callable

    @ensure_within_context
    def unpack(self):
        """Unpack the archive and store the contents in a sandbox."""
        if os.path.isdir(self.filepath):
            extract_tree(self.filepath, self.folder)
        elif tarfile.is_tarfile(self.filepath):
            extract_tar(self.filepath, self.folder, silent=True, nodes_export_subfolder=NODES_EXPORT_SUBFOLDER)
        elif zipfile.is_zipfile(self.filepath):
            extract_zip(self.filepath, self.folder, silent=True, nodes_export_subfolder=NODES_EXPORT_SUBFOLDER)
        else:
            raise CorruptArchive('unrecognized archive format')

        if not self.folder.get_content_list():
            raise ContentNotExistent('the provided archive {} is empty'.format(self.filepath))

        self._unpacked = True

    @property
    def filepath(self):
        """Return the filepath of the archive

        :return: the archive filepath
        """
        return self._filepath

    @property
    def folder(self):
        """Return the sandbox folder

        :return: sandbox folder :class:`aiida.common.folders.SandboxFolder`
        """
        return self._folder

    @property
    @ensure_within_context
    def data(self):
        """Return the loaded content of the data file

        :return: dictionary with contents of data file
        """
        if self._data is None:
            self._data = self._read_json_file(self.FILENAME_DATA)

        return self._data

    @property
    @ensure_within_context
    def meta_data(self):
        """Return the loaded content of the meta data file

        :return: dictionary with contents of meta data file
        """
        if self._meta_data is None:
            self._meta_data = self._read_json_file(self.FILENAME_METADATA)

        return self._meta_data

    @property
    @ensure_within_context
    def unpacked(self):
        """Return whether the archive has been unpacked into the sandbox folder."""
        return self._unpacked

    @ensure_within_context
    def get_info(self):
        """Return a dictionary with basic information about the archive.

        :return: a dictionary with basic details
        """
        info = {
            'version aiida': self.version_aiida,
            'version format': self.version_format,
        }

        if self.conversion_info:
            info['conversion info'] = '\n'.join(self.conversion_info)

        return info

    @ensure_within_context
    def get_data_statistics(self):
        """Return dictionary with statistics about data content, i.e. how many entries of each entity type it contains.

        :return: a dictionary with basic details
        """
        export_data = self.data.get('export_data', {})
        links_data = self.data.get('links_uuid', {})

        computers = export_data.get('Computer', {})
        groups = export_data.get('Group', {})
        nodes = export_data.get('Node', {})
        users = export_data.get('User', {})

        statistics = {
            'computers': len(computers),
            'groups': len(groups),
            'links': len(links_data),
            'nodes': len(nodes),
            'users': len(users),
        }

        return statistics

    @property
    @ensure_within_context
    def version_aiida(self):
        """Return the version of AiiDA the archive was created with.

        :return: version number
        """
        return self.meta_data['aiida_version']

    @property
    @ensure_within_context
    def version_format(self):
        """Return the version of the archive format.

        :return: version number
        """
        return self.meta_data['export_version']

    @property
    @ensure_within_context
    def conversion_info(self):
        """Return information about migration events that were applied to this archive.

        :return: list of conversion notifications
        """
        try:
            return self.meta_data['conversion_info']
        except KeyError:
            return None

    @ensure_within_context
    @ensure_unpacked
    def _read_json_file(self, filename):
        """Read the contents of a JSON file from the unpacked archive contents.

        :param filename: the filename relative to the sandbox folder
        :return: a dictionary with the loaded JSON content
        """
        with open(self.folder.get_abs_path(filename), 'r', encoding='utf8') as fhandle:
            return json.load(fhandle)


def extract_zip(infile, folder, nodes_export_subfolder=None, silent=False):
    """
    Extract the nodes to be imported from a zip file.

    :param infile: file path
    :type infile: str

    :param folder: a temporary folder used to extract the file tree
    :type folder: :py:class:`~aiida.common.folders.SandboxFolder`

    :param nodes_export_subfolder: name of the subfolder for AiiDA nodes
    :type nodes_export_subfolder: str

    :param silent: suppress debug print
    :type silent: bool

    :raises TypeError: if parameter types are not respected
    :raises `~aiida.tools.importexport.common.exceptions.CorruptArchive`: if the archive misses files or files have
        incorrect formats
    """
    # pylint: disable=fixme
    if not silent:
        print('READING DATA AND METADATA...')

    if nodes_export_subfolder:
        if not isinstance(nodes_export_subfolder, str):
            raise TypeError('nodes_export_subfolder must be a string')
    else:
        nodes_export_subfolder = NODES_EXPORT_SUBFOLDER

    try:
        with zipfile.ZipFile(infile, 'r', allowZip64=True) as handle:

            if not handle.namelist():
                raise CorruptArchive('no files detected')

            try:
                handle.extract(path=folder.abspath, member='metadata.json')
            except KeyError:
                raise CorruptArchive('required file `metadata.json` is not included')

            try:
                handle.extract(path=folder.abspath, member='data.json')
            except KeyError:
                raise CorruptArchive('required file `data.json` is not included')

            if not silent:
                print('EXTRACTING NODE DATA...')

            for membername in handle.namelist():
                # Check that we are only exporting nodes within the subfolder!
                # TODO: better check such that there are no .. in the
                # path; use probably the folder limit checks
                if not membername.startswith(nodes_export_subfolder + os.sep):
                    continue
                handle.extract(path=folder.abspath, member=membername)
    except zipfile.BadZipfile:
        raise ValueError('The input file format for import is not valid (not a zip file)')


def extract_tar(infile, folder, nodes_export_subfolder=None, silent=False):
    """
    Extract the nodes to be imported from a (possibly zipped) tar file.

    :param infile: file path
    :type infile: str

    :param folder: a temporary fodler used to extract the file tree
    :type folder: :py:class:`~aiida.common.folders.SandboxFolder`

    :param nodes_export_subfolder: name of the subfolder for AiiDA nodes
    :type nodes_export_subfolder: str

    :param silent: suppress debug print
    :type silent: bool

    :raises TypeError: if parameter types are not respected
    :raises `~aiida.tools.importexport.common.exceptions.CorruptArchive`: if the archive misses files or files have
        incorrect formats
    """
    # pylint: disable=fixme
    if not silent:
        print('READING DATA AND METADATA...')

    if nodes_export_subfolder:
        if not isinstance(nodes_export_subfolder, str):
            raise TypeError('nodes_export_subfolder must be a string')
    else:
        nodes_export_subfolder = NODES_EXPORT_SUBFOLDER

    try:
        with tarfile.open(infile, 'r:*', format=tarfile.PAX_FORMAT) as handle:

            try:
                handle.extract(path=folder.abspath, member=handle.getmember('metadata.json'))
            except KeyError:
                raise CorruptArchive('required file `metadata.json` is not included')

            try:
                handle.extract(path=folder.abspath, member=handle.getmember('data.json'))
            except KeyError:
                raise CorruptArchive('required file `data.json` is not included')

            if not silent:
                print('EXTRACTING NODE DATA...')

            for member in handle.getmembers():
                if member.isdev():
                    # safety: skip if character device, block device or FIFO
                    print('WARNING, device found inside the import file: {}'.format(member.name), file=sys.stderr)
                    continue
                if member.issym() or member.islnk():
                    # safety: in export, I set dereference=True therefore
                    # there should be no symbolic or hard links.
                    print('WARNING, link found inside the import file: {}'.format(member.name), file=sys.stderr)
                    continue
                # Check that we are only exporting nodes within the subfolder!
                # TODO: better check such that there are no .. in the
                # path; use probably the folder limit checks
                if not member.name.startswith(nodes_export_subfolder + os.sep):
                    continue
                handle.extract(path=folder.abspath, member=member)
    except tarfile.ReadError:
        raise ValueError('The input file format for import is not valid (1)')


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
