###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.engine.daemon.execmanager` module."""

import io
import pathlib

import pytest

from aiida.common.datastructures import CalcInfo, CodeInfo, FileCopyOperation, StashMode
from aiida.common.exceptions import StashingError
from aiida.common.folders import SandboxFolder
from aiida.engine.daemon import execmanager
from aiida.orm import CalcJobNode, FolderData, PortableCode, RemoteData, SinglefileData
from aiida.transports.plugins.local import LocalTransport


@pytest.fixture
def file_hierarchy():
    """Return a sample nested file hierarchy."""
    return {
        'file_a.txt': 'file_a',
        'path': {'file_b.txt': 'file_b', 'sub': {'file_c.txt': 'file_c', 'file_d.txt': 'file_d'}},
    }


@pytest.fixture
def file_hierarchy_simple():
    """Return a simple nested file hierarchy."""
    return {
        'sub': {
            'b': 'file_b',
        },
        'a': 'file_a',
    }


# Skip for any transport plugins that are locally installed but are not part of `aiida-core`
@pytest.fixture(
    scope='function',
    params=[
        ('core.local', None),
        ('core.ssh', None),
        ('core.ssh_async', 'asyncssh'),
        ('core.ssh_async', 'openssh'),
    ],
)
def node_and_calc_info(aiida_localhost, aiida_computer_ssh, aiida_computer_ssh_async, aiida_code_installed, request):
    """Return a ``CalcJobNode`` and associated ``CalcInfo`` instance."""

    if request.param[0] == 'core.local':
        node = CalcJobNode(computer=aiida_localhost)
    elif request.param[0] == 'core.ssh':
        node = CalcJobNode(computer=aiida_computer_ssh())
    elif request.param[0] == 'core.ssh_async':
        node = CalcJobNode(computer=aiida_computer_ssh_async(backend=request.param[1]))
    else:
        raise ValueError(f'unsupported transport: {request.param}')

    node.store()

    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash').store()
    code_info = CodeInfo()
    code_info.code_uuid = code.uuid

    calc_info = CalcInfo()
    calc_info.uuid = node.uuid
    calc_info.codes_info = [code_info]

    return node, calc_info


def test_hierarchy_utility(file_hierarchy, tmp_path, create_file_hierarchy, serialize_file_hierarchy):
    """Test that the ``create_file_hierarchy`` and ``serialize_file_hierarchy`` function as intended.

    This is tested by performing a round-trip.
    """
    create_file_hierarchy(file_hierarchy, tmp_path)
    assert serialize_file_hierarchy(tmp_path, read_bytes=False) == file_hierarchy


