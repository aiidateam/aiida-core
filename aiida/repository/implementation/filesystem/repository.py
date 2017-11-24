# -*- coding: utf-8 -*-
import os
import errno
import shutil
from abc import ABCMeta, abstractmethod
from aiida.repository.repository import Repository

class FileSystemRepository(Repository):
    """
    Filesystem implementation for the permanent repository where files associated with nodes will be
    stored that need to be kept permanently
    """

    __metaclass__ = ABCMeta

    def __init__(self, repo_config):
        """
        Requires the following parameters to properly configure the Repository

         * repo_name: A human readable label that is stored in the database and is also used
                      as the key to retrieve the corresponding settings from the configuration
         * base_path: Absolute path that points to the root folder of the repository
         * uuid_path: Absolute path of file that contains the UUID of the repository

        :param repo_config: dictionary with configuration details for repository
        """
        self.repo_name = repo_config['repo_name']
        self.base_path = repo_config['base_path']
        self.uuid_path = repo_config['uuid_path']


    def _mkdir(self, path):
        """
        Given a directory path, will attempt to create the directory even
        if it contains multiple nested directories that do not exist yet

        :param path: string directory path
        """
        try:
            os.makedirs(path)
        except OSError as error:
            if error.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise


    def _uniquify(self, key):
        """
        Given a key for an object, make sure it is unique, by adding a suffix
        of the format '(%d)' to the original key, such that the resulting new key
        corresponds to a filepath that does not yet exist.

        :param key: string with object key
        :return: string with unique object key
        """
        filepath = os.path.join(self.base_path, key)

        count = 1
        unique_path = '%s(%d)' % (filepath, count)
        while os.path.isfile(unique_path):
            count += 1
            unique_path = '%s(%d)' % (filepath, count)

        unique_key = os.path.relpath(unique_path, self.base_path)

        return unique_key


    def _validate_key(self, key):
        """
        Validate a key. In this file system implementation the key actually represents
        a real path, within the repository, where the content of an object will be
        stored in the file system.

        :raise ValueError: raises exception if key is not a normalized path
        :raise ValueError: raises exception if key represenat a path outside the current parent directory
        """
        if key != os.path.normpath(key):
            raise ValueError("Only normalized paths are allowed {}".format(os.path.normpath(key)))
        if key.startswith(os.path.pardir):
            raise ValueError("Cannot go outside parent directory: '{}'".format(key))


    def clean(self):
        """
        Completely clean the repository, i.e. remove all objects
        while making sure that the uuid file is kept
        """
        uuid = self.get_uuid()

        shutil.rmtree(self.base_path, ignore_errors=True)
        os.makedirs(self.base_path)

        with open(self.uuid_path, 'w') as f:
            f.write(uuid)


    def get_name(self):
        """
        Return the name of the repository which is a human-readable label

        :return name: the human readable label associated with this repository
        """
        return self.repo_name


    def set_uuid(self, uuid):
        """
        Store the UUID identifying the repository in itself.
        Each implementation will decide how to store it.

        :param uuid: the uuid associated with this repository
        :raise Exception: raises exception if storing failed 
        """
        with open(self.uuid_path, 'w') as f:
            f.write(uuid)


    def get_uuid(self):
        """
        Return the UUID identifying the repository.
        Each implementation will decide how to store it: 
        e.g. in a FS it could be a file repo_uuid.txt in the main folder,
        in a object store it could be stored under a key name 'repo_uuid' (making
        sure no object can be stored with the same name) etc.

        :return uuid: the uuid associated with this repository
        :raise ValueError: raises exception if the file that should contain the repo uuid cannot be read
        """
        try:
            with open(self.uuid_path) as f:
                content = f.read()
        except IOError as error:
            raise ValueError("Cannot read '{}' and therefore cannot retrieve the UUID associated with this repository".format(self.uuid_path))

        return content.strip()


    def exists(self, key):
        """
        Determine whether the object identified by key exists and is readable

        :return boolean: returns True if the object exists and is readable, False otherwise
        """
        filepath = os.path.join(self.base_path, key)
        try:
            with open(filepath) as f:
                is_readable = True
        except IOError as error:
            is_readable = False

        return is_readable


    def put_object(self, key, source, stop_if_exists=False):
        """
        Store a new object under 'key' with contents 'source' if it does not yet exist.
        Overwrite an existing object if stop_if_exists is set to False.
        Raise an exception if stop_if_exists is True and the object already exists.

        :param key: fully qualified identifier for the object within the repository
        :param source: filelike object with the content to be stored
        :param stop_if_exists:
        """
        self._validate_key(key)

        if stop_if_exists and self.exists(key):
            raise ValueError("Cannot write to '{}' because the object already exists".format(key))

        directory = os.path.join(self.base_path, os.path.dirname(key))
        filepath  = os.path.join(self.base_path, key)

        try:
            self._mkdir(directory)

            with open(filepath, 'w') as f:
                f.write(source.read())
                source.seek(0)
        except IOError as error:
            raise ValueError("Writing object with key '{}' to '{}' failed".format(key, os.path.join(self.base_path, key)))

        return key


    def put_new_object(self, key, source):
        """
        Store a new object under 'key' with contents 'source'
        If the provided key already exists, it will be adapted to
        ensure that it is unique. The eventual key under which the
        newly created object is stored is returned upon success

        :param key: fully qualified identifier for the object within the repository
        :param source: filelike object with the content to be stored
        :return: the key of the newly generated object
        """
        if self.exists(key):
            key = self._uniquify(key)

        try:
            key = self.put_object(key, source, True)
        except ValueError as error:
            raise

        return key


    def get_object(self, key):
        """
        Return the content of a object identified by key

        :param key: fully qualified identifier for the object within the repository
        :raise ValueError: raises exception if given key can not be resolved to readable object
        """
        filepath = os.path.join(self.base_path, key)
        try:
            with open(filepath) as f:
                content = f.read()
        except IOError as error:
            raise ValueError("Provided key can not be mapped to an existing object")

        return content


    def del_object(self, key):
        """
        Delete the object from the repository

        :param key: fully qualified identifier for the object within the repository
        :raises: OSErrors are reraised except in the case of errno.ENOENT which means the object did not exist
        """
        filepath = os.path.join(self.base_path, key)
        try:
            os.remove(filepath)
        except OSError as error:
            if error.errno != errno.ENOENT:
                raise

        return