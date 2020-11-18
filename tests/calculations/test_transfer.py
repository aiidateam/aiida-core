# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `TransferCalculation` plugin."""
import os
import pytest

from aiida import orm
from aiida.common import datastructures
#from aiida.calculations.transfer import TransferCalculation


@pytest.mark.usefixtures('clear_database_before_test')
def test_get_transfer(fixture_sandbox, aiida_localhost, generate_calc_job, tmp_path):
    """Test a default `TransferCalculation`."""

    file1 = tmp_path / 'file1'
    file1.write_text('file 1 content')
    folder = tmp_path / 'folder'
    folder.mkdir()
    file2 = folder / 'file2'
    file2.write_text('file 2 content')
    data_source = orm.RemoteData(computer=aiida_localhost, remote_path=str(tmp_path))

    entry_point_name = 'core.transfer'
    list_of_files = [
        ('data_source', 'file1.txt', 'folder/file1.txt'),
        ('data_source', 'folder/file2.txt', 'file2.txt'),
    ]
    list_of_nodes = {'data_source': data_source}
    instructions = orm.Dict(dict={'retrieve_files': True, 'symlink_files': list_of_files})
    inputs = {'instructions': instructions, 'source_nodes': list_of_nodes, 'metadata': {'computer': aiida_localhost}}

    # Generate calc_info and verify basics
    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)
    assert isinstance(calc_info, datastructures.CalcInfo)
    assert isinstance(calc_info.codes_info, list)
    assert len(calc_info.codes_info) == 0
    assert calc_info.skip_submit

    # Check that the lists were set correctly
    copy_list = [
        (aiida_localhost.uuid, os.path.join(data_source.get_remote_path(), 'file1.txt'), 'folder/file1.txt'),
        (aiida_localhost.uuid, os.path.join(data_source.get_remote_path(), 'folder/file2.txt'), 'file2.txt'),
    ]
    retrieve_list = [('folder/file1.txt'), ('file2.txt')]
    assert sorted(calc_info.remote_symlink_list) == sorted(copy_list)
    assert sorted(calc_info.remote_copy_list) == sorted(list())
    assert sorted(calc_info.local_copy_list) == sorted(list())
    assert sorted(calc_info.retrieve_list) == sorted(retrieve_list)

    # Now without symlinks
    instructions = orm.Dict(dict={'retrieve_files': True, 'remote_files': list_of_files})
    inputs = {'instructions': instructions, 'source_nodes': list_of_nodes, 'metadata': {'computer': aiida_localhost}}
    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)
    assert sorted(calc_info.remote_symlink_list) == sorted(list())
    assert sorted(calc_info.remote_copy_list) == sorted(copy_list)
    assert sorted(calc_info.local_copy_list) == sorted(list())
    assert sorted(calc_info.retrieve_list) == sorted(retrieve_list)


@pytest.mark.usefixtures('clear_database_before_test')
def test_put_transfer(fixture_sandbox, aiida_localhost, generate_calc_job, tmp_path):
    """Test a default `TransferCalculation`."""

    file1 = tmp_path / 'file1'
    file1.write_text('file 1 content')
    folder = tmp_path / 'folder'
    folder.mkdir()
    file2 = folder / 'file2'
    file2.write_text('file 2 content')
    data_source = orm.FolderData(tree=str(tmp_path))

    entry_point_name = 'core.transfer'
    list_of_files = [
        ('data_source', 'file1.txt', 'folder/file1.txt'),
        ('data_source', 'folder/file2.txt', 'file2.txt'),
    ]
    list_of_nodes = {'data_source': data_source}
    instructions = orm.Dict(dict={'retrieve_files': False, 'local_files': list_of_files})
    inputs = {'instructions': instructions, 'source_nodes': list_of_nodes, 'metadata': {'computer': aiida_localhost}}

    # Generate calc_info and verify basics
    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)
    assert isinstance(calc_info, datastructures.CalcInfo)
    assert isinstance(calc_info.codes_info, list)
    assert len(calc_info.codes_info) == 0
    assert calc_info.skip_submit

    # Check that the lists were set correctly
    copy_list = [
        (data_source.uuid, 'file1.txt', 'folder/file1.txt'),
        (data_source.uuid, 'folder/file2.txt', 'file2.txt'),
    ]
    assert sorted(calc_info.remote_symlink_list) == sorted(list())
    assert sorted(calc_info.remote_copy_list) == sorted(list())
    assert sorted(calc_info.local_copy_list) == sorted(copy_list)
    assert sorted(calc_info.retrieve_list) == sorted(list())
