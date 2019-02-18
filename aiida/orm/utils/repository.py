# -*- coding: utf-8 -*-
"""Class that represents the repository of a `Node` instance."""
from __future__ import absolute_import

import os

from aiida.common import exceptions
from aiida.common.folders import RepositoryFolder, SandboxFolder


class Repository(object):  # pylint: disable=useless-object-inheritance
    """
    A mixin class that knows about file repositories, to mix in
    with the BackendNode class
    """

    # Name to be used for the Repository section
    _section_name = 'node'

    # The name of the subfolder in which to put the files/directories
    # added with add_path
    _path_subfolder_name = 'path'

    # Flag that says if the node is storable or not.
    # By default, bare nodes (and also ProcessNodes) are not storable,
    # all subclasses (WorkflowNode, CalculationNode, Data and their subclasses)
    # are storable. This flag is checked in store()
    _storable = False
    _unstorable_message = 'only Data, WorkflowNode, CalculationNode or their subclasses can be stored'

    def __init__(self, uuid, is_stored):
        self._is_stored = is_stored
        self._temp_folder = None
        self._repo_folder = RepositoryFolder(section=self._section_name, uuid=uuid)

    def __del__(self):
        """Clean the sandboxfolder if it was instantiated."""
        if getattr(self, '_temp_folder', None) is not None:
            self._temp_folder.erase()

    @property
    def folder(self):
        """
        Get the folder associated with the node,
        whether it is in the temporary or the permanent repository.

        :return: the RepositoryFolder object.
        """
        if self._is_stored:
            return self._repo_folder

        return self._get_temp_folder()

    def store(self):
        """Store the contents of the sandbox folder into the repository folder."""
        self._repo_folder.replace_with_folder(self._get_temp_folder().abspath, move=True, overwrite=True)
        self._is_stored = True

    def restore(self):
        """Move the contents from the repository folder back into the sandbox folder."""
        self._temp_folder.replace_with_folder(self._repo_folder.abspath, move=True, overwrite=True)
        self._is_stored = False

    @property
    def _get_folder_pathsubfolder(self):
        """
        Get the subfolder in the repository.

        :return: a Folder object.
        """
        return self.folder.get_subfolder(self._path_subfolder_name, reset_limit=True)

    def get_abs_path(self, relpath, check_existence=False):
        """
        Return an absolute path for a file or folder in this folder.

        The advantage of using this method is that it checks that filename
        is a valid filename within this folder,
        and not something e.g. containing slashes.

        :param filename: The file or directory.
        :param check_existence: if False, just return the file path.
            Otherwise, also check if the file or directory actually exists.
            Raise OSError if it does not.
        """
        return self._get_folder_pathsubfolder.get_abs_path(relpath, check_existence)

    def get_folder_list(self, subfolder='.'):
        """
        Get the the list of files/directory in the repository of the object.

        :param subfolder: get the list of a subfolder
        :return: a list of strings.
        """
        return self._get_folder_pathsubfolder.get_subfolder(subfolder).get_content_list()

    def _get_temp_folder(self):
        """
        Get the folder of the Node in the temporary repository.

        :return: a SandboxFolder object mapping the node in the repository.
        """
        # I create the temp folder only at is first usage
        if self._temp_folder is None:
            self._temp_folder = SandboxFolder()  # This is also created
            # Create the 'path' subfolder in the Sandbox
            self._get_folder_pathsubfolder.create()
        return self._temp_folder

    def remove_path(self, path):
        """
        Remove a file or directory from the repository directory.
        Can be called only before storing.

        :param str path: relative path to file/directory.
        """
        if self._is_stored:
            raise exceptions.ModificationNotAllowed("Cannot delete a path after storing the node")

        if os.path.isabs(path):
            raise ValueError("The destination path in remove_path " "must be a relative path")
        self._get_folder_pathsubfolder.remove_path(path)

    def add_path(self, src_abs, dst_path=None):
        """
        Copy a file or folder from a local file inside the repository directory.
        If there is a subpath, folders will be created.

        Copy to a cache directory if the entry has not been saved yet.

        :param str src_abs: the absolute path of the file to copy.
        :param str dst_filename: the (relative) path on which to copy.

        :todo: in the future, add an add_attachment() that has the same
            meaning of a extras file. Decide also how to store. If in two
            separate subfolders, remember to reset the limit.
        """
        if self._is_stored:
            raise exceptions.ModificationNotAllowed("Cannot insert a path after storing the node")

        if not os.path.isabs(src_abs):
            raise ValueError("The source path in add_path must be absolute")
        if os.path.isabs(dst_path):
            raise ValueError("The destination path in add_path must be a filename without any subfolder")
        self._get_folder_pathsubfolder.insert_path(src_abs, dst_path)

    def create_file_from_filelike(self, src_filelike, dest_name):
        self._get_folder_pathsubfolder.create_file_from_filelike(src_filelike, dest_name)