@pytest.mark.parametrize(
    'retrieve_list, expected_hierarchy',
    (
        # Single file or folder, either toplevel or nested
        (['file_a.txt'], {'file_a.txt': 'file_a'}),
        (['path/sub/file_c.txt'], {'file_c.txt': 'file_c'}),
        (['path'], {'path': {'file_b.txt': 'file_b', 'sub': {'file_c.txt': 'file_c', 'file_d.txt': 'file_d'}}}),
        (['path/sub'], {'sub': {'file_c.txt': 'file_c', 'file_d.txt': 'file_d'}}),
        (['*.txt'], {'file_a.txt': 'file_a'}),
        (['*/*.txt'], {'file_b.txt': 'file_b'}),
        # Single nested file that is retrieved keeping a varying level of depth of original hierarchy
        ([('path/sub/file_c.txt', '.', 3)], {'path': {'sub': {'file_c.txt': 'file_c'}}}),
        ([('path/sub/file_c.txt', '.', 2)], {'sub': {'file_c.txt': 'file_c'}}),
        ([('path/sub/file_c.txt', '.', 1)], {'file_c.txt': 'file_c'}),
        ([('path/sub/file_c.txt', '.', 0)], {'file_c.txt': 'file_c'}),
        # Single nested folder that is retrieved keeping a varying level of depth of original hierarchy
        ([('path/sub', '.', 2)], {'path': {'sub': {'file_c.txt': 'file_c', 'file_d.txt': 'file_d'}}}),
        ([('path/sub', '.', 1)], {'sub': {'file_c.txt': 'file_c', 'file_d.txt': 'file_d'}}),
        # Using globbing patterns
        ([('path/*', '.', 0)], {'file_b.txt': 'file_b', 'sub': {'file_c.txt': 'file_c', 'file_d.txt': 'file_d'}}),
        (
            [('path/sub/*', '.', 0)],
            {'file_c.txt': 'file_c', 'file_d.txt': 'file_d'},
        ),  # This is identical to ['path/sub']
        ([('path/sub/*c.txt', '.', 2)], {'sub': {'file_c.txt': 'file_c'}}),
        ([('path/sub/*c.txt', '.', 0)], {'file_c.txt': 'file_c'}),
        # Using globbing with depth `None` should maintain exact folder hierarchy
        ([('path/*.txt', '.', None)], {'path': {'file_b.txt': 'file_b'}}),
        ([('path/sub/*.txt', '.', None)], {'path': {'sub': {'file_c.txt': 'file_c', 'file_d.txt': 'file_d'}}}),
        # Different target directory
        ([('path/sub/file_c.txt', 'target', 3)], {'target': {'path': {'sub': {'file_c.txt': 'file_c'}}}}),
        ([('path/sub', 'target', 1)], {'target': {'sub': {'file_c.txt': 'file_c', 'file_d.txt': 'file_d'}}}),
        ([('path/sub/*c.txt', 'target', 2)], {'target': {'sub': {'file_c.txt': 'file_c'}}}),
        # Missing files should be ignored and not cause the retrieval to except
        (['file_a.txt', 'file_u.txt', 'path/file_u.txt', ('path/sub/file_u.txt', '.', 3)], {'file_a.txt': 'file_a'}),
    ),
)
@pytest.mark.asyncio
async def test_retrieve_files_from_list(
    tmp_path_factory,
    generate_calcjob_node,
    file_hierarchy,
    retrieve_list,
    expected_hierarchy,
    create_file_hierarchy,
    serialize_file_hierarchy,
):
    """Test the `retrieve_files_from_list` function."""
    source = tmp_path_factory.mktemp('source')
    target = tmp_path_factory.mktemp('target')

    create_file_hierarchy(file_hierarchy, source)

    with LocalTransport() as transport:
        node = generate_calcjob_node(workdir=source)
        await execmanager.retrieve_files_from_list(node, transport, target, retrieve_list)

    assert serialize_file_hierarchy(target, read_bytes=False) == expected_hierarchy


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('local_copy_list', 'expected_hierarchy'),
    (
        ([None, None], {'sub': {'b': 'file_b'}, 'a': 'file_a'}),
        (['.', None], {'sub': {'b': 'file_b'}, 'a': 'file_a'}),
        ([None, '.'], {'sub': {'b': 'file_b'}, 'a': 'file_a'}),
        (['.', '.'], {'sub': {'b': 'file_b'}, 'a': 'file_a'}),
        ([None, ''], {'sub': {'b': 'file_b'}, 'a': 'file_a'}),
        (['sub', None], {'b': 'file_b'}),
        ([None, 'target'], {'target': {'sub': {'b': 'file_b'}, 'a': 'file_a'}}),
        (['sub', 'target'], {'target': {'b': 'file_b'}}),
        (['sub', 'target/another-sub'], {'target': {'another-sub': {'b': 'file_b'}}}),
    ),
)
async def test_upload_local_copy_list(
    fixture_sandbox,
    node_and_calc_info,
    file_hierarchy_simple,
    tmp_path,
    local_copy_list,
    expected_hierarchy,
    create_file_hierarchy,
    serialize_file_hierarchy,
):
    """Test the ``local_copy_list`` functionality in ``upload_calculation``."""
    create_file_hierarchy(file_hierarchy_simple, tmp_path)
    folder = FolderData()
    folder.base.repository.put_object_from_tree(tmp_path)
    folder.store()

    node, calc_info = node_and_calc_info
    calc_info.local_copy_list = [[folder.uuid] + local_copy_list]

    with node.computer.get_transport() as transport:
        await execmanager.upload_calculation(node, transport, calc_info, fixture_sandbox)

    # Check that none of the files were written to the repository of the calculation node, since they were communicated
    # through the ``local_copy_list``.
    assert node.base.repository.list_object_names() == []

    # Now check that all contents were successfully written to the remote work directory
    written_hierarchy = serialize_file_hierarchy(pathlib.Path(node.get_remote_workdir()), read_bytes=False)
    assert written_hierarchy == expected_hierarchy


