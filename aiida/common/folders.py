# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions to operate on filesystem folders."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import fnmatch
import io
import itertools
import os
import shutil
import tempfile

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

import six

from aiida.common.utils import get_repository_folder

# If True, tries to make everything (dirs, files) group-writable.
# Otherwise, tries to make everything only readable and writable by the user.
GROUP_WRITABLE = True

VALID_SECTIONS = ['node']


def find_path(root, dir_name):
    """Iteratively recurse uopwards from a root folder to try and find a given directory.

    :param root: path to start from
    :param dir_name: name of the directory to try and find
    :return: path of the directory if found
    :raises OSError: if directory could not be found
    """
    path = Path(os.path.abspath(root))
    for parent in itertools.chain([path], path.parents):
        directory = parent / dir_name
        if directory.is_dir():
            return directory
    raise OSError('No directory found')


class Folder(object):  # pylint: disable=useless-object-inheritance
    """
    A class to manage generic folders, avoiding to get out of
    specific given folder borders.

    .. todo::
        fix this, os.path.commonprefix of /a/b/c and /a/b2/c will give
        a/b, check if this is wanted or if we want to put trailing slashes.
        (or if we want to use os.path.relpath and check for a string starting
        with os.pardir?)

    .. todo::
        rethink whether the folder_limit option is still useful. If not, remove
        it alltogether (it was a nice feature, but unfortunately all the calls
        to os.path.abspath or normpath are quite slow).
    """

    def __init__(self, abspath, folder_limit=None):
        abspath = os.path.abspath(abspath)
        if folder_limit is None:
            folder_limit = abspath
        else:
            folder_limit = os.path.abspath(folder_limit)

            # check that it is a subfolder
            if not os.path.commonprefix([abspath, folder_limit]) == folder_limit:
                raise ValueError("The absolute path for this folder is not within the "
                                 "folder_limit. abspath={}, folder_limit={}.".format(abspath, folder_limit))

        self._abspath = abspath
        self._folder_limit = folder_limit

    @property
    def mode_dir(self):
        """
        Return the mode with which the folders should be created
        """
        if GROUP_WRITABLE:
            return 0o770

        return 0o700

    @property
    def mode_file(self):
        """
        Return the mode with which the files should be created
        """
        if GROUP_WRITABLE:
            return 0o660

        return 0o600

    def get_subfolder(self, subfolder, create=False, reset_limit=False):
        """
        Return a Folder object pointing to a subfolder.

        :param subfolder: a string with the relative path of the subfolder,
                relative to the absolute path of this object. Note that
                this may also contain '..' parts,
                as far as this does not go beyond the folder_limit.
        :param create: if True, the new subfolder is created, if it does not exist.
        :param reset_limit: when doing ``b = a.get_subfolder('xxx', reset_limit=False)``,
                the limit of b will be the same limit of a.
                if True, the limit will be set to the boundaries of folder b.

        :Returns: a Folder object pointing to the subfolder.
        """
        dest_abs_dir = os.path.abspath(os.path.join(self.abspath, six.text_type(subfolder)))

        if reset_limit:
            # Create a new Folder object, with a limit to itself (cannot go
            # back to this folder)
            folder_limit = None
        else:
            # Create a new Folder object, with the same limit of the parent
            folder_limit = self.folder_limit

        new_folder = Folder(abspath=dest_abs_dir, folder_limit=folder_limit)

        if create:
            new_folder.create()

        return new_folder

    def get_content_list(self, pattern='*', only_paths=True):
        """
        Return a list of files (and subfolders) in the folder,
        matching a given pattern.

        Example: If you want to exclude files starting with a dot, you can
        call this method with ``pattern='[!.]*'``

        :param pattern: a pattern for the file/folder names, using Unix filename
                pattern matching (see Python standard module fnmatch).
                By default, pattern is '*', matching all files and folders.
        :param only_paths: if False (default), return pairs (name, is_file).
                if True, return only a flat list.

        :Returns:
            a list of tuples of two elements, the first is the file name and
            the second is True if the element is a file, False if it is a
            directory.
        """
        file_list = [fname for fname in os.listdir(self.abspath) if fnmatch.fnmatch(fname, pattern)]

        if only_paths:
            return file_list

        return [(fname, not os.path.isdir(os.path.join(self.abspath, fname))) for fname in file_list]

    def create_symlink(self, src, name):
        """
        Create a symlink inside the folder to the location 'src'.

        :param src: the location to which the symlink must point. Can be
                either a relative or an absolute path. Should, however,
                be relative to work properly also when the repository is
                moved!
        :param name: the filename of the symlink to be created.
        """
        dest_abs_path = self.get_abs_path(name)
        os.symlink(src, dest_abs_path)

        # For symlinks, permissions should not be set

    def insert_path(self, src, dest_name=None, overwrite=True):
        """
        Copy a file to the folder.

        :param src: the source filename to copy
        :param dest_name: if None, the same basename of src is used. Otherwise,
                the destination filename will have this file name.
        :param overwrite: if ``False``, raises an error on existing destination;
                otherwise, delete it first.
        """
        # pylint: disable=too-many-branches
        if dest_name is None:
            filename = six.text_type(os.path.basename(src))
        else:
            filename = six.text_type(dest_name)

        src = six.text_type(src)

        dest_abs_path = self.get_abs_path(filename)

        if not os.path.isabs(src):
            raise ValueError("src must be an absolute path in insert_file")

        # In this way, the destination is always correct (i.e., if I copy to a
        # folder, I point to the correct location inside it)
        if os.path.isdir(dest_abs_path):
            dest_abs_path = os.path.join(dest_abs_path, os.path.basename(src))

        if os.path.isfile(src):
            if os.path.exists(dest_abs_path):
                if overwrite:
                    if os.path.isdir(dest_abs_path):
                        shutil.rmtree(dest_abs_path)
                    else:
                        os.remove(dest_abs_path)
                    # This automatically overwrites files
                    shutil.copyfile(src, dest_abs_path)
                else:
                    raise IOError("destination already exists: {}".format(os.path.join(dest_abs_path)))
            else:
                shutil.copyfile(src, dest_abs_path)
        elif os.path.isdir(src):
            if os.path.exists(dest_abs_path):
                if overwrite:
                    if os.path.isdir(dest_abs_path):
                        shutil.rmtree(dest_abs_path)
                    else:
                        os.remove(dest_abs_path)
                    # This automatically overwrites files
                    shutil.copytree(src, dest_abs_path)
                else:
                    raise IOError("destination already exists: {}".format(os.path.join(dest_abs_path)))
            else:
                shutil.copytree(src, dest_abs_path)
        else:
            raise ValueError("insert_path can only insert files or paths, not symlinks or the like")

        return dest_abs_path

    def create_file_from_filelike(self, filelike, filename, mode='wb', encoding=None):
        """Create a file with the given filename from a filelike object.

        :param filelike: a filelike object whose contents to copy
        :param filename: the filename for the file that is to be created
        :param mode: the mode with which the target file will be written
        :param encoding: the encoding with which the target file will be written
        :return: the absolute filepath of the created file
        """
        filename = six.text_type(filename)
        filepath = self.get_abs_path(filename)

        with io.open(filepath, mode=mode, encoding=encoding) as handle:

            # In python 2 a string literal can either be of unicode or string (bytes) type. Since we do not know what
            # will be coming in, if the requested mode is not binary, in the case of incoming bytes, the content will
            # have to be encoded. Therefore in the case of a non-binary mode for python2, we attempt to encode the
            # incoming filelike object and in case of failure do nothing.
            if six.PY2 and 'b' not in mode:
                import codecs
                utf8reader = codecs.getreader('utf8')

                try:
                    shutil.copyfileobj(utf8reader(filelike), handle)
                except (UnicodeDecodeError, UnicodeEncodeError):
                    shutil.copyfileobj(filelike, handle)
            else:
                shutil.copyfileobj(filelike, handle)

        os.chmod(filepath, self.mode_file)

        return filepath

    def remove_path(self, filename):
        """
        Remove a file or folder from the folder.

        :param filename: the relative path name to remove
        """
        # I get the full path of the filename, checking also that I don't
        # go beyond the folder limits
        dest_abs_path = self.get_abs_path(filename, check_existence=True)

        if os.path.isdir(dest_abs_path):
            shutil.rmtree(dest_abs_path)
        else:
            os.remove(dest_abs_path)

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
        if os.path.isabs(relpath):
            raise ValueError("relpath must be a relative path")
        dest_abs_path = os.path.join(self.abspath, relpath)

        if not os.path.commonprefix([dest_abs_path, self.folder_limit]) == self.folder_limit:
            errstr = "You didn't specify a valid filename: {}".format(relpath)
            raise ValueError(errstr)

        if check_existence:
            if not os.path.exists(dest_abs_path):
                raise OSError("{} does not exist within the folder {}".format(relpath, self.abspath))

        return dest_abs_path

    def open(self, name, mode='r', encoding='utf8', check_existence=False):
        """
        Open a file in the current folder and return the corresponding file object.

        :param check_existence: if False, just return the file path.
            Otherwise, also check if the file or directory actually exists.
            Raise OSError if it does not.
        """
        if 'b' in mode:
            encoding = None

        return io.open(self.get_abs_path(name, check_existence=check_existence), mode, encoding=encoding)

    @property
    def abspath(self):
        """
        The absolute path of the folder.
        """
        return self._abspath

    @property
    def folder_limit(self):
        """
        The folder limit that cannot be crossed when creating files and folders.
        """
        return self._folder_limit

    def exists(self):
        """
        Return True if the folder exists, False otherwise.
        """
        return os.path.exists(self.abspath)

    def isfile(self, relpath):
        """
        Return True if 'relpath' exists inside the folder and is a file,
        False otherwise.
        """
        return os.path.isfile(os.path.join(self.abspath, relpath))

    def isdir(self, relpath):
        """
        Return True if 'relpath' exists inside the folder and is a directory,
        False otherwise.
        """
        return os.path.isdir(os.path.join(self.abspath, relpath))

    def erase(self, create_empty_folder=False):
        """
        Erases the folder. Should be called only in very specific cases,
        in general folder should not be erased!

        Doesn't complain if the folder does not exist.

        :param create_empty_folder: if True, after erasing, creates an empty dir.
        """
        if self.exists():
            shutil.rmtree(self.abspath)

        if create_empty_folder:
            self.create()

    def create(self):
        """
        Creates the folder, if it does not exist on the disk yet.

        It will also create top directories, if absent.

        It is always safe to call it, it will do nothing if the folder
        already exists.
        """
        if not self.exists():
            os.makedirs(self.abspath, mode=self.mode_dir)

    def replace_with_folder(self, srcdir, move=False, overwrite=False):
        """
        This routine copies or moves the source folder 'srcdir' to the local
        folder pointed by this Folder object.

        :param srcdir: the source folder on the disk; this must be a string with
                an absolute path
        :param move: if True, the srcdir is moved to the repository. Otherwise, it
                is only copied.
        :param overwrite: if True, the folder will be erased first.
                if False, a IOError is raised if the folder already exists.
                Whatever the value of this flag, parent directories will be
                created, if needed.

        :Raises:
            OSError or IOError: in case of problems accessing or writing
            the files.
        :Raises:
            ValueError: if the section is not recognized.
        """
        if not os.path.isabs(srcdir):
            raise ValueError('srcdir must be an absolute path')
        if overwrite:
            self.erase()
        elif self.exists():
            raise IOError("Location {} already exists, and overwrite is set to False".format(self.abspath))

        # Create parent dir, if needed, with the right mode
        pardir = os.path.dirname(self.abspath)
        if not os.path.exists(pardir):
            os.makedirs(pardir, mode=self.mode_dir)

        if move:
            shutil.move(srcdir, self.abspath)
        else:
            shutil.copytree(srcdir, self.abspath)

        # Set the mode also for the current dir, recursively
        for dirpath, _, filenames in os.walk(self.abspath, followlinks=False):
            # dirpath should already be absolute, because I am passing
            # an absolute path to os.walk
            os.chmod(dirpath, self.mode_dir)
            for filename in filenames:
                # do not change permissions of symlinks (this would
                # actually change permissions of the linked file/dir)
                # Toc check whether this is a big speed loss
                full_file_path = os.path.join(dirpath, filename)
                if not os.path.islink(full_file_path):
                    os.chmod(full_file_path, self.mode_file)


