###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test utility functions."""

from archive_path import TarPath, ZipPath

from aiida.storage.sqlite_zip.migrations.utils import copy_tar_to_zip, copy_zip_to_zip


def test_copy_zip_to_zip(tmp_path):
    """Test copying a zipfile to a new zipfile"""
    existing_path = tmp_path / 'in.zip'
    new_path = tmp_path / 'out.zip'
    with ZipPath(existing_path, mode='w') as path:
        path.joinpath('folder/file').write_text('content')
    paths = []

    def callback(inpath, outpath):
        paths.append((inpath.at, outpath.at))
        return False

    copy_zip_to_zip(existing_path, new_path, callback)
    assert new_path.exists()
    assert paths == [('folder/file', 'folder/file')]
    with ZipPath(new_path, mode='r') as path:
        assert {p.at for p in path.glob('**/*')} == {'folder', 'folder/file'}


def test_copy_tar_to_zip(tmp_path):
    """Test copying a tarfile to a new zipfile"""
    existing_path = tmp_path / 'in.tar'
    new_path = tmp_path / 'out.zip'
    with TarPath(existing_path, mode='w') as path:
        path.joinpath('folder/file').write_text('content')
    paths = []

    def callback(inpath, outpath):
        paths.append((inpath.as_posix(), outpath.at))
        return False

    copy_tar_to_zip(existing_path, new_path, callback)
    assert new_path.exists()
    assert paths == [('folder', 'folder'), ('folder/file', 'folder/file')]
    with ZipPath(new_path, mode='r') as path:
        assert {p.at for p in path.glob('**/*')} == {'folder', 'folder/file'}
