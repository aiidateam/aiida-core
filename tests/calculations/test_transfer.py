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

from aiida import orm
from aiida.common import datastructures


def test_get_transfer(fixture_sandbox, aiida_localhost, generate_calc_job, tmp_path):
    """Test a default `TransferCalculation`."""
    file1 = tmp_path / 'file1.txt'
    file1.write_text('file 1 content')
    folder = tmp_path / 'folder'
    folder.mkdir()
    file2 = folder / 'file2.txt'
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
    assert sorted(calc_info.remote_copy_list) == sorted([])
    assert sorted(calc_info.local_copy_list) == sorted([])
    assert sorted(calc_info.retrieve_list) == sorted(retrieve_list)

    # Now without symlinks
    instructions = orm.Dict(dict={'retrieve_files': True, 'remote_files': list_of_files})
    inputs = {'instructions': instructions, 'source_nodes': list_of_nodes, 'metadata': {'computer': aiida_localhost}}
    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)
    assert sorted(calc_info.remote_symlink_list) == sorted([])
    assert sorted(calc_info.remote_copy_list) == sorted(copy_list)
    assert sorted(calc_info.local_copy_list) == sorted([])
    assert sorted(calc_info.retrieve_list) == sorted(retrieve_list)


def test_put_transfer(fixture_sandbox, aiida_localhost, generate_calc_job, tmp_path):
    """Test a default `TransferCalculation`."""
    file1 = tmp_path / 'file1.txt'
    file1.write_text('file 1 content')
    folder = tmp_path / 'folder'
    folder.mkdir()
    file2 = folder / 'file2.txt'
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
    assert sorted(calc_info.remote_symlink_list) == sorted([])
    assert sorted(calc_info.remote_copy_list) == sorted([])
    assert sorted(calc_info.local_copy_list) == sorted(copy_list)
    assert sorted(calc_info.retrieve_list) == sorted([])


def test_validate_instructions():
    """Test the `TransferCalculation` validators."""
    from aiida.calculations.transfer import validate_instructions

    instructions = orm.Dict(dict={}).store()
    result = validate_instructions(instructions, None)
    expected = (
        '\n\nno indication of what to do in the instruction node:\n'
        f' > {instructions.uuid}\n'
        '(to store the files in the repository set retrieve_files=True,\n'
        'to copy them to the specified folder on the remote computer,\n'
        'set it to False)\n'
    )
    assert result == expected

    instructions = orm.Dict(dict={'retrieve_files': 12}).store()
    result = validate_instructions(instructions, None)
    expected = (
        'entry for retrieve files inside of instruction node:\n'
        f' > {instructions.uuid}\n'
        'must be either True or False; instead, it is:\n > 12\n'
    )
    assert result == expected

    instructions = orm.Dict(dict={'retrieve_files': True}).store()
    result = validate_instructions(instructions, None)
    expected = (
        'no indication of which files to copy were found in the instruction node:\n'
        f' > {instructions.uuid}\n'
        'Please include at least one of `local_files`, `remote_files`, or `symlink_files`.\n'
        'These should be lists containing 3-tuples with the following format:\n'
        '    (source_node_key, source_relpath, target_relpath)\n'
    )
    assert result == expected