class SandboxFolder(Folder):
    """
    A class to manage the creation and management of a sandbox folder.

    Note: this class must be used within a context manager, i.e.:

    with SandboxFolder as f:
        ## do something with f

    In this way, the sandbox folder is removed from disk
    (if it wasn't removed already) when exiting the 'with' block.

    .. todo:: Implement check of whether the folder has been removed.
    """

    def __init__(self, sandbox_in_repo=True):
        """
        Initializes the object by creating a new temporary folder in the
        sandbox.

        :param bool sandbox_in_repo:
            If True (default), creates the folder in the repository.
            If false,  relies on the defaults of tempfile.mkdtemp
        """
        # First check if the sandbox folder already exists
        if sandbox_in_repo:
            sandbox = get_repository_folder('sandbox')
            if not os.path.exists(sandbox):
                os.makedirs(sandbox)
            abspath = tempfile.mkdtemp(dir=sandbox)
        else:
            abspath = tempfile.mkdtemp()
        super(SandboxFolder, self).__init__(abspath=abspath)

    def __enter__(self):
        """
        Called when entering in the with statement
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        In exit, I remove the sandbox folder from disk, if it still exists
        """
        self.erase()


class RepositoryFolder(Folder):
    """
    A class to manage the local AiiDA repository folders.
    """

    def __init__(self, section, uuid, subfolder=os.curdir):
        """
        Initializes the object by pointing it to a folder in the repository.

        Pass the uuid as a string.
        """
        if section not in VALID_SECTIONS:
            retstr = ("Repository section '{}' not allowed. "
                      "Valid sections are: {}".format(section, ",".join(VALID_SECTIONS)))
            raise ValueError(retstr)
        self._section = section
        self._uuid = uuid

        # If you want to change the sharding scheme, this is the only place
        # where changes should be needed FOR NODES AND WORKFLOWS
        # Of course, remember to migrate data!
        # We set a sharding of level 2+2
        # Note that a similar sharding should probably has to be done
        # independently for calculations sent to remote computers in the
        # execmanager.
        # Note: I don't do any os.path.abspath (that internally calls
        # normpath, that may be slow): this is done abywat by the super
        # class.
        entity_dir = os.path.join(
            get_repository_folder('repository'), six.text_type(section),
            six.text_type(uuid)[:2],
            six.text_type(uuid)[2:4],
            six.text_type(uuid)[4:])
        dest = os.path.join(entity_dir, six.text_type(subfolder))

        # Internal variable of this class
        self._subfolder = subfolder

        # This will also do checks on the folder limits
        super(RepositoryFolder, self).__init__(abspath=dest, folder_limit=entity_dir)

    @property
    def section(self):
        """
        The section to which this folder belongs.
        """
        return self._section

    @property
    def uuid(self):
        """
        The uuid to which this folder belongs.
        """
        return self._uuid

    @property
    def subfolder(self):
        """
        The subfolder within the section/uuid folder.
        """
        return self._subfolder

    def get_topdir(self):
        """
        Returns the top directory, i.e., the section/uuid folder object.
        """
        return RepositoryFolder(self.section, self.uuid)

        # NOTE! The get_subfolder method will return a Folder object, and not a RepositoryFolder object
