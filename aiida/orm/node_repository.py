# -*- coding: utf-8 -*-
import os
from aiida.common.exceptions import ModificationNotAllowed

class NodeRepository(object):
    """
    The class that serves as the gateway for a Node to register and retrieve files that it
    has stored in a repository. If one ever needs to register new files or directories in a
    repository for a Node, or one wants to retrieve already registered files, one should 
    always and only go through the NodeRepository
    """

    def __init__(self, node, repository, repotable):
        self._node = node
        self._repository = repository
        self._repotable = repotable


    def copy_tree(self, path_tree):
        """
        Copy the entire tree at path to the node repository

        :param path_tree: absolute path to the beginning of the tree that is to be copied
        """
        for root, directories, files in os.walk(path_tree):

            # Relative base path of current root with respect to path of the tree
            basepath = os.path.relpath(root, path_tree)

            for directory in directories:
                path_relative = os.path.normpath(os.path.join(basepath, directory))
                self.put_directory(path_relative)

            for file in files:
                path_absolute = os.path.join(root, file)
                path_relative = os.path.normpath(os.path.join(basepath, file))

                with open(path_absolute, 'rb') as fp:
                    self.put_file(fp, path_relative)


    def get_directory(self, path):
        """
        Return the NodeFile corresponding to the directory
        with internal relative path 'path'

        :param path: string representing the relative path of the directory within the node's virtual hierarchy
        :return: DbNodeFile
        :raises: ValueError if the directory does not exist in the database
        """
        try:
            dbnodefile = self._repotable.get_directory(self._node, path)
        except ValueError as exception:
            raise

        return dbnodefile


    def get_file(self, path):
        """
        Return the NodeFile corresponding to the file
        with internal relative path 'path'

        :param path: string representing the relative path of the file within the node's virtual hierarchy
        :return: DbNodeFile
        :raises: ValueError if the directory does not exist in the database
        """
        try:
            dbnodefile = self._repotable.get_file(self._node, path)
        except ValueError as exception:
            raise

        return dbnodefile


    def get_file_content(self, path):
        """
        Return the content of a given file with filepath 'path'

        :param path: string representing the relative path of the file within the node's virtual hierarchy
        :return: string with content of the file
        :raises: ValueError if the directory does not exist in the database
        """
        try:
            dbfile = self._repotable.get_file(self._node, path).file
            content = self._repository.get_object(dbfile.key)
        except ValueError as exception:
            raise

        return content


    def put_directory(self, path, recursive=False, stop_if_exists=True):
        """
        Creates a new empty directory. The directory will only be registered
        in the database and will not physically be created in the actual repository.
        Raises an exception if the directory already exists and stop_if_exists=True

        :param path: relative path of the directory within the node's virtual hierarchy
        :param recursive: if True will create non-existing subfolders first
        :param stop_if_exists: relative path of the directory within the node's virtual hierarchy
        """
        try:
            self._repotable.register_directory(node=self._node, path=path)
        except ValueError as exception:
            raise
        except ModificationNotAllowed as exception:
            raise


    def put_file(self, source, path):
        """
        This function will attempt to have the Repository write the source
        to path, relative to the virtual file hierarchy of the node.
        Only when Repository successfully stored the source, is the file
        registered with the Repotable.

        Since the register_file method of the Repotable can only be called
        from within the store method of the Node, this method put_file can
        in turn also only be called from within a node's store method

        The Repository might potentially change the key, for example in a
        naming clash, but will always return the key that is actually used.
        The call to the Repotable should therefore always use the returned
        key.

        :param source: filelike object with the to be written content
        :param path: relative path of the file within the virtual file hierarchy of the node
        """
        try:
            uuid = self._node.uuid
            key = os.path.join('repository', 'node', uuid[:2], uuid[2:4], uuid[4:], 'path', path)
            key = self._repository.put_new_object(key, source)
        except ValueError as exception:
            raise
        except ModificationNotAllowed as exception:
            raise

        self._repotable.register_file(self._node, path, self._repository, key)


    def ls(self, directory='.', sort=True):
        """
        Return a list of files and directories that are stored in 'directory' of the
        virtual file hierarchy of the node

        :param directory: relative path whose contents to return
        :return: list of DbNodeFile
        """
        entries = self._repotable.get_entries(self._node, directory)

        if entries and sort:
            entries.sort(key=lambda x: x.path, reverse=False)

        return entries


    def print_tree(self, directory='.', indentation=4, sort=True):
        """
        Visualize the virtual file hierarchy of the node starting from
        the path 'directory'

        :param directory: relative path to base directory
        """
        self.print_branch(directory, level=0, indentation=indentation, sort=sort)


    def print_branch(self, directory, level, indentation, sort=True):
        """
        Visualize the virtual file hierarchy of the node starting from
        the path 'directory'

        :param directory: relative path to base directory
        """
        for dbnodefile in self.ls(directory, sort=sort):
            indent = ' ' * indentation * level
            print '{}{}'.format(indent, os.path.basename(os.path.normpath(dbnodefile.path)))
            self.print_branch(dbnodefile.path, level=level+1, indentation=indentation, sort=sort)