def test_validate_transfer_inputs(aiida_localhost, tmp_path):
    """Test the `TransferCalculation` validators."""
    from aiida.calculations.transfer import check_node_type, validate_transfer_inputs
    from aiida.orm import Computer

    fake_localhost = Computer(
        label='localhost-fake',
        description='extra localhost computer set up by test',
        hostname='localhost-fake',
        workdir=str(tmp_path),
        transport_type='core.local',
        scheduler_type='core.direct',
    )
    fake_localhost.store()
    fake_localhost.set_minimum_job_poll_interval(0.0)
    fake_localhost.configure()

    inputs = {
        'source_nodes': {
            'unused_node': orm.RemoteData(computer=aiida_localhost, remote_path=str(tmp_path)),
        },
        'instructions': orm.Dict(
            dict={
                'local_files': [('inexistent_node', None, None)],
                'remote_files': [('inexistent_node', None, None)],
                'symlink_files': [('inexistent_node', None, None)],
            }
        ),
        'metadata': {'computer': fake_localhost},
    }
    expected_list = []
    expected_list.append(
        (
            f' > remote node `unused_node` points to computer `{aiida_localhost}`, '
            f'not the one being used (`{fake_localhost}`)'
        )
    )
    expected_list.append(check_node_type('local_files', 'inexistent_node', None, orm.FolderData))
    expected_list.append(check_node_type('remote_files', 'inexistent_node', None, orm.RemoteData))
    expected_list.append(check_node_type('symlink_files', 'inexistent_node', None, orm.RemoteData))
    expected_list.append(' > node `unused_node` provided as inputs is not being used')

    expected = '\n\n'
    for addition in expected_list:
        expected = expected + addition + '\n'

    result = validate_transfer_inputs(inputs, None)
    assert result == expected

    result = check_node_type('list_name', 'node_label', None, orm.RemoteData)
    expected = ' > node `node_label` requested on list `list_name` not found among inputs'
    assert result == expected

    result = check_node_type('list_name', 'node_label', orm.FolderData(), orm.RemoteData)
    expected_type = orm.RemoteData.class_node_type
    expected = f' > node `node_label`, requested on list `list_name` should be of type `{expected_type}`'
    assert result == expected


def test_integration_transfer(aiida_localhost, tmp_path):
    """Test a default `TransferCalculation`."""
    from aiida.calculations.transfer import TransferCalculation
    from aiida.engine import run

    content_local = 'Content of local file'
    srcfile_local = tmp_path / 'file_local.txt'
    srcfile_local.write_text(content_local)
    srcnode_local = orm.FolderData(tree=str(tmp_path))

    content_remote = 'Content of remote file'
    srcfile_remote = tmp_path / 'file_remote.txt'
    srcfile_remote.write_text(content_remote)
    srcnode_remote = orm.RemoteData(computer=aiida_localhost, remote_path=str(tmp_path))

    list_of_nodes = {}
    list_of_nodes['source_local'] = srcnode_local
    list_for_local = [('source_local', 'file_local.txt', 'file_local.txt')]
    list_of_nodes['source_remote'] = srcnode_remote
    list_for_remote = [('source_remote', 'file_remote.txt', 'file_remote.txt')]

    instructions = orm.Dict(
        dict={
            'retrieve_files': True,
            'local_files': list_for_local,
            'remote_files': list_for_remote,
        }
    )
    inputs = {'instructions': instructions, 'source_nodes': list_of_nodes, 'metadata': {'computer': aiida_localhost}}

    output_nodes = run(TransferCalculation, **inputs)

    output_remotedir = output_nodes['remote_folder']
    output_retrieved = output_nodes['retrieved']

    # Check the retrieved folder
    assert sorted(output_retrieved.base.repository.list_object_names()) == sorted(['file_local.txt', 'file_remote.txt'])
    assert output_retrieved.base.repository.get_object_content('file_local.txt') == content_local
    assert output_retrieved.base.repository.get_object_content('file_remote.txt') == content_remote

    # Check the remote folder
    assert 'file_local.txt' in output_remotedir.listdir()
    assert 'file_remote.txt' in output_remotedir.listdir()
    output_remotedir.getfile(relpath='file_local.txt', destpath=str(tmp_path / 'retrieved_local.txt'))
    output_remotedir.getfile(relpath='file_remote.txt', destpath=str(tmp_path / 'retrieved_remote.txt'))
    assert (tmp_path / 'retrieved_local.txt').read_text() == content_local
    assert (tmp_path / 'retrieved_remote.txt').read_text() == content_remote
