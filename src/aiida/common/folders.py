###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions to operate on filesystem folders."""

from __future__ import annotations

import contextlib
import errno
import fnmatch
import os
import pathlib
import shutil
import tempfile
import typing as t
from collections.abc import Iterator

from typing_extensions import Self

from . import timezone
from .lang import type_check
from .typing import FilePath

# If True, tries to make everything (dirs, files) group-writable.
# Otherwise, tries to make everything only readable and writable by the user.
GROUP_WRITABLE = True

# Name of directory in which to place the input files created by running a dry run for a `CalcJob`
CALC_JOB_DRY_RUN_BASE_PATH = 'submit_test'


def _is_path_within(path: str, directory: str) -> bool:
    """Return True if path is the same as or contained within directory."""
    path_resolved = pathlib.Path(path).resolve()
    dir_resolved = pathlib.Path(directory).resolve()
    return path_resolved.is_relative_to(dir_resolved)


class Folder:
    """A class to manage generic folders, avoiding to get out of
    specific given folder borders.

    .. todo::
        rethink whether the folder_limit option is still useful. If not, remove
        it alltogether (it was a nice feature, but unfortunately all the calls
        to os.path.abspath or normpath are quite slow).
    """

    def __init__(self, abspath: FilePath, folder_limit: FilePath | None = None):
        """Construct a new instance."""
        abspath = os.path.abspath(abspath)
        if folder_limit is None:
            folder_limit = abspath
        else:
            folder_limit = os.path.abspath(folder_limit)

            # check that it is a subfolder
            if not _is_path_within(str(abspath), str(folder_limit)):
                raise ValueError(
                    'The absolute path for this folder is not within the '
                    'folder_limit. abspath={}, folder_limit={}.'.format(abspath, folder_limit)
                )

        self._abspath = abspath
        self._folder_limit = folder_limit

    @property
    def mode_dir(self) -> int:
        """Return the mode with which the folders should be created"""
        if GROUP_WRITABLE:
            return 0o770

        return 0o700

    @property
    def mode_file(self) -> int:
        """Return the mode with which the files should be created"""
        if GROUP_WRITABLE:
            return 0o660

        return 0o600

    def get_subfolder(self, subfolder: FilePath, create: bool = False, reset_limit: bool = False) -> Folder:
        """Return a Folder object pointing to a subfolder.

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
        dest_abs_dir = os.path.abspath(os.path.join(self.abspath, str(subfolder)))

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

    @t.overload
    def get_content_list(self, pattern: str = '*', only_paths: t.Literal[True] = True) -> list[str]: ...

    @t.overload
    def get_content_list(self, pattern: str = '*', only_paths: t.Literal[False] = False) -> list[tuple[str, bool]]: ...

    def get_content_list(self, pattern: str = '*', only_paths: bool = True) -> list[str] | list[tuple[str, bool]]:
        """Return a list of files (and subfolders) in the folder, matching a given pattern.

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

    def create_symlink(self, src: FilePath, name: FilePath) -> None:
        """Create a symlink inside the folder to the location 'src'.

        :param src: the location to which the symlink must point. Can be
                either a relative or an absolute path. Should, however,
                be relative to work properly also when the repository is
                moved!
        :param name: the filename of the symlink to be created.
        """
        dest_abs_path = self.get_abs_path(name)
        os.symlink(src, dest_abs_path)

        # For symlinks, permissions should not be set

    def insert_path(self, src: FilePath, dest_name: FilePath | None = None, overwrite: bool = True) -> FilePath:
        """Copy a file to the folder.

        :param src: the source filename to copy
        :param dest_name: if None, the same basename of src is used. Otherwise,
                the destination filename will have this file name.
        :param overwrite: if ``False``, raises an error on existing destination;
                otherwise, delete it first.
        """
        if dest_name is None:
            filename = str(os.path.basename(src))
        else:
            filename = str(dest_name)

        src = str(src)

        dest_abs_path = self.get_abs_path(filename)

        if not os.path.isabs(src):
            raise ValueError('src must be an absolute path in insert_file')

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
                    raise OSError(f'destination already exists: {os.path.join(dest_abs_path)}')
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
                    raise OSError(f'destination already exists: {os.path.join(dest_abs_path)}')
            else:
                shutil.copytree(src, dest_abs_path)
        else:
            raise ValueError('insert_path can only insert files or paths, not symlinks or the like')

        return dest_abs_path

    def create_file_from_filelike(
        self, filelike: t.IO[t.AnyStr], filename: FilePath, mode: str = 'wb', encoding: str | None = None
    ) -> FilePath:
        """Create a file with the given filename from a filelike object.

        :param filelike: a filelike object whose contents to copy
        :param filename: the filename for the file that is to be created
        :param mode: the mode with which the target file will be written
        :param encoding: the encoding with which the target file will be written
        :return: the absolute filepath of the created file
        """
        filename = str(filename)
        filepath = self.get_abs_path(filename)

        if 'b' in mode:
            encoding = None

        with open(filepath, mode=mode, encoding=encoding) as handle:
            shutil.copyfileobj(filelike, handle)

        os.chmod(filepath, self.mode_file)

        return filepath

    def remove_path(self, filename: FilePath) -> None:
        """Remove a file or folder from the folder.

        :param filename: the relative path name to remove
        """
        # I get the full path of the filename, checking also that I don't
        # go beyond the folder limits
        dest_abs_path = self.get_abs_path(filename, check_existence=True)

        if os.path.isdir(dest_abs_path):
            shutil.rmtree(dest_abs_path)
        else:
            os.remove(dest_abs_path)

    def get_abs_path(self, relpath: FilePath, check_existence: bool = False) -> FilePath:
        """Return an absolute path for a file or folder in this folder.

        The advantage of using this method is that it checks that filename
        is a valid filename within this folder,
        and not something e.g. containing slashes.

        :param filename: The file or directory.
        :param check_existence: if False, just return the file path.
            Otherwise, also check if the file or directory actually exists.
            Raise OSError if it does not.
        """
        if os.path.isabs(relpath):
            raise ValueError('relpath must be a relative path')
        dest_abs_path = os.path.join(self.abspath, relpath)

        if not _is_path_within(dest_abs_path, str(self.folder_limit)):
            errstr = f"You didn't specify a valid filename: {relpath}"
            raise ValueError(errstr)

        if check_existence:
            if not os.path.exists(dest_abs_path):
                raise OSError(f'{relpath} does not exist within the folder {self.abspath}')

        return dest_abs_path

    @contextlib.contextmanager
    def open(
        self, name: FilePath, mode: str = 'r', encoding: str | None = 'utf8', check_existence: bool = False
    ) -> Iterator[t.Any]:
        """Open a file in the current folder and return the corresponding file object.

        :param check_existence: if False, just return the file path.
            Otherwise, also check if the file or directory actually exists.
            Raise OSError if it does not.
        """
        if 'b' in mode:
            encoding = None

        with open(self.get_abs_path(name, check_existence=check_existence), mode, encoding=encoding) as handle:
            yield handle

    @property
    def abspath(self) -> FilePath:
        """The absolute path of the folder."""
        return self._abspath

    @property
    def folder_limit(self) -> FilePath:
        """The folder limit that cannot be crossed when creating files and folders."""
        return self._folder_limit

    def exists(self) -> bool:
        """Return True if the folder exists, False otherwise."""
        return os.path.exists(self.abspath)

    def isfile(self, relpath: FilePath) -> bool:
        """Return True if 'relpath' exists inside the folder and is a file,
        False otherwise.
        """
        return os.path.isfile(os.path.join(self.abspath, relpath))

    def isdir(self, relpath: FilePath) -> bool:
        """Return True if 'relpath' exists inside the folder and is a directory,
        False otherwise.
        """
        return os.path.isdir(os.path.join(self.abspath, relpath))

    def erase(self, create_empty_folder: bool = False) -> None:
        """Erases the folder. Should be called only in very specific cases,
        in general folder should not be erased!

        Doesn't complain if the folder does not exist.

        :param create_empty_folder: if True, after erasing, creates an empty dir.
        """
        if self.exists():
            shutil.rmtree(self.abspath)

        if create_empty_folder:
            self.create()

    def create(self) -> None:
        """Creates the folder, if it does not exist on the disk yet.

        It will also create top directories, if absent.

        It is always safe to call it, it will do nothing if the folder
        already exists.
        """
        os.makedirs(self.abspath, mode=self.mode_dir, exist_ok=True)

    def replace_with_folder(self, srcdir: FilePath, move: bool = False, overwrite: bool = False) -> None:
        """This routine copies or moves the source folder 'srcdir' to the local folder pointed to by this Folder.

        :param srcdir: the source folder on the disk; this must be an absolute path
        :type srcdir: str
        :param move: if True, the srcdir is moved to the repository. Otherwise, it is only copied.
        :type move: bool
        :param overwrite: if True, the folder will be erased first.
            if False, an OSError is raised if the folder already exists.
            Whatever the value of this flag, parent directories will be created, if needed.
        :type overwrite: bool

        :raises OSError: in case of problems accessing or writing the files.
        :raises OSError: in case of problems accessing or writing the files (from ``shutil`` module).
        :raises ValueError: if the section is not recognized.
        """
        if not os.path.isabs(srcdir):
            raise ValueError('srcdir must be an absolute path')
        if overwrite:
            self.erase()
        elif self.exists():
            raise OSError(f'Location {self.abspath} already exists, and overwrite is set to False')

        # Create parent dir, if needed, with the right mode
        pardir = os.path.dirname(self.abspath)
        os.makedirs(pardir, mode=self.mode_dir, exist_ok=True)

        if move:
            shutil.move(srcdir, self.abspath)
        else:
            shutil.copytree(srcdir, self.abspath)

        # Set the mode also for the current dir, recursively
        for dirpath, _, filenames in os.walk(self.abspath, followlinks=False):
            # dirpath should already be absolute, because I am passing an absolute path to os.walk
            os.chmod(dirpath, self.mode_dir)
            for filename in filenames:
                # do not change permissions of symlinks (this would actually change permissions of the linked file/dir)
                # TODO check whether this is a big speed loss
                full_file_path = os.path.join(dirpath, filename)
                if not os.path.islink(full_file_path):
                    os.chmod(full_file_path, self.mode_file)


