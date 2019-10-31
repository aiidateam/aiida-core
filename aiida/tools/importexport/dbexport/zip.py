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
# pylint: disable=missing-docstring,redefined-builtin
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import os
import zipfile

import six


class MyWritingZipFile(object):

    def __init__(self, zip_file, fname):
        self._zipfile = zip_file
        self._fname = fname
        self._buffer = None

    def open(self):
        if self._buffer is not None:
            raise IOError('Cannot open again!')
        self._buffer = six.moves.StringIO()

    def write(self, data):
        self._buffer.write(data)

    def close(self):
        self._buffer.seek(0)
        self._zipfile.writestr(self._fname, self._buffer.read())
        self._buffer = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        self.close()


class ZipFolder(object):
    """
    To improve: if zipfile is closed, do something
    (e.g. add explicit open method, rename open to openfile,
    set _zipfile to None, ...)
    """

    def __init__(self, zipfolder_or_fname, mode=None, subfolder='.', use_compression=True, allowZip64=True):
        """
        :param zipfolder_or_fname: either another ZipFolder instance,
          of which you want to get a subfolder, or a filename to create.
        :param mode: the file mode; see the zipfile.ZipFile docs for valid
          strings. Note: can be specified only if zipfolder_or_fname is a
          string (the filename to generate)
        :param subfolder: the subfolder that specified the "current working
          directory" in the zip file. If zipfolder_or_fname is a ZipFolder,
          subfolder is a relative path from zipfolder_or_fname.subfolder
        :param use_compression: either True, to compress files in the Zip, or
          False if you just want to pack them together without compressing.
          It is ignored if zipfolder_or_fname is a ZipFolder isntance.
        """
        if isinstance(zipfolder_or_fname, six.string_types):
            the_mode = mode
            if the_mode is None:
                the_mode = 'r'
            if use_compression:
                compression = zipfile.ZIP_DEFLATED
            else:
                compression = zipfile.ZIP_STORED
            self._zipfile = zipfile.ZipFile(
                zipfolder_or_fname, mode=the_mode, compression=compression, allowZip64=allowZip64
            )
            self._pwd = subfolder
        else:
            if mode is not None:
                raise ValueError("Cannot specify 'mode' when passing a ZipFolder")
            self._zipfile = zipfolder_or_fname._zipfile  # pylint: disable=protected-access
            self._pwd = os.path.join(zipfolder_or_fname.pwd, subfolder)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        self._zipfile.close()

    @property
    def pwd(self):
        return self._pwd

    def open(self, fname, mode='r'):
        if mode == 'w':
            return MyWritingZipFile(zip_file=self._zipfile, fname=self._get_internal_path(fname))
        # else
        return self._zipfile.open(self._get_internal_path(fname), mode)

    def _get_internal_path(self, filename):
        return os.path.normpath(os.path.join(self.pwd, filename))

    # pylint: disable=unused-argument
    def get_subfolder(self, subfolder, create=False, reset_limit=False):
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
        if dest_name is None:
            base_filename = six.text_type(os.path.basename(src))
        else:
            base_filename = six.text_type(dest_name)

        base_filename = self._get_internal_path(base_filename)

        src = six.text_type(src)

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
