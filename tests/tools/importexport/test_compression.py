# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test compression utilities"""
import pytest

from aiida.tools.importexport.archive.zip_path import ZipPath


def test_zip_path(tmp_path):
    """Test the basic functionality of the ``ZipPath`` class."""

    # test write
    with ZipPath(tmp_path / 'test.zip', mode='w') as zip_file:

        assert zip_file.zippath == '.'
        new_file = zip_file / 'new_file.txt'
        assert new_file.zippath == 'new_file.txt'
        assert not new_file.exists()
        new_file.write_text('some text')
        assert new_file.exists()
        assert new_file.is_file()
        with pytest.raises(FileExistsError, match="cannot write to an existing path: 'new_file.txt'"):
            new_file.write_text('some text')
        zip_file.joinpath('bytes.exe').write_bytes(b'some bytes')

        # test shutil functionality
        tmp_path.joinpath('other_file.txt').write_text('other text')
        zip_file.joinpath('folder', 'other_file.txt').copyfile(tmp_path.joinpath('other_file.txt'))
        assert zip_file.joinpath('folder').exists()
        assert zip_file.joinpath('folder').is_dir()

        tmp_path.joinpath('other_folder', 'sub_folder').mkdir(parents=True)
        tmp_path.joinpath('other_folder', 'sub_file.txt').write_text('sub_file text')
        (zip_file / 'other_folder').copytree(tmp_path.joinpath('other_folder'))

        assert {p.zippath for p in new_file.parent.iterdir()} == {'new_file.txt', 'bytes.exe', 'folder', 'other_folder'}

    # test read
    zip_file_read = ZipPath(tmp_path / 'test.zip', mode='r')
    assert zip_file_read == zip_file

    assert {p.zippath for p in zip_file_read.iterdir()} == {'new_file.txt', 'bytes.exe', 'folder', 'other_folder'}
    assert {p.zippath for p in zip_file_read.joinpath('folder').iterdir()} == {'other_file.txt'}
    assert {p.zippath for p in zip_file_read.joinpath('other_folder').iterdir()} == {'sub_folder', 'sub_file.txt'}
    assert (zip_file_read / 'new_file.txt').read_text() == 'some text'
    assert (zip_file_read / 'bytes.exe').read_bytes() == b'some bytes'
    assert (zip_file_read / 'folder' / 'other_file.txt').read_text() == 'other text'
