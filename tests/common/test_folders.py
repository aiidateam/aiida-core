# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :class:`aiida.common.folders.Folder` class."""
import io
import pathlib
import sys
import tempfile

import pytest

from aiida.common.folders import Folder


def fs_encoding_is_utf8():
    """Return whether the current filesystem encoding is set to UTF-8.

    :return: True if the current filesystem encoding is set to UTF-8
    """
    return sys.getfilesystemencoding() == 'utf-8'


@pytest.mark.skipif(
    not fs_encoding_is_utf8(), reason='Testing for unicode folders requires UTF-8 to be set for filesystem encoding'
)
def test_unicode(tmpdir):
    """Check that there are no exceptions raised when using unicode folders."""
    with tempfile.TemporaryDirectory() as dirpath_target:

        (pathlib.Path(tmpdir) / 'sąžininga').write_text('test')
        (pathlib.Path(tmpdir) / 'žąsis').write_text('test')

        folder = Folder(dirpath_target)
        folder.insert_path(tmpdir, 'destination')
        folder.insert_path(tmpdir, 'šaltinis')

        assert sorted(folder.get_content_list()) == sorted(['destination', 'šaltinis'])
        assert sorted(folder.get_subfolder('destination').get_content_list()) == sorted(['sąžininga', 'žąsis'])
        assert sorted(folder.get_subfolder('šaltinis').get_content_list()) == sorted(['sąžininga', 'žąsis'])

        folder = Folder(pathlib.Path(tmpdir) / 'šaltinis')
        folder.insert_path(dirpath_target, 'destination')
        folder.insert_path(dirpath_target, 'kitas-šaltinis')
        assert sorted(folder.get_content_list()) == sorted(['destination', 'kitas-šaltinis'])


def test_get_abs_path_without_limit():
    """Check that the absolute path function can get an absolute path."""
    folder = Folder('/tmp')
    assert folder.get_abs_path('test_file.txt') == '/tmp/test_file.txt'


def test_create_file_from_filelike(tmpdir):
    """Test the :meth:`aiida.common.folders.Folder.create_file_from_filelike` method."""
    unicode_string = 'unicode_string'
    byte_string = b'byte_string'

    folder = Folder(tmpdir)

    folder.create_file_from_filelike(io.StringIO(unicode_string), 'random.dat', mode='w', encoding='utf-8')
    folder.create_file_from_filelike(io.BytesIO(byte_string), 'random.dat', mode='wb', encoding=None)

    with pytest.raises(TypeError):
        folder.create_file_from_filelike(io.StringIO(unicode_string), 'random.dat', mode='wb')

    with pytest.raises(TypeError):
        folder.create_file_from_filelike(io.BytesIO(byte_string), 'random.dat', mode='w')


def test_open(tmpdir):
    """Test the :meth:`aiida.common.folders.Folder.open` method."""
    filename = 'random.dat'
    folder = Folder(tmpdir)
    folder.create_file_from_filelike(io.StringIO('test'), filename, mode='w', encoding='utf-8')

    with folder.open(filename) as handle:
        assert handle.read() == 'test'
