# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Export a zip-file."""
# pylint: disable=redefined-builtin
import os
import warnings
import zipfile

from aiida.common.warnings import AiidaWarning


class ZipFileWrapper:
    """"Wrap" zipfile.ZipFile to make `write` method equal `writestr`"""

    def __init__(self, zip_file, filename):
        self._zipfile = zip_file
        self._filename = filename

    def write(self, data):
        self._zipfile.writestr(self._filename, data)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass


class ZipFolder:
    """"Wrap" for zipfile.ZipFile in order to act as a ZipFolder.

    This class is supposed to imitate :py:class:`aiida.common.folders.Folder`.

    NOTE: To improve: if zipfile is closed, do something
    (e.g. add explicit open method, rename open to openfile,
    set _zipfile to None, ...)

    :param zipfolder_or_name: either another ZipFolder instance,
        of which you want to get a subfolder, or a filename to create.
    :param mode: the file mode; see the zipfile.ZipFile docs for valid
        strings. Note: can be specified only if zipfolder_or_name is a
        string (the filename to generate)
    :param subfolder: the subfolder that specified the "current working
        directory" in the zip file. If zipfolder_or_name is a ZipFolder,
        subfolder is a relative path from zipfolder_or_name.path.
    :param use_compression: either True, to compress files in the Zip, or
        False if you just want to pack them together without compressing.
        It is ignored if zipfolder_or_name is a ZipFolder instance.
    """

    def __init__(self, zipfolder_or_name, mode=None, subfolder='.', use_compression=True, allowZip64=True):
        if isinstance(zipfolder_or_name, str):
            the_mode = mode
            if the_mode is None:
                the_mode = 'r'
            if use_compression:
                compression = zipfile.ZIP_DEFLATED
            else:
                compression = zipfile.ZIP_STORED
            self._zipfile = zipfile.ZipFile(
                zipfolder_or_name, mode=the_mode, compression=compression, allowZip64=allowZip64
            )
            self._path = subfolder
        else:
            if mode is not None:
                raise ValueError("Cannot specify 'mode' when passing a ZipFolder")
            self._zipfile = zipfolder_or_name._zipfile  # pylint: disable=protected-access
            self._path = os.path.join(zipfolder_or_name.path, subfolder)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        self._zipfile.close()

    @property
    def path(self):
        return self._path

    def open(self, name, mode='r', encoding=None, check_existence=False):
        """Open a file or folder within the current ZipFolder for reading or writing

        Imitating :py:meth:`aiida.common.folders.Folder.open`.

        Since zipfile.ZipFile.writestr is str/bytes agnostic, we don't care about encoding.
        NOTE: This means encoding other than UTF-8/Unicode is not supported
        (since it is not supported by zipfile.ZipFile).
        The encoding parameter is still present to be similar to :py:class:`aiida.common.folders.Folder`.
        """
        if encoding is not None:
            warnings.warn(  # pylint: disable=no-member
                'encoding has no effect for ZipFolder, it will always be "utf-8". '
                'See zipfile docs for more information.',
                AiidaWarning
            )

        if 'w' in mode:
            return ZipFileWrapper(zip_file=self._zipfile, filename=self.get_path(name, check_existence=check_existence))

        return self._zipfile.open(self.get_path(name, check_existence=check_existence), mode)

    def get_path(self, relpath, check_existence=False):
        """Return a normalized path of internal path within ZipFolder

        Similar to :py:meth:`aiida.common.folders.Folder.get_abs_path`.
        """
        if os.path.isabs(relpath):
            raise ValueError('relpath must be a relative path')

        dest = os.path.normpath(os.path.join(self.path, relpath))

        if check_existence:
            if not os.path.exists(dest):
                raise OSError('{} does not exist within the zip-folder {}'.format(relpath, self.path))

        return dest

    def get_subfolder(self, subfolder, create=False, reset_limit=False):  # pylint: disable=unused-argument
        # reset_limit: ignored
        # create: ignored, for the time being
        return ZipFolder(self, subfolder=subfolder)

    def exists(self, path):
        """Check whether path already exists in the ZipFolder"""
        try:
            self._zipfile.getinfo(path)
            exists = True
        except KeyError:
            exists = False
        return exists

    def insert_path(self, src, dest_name=None, overwrite=True):
        """Copy a file or folder to the ZipFolder.

        Similar functionality to :py:meth:`aiida.common.folders.Folder.insert_path`.

        :param src: the source filename to copy
        :param dest_name: if None, the same basename of src is used. Otherwise,
                the destination filename will have this file name.
        :param overwrite: if ``False``, raises an error on existing destination;
                otherwise, delete it first.
        """
        if dest_name is None:
            base_filename = str(os.path.basename(src))
        else:
            base_filename = str(dest_name)

        base_filename = self.get_path(base_filename)

        src = str(src)

        if not os.path.isabs(src):
            raise ValueError('src must be an absolute path in insert_file')

        if not overwrite and self.exists(base_filename):
            raise IOError('destination already exists: {}'.format(base_filename))

        if os.path.isdir(src):
            for dirpath, dirnames, filenames in os.walk(src):
                relpath = os.path.relpath(dirpath, src)
                if not dirnames and not filenames:
                    real_src = dirpath
                    real_dest = os.path.join(base_filename, relpath) + os.path.sep
                    if not self.exists(real_dest):
                        self._zipfile.write(real_src, real_dest)
                else:
                    for fname in dirnames + filenames:
                        real_src = os.path.join(dirpath, fname)
                        real_dest = os.path.join(base_filename, relpath, fname)
                        if not self.exists(real_dest):
                            self._zipfile.write(real_src, real_dest)
        else:
            self._zipfile.write(src, base_filename)
