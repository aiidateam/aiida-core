###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions to operate on filesystem files."""

import hashlib
from typing import BinaryIO

from .typing import FilePath


def md5_from_filelike(filelike: BinaryIO, block_size_factor: int = 128) -> str:
    """Create the hexdigested md5 checksum of the contents from a filelike object.

    :param filelike: the filelike object for whose contents to generate the md5 checksum
    :param block_size_factor: the file is read at chunks of size ``block_size_factor * md5.block_size``, where
        ``md5.block_size`` is the block_size used internally by the hashlib module.
    :returns: a string with the hexdigest md5.
    :raises: no checks are done on the filelike object, so it may raise OSError if it cannot be read from.
    """
    md5 = hashlib.md5()

    # I read 128 bytes at a time until it returns the empty string b''
    for chunk in iter(lambda: filelike.read(block_size_factor * md5.block_size), b''):
        md5.update(chunk)

    return md5.hexdigest()


def md5_file(filepath: FilePath, block_size_factor: int = 128) -> str:
    """Create the hexdigested md5 checksum of the contents from

    :param filepath: the filepath of the file for which we want the md5sum
    :param block_size_factor: the file is read at chunks of size ``block_size_factor * md5.block_size``, where
        ``md5.block_size`` is the block_size used internally by the hashlib module.
    :returns: a string with the hexdigest md5.
    :raises: No checks are done on the file, so if it doesn't exists it may
        raise OSError.
    """
    with open(filepath, 'rb', encoding=None) as handle:
        return md5_from_filelike(handle, block_size_factor=block_size_factor)


def sha1_file(filename: FilePath, block_size_factor: int = 128) -> str:
    """Open a file and return its sha1sum (hexdigested).

    :param filename: the filename of the file for which we want the sha1sum
    :param block_size_factor: the file is read at chunks of size
        ``block_size_factor * sha1.block_size``,
        where ``sha1.block_size`` is the block_size used internally by the
        hashlib module.

    :returns: a string with the hexdigest sha1.

    :raises: No checks are done on the file, so if it doesn't exists it may
        raise OSError.
    """
    sha1 = hashlib.sha1()
    with open(filename, 'rb', encoding=None) as fhandle:
        # I read 128 bytes at a time until it returns the empty string b''
        for chunk in iter(lambda: fhandle.read(block_size_factor * sha1.block_size), b''):
            sha1.update(chunk)
    return sha1.hexdigest()
