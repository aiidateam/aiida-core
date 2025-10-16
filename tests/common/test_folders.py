###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.common.folders` module."""

import io
import pathlib
import sys
import tempfile

import pytest

from aiida.common.folders import Folder, SandboxFolder


def fs_encoding_is_utf8():
    """Return whether the current filesystem encoding is set to UTF-8.

    :return: True if the current filesystem encoding is set to UTF-8
    """
    return sys.getfilesystemencoding() == 'utf-8'


@pytest.mark.skipif(
    not fs_encoding_is_utf8(), reason='Testing for unicode folders requires UTF-8 to be set for filesystem encoding'
)
def test_unicode(tmp_path_factory):
    """Check that there are no exceptions raised when using unicode folders."""
    dirpath_source = tmp_path_factory.mktemp('source')
    dirpath_target = tmp_path_factory.mktemp('target')

    (dirpath_source / 'sąžininga').write_text('test')
    (dirpath_source / 'žąsis').write_text('test')

    folder = Folder(dirpath_target)
    folder.insert_path(dirpath_source, 'destination')
    folder.insert_path(dirpath_source, 'šaltinis')

    assert sorted(folder.get_content_list()) == sorted(['destination', 'šaltinis'])
    assert sorted(folder.get_subfolder('destination').get_content_list()) == sorted(['sąžininga', 'žąsis'])
    assert sorted(folder.get_subfolder('šaltinis').get_content_list()) == sorted(['sąžininga', 'žąsis'])

    folder = Folder(dirpath_source / 'šaltinis')
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


def test_sandbox():
    """Test the :class:`aiida.common.folders.SandboxFolder` class."""
    sandbox = SandboxFolder()

    # By default, the created sandbox should be relative to the default temporary directory of the OS.
    assert pathlib.Path(sandbox.abspath).relative_to(tempfile.gettempdir())


def test_sandbox_filepath(tmp_path):
    """Test the :class:`aiida.common.folders.SandboxFolder` class with the ``filepath`` argument."""
    sandbox = SandboxFolder(filepath=tmp_path)
    assert pathlib.Path(sandbox.abspath).relative_to(tmp_path)


def test_sandbox_filepath_not_existing(tmp_path):
    """Test the :class:`aiida.common.folders.SandboxFolder` class with the ``filepath`` argument.

    Ensure that a non-existing ``filepath`` is created automatically, including parent directories.
    """
    filepath = tmp_path / 'some' / 'sub' / 'folder'
    assert not filepath.exists()
    sandbox = SandboxFolder(filepath=filepath)
    assert pathlib.Path(sandbox.abspath).relative_to(filepath)


def test_sandbox_filepath_multiple(tmp_path):
    """Test the :class:`aiida.common.folders.SandboxFolder` class with the ``filepath`` argument.

    Ensure that multiple instances using the same ``filepath`` get individual subfolders.
    """
    sandbox_01 = SandboxFolder(filepath=tmp_path)
    sandbox_02 = SandboxFolder(filepath=tmp_path)
    assert sandbox_01.abspath != sandbox_02.abspath
