###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for utility functions for the dumping data to disk."""

from pathlib import Path

import pytest

filename = 'file.txt'
node_metadata_file = '.aiida_node_metadata.yaml'


@pytest.mark.usefixtures('chdir_tmp_path')
def test_prepare_dump_path(tmp_path):
    from aiida.tools.dumping.utils import prepare_dump_path

    test_dir = tmp_path / Path('test-dir')
    test_file = test_dir / filename
    safeguard_file = node_metadata_file
    safeguard_file_path = test_dir / safeguard_file

    # Cannot set both overwrite and incremental to True
    with pytest.raises(ValueError):
        prepare_dump_path(path_to_validate=test_dir, overwrite=True, incremental=True)

    # Check that fails if file with same name as output dir
    test_dir.touch()
    with pytest.raises(FileExistsError):
        prepare_dump_path(path_to_validate=test_dir)
    test_dir.unlink()

    # Check if path created if non-existent
    prepare_dump_path(path_to_validate=test_dir)
    assert test_dir.exists()
    assert safeguard_file_path.is_file()

    # Directory exists, but empty -> is fine
    safeguard_file_path.unlink()
    prepare_dump_path(path_to_validate=test_dir)
    assert test_dir.exists()
    assert safeguard_file_path.is_file()

    # Fails if directory not empty, safeguard file existent, and overwrite set to False
    test_file.touch()
    safeguard_file_path.touch()
    with pytest.raises(FileExistsError):
        prepare_dump_path(path_to_validate=test_dir, overwrite=False, incremental=False)

    # Fails if directory not empty, overwrite set to True, but safeguard_file not found (for safety reasons)
    safeguard_file_path.unlink()
    test_file.touch()
    with pytest.raises(FileNotFoundError):
        prepare_dump_path(path_to_validate=test_dir, overwrite=True, incremental=False)

    # Works if directory not empty, overwrite set to True and safeguard_file contained
    # -> After function call, test_file is deleted, and safeguard_file again created
    safeguard_file_path.touch()
    prepare_dump_path(
        path_to_validate=test_dir,
        safeguard_file=safeguard_file,
        overwrite=True,
        incremental=False,
    )
    assert not test_file.is_file()
    assert safeguard_file_path.is_file()

    # Works if directory not empty, but incremental=True and safeguard_file (e.g. `.aiida_node_metadata.yaml`) contained
    # -> After function call, test file and safeguard_file still there
    test_file.touch()
    prepare_dump_path(path_to_validate=test_dir, safeguard_file=safeguard_file, incremental=True)
    assert safeguard_file_path.is_file()
    assert test_file.is_file()
