# -*- coding: utf-8 -*-
import os
from aiida.backends.djsite.db.models import DbNode, DbRepository, DbFile, DbNodeFile
from aiida.common.exceptions import ModificationNotAllowed
from aiida.orm.repotable import Repotable
from django.db import transaction

class DjangoRepotable(Repotable):

    def get_entries(self, node, directory, get_all=False):
        """
        Return all DbNodeFile records belonging to the node that are
        directly in the directory pointed to by 'directory' 

        :param node: instance of Node
        :param directory: string base path within the node's virtual hierarchy
        :return: list of DbNodeFile
        :raises: ValueError if the node does not exist in the database
        """
        try:
            dbnode = DbNode.objects.get(pk=node.pk)
        except DbNode.DoesNotExist:
            raise ValueError("The node '{}' does not exist".format(node.uuid))

        dbnodefiles = DbNodeFile.objects.filter(node__pk=dbnode.pk)

        if get_all:
            return dbnodefiles

        result = []
        for dbnodefile in dbnodefiles:
            current_dir = os.path.normpath(directory) or '.'
            parent_dir  = os.path.dirname(os.path.normpath(dbnodefile.path)) or '.'
            if parent_dir == current_dir:
                result.append(dbnodefile)

        return result


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
        try:
            dbnode = DbNode.objects.get(pk=node.pk)
        except DbNode.DoesNotExist:
            raise ValueError("The node '{}' does not exist".format(node.uuid))

        # Make sure the eventual path has a trailing slash
        path = os.path.join(path, '')

        try:
            dbnodefile = DbNodeFile.objects.get(node__pk=dbnode.pk, path=path)
        except DbNodeFile.DoesNotExist:
            raise ValueError("The directory '{}' does not exist".format(path))

        return dbnodefile


    def get_file(self, node, path):
        """
        Return the DbNodeFile record belonging to the file stored at
        the internal relative path 'path'

        :param node: instance of Node
        :param path: string representing the relative path of the file within the node's virtual hierarchy
        :return: DbNodeFile
        :raises: ValueError if the file does not exist in the database
        """
        try:
            dbnode = DbNode.objects.get(pk=node.pk)
        except DbNode.DoesNotExist:
            raise ValueError("The node '{}' does not exist".format(node.uuid))

        try:
            dbnodefile = DbNodeFile.objects.get(node__pk=dbnode.pk, path=path)
        except DbNodeFile.DoesNotExist:
            raise ValueError("The file '{}' does not exist".format(path))

        return dbnodefile


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
        if node.pk is None:
            raise ValueError('The specified node does not have a pk yet. '
                'This method should only be called from the node.store() method')
        if node.is_stored:
            raise ModificationNotAllowed('The specified node is already stored and directories can no longer be registered')

        try:
            dbnode = DbNode.objects.get(pk=node.pk)
        except DbNode.DoesNotExist as exception:
            raise ValueError('The specified node with pk={} does not exist'.format(node.pk))

        # Make sure the actual path and basepath have trailing slashes
        dir_fullpath = os.path.join(path, '')
        dir_basepath = os.path.join(os.path.dirname(path), '')

        # Check if the path contains subdirectories
        if dir_basepath:

            # Check whether the NodeFile for the basepath already exists
            dbnodefile_base = DbNodeFile.objects.get(node__pk=dbnode.pk, path=dir_basepath)

            if dbnodefile_base:
                dbnodefile = DbNodeFile(node=dbnode, path=dir_fullpath)
            else:
                self.register_directory(node, dir_basepath)

        else:
            dbnodefile = DbNodeFile(node=dbnode, path=dir_fullpath)

        dbnodefile.save()

        return dbnodefile


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
        if node.pk is None:
            raise ValueError('The specified node does not have a pk yet. '
                'This method should only be called from the node.store() method')
        if node.is_stored:
            raise ModificationNotAllowed('The specified node is already stored and files can no longer be registered')

        try:
            dbnode = DbNode.objects.get(pk=node.pk)
        except DbNode.DoesNotExist as exception:
            raise ValueError('The specified node with pk={} does not exist'.format(node.pk))

        try:
            dbrepo = DbRepository.objects.get(name=repo.name)
        except DbRepository.DoesNotExist as exception:
            raise ValueError()

        try:
            sid = transaction.savepoint()

            dbfile = DbFile(repository=dbrepo, key=key)
            dbfile.save()

            dbnodefile = DbNodeFile(file=dbfile, node=dbnode, path=path)
            dbnodefile.save()

            transaction.savepoint_commit(sid)
        except BaseException as e:
            transaction.savepoint_rollback(sid)
            raise

        return dbnodefile