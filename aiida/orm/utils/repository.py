# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Class that represents the repository of a `Node` instance."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import collections
import enum
import io
import os

from aiida.common import exceptions
from aiida.common.folders import RepositoryFolder, SandboxFolder


class FileType(enum.Enum):

    DIRECTORY = 0
    FILE = 1


File = collections.namedtuple('File', ['name', 'type'])


class Repository(object):  # pylint: disable=useless-object-inheritance
    """Class that represents the repository of a `Node` instance."""

    # Name to be used for the Repository section
    _section_name = 'node'

    def __init__(self, uuid, is_stored, base_path=None):
        self._is_stored = is_stored
        self._base_path = base_path
        self._temp_folder = None
        self._repo_folder = RepositoryFolder(section=self._section_name, uuid=uuid)

    def __del__(self):
        """Clean the sandboxfolder if it was instantiated."""
        if getattr(self, '_temp_folder', None) is not None:
            self._temp_folder.erase()

    def validate_mutability(self):
        """Raise if the repository is immutable.

        :raises aiida.common.ModificationNotAllowed: if repository is marked as immutable because the corresponding node
            is stored
        """
        if self._is_stored:
            raise exceptions.ModificationNotAllowed('cannot modify the repository after the node has been stored')

    @staticmethod
    def validate_object_key(key):
        """Validate the key of an object.

        :param key: an object key in the repository
        :raises ValueError: if the key is not a valid object key
        """
        if key and os.path.isabs(key):
            raise ValueError('the key must be a relative path')

    def list_objects(self, key=None):
        """Return a list of the objects contained in this repository, optionally in the given sub directory.

        :param key: fully qualified identifier for the object within the repository
        :return: a list of `File` named tuples representing the objects present in directory with the given key
        """
        folder = self._get_base_folder()

        if key:
            folder = folder.get_subfolder(key)

        objects = []

        for filename in folder.get_content_list():
            if os.path.isdir(os.path.join(folder.abspath, filename)):
                objects.append(File(filename, FileType.DIRECTORY))
            else:
                objects.append(File(filename, FileType.FILE))

        return sorted(objects, key=lambda x: x.name)

    def list_object_names(self, key=None):
        """Return a list of the object names contained in this repository, optionally in the given sub directory.

        :param key: fully qualified identifier for the object within the repository
        :return: a list of `File` named tuples representing the objects present in directory with the given key
        """
        return [entry.name for entry in self.list_objects(key)]

    def open(self, key, mode='r'):
        """Open a file handle to an object stored under the given key.

        :param key: fully qualified identifier for the object within the repository
        :param mode: the mode under which to open the handle
        """
        return io.open(self._get_base_folder().get_abs_path(key), mode=mode)

    def get_object(self, key):
        """Return the object identified by key.

        :param key: fully qualified identifier for the object within the repository
        :return: a `File` named tuple representing the object located at key
        """
        self.validate_object_key(key)

        try:
            directory, filename = key.rsplit(os.sep, 1)
        except ValueError:
            directory, filename = None, key

        folder = self._get_base_folder()

        if directory:
            folder = folder.get_subfolder(directory)

        if os.path.isdir(os.path.join(folder.abspath, filename)):
            return File(filename, FileType.DIRECTORY)

        return File(filename, FileType.FILE)

    def get_object_content(self, key):
        """Return the content of a object identified by key.

        :param key: fully qualified identifier for the object within the repository
        """
        with self.open(key) as handle:
            return handle.read()

    def put_object_from_tree(self, path, key=None, contents_only=True, force=False):
        """Store a new object under `key` with the contents of the directory located at `path` on this file system.

        .. warning:: If the repository belongs to a stored node, a `ModificationNotAllowed` exception will be raised.
            This check can be avoided by using the `force` flag, but this should be used with extreme caution!

        :param path: absolute path of directory whose contents to copy to the repository
        :param key: fully qualified identifier for the object within the repository
        :param contents_only: boolean, if True, omit the top level directory of the path and only copy its contents.
        :param force: boolean, if True, will skip the mutability check
        :raises aiida.common.ModificationNotAllowed: if repository is immutable and `force=False`
        """
        if not force:
            self.validate_mutability()

        self.validate_object_key(key)

        if not os.path.isabs(path):
            raise ValueError('the `path` must be an absolute path')

        folder = self._get_base_folder()

        if key:
            folder = folder.get_subfolder(key, create=True)

        if contents_only:
            for entry in os.listdir(path):
                folder.insert_path(os.path.join(path, entry))
        else:
            folder.insert_path(path)

    def put_object_from_file(self, path, key, mode='w', encoding='utf8', force=False):
        """Store a new object under `key` with contents of the file located at `path` on this file system.

        .. warning:: If the repository belongs to a stored node, a `ModificationNotAllowed` exception will be raised.
            This check can be avoided by using the `force` flag, but this should be used with extreme caution!

        :param path: absolute path of file whose contents to copy to the repository
        :param key: fully qualified identifier for the object within the repository
        :param mode: the file mode with which the object will be written
        :param encoding: the file encoding with which the object will be written
        :param force: boolean, if True, will skip the mutability check
        :raises aiida.common.ModificationNotAllowed: if repository is immutable and `force=False`
        """
        if not force:
            self.validate_mutability()

        self.validate_object_key(key)

        with io.open(path) as handle:
            self.put_object_from_filelike(handle, key, mode=mode, encoding=encoding)

    def put_object_from_filelike(self, handle, key, mode='w', encoding='utf8', force=False):
        """Store a new object under `key` with contents of filelike object `handle`.

        .. warning:: If the repository belongs to a stored node, a `ModificationNotAllowed` exception will be raised.
            This check can be avoided by using the `force` flag, but this should be used with extreme caution!

        :param handle: filelike object with the content to be stored
        :param key: fully qualified identifier for the object within the repository
        :param mode: the file mode with which the object will be written
        :param encoding: the file encoding with which the object will be written
        :param force: boolean, if True, will skip the mutability check
        :raises aiida.common.ModificationNotAllowed: if repository is immutable and `force=False`
        """
        if not force:
            self.validate_mutability()

        self.validate_object_key(key)

        folder = self._get_base_folder()

        if os.sep in key:
            basepath, key = key.split(os.sep, 1)
            folder = folder.get_subfolder(basepath, create=True)

        folder.create_file_from_filelike(handle, key, mode=mode, encoding=encoding)

    def delete_object(self, key, force=False):
        """Delete the object from the repository.

        .. warning:: If the repository belongs to a stored node, a `ModificationNotAllowed` exception will be raised.
            This check can be avoided by using the `force` flag, but this should be used with extreme caution!

        :param key: fully qualified identifier for the object within the repository
        :param force: boolean, if True, will skip the mutability check
        :raises aiida.common.ModificationNotAllowed: if repository is immutable and `force=False`
        """
        if not force:
            self.validate_mutability()

        self.validate_object_key(key)

        self._get_base_folder().remove_path(key)

    def erase(self, force=False):
        """Delete the repository folder.

        .. warning:: If the repository belongs to a stored node, a `ModificationNotAllowed` exception will be raised.
            This check can be avoided by using the `force` flag, but this should be used with extreme caution!

        :param force: boolean, if True, will skip the mutability check
        :raises aiida.common.ModificationNotAllowed: if repository is immutable and `force=False`
        """
        if not force:
            self.validate_mutability()

        self._repo_folder.erase()

    def store(self):
        """Store the contents of the sandbox folder into the repository folder."""
        if self._is_stored:
            raise exceptions.ModificationNotAllowed('repository is already stored')

        self._repo_folder.replace_with_folder(self._get_temp_folder().abspath, move=True, overwrite=True)
        self._is_stored = True

    def restore(self):
        """Move the contents from the repository folder back into the sandbox folder."""
        if not self._is_stored:
            raise exceptions.ModificationNotAllowed('repository is not yet stored')

        self._temp_folder.replace_with_folder(self._repo_folder.abspath, move=True, overwrite=True)
        self._is_stored = False

    def _get_base_folder(self):
        """Return the base sub folder in the repository.

        :return: a Folder object.
        """
        if self._is_stored:
            folder = self._repo_folder
        else:
            folder = self._get_temp_folder()

        if self._base_path is not None:
            folder = folder.get_subfolder(self._base_path, reset_limit=True)
            folder.create()

        return folder

    def _get_temp_folder(self):
        """Return the temporary sandbox folder.

        :return: a SandboxFolder object mapping the node in the repository.
        """
        if self._temp_folder is None:
            self._temp_folder = SandboxFolder()

        return self._temp_folder