@pytest.mark.asyncio
async def test_upload_local_copy_list_files_folders(
    fixture_sandbox, node_and_calc_info, file_hierarchy, tmp_path, create_file_hierarchy, serialize_file_hierarchy
):
    """Test the ``local_copy_list`` functionality in ``upload_calculation``.

    Specifically, verify that files in the ``local_copy_list`` do not end up in the repository of the node.
    """
    create_file_hierarchy(file_hierarchy, tmp_path)
    folder = FolderData()
    folder.base.repository.put_object_from_tree(tmp_path)

    inputs = {
        'file_x': SinglefileData(io.BytesIO(b'content_x')).store(),
        'file_y': SinglefileData(io.BytesIO(b'content_y')).store(),
        'folder': folder.store(),
    }

    node, calc_info = node_and_calc_info

    calc_info.local_copy_list = [
        (inputs['file_x'].uuid, inputs['file_x'].filename, './files/file_x'),
        (inputs['file_y'].uuid, inputs['file_y'].filename, './files/file_y'),
        (inputs['folder'].uuid, None, '.'),
    ]

    with node.computer.get_transport() as transport:
        await execmanager.upload_calculation(node, transport, calc_info, fixture_sandbox)

    # Check that none of the files were written to the repository of the calculation node, since they were communicated
    # through the ``local_copy_list``.
    assert node.base.repository.list_object_names() == []

    # Now check that all contents were successfully written to the remote working directory
    written_hierarchy = serialize_file_hierarchy(pathlib.Path(node.get_remote_workdir()), read_bytes=False)
    expected_hierarchy = file_hierarchy
    expected_hierarchy['files'] = {}
    expected_hierarchy['files']['file_x'] = 'content_x'
    expected_hierarchy['files']['file_y'] = 'content_y'
    assert expected_hierarchy == written_hierarchy


@pytest.mark.asyncio
async def test_upload_remote_symlink_list(
    fixture_sandbox, node_and_calc_info, file_hierarchy, tmp_path, create_file_hierarchy
):
    """Test the ``remote_symlink_list`` functionality in ``upload_calculation``.

    Nested subdirectories in the target should be automatically created.
    """
    create_file_hierarchy(file_hierarchy, tmp_path)
    node, calc_info = node_and_calc_info

    calc_info.remote_symlink_list = [
        (node.computer.uuid, str(tmp_path / 'path' / 'sub'), 'path/sub'),
        (node.computer.uuid, str(tmp_path / 'file_a.txt'), 'file_a.txt'),
    ]

    with node.computer.get_transport() as transport:
        await execmanager.upload_calculation(node, transport, calc_info, fixture_sandbox)

    filepath_workdir = pathlib.Path(node.get_remote_workdir())
    assert (filepath_workdir / 'file_a.txt').is_symlink()
    assert (filepath_workdir / 'path' / 'sub').is_symlink()
    assert (filepath_workdir / 'file_a.txt').read_text() == 'file_a'
    assert (filepath_workdir / 'path' / 'sub' / 'file_c.txt').read_text() == 'file_c'


