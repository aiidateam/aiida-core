# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=fixme
"""Utility functions and classes to interact with AiiDA export archives."""

import io
import os
import sys
import tarfile
import zipfile

from wrapt import decorator

from aiida.common import json
from aiida.common.folders import SandboxFolder
from aiida.tools.importexport.common.config import NODES_EXPORT_SUBFOLDER
from aiida.tools.importexport.common.exceptions import CorruptArchive, InvalidArchiveOperation, ArchiveOperationError

__all__ = ('Archive',)

FILENAME_DATA = 'data.json'
FILENAME_METADATA = 'metadata.json'
JSON_FILES = [FILENAME_DATA, FILENAME_METADATA]


@decorator
def ensure_within_context(wrapped, instance, args, kwargs):
    """Decorator to ensure that the instance is called within a context manager."""
    if instance:
        instance._ensure_within_context()  # pylint: disable=protected-access
    return wrapped(*args, **kwargs)


@decorator
def ensure_unpacked(wrapped, instance, args, kwargs):
    """Decorator to ensure that the archive is unpacked before entering the decorated function."""
    if instance and not instance.unpacked:
        instance.unpack()

    return wrapped(*args, **kwargs)


class Archive:
    """Utility class to operate on exported archive files or directories.

    The main usage should be to construct the class with the filepath of the export archive as an argument.
    The contents will be lazily unpacked into a sand box folder which is constructed upon entering the instance
    within a context and which will be automatically cleaned upon leaving that context. Example::

        with Archive('/some/path/archive.aiida') as archive:
            archive.version

    """
    # TODO: These sets should be determined from config.py - or similar - when the export function is updated to do the
    # same. This will make it easy to update from a single place in the future, if needed.
    MANDATORY_DATA_KEYS = {'node_attributes', 'node_extras', 'export_data', 'links_uuid', 'groups_uuid'}
    MANDATORY_METADATA_KEYS = {'aiida_version', 'export_version', 'all_fields_info', 'unique_identifiers'}

    def __init__(self, filepath, silent=True):
        self._filepath = filepath
        self._silent = silent
        self._folder = None
        self._unpacked = False
        self._keep = False
        self._data = None
        self._meta_data = None
        self._archive_format = None

    def __enter__(self):
        """Instantiate a SandboxFolder into which the archive can be lazily unpacked."""
        self._folder = SandboxFolder(sandbox_in_repo=True)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Clean the sandbox folder if it was instantiated."""
        if not self.keep and self.folder:
            self.folder.erase()

    def _ensure_within_context(self):
        """Overridable function that processes decorator ``@ensure_within_context``"""
        if not self.folder:
            raise InvalidArchiveOperation('the Archive class should be used within a context')

    @ensure_within_context
    def unpack(self):
        """Unpack the archive and store the contents in a sandbox."""
        try:
            self._archive_format = 'zip'
            if os.path.isdir(self.filepath):
                self._redirect_archive_folder()
                # Update self.folder to be a Folder()
                # Since we are now dealing with source data, we do not want to delete the folder upon exit.
                # self._folder = get_tree(self.filepath)
                self._keep = True
            elif tarfile.is_tarfile(self.filepath):
                extract_tar(
                    self.filepath, self.folder, silent=self._silent, nodes_export_subfolder=NODES_EXPORT_SUBFOLDER
                )
                self._archive_format = 'tar'
            elif zipfile.is_zipfile(self.filepath):
                extract_zip(
                    self.filepath, self.folder, silent=self._silent, nodes_export_subfolder=NODES_EXPORT_SUBFOLDER
                )
            else:
                raise CorruptArchive('unrecognized archive format')
        except Exception as why:
            raise CorruptArchive('Error during unpacking of {}: {}'.format(self.filepath, why))

        if not self.folder.get_content_list():
            raise CorruptArchive('the provided archive {} is empty'.format(self.filepath))

        self._unpacked = True

    @ensure_unpacked
    @ensure_within_context
    def repack(self, output_filepath=None, overwrite=False):
        """Repack the archive.

        Set new filepath name for repacked archive (if requested), write current data and meta_data dictionaries
        to folder.

        :param output_filepath: the filename, if an absolute path is not provided,
            it will be created in the current working directory.
        :type output_filepath: str
        :param overwrite: whether or not to overwrite output_filepath, if it already exists (default: False).
        :type overwrite: bool
        """
        import six

        # Try to create an output_filepath automatically (based on time and date), if none has been specified
        if not output_filepath:
            output_filepath = self._new_output_filename(overwrite)
        elif not isinstance(output_filepath, six.string_types):
            raise InvalidArchiveOperation(
                'output_filepath must be a string, instead {} was given'.format(type(output_filepath))
            )

        if os.path.exists(output_filepath) and not overwrite:
            raise ArchiveOperationError('output file for repacking already exists')

        self._write_json_file(FILENAME_DATA, self.data)
        self._write_json_file(FILENAME_METADATA, self.meta_data)

        if self._archive_format == 'tar':
            with tarfile.open(output_filepath, 'w:gz', format=tarfile.PAX_FORMAT, dereference=True) as out_file:
                out_file.add(self.folder.abspath, arcname='')
        elif self._archive_format == 'zip':
            with zipfile.ZipFile(
                output_filepath, mode='w', compression=zipfile.ZIP_DEFLATED, allowZip64=True
            ) as out_file:
                for dirpath, dirnames, filenames in os.walk(self.folder.abspath):
                    relpath = os.path.relpath(dirpath, self.folder.abspath)
                    for filename in dirnames + filenames:
                        real_src = os.path.join(dirpath, filename)
                        real_dest = os.path.join(relpath, filename)
                        out_file.write(real_src, real_dest)
        else:
            raise ArchiveOperationError('archive_format must be set prior to exit, when Archive should be kept')

    def _new_output_filename(self, overwrite):
        """Create and return new filename based on self.filepath to repack into.

        :param overwrite: whether or not to overwrite existing file, if necessary.
        :type overwrite: bool
        """
        from aiida.common import timezone

        filepath_split = os.path.basename(self.filepath).split('.')
        unique_name = timezone.localtime(timezone.now()).strftime('%Y%m%d-%H%M%S')
        new_filename = '.'.join([
            '{}_migrated-{}'.format('.'.join(filepath_split[:-1]), unique_name), filepath_split[-1]
        ])
        i = 0
        while os.path.exists(new_filename) and not overwrite:
            i += 1
            basename = new_filename.split('.')
            new_filename = '.'.join([basename[0] + '_{}'.format(i), basename[1]])
            if i == 100:
                raise ArchiveOperationError('an output file for repacking cannot be created')

        return new_filename

    @property
    def filepath(self):
        """Return the filepath of the archive

        :return: the archive filepath
        """
        return self._filepath

    @property
    def folder(self):
        """Return the folder

        :return: folder
        :rtype: :py:class:`~aiida.common.folders.SandboxFolder`, :py:class:`~aiida.common.folders.Folder`
        """
        return self._folder

    @property
    @ensure_within_context
    def keep(self):
        """Return whether to keep the archive upon exit."""
        return self._keep

    @property
    @ensure_within_context
    def data(self):
        """Return the loaded content of the data file

        :return: dictionary with contents of data file
        """
        if self._data is None:
            self._data = self._read_json_file(FILENAME_DATA)

        return self._data

    @property
    @ensure_within_context
    def meta_data(self):
        """Return the loaded content of the meta data file

        :return: dictionary with contents of meta data file
        """
        if self._meta_data is None:
            self._meta_data = self._read_json_file(FILENAME_METADATA)

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
        export_data = self.get_data_member('export_data')
        links_data = self.get_data_member('links_uuid')

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
        return self.get_meta_data_member('aiida_version')

    @property
    @ensure_within_context
    def version_format(self):
        """Return the version of the archive format.

        :return: version number
        """
        return self.get_meta_data_member('export_version')

    @property
    @ensure_within_context
    def conversion_info(self):
        """Return information about migration events that were applied to this archive.

        :return: list of conversion notifications
        """
        return self.get_meta_data_member('conversion_info')

    @ensure_within_context
    @ensure_unpacked
    def _read_json_file(self, filename):
        """Read the contents of a JSON file from the unpacked archive contents.

        :param filename: the filename relative to the sandbox folder
        :return: a dictionary with the loaded JSON content

        :raises ~aiida.tools.importexport.common.exceptions.CorruptArchive: if there was an error reading the JSON file
        """
        try:
            with io.open(self.folder.get_abs_path(filename), 'r', encoding='utf8') as fhandle:
                return json.load(fhandle)
        except OSError as error:
            raise CorruptArchive('Error reading {}: {}'.format(filename, error))

    @ensure_within_context
    @ensure_unpacked
    def _read_json_file_content(self, json_filename, key):
        """Return value in JSON file

        :param json_filename: Valid archive JSON file name.
        :type json_filename: str
        :param key: Key matching the value to be returned.
        :type key: str

        :return: Value of key in JSON file
        :rtype: dict, str, list

        :raises ~aiida.tools.importexport.common.exceptions.CorruptArchive: if the key cannot be found in JSON file
        """
        if json_filename == FILENAME_DATA:
            json_content = self.data
            mandatory_keys = self.MANDATORY_DATA_KEYS
        elif json_filename == FILENAME_METADATA:
            json_content = self.meta_data
            mandatory_keys = self.MANDATORY_METADATA_KEYS
        else:
            raise CorruptArchive('{} is not a valid archive JSON file'.format(json_content))

        try:
            return json_content[key]
        except KeyError:
            if key not in mandatory_keys:
                return {}

        raise CorruptArchive('{} is missing the mandatory key "{}"'.format(json_filename, key))

    @ensure_within_context
    def get_data_member(self, member):
        """Return value in data.json

        :param member: Member to be returned, i.e., the dictionary key matching the value to be returned
        :type member: str
        """
        return self._read_json_file_content(FILENAME_DATA, member)

    @ensure_within_context
    def get_meta_data_member(self, member):
        """Return value in metadata.json

        :param member: Member to be returned, i.e., the dictionary key matching the value to be returned
        :type member: str
        """
        return self._read_json_file_content(FILENAME_METADATA, member)

    @ensure_within_context
    @ensure_unpacked
    def _write_json_file(self, filename, data):
        """Write the contents of a dictionary to a JSON file in the unpacked archive.

        :param filename: the filename relative to the sandbox folder
        :type filename: str
        :param data: the data to be written to a JSON file
        :type data: dict

        :raises ~aiida.tools.importexport.common.exceptions.CorruptArchive: if there was an error writing the JSON file
        """
        try:
            with io.open(self.folder.get_abs_path(filename), 'wb') as fhandle:
                json.dump(data, fhandle)

            self._keep = True
        except OSError as error:
            raise ArchiveOperationError('Error writing {}: {}'.format(filename, error))

    @ensure_within_context
    def _redirect_archive_folder(self):
        """Return new Folder, pointing to path, which will not erase path upon exit.

        Erase SandboxFolder, if it was instantiated (it shouldn't have been).
        Redirect self.folder to point at self.filepath, since this should be a valid unpacked archive.
        Before this, however, do a superficial check of the folder's contents.
        """
        from aiida.common.folders import Folder

        if self.folder and isinstance(self.folder, SandboxFolder):
            self.folder.erase()

        # Make sure necessary top-level files and folder exists in the filepath
        for required_file_or_folder in JSON_FILES + [NODES_EXPORT_SUBFOLDER]:
            if not os.path.exists(os.path.join(self.filepath, required_file_or_folder)):
                raise CorruptArchive('required file or folder `{}` is not included'.format(required_file_or_folder))

        self._folder = Folder(self.filepath)


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

            if not handle.infolist():
                raise CorruptArchive('no files detected')

            for json_file in JSON_FILES:
                try:
                    handle.extract(path=folder.abspath, member=json_file)
                except KeyError:
                    raise CorruptArchive('required file `{}` is not included'.format(json_file))

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
        with tarfile.open(infile, 'r:*', format=tarfile.PAX_FORMAT) as handle:

            for json_file in JSON_FILES:
                try:
                    handle.extract(path=folder.abspath, member=handle.getmember(json_file))
                except KeyError:
                    raise CorruptArchive('required file `{}` is not included'.format(json_file))

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
        raise ValueError('The input file format for import is not valid (not a compressed tar file)')
