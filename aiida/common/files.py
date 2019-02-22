# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions to operate on filesystem files."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import hashlib
import io
import os
import sys


def md5_from_filelike(filelike, block_size_factor=128):
    """Create the hexdigested md5 checksum of the contents from a filelike object.

    :param filelike: the filelike object for whose contents to generate the md5 checksum
    :param block_size_factor: the file is read at chunks of size ``block_size_factor * md5.block_size``, where
        ``md5.block_size`` is the block_size used internally by the hashlib module.
    :returns: a string with the hexdigest md5.
    :raises: no checks are done on the filelike object, so it may raise IOError if it cannot be read from.
    """
    md5 = hashlib.md5()

    # I read 128 bytes at a time until it returns the empty string b''
    for chunk in iter(lambda: filelike.read(block_size_factor * md5.block_size), b''):
        md5.update(chunk)

    return md5.hexdigest()


def md5_file(filepath, block_size_factor=128):
    """Create the hexdigested md5 checksum of the contents from

    :param filepath: the filepath of the file for which we want the md5sum
    :param block_size_factor: the file is read at chunks of size ``block_size_factor * md5.block_size``, where
        ``md5.block_size`` is the block_size used internally by the hashlib module.
    :returns: a string with the hexdigest md5.
    :raises: No checks are done on the file, so if it doesn't exists it may
        raise IOError.
    """
    with io.open(filepath, 'rb', encoding=None) as handle:
        return md5_from_filelike(handle, block_size_factor=block_size_factor)


def sha1_file(filename, block_size_factor=128):
    """
    Open a file and return its sha1sum (hexdigested).

    :param filename: the filename of the file for which we want the sha1sum
    :param block_size_factor: the file is read at chunks of size
        ``block_size_factor * sha1.block_size``,
        where ``sha1.block_size`` is the block_size used internally by the
        hashlib module.

    :returns: a string with the hexdigest sha1.

    :raises: No checks are done on the file, so if it doesn't exists it may
        raise IOError.
    """
    sha1 = hashlib.sha1()
    with io.open(filename, 'rb', encoding=None) as fhandle:
        # I read 128 bytes at a time until it returns the empty string b''
        for chunk in iter(lambda: fhandle.read(block_size_factor * sha1.block_size), b''):
            sha1.update(chunk)
    return sha1.hexdigest()


def get_mode_string(mode):
    """
    Convert a file's mode to a string of the form '-rwxrwxrwx'.
    Taken (simplified) from cpython 3.3 stat module: https://hg.python.org/cpython/file/3.3/Lib/stat.py
    """
    # pylint: disable=invalid-name,unused-variable,too-many-locals

    # Constants used as S_IFMT() for various file types
    # (not all are implemented on all systems)

    S_IFDIR = 0o040000  # directory
    S_IFCHR = 0o020000  # character device
    S_IFBLK = 0o060000  # block device
    S_IFREG = 0o100000  # regular file
    S_IFIFO = 0o010000  # fifo (named pipe)
    S_IFLNK = 0o120000  # symbolic link
    S_IFSOCK = 0o140000  # socket file

    # Names for permission bits

    S_ISUID = 0o4000  # set UID bit
    S_ISGID = 0o2000  # set GID bit
    S_ENFMT = S_ISGID  # file locking enforcement
    S_ISVTX = 0o1000  # sticky bit
    S_IREAD = 0o0400  # Unix V7 synonym for S_IRUSR
    S_IWRITE = 0o0200  # Unix V7 synonym for S_IWUSR
    S_IEXEC = 0o0100  # Unix V7 synonym for S_IXUSR
    S_IRWXU = 0o0700  # mask for owner permissions
    S_IRUSR = 0o0400  # read by owner
    S_IWUSR = 0o0200  # write by owner
    S_IXUSR = 0o0100  # execute by owner
    S_IRWXG = 0o0070  # mask for group permissions
    S_IRGRP = 0o0040  # read by group
    S_IWGRP = 0o0020  # write by group
    S_IXGRP = 0o0010  # execute by group
    S_IRWXO = 0o0007  # mask for others (not in group) permissions
    S_IROTH = 0o0004  # read by others
    S_IWOTH = 0o0002  # write by others
    S_IXOTH = 0o0001  # execute by others

    # yapf:disable
    _filemode_table = (
        ((S_IFLNK, 'l'),
         (S_IFREG, '-'),
         (S_IFBLK, 'b'),
         (S_IFDIR, 'd'),
         (S_IFCHR, 'c'),
         (S_IFIFO, 'p')),

        ((S_IRUSR, 'r'),),
        ((S_IWUSR, 'w'),),
        ((S_IXUSR | S_ISUID, 's'),
         (S_ISUID, 'S'),
         (S_IXUSR, 'x')),

        ((S_IRGRP, 'r'),),
        ((S_IWGRP, 'w'),),
        ((S_IXGRP | S_ISGID, 's'),
         (S_ISGID, 'S'),
         (S_IXGRP, 'x')),

        ((S_IROTH, 'r'),),
        ((S_IWOTH, 'w'),),
        ((S_IXOTH | S_ISVTX, 't'),
         (S_ISVTX, 'T'),
         (S_IXOTH, 'x'))
    )
    # yapf:enable

    perm = []
    for table in _filemode_table:
        for bit, char in table:
            if mode & bit == bit:
                perm.append(char)
                break
        else:
            perm.append('-')
    return ''.join(perm)


# NOTE: this function is taken from shutil.which in python 3.5
# When we upgrade to python3 only, this function will not be needed anumore
def which(cmd, mode=os.F_OK | os.X_OK, path=None):
    """Given a command, mode, and a PATH string, return the path which
    conforms to the given mode on the PATH, or None if there is no such
    file.

    `mode` defaults to os.F_OK | os.X_OK. `path` defaults to the result
    of os.environ.get("PATH"), or can be overridden with a custom search
    path.

    """

    # pylint: disable=too-many-branches

    # Check that a given file can be accessed with the correct mode.
    # Additionally check that `file` is not a directory, as on Windows
    # directories pass the os.access check.
    def _access_check(filename, mode):
        return os.path.exists(filename) and os.access(filename, mode) and not os.path.isdir(filename)

    # If we're given a path with a directory part, look it up directly rather
    # than referring to PATH directories. This includes checking relative to the
    # current directory, e.g. ./script
    if os.path.dirname(cmd):
        if _access_check(cmd, mode):
            return cmd
        return None

    if path is None:
        path = os.environ.get("PATH", os.defpath)
    if not path:
        return None
    path = path.split(os.pathsep)

    if sys.platform == "win32":
        # The current directory takes precedence on Windows.
        if os.curdir not in path:
            path.insert(0, os.curdir)

        # PATHEXT is necessary to check on Windows.
        pathext = os.environ.get("PATHEXT", "").split(os.pathsep)
        # See if the given file matches any of the expected path extensions.
        # This will allow us to short circuit when given "python.exe".
        # If it does match, only test that one, otherwise we have to try
        # others.
        if any(cmd.lower().endswith(ext.lower()) for ext in pathext):
            files = [cmd]
        else:
            files = [cmd + ext for ext in pathext]
    else:
        # On other platforms you don't have things like PATHEXT to tell you
        # what file suffixes are executable, so just pass on cmd as-is.
        files = [cmd]

    seen = set()
    for directory in path:
        normdir = os.path.normcase(directory)
        if normdir not in seen:
            seen.add(normdir)
            for thefile in files:
                name = os.path.join(directory, thefile)
                if _access_check(name, mode):
                    return name
    return None