@pytest.mark.parametrize(
    'order, expected',
    (
        (None, 'remote'),  # Default order should have remote last
        (
            [
                FileCopyOperation.SANDBOX,
                FileCopyOperation.REMOTE,
                FileCopyOperation.LOCAL,
            ],
            'local',
        ),
        (
            [
                FileCopyOperation.REMOTE,
                FileCopyOperation.LOCAL,
                FileCopyOperation.SANDBOX,
            ],
            'sandbox',
        ),
    ),
)
@pytest.mark.asyncio
async def test_upload_file_copy_operation_order(node_and_calc_info, tmp_path, order, expected):
    """Test the ``CalcInfo.file_copy_operation_order`` controls the copy order."""
    node, calc_info = node_and_calc_info

    dirpath_remote = tmp_path / 'remote'
    dirpath_remote.mkdir()
    dirpath_local = tmp_path / 'local'
    dirpath_local.mkdir()
    dirpath_sandbox = tmp_path / 'sandbox'
    dirpath_sandbox.mkdir()

    filepath_remote = dirpath_remote / 'file.txt'
    filepath_remote.write_text('remote')
    filepath_local = dirpath_local / 'file.txt'
    filepath_local.write_text('local')

    remote_data = RemoteData(remote_path=str(dirpath_remote), computer=node.computer)
    folder_data = FolderData(tree=dirpath_local)
    sandbox = SandboxFolder(dirpath_sandbox)
    sandbox.create_file_from_filelike(io.BytesIO(b'sandbox'), 'file.txt')

    inputs = {
        'local': folder_data,
        'remote': remote_data,
    }

    calc_info.remote_copy_list = ((node.computer.uuid, str(filepath_remote), 'file.txt'),)
    calc_info.local_copy_list = ((folder_data.uuid, 'file.txt', 'file.txt'),)

    if order is not None:
        calc_info.file_copy_operation_order = order

    with node.computer.get_transport() as transport:
        await execmanager.upload_calculation(node, transport, calc_info, sandbox, inputs)
        filepath = pathlib.Path(node.get_remote_workdir()) / 'file.txt'
        assert filepath.is_file()
        assert filepath.read_text() == expected


