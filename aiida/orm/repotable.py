# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod, abstractproperty


class Repotable(object):
    """
    This is the AiiDA ORM class to access information about the files stored in the repository
    """
    __metaclass__ = ABCMeta


    @abstractmethod
    def get_entries(self, node, directory, get_all=False):
        """
        Return all DbNodeFile records belonging to the node that are
        directly in the directory pointed to by 'directory' 

        :param node: instance of Node
        :param directory: string base path within the node's virtual hierarchy
        :return: list of DbNodeFile
        :raises: ValueError if the node does not exist in the database
        """
        raise NotImplementedError


    @abstractmethod
    def get_directory(self, node, path):
        """
        Return the DbNodeFile record belonging to the directory stored at
        the internal relative path 'path'

        :param node: instance of Node
        :param path: string representing the relative path of the directory within the node's virtual hierarchy
        :return: DbNodeFile
        :raises: ValueError if the node does not exist in the database
        :raises: ValueError if the directory does not exist in the database
        """
        raise NotImplementedError


    @abstractmethod
    def get_file(self, node, path):
        """
        Return the DbNodeFile record belonging to the file stored at
        the internal relative path 'path'

        :param node: instance of Node
        :param path: string representing the relative path of the file within the node's virtual hierarchy
        :return: DbNodeFile
        :raises: ValueError if the file does not exist in the database
        """
        raise NotImplementedError


    @abstractmethod
    def register_directory(self, node, path):
        """
        Register a directory that is stored in the repository to its corresponding node

        A directory can only be registered to a node that already exists in the database
        as the DbNodeFile entry will need the primary key of the DbNode that it belongs
        to, however it should not be possible to add directories to a node that is 
        already stored. This means that the adding of directories to a node can only
        happen in the store() method of the node instance, which is the only
        location where a node instance does have a pk but is not yet 'stored'

        Note that directories are only registered in the DbNodeFile table and
        are not physically created in the Repository.

        :param node: instance of Node
        :param path: string representing the relative path of the file within the node's virtual hierarchy
        """
        raise NotImplementedError


    @abstractmethod
    def register_file(self, node, path, repo, key):
        """
        Register a file that is stored in the repository to its corresponding node

        A file can only be registered to a node that already exists in the database
        as the DbNodeFile entry will need the primary key of the DbNode that it belongs
        to, however it should not be possible to add files to a node that is 
        already stored. This means that the adding of files to a node can only
        happen in the store() method of the node instance, which is the only
        location where a node instance does have a pk but is not yet 'stored'

        :param node: instance of Node
        :param path: string representing the relative path of the file within the node's virtual hierarchy
        :param repo: instance of Repository
        :param key:  string representing the fully qualified URI of the file within the repository
        """
        raise NotImplementedError