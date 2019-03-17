# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions and classes to interact with AiiDA export archives."""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import io
import os
import sys
import tarfile
import zipfile
from functools import wraps

from aiida.common.exceptions import ContentNotExistent, InvalidOperation
from aiida.common.folders import SandboxFolder
from aiida.common import json


class Archive(object):  # pylint: disable=useless-object-inheritance
    """
    Utility class to operate on exported archive files or directories.

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

    def ensure_within_context(function):  # pylint: disable=no-self-argument
        """Decorator to ensure that the instance is called within a context manager."""

        @wraps(function)
        def decorated(self, *args, **kwargs):
            """The decorated function is guaranteed to be within the context."""
            if not self.folder:
                raise InvalidOperation('the Archive class should be used within a context')

            return function(self, *args, **kwargs)  # pylint: disable=not-callable

        return decorated

    def ensure_unpacked(function):  # pylint: disable=no-self-argument
        """Decorator to ensure that the archive is unpacked before entering the decorated function."""

        @wraps(function)
        def decorated_function(self, *args, **kwargs):
            """The decorated function is guaranteed to have access to the unpacked archive."""
            if not self.unpacked:
                self.unpack()

            return function(self, *args, **kwargs)  # pylint: disable=not-callable

        return decorated_function

    @ensure_within_context
    def unpack(self):
        """Unpack the archive and store the contents in a sandbox."""
        if os.path.isdir(self.filepath):
            extract_tree(self.filepath, self.folder)
        else:
            if tarfile.is_tarfile(self.filepath):
                extract_tar(self.filepath, self.folder, silent=True, nodes_export_subfolder='nodes')
            elif zipfile.is_zipfile(self.filepath):
                extract_zip(self.filepath, self.folder, silent=True, nodes_export_subfolder='nodes')
            else:
                raise ValueError('unrecognized archive format')

        if not self.folder.get_content_list():
            raise ContentNotExistent('the provided archive {} is empty'.format(self.filepath))

        self._unpacked = True

    @property
    def filepath(self):
        """
        Return the filepath of the archive

        :return: the archive filepath
        """
        return self._filepath

    @property
    def folder(self):
        """
        Return the sandbox folder

        :return: sandbox folder :class:`aiida.common.folders.SandboxFolder`
        """
        return self._folder

    @property
    @ensure_within_context
    def data(self):
        """
        Return the loaded content of the data file

        :return: dictionary with contents of data file
        """
        if self._data is None:
            self._data = self._read_json_file(self.FILENAME_DATA)

        return self._data

    @property
    @ensure_within_context
    def meta_data(self):
        """
        Return the loaded content of the meta data file

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
        """
        Return a dictionary with basic information about the archive.

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
        """
        Return a dictionary with statistics about data content, i.e. how many entries of each entity type it contains.

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
        """
        Return the version of AiiDA the archive was created with.

        :return: version number
        """
        return self.meta_data['aiida_version']

    @property
    @ensure_within_context
    def version_format(self):
        """
        Return the version of the archive format.

        :return: version number
        """
        return self.meta_data['export_version']

    @property
    @ensure_within_context
    def conversion_info(self):
        """
        Return information about migration events that were applied to this archive.

        :return: list of conversion notifications
        """
        try:
            return self.meta_data['conversion_info']
        except KeyError:
            return None

    @ensure_within_context
    @ensure_unpacked
    def _read_json_file(self, filename):
        """
        Read the contents of a JSON file from the unpacked archive contents.

        :param filename: the filename relative to the sandbox folder
        :return: a dictionary with the loaded JSON content
        """
        with io.open(self.folder.get_abs_path(filename), 'r', encoding='utf8') as fhandle:
            return json.load(fhandle)


def extract_zip(infile, folder, nodes_export_subfolder="nodes", silent=False):
    """
    Extract the nodes to be imported from a zip file.

    :param infile: file path
    :param folder: a SandboxFolder, used to extract the file tree
    :param nodes_export_subfolder: name of the subfolder for AiiDA nodes
    :param silent: suppress debug print
    """
    # pylint: disable=fixme
    if not silent:
        print("READING DATA AND METADATA...")

    try:
        with zipfile.ZipFile(infile, "r", allowZip64=True) as handle:

            if not handle.namelist():
                raise ValueError("The zip file is empty.")

            handle.extract(path=folder.abspath, member='metadata.json')
            handle.extract(path=folder.abspath, member='data.json')

            if not silent:
                print("EXTRACTING NODE DATA...")

            for membername in handle.namelist():
                # Check that we are only exporting nodes within
                # the subfolder!
                # TODO: better check such that there are no .. in the
                # path; use probably the folder limit checks
                if not membername.startswith(nodes_export_subfolder + os.sep):
                    continue
                handle.extract(path=folder.abspath, member=membername)
    except zipfile.BadZipfile:
        raise ValueError("The input file format for import is not valid (not" " a zip file)")


def extract_tar(infile, folder, nodes_export_subfolder="nodes", silent=False):
    """
    Extract the nodes to be imported from a (possibly zipped) tar file.

    :param infile: file path
    :param folder: a SandboxFolder, used to extract the file tree
    :param nodes_export_subfolder: name of the subfolder for AiiDA nodes
    :param silent: suppress debug print
    """
    # pylint: disable=fixme
    if not silent:
        print("READING DATA AND METADATA...")

    try:
        with tarfile.open(infile, "r:*", format=tarfile.PAX_FORMAT) as handle:

            handle.extract(path=folder.abspath, member=handle.getmember('metadata.json'))
            handle.extract(path=folder.abspath, member=handle.getmember('data.json'))

            if not silent:
                print("EXTRACTING NODE DATA...")

            for member in handle.getmembers():
                if member.isdev():
                    # safety: skip if character device, block device or FIFO
                    print("WARNING, device found inside the import file: {}".format(member.name), file=sys.stderr)
                    continue
                if member.issym() or member.islnk():
                    # safety: in export, I set dereference=True therefore
                    # there should be no symbolic or hard links.
                    print("WARNING, link found inside the import file: {}".format(member.name), file=sys.stderr)
                    continue
                # Check that we are only exporting nodes within
                # the subfolder!
                # TODO: better check such that there are no .. in the
                # path; use probably the folder limit checks
                if not member.name.startswith(nodes_export_subfolder + os.sep):
                    continue
                handle.extract(path=folder.abspath, member=member)
    except tarfile.ReadError:
        raise ValueError("The input file format for import is not valid (1)")


def extract_tree(infile, folder):
    """
    Prepare to import nodes from plain file system tree.

    :param infile: path
    :param folder: a SandboxFolder, used to extract the file tree
    """

    def add_files(args, path, files):
        """Add files to a folder."""
        folder = args['folder']
        root = args['root']
        for filename in files:
            fullpath = os.path.join(path, filename)
            relpath = os.path.relpath(fullpath, root)
            if os.path.isdir(fullpath):
                if os.path.dirname(relpath) != '':
                    folder.get_subfolder(os.path.dirname(relpath) + os.sep, create=True)
            elif not os.path.isfile(fullpath):
                continue
            if os.path.dirname(relpath) != '':
                folder.get_subfolder(os.path.dirname(relpath) + os.sep, create=True)
            folder.insert_path(os.path.abspath(fullpath), relpath)

    os.walk(infile, add_files, {'folder': folder, 'root': infile})