@pytest.mark.parametrize(
    'sandbox_hierarchy, local_copy_list_params, remote_copy_list_params, expected_hierarchy, expected_exception',
    [
        ## Single `FileCopyOperation`
        # Only Sandbox
        ({'pseudo': {'Ba.upf': 'Ba pseudo'}}, (), (), {'pseudo': {'Ba.upf': 'Ba pseudo'}}, None),
        # Only local copy of a `SinglefileData` to the "pseudo" directory
        # -> Makes the parent directory and copies the file to the parent directory
        # COUNTER-INTUITIVE: would fail with `cp` since the parent folder doesn't exist
        (
            {},
            ((SinglefileData, 'Ba pseudo', 'Ba.upf', 'pseudo/Ba.upf'),),
            (),
            {'pseudo': {'Ba.upf': 'Ba pseudo'}},
            None,
        ),
        # Only local copy of a single file to the "pseudo" directory
        # -> Makes the parent directory and copies the file to the parent directory
        # COUNTER-INTUITIVE: would fail with `cp` since the parent folder doesn't exist
        (
            {},
            ((FolderData, {'pseudo': {'Ba.upf': 'Ba pseudo'}}, 'pseudo/Ba.upf', 'pseudo/Ba.upf'),),
            (),
            {'pseudo': {'Ba.upf': 'Ba pseudo'}},
            None,
        ),
        # Only local copy of a single directory, specifying the target directory
        # -> Copies the contents of the folder to the target directory
        (
            {},
            ((FolderData, {'pseudo': {'Ba.upf': 'Ba pseudo'}}, 'pseudo', 'target'),),
            (),
            {'target': {'Ba.upf': 'Ba pseudo'}},
            None,
        ),
        # Only local copy of a single directory to the "current directory"
        # -> Copies the contents of the folder to the target current directory
        # COUNTER-INTUITIVE: emulates the behaviour of `cp` with forward slash: `cp -r pseudo/ .`
        (
            {},
            ((FolderData, {'pseudo': {'Ba.upf': 'Ba pseudo'}}, 'pseudo', '.'),),
            (),
            {'Ba.upf': 'Ba pseudo'},
            None,
        ),
        # Only local copy of a single nested directory to the same nested directory
        # -> Copies the contents of the nested folder to the target nested folder
        # COUNTER-INTUITIVE: this command would fail with `cp` since the parent folder does not exist
        (
            {},
            ((FolderData, {'out': {'HP': {'file': 'content'}}}, 'out/HP', 'out/HP'),),
            (),
            {'out': {'HP': {'file': 'content'}}},
            None,
        ),
        # Only local root copy of single nested directory to a nested directory
        # -> Copies the contents of entire FolderData to the target nested folder, leading to a 4-level hierarchy
        # COUNTER-INTUITIVE: this command would fail with `cp` since the parent folder does not exist
        (
            {},
            ((FolderData, {'out': {'HP': {'file': 'content'}}}, '.', 'new/sub'),),
            (),
            {'new': {'sub': {'out': {'HP': {'file': 'content'}}}}},
            None,
        ),
        # Only remote copy of a single file to the "pseudo" directory
        # -> Copy fails silently since target directory does not exist: final directory structure is empty
        # COUNTER-INTUITIVE: the silent behavior is expected. See `execmanager.py`::_copy_remote_files for more details
        (
            {},
            (),
            (({'pseudo': {'Ba.upf': 'Ba pseudo'}}, 'pseudo/Ba.upf', 'pseudo/Ba.upf'),),
            {},
            None,
        ),
        # -> Copy fails silently since target directory does not exist: final directory structure is empty
        # COUNTER-INTUITIVE: the silent behavior is expected. See `execmanager.py`::_copy_remote_files for more details
        (
            {},
            (),
            (({'Ba.upf': 'Ba pseudo'}, 'Ti.upf', 'Ti.upf'),),
            {},
            None,
        ),
        # Only remote copy of a single directory, specifying the target directory
        # -> Copies the contents of the folder to the target directory
        (
            {},
            (),
            (({'pseudo': {'Ba.upf': 'Ba pseudo'}}, 'pseudo', 'target'),),
            {'target': {'Ba.upf': 'Ba pseudo'}},
            None,
        ),
        # Only remote copy of a single directory to the "current directory"
        # -> Copies the folder to the target current directory
        (
            {},
            (),
            (({'pseudo': {'Ba.upf': 'Ba pseudo'}}, 'pseudo', '.'),),
            {'pseudo': {'Ba.upf': 'Ba pseudo'}},
            None,
        ),
        ## Two `FileCopyOperation`s
        # Sandbox creates folder; Local copy of a `SinglefileData` to target file in folder
        # Note: This is the QE use case for the `PwCalculation` plugin
        # -> Copies the file to the target file in the target folder
        (
            {'pseudo': {}},
            ((SinglefileData, 'Ba pseudo', 'Ba.upf', 'pseudo/Ba.upf'),),
            (),
            {'pseudo': {'Ba.upf': 'Ba pseudo'}},
            None,
        ),
        # Sandbox creates folder; Local copy of two `SinglefileData` to target file in folder
        # -> Copies both files to the target files in the target folder
        (
            {'pseudo': {}},
            (
                (SinglefileData, 'Ba pseudo', 'Ba.upf', 'pseudo/Ba.upf'),
                (SinglefileData, 'Ti pseudo', 'Ti.upf', 'pseudo/Ti.upf'),
            ),
            (),
            {'pseudo': {'Ba.upf': 'Ba pseudo', 'Ti.upf': 'Ti pseudo'}},
            None,
        ),
        # Sandbox creates folder; Local copy of a `SinglefileData` file from to target folder
        # -> Fails outright with `IsADirectoryError` since target folder exists
        # COUNTER-INTUITIVE: would succeed with the desired hierarchy with `cp`
        (
            {'pseudo': {}},
            ((SinglefileData, 'Ba pseudo', 'Ba.upf', 'pseudo'),),
            (),
            {'pseudo': {'Ba.upf': 'Ba pseudo'}},
            IsADirectoryError,
        ),
        # Sandbox creates folder; Local copy of a single file from a `FolderData` to target folder
        # -> Fails outright since target folder exists
        # COUNTER-INTUITIVE: would succeed with the desired hierarchy with `cp`
        (
            {'pseudo': {}},
            ((FolderData, {'pseudo': {'Ba.upf': 'Ba pseudo'}}, 'pseudo/Ba.upf', 'pseudo'),),
            (),
            {'pseudo': {'Ba.upf': 'Ba pseudo'}},
            IsADirectoryError,
        ),
        # Sandbox creates folder; Local copy of a folder inside a `FolderData`
        # -> Copies _contents_ of folder to target folder
        # COUNTER-INTUITIVE: emulates the behaviour of `cp` with forward slash: `cp -r pseudo/ pseudo`
        (
            {'pseudo': {}},
            ((FolderData, {'pseudo': {'Ba.upf': 'Ba pseudo'}}, 'pseudo', 'pseudo'),),
            (),
            {'pseudo': {'Ba.upf': 'Ba pseudo'}},
            None,
        ),
        # Sandbox creates folder; Remote copy of a single file to target file in folder
        # -> Copies the remote file to the target file in the target folder
        (
            {'pseudo': {}},
            (),
            (({'pseudo': {'Ba.upf': 'Ba pseudo'}}, 'pseudo/Ba.upf', 'pseudo/Ba.upf'),),
            {'pseudo': {'Ba.upf': 'Ba pseudo'}},
            None,
        ),
        # Sandbox creates folder; Remote copy of a single file to target folder
        # -> Copies the remote file to the target folder
        (
            {'pseudo': {}},
            (),
            (({'pseudo': {'Ba.upf': 'Ba pseudo'}}, 'pseudo/Ba.upf', 'pseudo'),),
            {'pseudo': {'Ba.upf': 'Ba pseudo'}},
            None,
        ),
        # Sandbox creates folder with nested folder; Local copy of nested folder to target nested folder
        # -> Copies contents of nested folder to target nested folder
        # COUNTER-INTUITIVE: emulates the behaviour of `cp` with forward slash
        (
            {'folder': {'nested_folder': {'file': 'content'}}},
            (
                (
                    FolderData,
                    {'folder': {'nested_folder': {'file': 'new_content'}}},
                    'folder/nested_folder',
                    'folder/nested_folder',
                ),
            ),
            (),
            {'folder': {'nested_folder': {'file': 'new_content'}}},
            None,
        ),
        # Sandbox creates folder with nested folder; Local copy of top-level folder to target top-level folder
        # -> Copies contents of top-level folder to target top-level folder
        # COUNTER-INTUITIVE: emulates the behaviour of `cp` with forward slash
        (
            {'folder': {'nested_folder': {'file': 'content'}}},
            (
                (
                    FolderData,
                    {'folder': {'nested_folder': {'file': 'new_content'}}},
                    'folder',
                    'folder',
                ),
            ),
            (),
            {'folder': {'nested_folder': {'file': 'new_content'}}},
            None,
        ),
        # Sandbox creates folder with nested folder; Remote copy of nested folder to target nested folder
        # -> Copies the remote nested folder _into_ target nested folder
        (
            {'folder': {'nested_folder': {'file': 'content'}}},
            (),
            (
                (
                    {'folder': {'nested_folder': {'file': 'new_content'}}},
                    'folder/nested_folder',
                    'folder/nested_folder',
                ),
            ),
            {'folder': {'nested_folder': {'file': 'content', 'nested_folder': {'file': 'new_content'}}}},
            None,
        ),
    ],
)
@pytest.mark.asyncio
async def test_upload_combinations(
    fixture_sandbox,
    node_and_calc_info,
    tmp_path,
    sandbox_hierarchy,
    local_copy_list_params,
    remote_copy_list_params,
    expected_hierarchy,
    expected_exception,
    create_file_hierarchy,
    serialize_file_hierarchy,
):
    """Test the ``upload_calculation`` functions for various combinations of sandbox folders and copy lists.

    The `local_copy_list_params` is formatted as a list of tuples, where each tuple contains the following elements:

        - The class of the data node to be copied.
        - The content of the data node to be copied. This can be either a string in case of a file, or a dictionary
          representing the file hierarchy in case of a folder.
        - The path of the file or directory to be copied, specified relative to the source node's working directory.
        - The destination path where the data will be copied, specified relative to the destination node's working
          directory.

    The `remote_copy_list_params` is formatted as a list of tuples, where each tuple contains the following elements:

        - A dictionary representing the file hierarchy that should be in the remote directory.
        - The source path of the file or directory to be copied.
        - The target path the file or directory should be copied to.

    """
    create_file_hierarchy(sandbox_hierarchy, fixture_sandbox)

    node, calc_info = node_and_calc_info

    calc_info.local_copy_list = []

    for copy_id, (data_class, content, filename, target_path) in enumerate(local_copy_list_params):
        # Create a sub directroy in the temporary folder for each copy to avoid conflicts
        sub_tmp_path_local = tmp_path / f'local_{copy_id}'

        if issubclass(data_class, SinglefileData):
            create_file_hierarchy({filename: content}, sub_tmp_path_local)
            copy_node = SinglefileData(sub_tmp_path_local / filename).store()

            calc_info.local_copy_list.append((copy_node.uuid, copy_node.filename, target_path))

        elif issubclass(data_class, FolderData):
            create_file_hierarchy(content, sub_tmp_path_local)
            serialize_file_hierarchy(sub_tmp_path_local, read_bytes=False)
            folder = FolderData()
            folder.base.repository.put_object_from_tree(sub_tmp_path_local)
            folder.store()

            calc_info.local_copy_list.append((folder.uuid, filename, target_path))

    calc_info.remote_copy_list = []

    for copy_id, (hierarchy, source_path, target_path) in enumerate(remote_copy_list_params):
        # Create a sub directroy in the temporary folder for each copy to avoid conflicts
        sub_tmp_path_remote = tmp_path / f'remote_{copy_id}'

        create_file_hierarchy(hierarchy, sub_tmp_path_remote)

        calc_info.remote_copy_list.append(
            (node.computer.uuid, (sub_tmp_path_remote / source_path).as_posix(), target_path)
        )
    if expected_exception is not None:
        with pytest.raises(expected_exception):
            with node.computer.get_transport() as transport:
                await execmanager.upload_calculation(node, transport, calc_info, fixture_sandbox)

            filepath_workdir = pathlib.Path(node.get_remote_workdir())

            assert serialize_file_hierarchy(filepath_workdir, read_bytes=False) == expected_hierarchy
    else:
        with node.computer.get_transport() as transport:
            await execmanager.upload_calculation(node, transport, calc_info, fixture_sandbox)

        filepath_workdir = pathlib.Path(node.get_remote_workdir())

        assert serialize_file_hierarchy(filepath_workdir, read_bytes=False) == expected_hierarchy