class SandboxFolder(Folder):
    """A class to manage the creation and management of a sandbox folder.

    .. note:: This class should be used with a context manager to guarantee automatic cleanup:

        with SandboxFolder() as folder:
            # Do something with ``folder``

    """

    def __init__(self, filepath: pathlib.Path | None = None):
        """Initialize a ``Folder`` object for an automatically created temporary directory.

        :param filepath: A filepath to a directory to use for the sandbox folder. This path will be actually used as the
            base path and a random subfolder will be generated inside it. This will guarantee that multiple instances of
            the class can be created with the same value for ``filepath`` while guaranteeing they are independent.
        """
        type_check(filepath, pathlib.Path, allow_none=True)

        if filepath is not None:
            filepath.mkdir(exist_ok=True, parents=True)

        super().__init__(abspath=tempfile.mkdtemp(dir=filepath))

    def __enter__(self) -> Self:
        """Enter a context and return self."""
        return self

    def __exit__(self, exc_type: t.Any, exc_value: t.Any, traceback: t.Any) -> None:
        """Erase the temporary directory created in the constructor."""
        self.erase()


class SubmitTestFolder(Folder):
    """Sandbox folder that can be used for the test submission of `CalcJobs`.

    The directory will be created in the current working directory with a configurable basename.
    Then a sub folder will be created within this base folder based on the current date and an index in order to
    not overwrite already existing created test folders.
    """

    def __init__(self, basepath: FilePath = CALC_JOB_DRY_RUN_BASE_PATH):
        """Construct and create the sandbox folder.

        The directory will be created in the current working directory with the name given by `basepath`.
        Then a sub folder will be created within this base folder based on the current date and an index in order to
        not overwrite already existing created test folders.

        :param basepath: name of the base directory that will be created in the current working directory
        """
        super().__init__(abspath=os.path.abspath(basepath))

        self.create()

        # Iteratively try to create a new sub folder based on the current date and an index that automatically increases
        counter = 0
        subfolder_basename = timezone.localtime(timezone.now()).strftime('%Y%m%d')

        while True:
            counter += 1
            subfolder_path = os.path.join(self.abspath, f'{subfolder_basename}-{counter:05d}')

            try:
                os.mkdir(subfolder_path)
                break
            except OSError as error:
                if error.errno == errno.EEXIST:
                    # The directory already exists, try the next iteration
                    continue
                # For all other errors re-raise to prevent endless loops
                raise

        self._sub_folder = self.get_subfolder(os.path.relpath(subfolder_path, self.abspath), reset_limit=True)

    def __enter__(self) -> Folder:
        """Return the sub folder that should be Called when entering in the with statement."""
        return self._sub_folder

    def __exit__(self, exc_type: t.Any, exc_value: t.Any, traceback: t.Any) -> None:
        """When context manager is exited, do not delete the folder."""