@pytest.mark.asyncio
async def test_upload_calculation_portable_code(fixture_sandbox, node_and_calc_info, tmp_path):
    """Test ``upload_calculation`` with a ``PortableCode`` for different transports.

    Regression test for https://github.com/aiidateam/aiida-core/issues/6518
    """
    subdir = tmp_path / 'sub'
    subdir.mkdir()
    (subdir / 'some-file').write_bytes(b'sub dummy')
    (tmp_path / 'bash').write_bytes(b'bash implementation')

    code = PortableCode(
        filepath_executable='bash',
        filepath_files=tmp_path,
    ).store()

    node, calc_info = node_and_calc_info
    code_info = CodeInfo()
    code_info.code_uuid = code.uuid
    calc_info.codes_info = [code_info]

    with node.computer.get_transport() as transport:
        await execmanager.upload_calculation(
            node,
            transport,
            calc_info,
            fixture_sandbox,
        )


@pytest.mark.parametrize(
    'file_hierarchy',
    [{'aiida.out': 'out', 'aiida.in': 'in', '_aiidasubmit.sh': 'script', 'folder': {'1': '1', '2': '2', '3': '3'}}],
)
@pytest.mark.parametrize(
    'stash_mode',
    [
        StashMode.COPY.value,
        StashMode.COMPRESS_TAR.value,
        StashMode.COMPRESS_TARBZ2.value,
        StashMode.COMPRESS_TARGZ.value,
        StashMode.COMPRESS_TARXZ.value,
    ],
)
@pytest.mark.asyncio
async def test_stashing(
    generate_calcjob_node,
    stash_mode,
    file_hierarchy,
    create_file_hierarchy,
    serialize_file_hierarchy,
    tmp_path,
    monkeypatch,
    caplog,
):
    """Test `stash_calculation`"""

    import logging

    computer_wdir = tmp_path / 'aiida'
    computer_wdir.mkdir()
    dest_path = tmp_path / 'stash_path'
    dest_path.mkdir()

    node = generate_calcjob_node()
    uuid = node.uuid
    node_workdir = computer_wdir / uuid[:2] / uuid[2:4] / uuid[4:]
    pathlib.Path(node_workdir).mkdir(parents=True)
    node.set_remote_workdir(str(node_workdir))
    create_file_hierarchy(file_hierarchy, node_workdir)

    if stash_mode == StashMode.COPY.value:
        node.set_option(
            'stash',
            {
                'source_list': ['*'],
                'target_base': str(dest_path),
                'stash_mode': stash_mode,
            },
        )
    else:
        node.set_option(
            'stash',
            {
                'source_list': ['*'],
                'target_base': str(dest_path),
                'stash_mode': stash_mode,
                'dereference': True,  # ignored in case of COPY
            },
        )

    def mock_get_authinfo(*args, **kwargs):
        class MockAuthInfo:
            def get_workdir(self, *args, **kwargs):
                return str(computer_wdir)

        return MockAuthInfo()

    monkeypatch.setattr(node, 'get_authinfo', mock_get_authinfo)

    ## 1) test the basic functionality
    # various transport plugins are tested in `test_all_plugins.py` to check the full functionality
    # of `transport.compress` and `transport.extract`.
    # Here we using local transport we test basic functionality of `stash_calculation`.

    with LocalTransport() as transport:
        await execmanager.stash_calculation(node, transport)

    if stash_mode != StashMode.COPY.value:
        # more detailed test on integrity of the zip file is in `test_all_plugins.py`
        assert pathlib.Path(str(dest_path / node.uuid) + '.' + stash_mode).is_file()

        with LocalTransport() as transport:
            transport.extract(str(dest_path / node.uuid) + '.' + stash_mode, dest_path / 'extracted')
        base_path = dest_path / 'extracted'

    else:
        assert pathlib.Path(dest_path).is_dir()
        base_path = dest_path

    serialize_file_hierarchy(base_path, read_bytes=True) == serialize_file_hierarchy(computer_wdir, read_bytes=True)

    ## 2) test Error handling
    dest_path_error = tmp_path / 'stash_path_error'
    dest_path_error.mkdir()

    if stash_mode == StashMode.COPY.value:
        node.set_option(
            'stash',
            {
                'source_list': ['*'],
                'target_base': str(dest_path_error),
                'stash_mode': stash_mode,
            },
        )
    else:
        node.set_option(
            'stash',
            {
                'source_list': ['*'],
                'target_base': str(dest_path_error),
                'stash_mode': stash_mode,
                'dereference': True,  # ignored in case of COPY
            },
        )

    with LocalTransport() as transport:
        if stash_mode == StashMode.COPY.value:

            async def mock_copy_async(*args, **kwargs):
                raise OSError('copy mocked error')

            monkeypatch.setattr(transport, 'copy_async', mock_copy_async)

            # StashingError should be raised for copy failures
            with pytest.raises(StashingError, match='Failed to copy'):
                await execmanager.stash_calculation(node, transport)
        else:

            async def mock_compress_async(*args, **kwargs):
                raise OSError('compress mocked error')

            monkeypatch.setattr(transport, 'compress_async', mock_compress_async)

            with caplog.at_level(logging.WARNING):
                await execmanager.stash_calculation(node, transport)
                assert any('Failed to stash' in message for message in caplog.messages)

    # Ensure no files were created in the destination path after the error
    assert not any(dest_path_error.iterdir())
