###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""This module contains a set of tests that every transport plugin should be able to
pass.
Plugin specific tests will be written in the corresponding test file.
"""

import io
import os
import re
import shutil
import signal
import tempfile
import time
import uuid
from pathlib import Path

import psutil
import pytest

from aiida.common.warnings import AiidaDeprecationWarning
from aiida.plugins import SchedulerFactory, TransportFactory
from aiida.transports import Transport

# TODO : test for copy with pattern
# TODO : test for copy with/without patterns, overwriting folder
# TODO : test for exotic cases of copy with source = destination
# TODO : silly cases of copy/put/get from self to self

CHDIR_WARNING = re.escape('`chdir()` is deprecated and will be removed')


@pytest.fixture(scope='function')
def tmp_path_remote(tmp_path_factory):
    """Provides a tmp path for mocking remote computer directory environment.

    Local and remote directories must be kept separate to ensure proper functionality testing.
    The created folder starts with prefix 'remote'
    """
    return tmp_path_factory.mktemp('remote')


@pytest.fixture(scope='function')
def tmp_path_local(tmp_path_factory):
    """Provides a tmp path for mocking local computer directory environment.

    Local and remote directories must be kept separate to ensure proper functionality testing.
    The created folder starts with prefix 'local'
    """
    return tmp_path_factory.mktemp('local')


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
def custom_transport(request, tmp_path_factory, monkeypatch) -> Transport:
    """Fixture that parametrizes over all the registered implementations of the transport plugins."""
    plugin = TransportFactory(request.param[0])

    if request.param[0] == 'core.ssh':
        kwargs = {'machine': 'localhost', 'timeout': 30, 'load_system_host_keys': True, 'key_policy': 'AutoAddPolicy'}
    elif request.param[0] == 'core.ssh_async':
        kwargs = {
            'machine': 'localhost',
            'backend': request.param[1],
        }
    else:
        kwargs = {}

    return plugin(**kwargs)


def test_is_open(custom_transport):
    """Test that the is_open property works."""
    assert not custom_transport.is_open

    with custom_transport:
        assert custom_transport.is_open

    assert not custom_transport.is_open


def test_makedirs(custom_transport, tmpdir):
    """Verify the functioning of makedirs command"""
    with custom_transport as transport:
        _scratch = Path(tmpdir / 'sampledir')
        transport.mkdir(_scratch)
        assert _scratch.exists()

        _scratch = tmpdir / 'sampledir2' / 'subdir'
        transport.makedirs(_scratch)
        assert _scratch.exists()

        # raise if directory already exists
        with pytest.raises(OSError):
            transport.makedirs(tmpdir / 'sampledir2')
        with pytest.raises(OSError):
            transport.mkdir(tmpdir / 'sampledir')


def test_is_dir(custom_transport, tmpdir):
    with custom_transport as transport:
        _scratch = tmpdir / 'sampledir'
        transport.mkdir(_scratch)

        assert transport.isdir(_scratch)
        assert not transport.isdir(_scratch / 'does_not_exist')


def test_rmtree(custom_transport, tmp_path_remote, tmp_path_local):
    """Verify the functioning of rmtree command"""
    with custom_transport as transport:
        _remote = tmp_path_remote
        _local = tmp_path_local

        Path(_local / 'samplefile').touch()

        # remove a non-empty directory with rmtree()
        _scratch = _remote / 'sampledir'
        _scratch.mkdir()
        Path(_remote / 'sampledir' / 'samplefile_remote').touch()
        transport.rmtree(_scratch)
        assert not _scratch.exists()

        # remove a non-empty directory should raise with rmdir()
        transport.mkdir(_remote / 'sampledir')
        Path(_remote / 'sampledir' / 'samplefile_remote').touch()
        with pytest.raises(OSError):
            transport.rmdir(_remote / 'sampledir')

        # remove a file with remove()
        transport.remove(_remote / 'sampledir' / 'samplefile_remote')
        assert not Path(_remote / 'sampledir' / 'samplefile_remote').exists()

        # remove a empty directory with rmdir
        transport.rmdir(_remote / 'sampledir')
        assert not _scratch.exists()


def test_listdir(custom_transport, tmp_path_remote):
    """Create directories, verify listdir, delete a folder with subfolders"""
    with custom_transport as transport:
        list_of_dir = ['1', '-f a&', 'as', 'a2', 'a4f']
        list_of_dir = ['1', '-f', 'as', 'a2', 'a4f']
        list_of_files = ['a', 'b']
        for this_dir in list_of_dir:
            transport.mkdir(tmp_path_remote / this_dir)

        for fname in list_of_files:
            with tempfile.NamedTemporaryFile() as tmpf:
                # Just put an empty file there at the right file name
                transport.putfile(tmpf.name, tmp_path_remote / fname)

        list_found = transport.listdir(tmp_path_remote)

        assert sorted(list_found) == sorted(list_of_dir + list_of_files)

        assert sorted(transport.listdir(tmp_path_remote, 'a*')), sorted(['as', 'a2', 'a4f'])
        assert sorted(transport.listdir(tmp_path_remote, 'a?')), sorted(['as', 'a2'])
        assert sorted(transport.listdir(tmp_path_remote, 'a[2-4]*')), sorted(['a2', 'a4f'])


def test_listdir_withattributes(custom_transport, tmp_path_remote):
    """Create directories, verify listdir_withattributes, delete a folder with subfolders"""

    def simplify_attributes(data):
        """Take data from listdir_withattributes and return a dictionary
        {fname: isdir}

        :param data: the output of listdir_withattributes
        :return: dictionary: the key is a filename, the value is True if it's a directory, False otherwise
        """
        return {_['name']: _['isdir'] for _ in data}

    with custom_transport as transport:
        list_of_dir = ['1', '-f a&', 'as', 'a2', 'a4f']
        list_of_dir = ['1', '-f', 'as', 'a2', 'a4f']
        list_of_files = ['a', 'b']
        for this_dir in list_of_dir:
            transport.mkdir(tmp_path_remote / this_dir)
        for fname in list_of_files:
            with tempfile.NamedTemporaryFile() as tmpf:
                # Just put an empty file there at the right file name
                transport.putfile(tmpf.name, tmp_path_remote / fname)

        comparison_list = {k: True for k in list_of_dir}
        for k in list_of_files:
            comparison_list[k] = False

        assert simplify_attributes(transport.listdir_withattributes(tmp_path_remote)), comparison_list
        assert simplify_attributes(transport.listdir_withattributes(tmp_path_remote, 'a*')), {
            'as': True,
            'a2': True,
            'a4f': True,
            'a': False,
        }
        assert simplify_attributes(transport.listdir_withattributes(tmp_path_remote, 'a?')), {
            'as': True,
            'a2': True,
        }
        assert simplify_attributes(transport.listdir_withattributes(tmp_path_remote, 'a[2-4]*')), {
            'a2': True,
            'a4f': True,
        }


def test_dir_copy(custom_transport, tmp_path_remote):
    """Verify if in the copy of a directory also the protection bits
    are carried over
    """
    with custom_transport as transport:
        src_dir = tmp_path_remote / 'copy_src'
        transport.mkdir(src_dir)

        dst_dir = tmp_path_remote / 'copy_dst'
        transport.copy(src_dir, dst_dir)

        with pytest.raises(ValueError):
            transport.copy(src_dir, '')

        with pytest.raises(ValueError):
            transport.copy('', dst_dir)


def test_dir_permissions_creation_modification(custom_transport, tmp_path_remote):
    """Verify if chmod raises OSError when trying to change bits on a
    non-existing folder
    """
    with custom_transport as transport:
        directory = tmp_path_remote / 'test'

        transport.makedirs(directory)
        # change permissions
        transport.chmod(directory, 0o777)

        # test if the security bits have changed
        assert transport.get_mode(directory) == 0o777

        # change permissions
        transport.chmod(directory, 0o511)

        # test if the security bits have changed
        assert transport.get_mode(directory) == 0o511

        # TODO : bug in paramiko. When changing the directory to very low \
        # I cannot set it back to higher permissions

        # TODO: probably here we should then check for
        # the new directory modes. To see if we want a higher
        # level function to ask for the mode, or we just
        # use get_attribute

        # change permissions of an empty string, non existing folder.
        with pytest.raises(OSError):
            transport.chmod('', 0o777)

        # change permissions of a non existing folder.
        fake_dir = 'pippo'
        with pytest.raises(OSError):
            # chmod to a non existing folder
            transport.chmod(tmp_path_remote / fake_dir, 0o777)


def test_dir_reading_permissions(custom_transport, tmp_path_remote):
    """Try to enter a directory with no read & write permissions."""
    with custom_transport as transport:
        directory = tmp_path_remote / 'test'

        # create directory with non default permissions
        transport.mkdir(directory)

        # change permissions to low ones
        transport.chmod(directory, 0)

        # test if the security bits have changed
        assert transport.get_mode(directory) == 0

        # TODO : the test leaves a directory even if it is successful
        #        The bug is in paramiko. After lowering the permissions,
        #        I cannot restore them to higher values
        # transport.rmdir(directory)


def test_isfile_isdir(custom_transport, tmp_path_remote):
    with custom_transport as transport:
        # return False on empty string
        assert not transport.isdir('')
        assert not transport.isfile('')
        # return False on non-existing files
        assert not transport.isfile(tmp_path_remote / 'does_not_exist')
        assert not transport.isdir(tmp_path_remote / 'does_not_exist')

        # isfile and isdir should not confuse files and directories
        Path(tmp_path_remote / 'samplefile').touch()
        assert transport.isfile(tmp_path_remote / 'samplefile')
        assert not transport.isdir(tmp_path_remote / 'samplefile')

        transport.mkdir(tmp_path_remote / 'sampledir')

        assert transport.isdir(tmp_path_remote / 'sampledir')
        assert not transport.isfile(tmp_path_remote / 'sampledir')


def test_chdir_to_empty_string(custom_transport):
    """I check that if I pass an empty string to chdir, the cwd does
    not change (this is a paramiko default behavior), but getcwd()
    is still correctly defined.

    chdir() is no longer an abstract method, to be removed from interface
    """
    if not hasattr(custom_transport, 'chdir'):
        return

    with custom_transport as transport:
        with pytest.warns(AiidaDeprecationWarning, match=CHDIR_WARNING):
            new_dir = transport.normalize(os.path.join('/', 'tmp'))
            transport.chdir(new_dir)
            transport.chdir('')
            assert new_dir == transport.getcwd()


def test_put_and_get(custom_transport, tmp_path_remote, tmp_path_local):
    """Test putting and getting files."""
    directory = 'tmp_try'

    with custom_transport as transport:
        (tmp_path_local / directory).mkdir()
        transport.mkdir(tmp_path_remote / directory)

        local_file_name = 'file.txt'
        retrieved_file_name = 'file_retrieved.txt'

        remote_file_name = 'file_remote.txt'

        # here use full path in src and dst
        local_file_abs_path = tmp_path_local / directory / local_file_name
        retrieved_file_abs_path = tmp_path_local / directory / retrieved_file_name
        remote_file_abs_path = tmp_path_remote / directory / remote_file_name

        text = 'Viva Verdi\n'
        with open(local_file_abs_path, 'w', encoding='utf8') as fhandle:
            fhandle.write(text)

        transport.put(local_file_abs_path, remote_file_abs_path)
        transport.get(remote_file_abs_path, retrieved_file_abs_path)

        list_of_files = transport.listdir((tmp_path_remote / directory))
        # it is False because local_file_name has the full path,
        # while list_of_files has not
        assert local_file_name not in list_of_files
        assert remote_file_name in list_of_files
        assert retrieved_file_name not in list_of_files


def test_putfile_and_getfile(custom_transport, tmp_path_remote, tmp_path_local):
    """Test putting and getting files."""
    local_dir = tmp_path_local
    remote_dir = tmp_path_remote

    directory = 'tmp_try'

    with custom_transport as transport:
        (local_dir / directory).mkdir()
        transport.mkdir((remote_dir / directory))

        local_file_name = 'file.txt'
        retrieved_file_name = 'file_retrieved.txt'

        remote_file_name = 'file_remote.txt'

        # here use full path in src and dst
        local_file_abs_path = local_dir / directory / local_file_name
        retrieved_file_abs_path = local_dir / directory / retrieved_file_name
        remote_file_abs_path = remote_dir / directory / remote_file_name

        text = 'Viva Verdi\n'
        with open(local_file_abs_path, 'w', encoding='utf8') as fhandle:
            fhandle.write(text)

        transport.putfile(local_file_abs_path, remote_file_abs_path)
        transport.getfile(remote_file_abs_path, retrieved_file_abs_path)

        list_of_files = transport.listdir(remote_dir / directory)
        # it is False because local_file_name has the full path,
        # while list_of_files has not
        assert local_file_name not in list_of_files
        assert remote_file_name in list_of_files
        assert retrieved_file_name not in list_of_files


def test_put_get_abs_path_file(custom_transport, tmp_path_remote, tmp_path_local):
    """Test of exception for non existing files and abs path"""
    local_dir = tmp_path_local
    remote_dir = tmp_path_remote

    directory = 'tmp_try'

    with custom_transport as transport:
        (local_dir / directory).mkdir()
        transport.mkdir((remote_dir / directory))

        local_file_name = 'file.txt'
        retrieved_file_name = 'file_retrieved.txt'

        remote_file_name = 'file_remote.txt'
        local_file_rel_path = local_file_name
        remote_file_rel_path = remote_file_name

        retrieved_file_abs_path = local_dir / directory / retrieved_file_name
        remote_file_abs_path = remote_dir / directory / remote_file_name

        # partial_file_name is not an abs path
        with pytest.raises(ValueError):
            transport.put(local_file_rel_path, remote_file_abs_path)
        with pytest.raises(ValueError):
            transport.putfile(local_file_rel_path, remote_file_abs_path)

        # retrieved_file_name does not exist
        with pytest.raises(OSError):
            transport.put(retrieved_file_abs_path, remote_file_abs_path)
        with pytest.raises(OSError):
            transport.putfile(retrieved_file_abs_path, remote_file_abs_path)

        # remote_file_name does not exist
        with pytest.raises(OSError):
            transport.get(remote_file_abs_path, retrieved_file_abs_path)
        with pytest.raises(OSError):
            transport.getfile(remote_file_abs_path, retrieved_file_abs_path)

        # remote filename is not an abs path
        with pytest.raises(ValueError):
            transport.get(remote_file_rel_path, 'delete_me.txt')
        with pytest.raises(ValueError):
            transport.getfile(remote_file_rel_path, 'delete_me.txt')


def test_put_get_empty_string_file(custom_transport, tmp_path_remote, tmp_path_local):
    """Test of exception put/get of empty strings"""
    # TODO : verify the correctness of \n at the end of a file
    local_dir = tmp_path_local
    remote_dir = tmp_path_remote
    directory = 'tmp_try'

    with custom_transport as transport:
        (local_dir / directory).mkdir()
        transport.mkdir((remote_dir / directory))

        local_file_name = 'file.txt'
        retrieved_file_name = 'file_retrieved.txt'

        remote_file_name = 'file_remote.txt'

        # here use full path in src and dst
        local_file_abs_path = local_dir / directory / local_file_name
        retrieved_file_abs_path = local_dir / directory / retrieved_file_name
        remote_file_abs_path = remote_dir / directory / remote_file_name

        text = 'Viva Verdi\n'
        with open(local_file_abs_path, 'w', encoding='utf8') as fhandle:
            fhandle.write(text)

        # localpath is an empty string
        # ValueError because it is not an abs path
        with pytest.raises(ValueError):
            transport.put('', remote_file_abs_path)
        with pytest.raises(ValueError):
            transport.putfile('', remote_file_abs_path)

        # remote path is an empty string
        with pytest.raises(OSError):
            transport.put(local_file_abs_path, '')
        with pytest.raises(OSError):
            transport.putfile(local_file_abs_path, '')

        transport.put(local_file_abs_path, remote_file_abs_path)
        # overwrite the remote_file_name
        transport.putfile(local_file_abs_path, remote_file_abs_path)

        # remote path is an empty string
        with pytest.raises(OSError):
            transport.get('', retrieved_file_abs_path)
        with pytest.raises(OSError):
            transport.getfile('', retrieved_file_abs_path)

        # local path is an empty string
        # ValueError because it is not an abs path
        with pytest.raises(ValueError):
            transport.get(remote_file_abs_path, '')
        with pytest.raises(ValueError):
            transport.getfile(remote_file_abs_path, '')

        # TODO : get doesn't retrieve empty files.
        # Is it what we want?
        transport.get(remote_file_abs_path, retrieved_file_abs_path)
        assert Path(retrieved_file_abs_path).exists()
        t1 = Path(retrieved_file_abs_path).stat().st_mtime_ns

        # overwrite retrieved_file_name in 0.01 s
        time.sleep(1)
        transport.getfile(remote_file_abs_path, retrieved_file_abs_path)
        assert Path(retrieved_file_abs_path).exists()
        t2 = Path(retrieved_file_abs_path).stat().st_mtime_ns

        # Check st_mtime_ns to sure it is overwritten
        # Note: this test will fail if getfile() would preserve the remote timestamp,
        # this is supported by core.ssh_async, but the default value is False
        assert t2 > t1


def test_put_and_get_tree(custom_transport, tmp_path_remote, tmp_path_local):
    """Test putting and getting files."""
    local_dir = tmp_path_local
    remote_dir = tmp_path_remote

    directory = 'tmp_try'

    with custom_transport as transport:
        local_subfolder: Path = local_dir / directory / 'tmp1'
        remote_subfolder: Path = remote_dir / 'tmp2'
        retrieved_subfolder: Path = local_dir / directory / 'tmp3'

        local_subfolder.mkdir(parents=True)

        local_file = local_subfolder / 'file.txt'

        text = 'Viva Verdi\n'
        with open(local_file, 'w', encoding='utf8') as fhandle:
            fhandle.write(text)

        # here use full path in src and dst
        transport.puttree((local_subfolder), (remote_subfolder))
        transport.gettree((remote_subfolder), (retrieved_subfolder))

        list_of_dirs = [p.name for p in (local_dir / directory).iterdir()]

        assert local_subfolder not in list_of_dirs
        assert remote_subfolder not in list_of_dirs
        assert retrieved_subfolder not in list_of_dirs
        assert 'tmp1' in list_of_dirs
        assert 'tmp3' in list_of_dirs

        list_pushed_file = transport.listdir(remote_subfolder)
        list_retrieved_file = [p.name for p in retrieved_subfolder.iterdir()]
        assert 'file.txt' in list_pushed_file
        assert 'file.txt' in list_retrieved_file


@pytest.mark.parametrize(
    'local_hierarchy, target_hierarchy, src_dest, expected_hierarchy',
    (
        ({'file.txt': 'Viva verdi'}, {}, ('.', '.'), {'file.txt': 'Viva verdi'}),
        (
            {'local': {'file.txt': 'New verdi'}},
            {'local': {'file.txt': 'Old verdi'}},
            ('local', '.'),
            {'local': {'file.txt': 'New verdi'}},
        ),
        (
            {'local': {'file.txt': 'Viva verdi'}},
            {'local': {'file.txt': 'Viva verdi'}},
            ('local', 'local'),
            {'local': {'file.txt': 'Viva verdi', 'local': {'file.txt': 'Viva verdi'}}},
        ),
        (
            {'local': {'sub': {'file.txt': 'Viva verdi'}}},
            {},
            ('local/sub', 'local/sub'),
            {'local': {'sub': {'file.txt': 'Viva verdi'}}},
        ),
    ),
)
def test_put_and_get_overwrite(
    custom_transport,
    tmp_path,
    create_file_hierarchy,
    serialize_file_hierarchy,
    local_hierarchy,
    target_hierarchy,
    src_dest,
    expected_hierarchy,
):
    """Test putting and getting files with overwrites.

    The parametrized inputs are:

    - local_hierarchy: the hierarchy of files to be created in the "local" folder
    - target_hierarchy: the hierarchy of files to be created in the "remote" folder for testing `puttree`, and the
      "retrieved" folder for testing `gettree`.
    - src_dest: a tuple with the source and destination of the files to put/get
    - expected_hierarchy: the expected hierarchy of files in the "remote" and "retrieved" folder after the overwrite
    """

    local_folder = tmp_path / 'local'
    remote_folder = tmp_path / 'remote'
    retrieved_folder = tmp_path / 'retrieved'

    create_file_hierarchy(local_hierarchy, local_folder)
    create_file_hierarchy(target_hierarchy, remote_folder)
    create_file_hierarchy(target_hierarchy, retrieved_folder)

    source, destination = src_dest

    with custom_transport as transport:
        transport.puttree((local_folder / source).as_posix(), (remote_folder / destination).as_posix())
        transport.gettree((local_folder / source).as_posix(), (retrieved_folder / destination).as_posix())

        assert serialize_file_hierarchy(remote_folder, read_bytes=False) == expected_hierarchy
        assert serialize_file_hierarchy(retrieved_folder, read_bytes=False) == expected_hierarchy

        # Attempting to exectute the put/get operations with `overwrite=False` should raise an OSError
        with pytest.raises(OSError):
            transport.put((tmp_path / source).as_posix(), (remote_folder / destination).as_posix(), overwrite=False)
        with pytest.raises(OSError):
            transport.get(
                (remote_folder / source).as_posix(), (retrieved_folder / destination).as_posix(), overwrite=False
            )
        with pytest.raises(OSError):
            transport.puttree((tmp_path / source).as_posix(), (remote_folder / destination).as_posix(), overwrite=False)
        with pytest.raises(OSError):
            transport.gettree(
                (remote_folder / source).as_posix(), (retrieved_folder / destination).as_posix(), overwrite=False
            )


def test_copy(custom_transport, tmp_path_remote):
    """Test copying from a remote src to remote dst"""
    remote_dir = tmp_path_remote

    directory = 'tmp_try'

    with custom_transport as transport:
        workdir = remote_dir / directory

        transport.mkdir(workdir)

        base_dir = workdir / 'origin'
        base_dir.mkdir()

        # first create three files
        file_1 = base_dir / 'a.txt'
        file_2 = base_dir / 'b.tmp'
        file_3 = base_dir / 'c.txt'
        text = 'Viva Verdi\n'
        for filename in [file_1, file_2, file_3]:
            with open(filename, 'w', encoding='utf8') as fhandle:
                fhandle.write(text)

        # first test the copy. Copy of two files matching patterns, into a folder
        transport.copy(base_dir / '*.txt', workdir)
        assert set(['a.txt', 'c.txt', 'origin']) == set(transport.listdir(workdir))
        transport.remove(workdir / 'a.txt')
        transport.remove(workdir / 'c.txt')

        # second test copy. Copy of two folders
        transport.copy(base_dir, workdir / 'prova')
        assert set(['prova', 'origin']) == set(transport.listdir(workdir))
        assert set(['a.txt', 'b.tmp', 'c.txt']) == set(transport.listdir(workdir / 'prova'))
        transport.rmtree(workdir / 'prova')

        # third test copy. Can copy one file into a new file
        transport.copy(base_dir / '*.tmp', workdir / 'prova')
        assert transport.isfile(workdir / 'prova')
        transport.remove(workdir / 'prova')

        # fourth test copy: can't copy more than one file on the same file,
        # i.e., the destination should be a folder
        with pytest.raises(OSError):
            transport.copy(base_dir / '*.txt', workdir / 'prova')

        # fifth test, copying one file into a folder
        transport.mkdir((workdir / 'prova'))
        transport.copy((base_dir / 'a.txt'), (workdir / 'prova'))
        assert set(transport.listdir((workdir / 'prova'))) == set(['a.txt'])
        transport.rmtree((workdir / 'prova'))

        # sixth test, copying one file into a file
        transport.copy((base_dir / 'a.txt'), (workdir / 'prova'))
        assert transport.isfile((workdir / 'prova'))
        transport.remove((workdir / 'prova'))
        # copy of folder into an existing folder
        # NOTE: the command cp has a different behavior on Mac vs Ubuntu
        # tests performed locally on a Mac may result in a failure.
        transport.mkdir((workdir / 'prova'))
        transport.copy((base_dir), (workdir / 'prova'))
        assert set(['origin']) == set(transport.listdir((workdir / 'prova')))
        assert set(['a.txt', 'b.tmp', 'c.txt']) == set(transport.listdir((workdir / 'prova' / 'origin')))


def test_put(custom_transport, tmp_path_remote, tmp_path_local):
    """Test putting files.
    These are similar tests of copy, just with the put function which copy from mocked local to mocked remote
    and therefore the local path must be absolute
    """
    local_dir = tmp_path_local
    remote_dir = tmp_path_remote
    directory = 'tmp_try'

    with custom_transport as transport:
        local_workdir = local_dir / directory
        remote_workdir = remote_dir / directory

        transport.mkdir(remote_workdir)

        local_base_dir: Path = local_workdir / 'origin'
        local_base_dir.mkdir(parents=True)

        # first test put: I create three files in local
        file_1 = local_base_dir / 'a.txt'
        file_2 = local_base_dir / 'b.tmp'
        file_3 = local_base_dir / 'c.txt'
        text = 'Viva Verdi\n'
        for filename in [file_1, file_2, file_3]:
            with open(filename, 'w', encoding='utf8') as fhandle:
                fhandle.write(text)

        # first test the put. Copy of two files matching patterns, into a folder
        transport.put((local_base_dir / '*.txt'), (remote_workdir))
        assert set(['a.txt', 'c.txt']) == set(transport.listdir((remote_workdir)))
        transport.remove((remote_workdir / 'a.txt'))
        transport.remove((remote_workdir / 'c.txt'))

        # second test put. Put of two folders
        transport.put((local_base_dir), (remote_workdir / 'prova'))
        assert set(['prova']) == set(transport.listdir((remote_workdir)))
        assert set(['a.txt', 'b.tmp', 'c.txt']) == set(transport.listdir((remote_workdir / 'prova')))
        transport.rmtree((remote_workdir / 'prova'))

        # third test put. Can copy one file into a new file
        transport.put((local_base_dir / '*.tmp'), (remote_workdir / 'prova'))
        assert transport.isfile((remote_workdir / 'prova'))
        transport.remove((remote_workdir / 'prova'))

        # fourth test put: can't copy more than one file to the same file,
        # i.e., the destination should be a folder
        with pytest.raises(OSError):
            transport.put((local_base_dir / '*.txt'), (remote_workdir / 'prova'))

        # can't copy folder to an exist file
        with open(remote_workdir / 'existing.txt', 'w', encoding='utf8') as fhandle:
            fhandle.write(text)
        with pytest.raises(OSError):
            transport.put((local_base_dir), (remote_workdir / 'existing.txt'))
        transport.remove((remote_workdir / 'existing.txt'))

        # fifth test, copying one file into a folder
        transport.mkdir((remote_workdir / 'prova'))
        transport.put((local_base_dir / 'a.txt'), (remote_workdir / 'prova'))
        assert set(transport.listdir((remote_workdir / 'prova'))) == set(['a.txt'])
        transport.rmtree((remote_workdir / 'prova'))

        # sixth test, copying one file into a file
        transport.put((local_base_dir / 'a.txt'), (remote_workdir / 'prova'))
        assert transport.isfile((remote_workdir / 'prova'))
        transport.remove((remote_workdir / 'prova'))

        # put of folder into an existing folder
        # NOTE: the command cp has a different behavior on Mac vs Ubuntu
        # tests performed locally on a Mac may result in a failure.
        transport.mkdir((remote_workdir / 'prova'))
        transport.put((local_base_dir), (remote_workdir / 'prova'))
        assert set(['origin']) == set(transport.listdir((remote_workdir / 'prova')))
        assert set(['a.txt', 'b.tmp', 'c.txt']) == set(transport.listdir((remote_workdir / 'prova' / 'origin')))
        transport.rmtree((remote_workdir / 'prova'))
        # exit
        transport.rmtree((remote_workdir))


def test_get(custom_transport, tmp_path_remote, tmp_path_local):
    """Test getting files."""
    # exactly the same tests of copy, just with the put function
    # and therefore the local path must be absolute
    local_dir = tmp_path_local
    remote_dir = tmp_path_remote
    directory = 'tmp_try'

    with custom_transport as transport:
        local_workdir: Path = local_dir / directory
        remote_workdir: Path = remote_dir / directory

        local_workdir.mkdir()

        remote_base_dir: Path = remote_workdir / 'origin'
        remote_base_dir.mkdir(parents=True)

        # first test put: I create three files in remote
        file_1 = remote_base_dir / 'a.txt'
        file_2 = remote_base_dir / 'b.tmp'
        file_3 = remote_base_dir / 'c.txt'
        text = 'Viva Verdi\n'
        for filename in [file_1, file_2, file_3]:
            with open(filename, 'w', encoding='utf8') as fhandle:
                fhandle.write(text)

        # first test get. Get two files matching patterns, from mocked remote folder into a local folder
        transport.get((remote_base_dir / '*.txt'), (local_workdir))
        assert set(['a.txt', 'c.txt']) == set([p.name for p in (local_workdir).iterdir()])
        (local_workdir / 'a.txt').unlink()
        (local_workdir / 'c.txt').unlink()

        # second. Copy of folder into a non existing folder
        transport.get((remote_base_dir), (local_workdir / 'prova'))
        assert set(['prova']) == set([p.name for p in local_workdir.iterdir()])
        assert set(['a.txt', 'b.tmp', 'c.txt']) == set([p.name for p in (local_workdir / 'prova').iterdir()])
        shutil.rmtree(local_workdir / 'prova')

        # third. copy of folder into an existing folder
        (local_workdir / 'prova').mkdir()
        transport.get((remote_base_dir), (local_workdir / 'prova'))
        assert set(['prova']) == set([p.name for p in local_workdir.iterdir()])
        assert set(['origin']) == set([p.name for p in (local_workdir / 'prova').iterdir()])
        assert set(['a.txt', 'b.tmp', 'c.txt']) == set([p.name for p in (local_workdir / 'prova' / 'origin').iterdir()])
        shutil.rmtree(local_workdir / 'prova')

        # test get one file into a new file prova
        transport.get((remote_base_dir / '*.tmp'), (local_workdir / 'prova'))
        assert set(['prova']) == set([p.name for p in local_workdir.iterdir()])
        assert (local_workdir / 'prova').is_file()
        (local_workdir / 'prova').unlink()

        # fourth test copy: can't copy more than one file on the same file,
        # i.e., the destination should be a folder
        with pytest.raises(OSError):
            transport.get((remote_base_dir / '*.txt'), (local_workdir / 'prova'))
        # copy of folder into file
        with open(local_workdir / 'existing.txt', 'w', encoding='utf8') as fhandle:
            fhandle.write(text)
        with pytest.raises(OSError):
            transport.get((remote_base_dir), (local_workdir / 'existing.txt'))
        (local_workdir / 'existing.txt').unlink()

        # fifth test, copying one file into a folder
        (local_workdir / 'prova').mkdir()
        transport.get((remote_base_dir / 'a.txt'), (local_workdir / 'prova'))
        assert set(['a.txt']) == set([p.name for p in (local_workdir / 'prova').iterdir()])
        shutil.rmtree(local_workdir / 'prova')

        # sixth test, copying one file into a file
        transport.get((remote_base_dir / 'a.txt'), (local_workdir / 'prova'))
        assert (local_workdir / 'prova').is_file()
        (local_workdir / 'prova').unlink()


def test_put_get_abs_path_tree(custom_transport, tmp_path_remote, tmp_path_local):
    """Test of exception for non existing files and abs path"""
    local_dir = tmp_path_local
    remote_dir = tmp_path_remote
    directory = 'tmp_try'

    with custom_transport as transport:
        local_subfolder = local_dir / directory / 'tmp1'
        remote_subfolder = remote_dir / 'tmp2'
        retrieved_subfolder = local_dir / directory / 'tmp3'

        (local_dir / directory / local_subfolder).mkdir(parents=True)

        local_file_name = Path(local_subfolder) / 'file.txt'

        text = 'Viva Verdi\n'
        with open(local_file_name, 'w', encoding='utf8') as fhandle:
            fhandle.write(text)

        # here use absolute path in src and dst
        # 'tmp1' is not an abs path
        with pytest.raises(ValueError):
            transport.put('tmp1', remote_subfolder)
        with pytest.raises(ValueError):
            transport.putfile('tmp1', remote_subfolder)
        with pytest.raises(ValueError):
            transport.puttree('tmp1', remote_subfolder)

        # 'tmp3' does not exist
        with pytest.raises(OSError):
            transport.put(retrieved_subfolder, remote_subfolder)
        with pytest.raises(OSError):
            transport.putfile(retrieved_subfolder, remote_subfolder)
        with pytest.raises(OSError):
            transport.puttree(retrieved_subfolder, remote_subfolder)

        # remote_file_name does not exist
        with pytest.raises(OSError):
            transport.get('non_existing', retrieved_subfolder)
        with pytest.raises(OSError):
            transport.getfile('non_existing', retrieved_subfolder)
        with pytest.raises(OSError):
            transport.gettree('non_existing', retrieved_subfolder)

        transport.put(local_subfolder, remote_subfolder)

        # local filename is not an abs path
        with pytest.raises(ValueError):
            transport.get(remote_subfolder, 'delete_me_tree')
        with pytest.raises(ValueError):
            transport.getfile(remote_subfolder, 'delete_me_tree')
        with pytest.raises(ValueError):
            transport.gettree(remote_subfolder, 'delete_me_tree')


def test_put_get_empty_string_tree(custom_transport, tmp_path_remote, tmp_path_local):
    """Test of exception put/get of empty strings"""
    local_dir = tmp_path_local
    remote_dir = tmp_path_remote
    directory = 'tmp_try'

    with custom_transport as transport:
        local_subfolder: Path = local_dir / directory / 'tmp1'
        remote_subfolder: Path = remote_dir / 'tmp2'
        retrieved_subfolder: Path = local_dir / directory / 'tmp3'

        local_subfolder.mkdir(parents=True)

        local_file = local_subfolder / 'file.txt'

        text = 'Viva Verdi\n'
        with open(local_file, 'w', encoding='utf8') as fhandle:
            fhandle.write(text)

        # localpath is an empty string
        # ValueError because it is not an abs path
        with pytest.raises(ValueError):
            transport.puttree('', remote_subfolder)

        # remote path is an empty string
        with pytest.raises(OSError):
            transport.puttree(local_subfolder, '')

        transport.puttree(local_subfolder, remote_subfolder)

        # remote path is an empty string
        with pytest.raises(OSError):
            transport.gettree('', retrieved_subfolder)

        # local path is an empty string
        # ValueError because it is not an abs path
        with pytest.raises(ValueError):
            transport.gettree(remote_subfolder, '')

        # TODO : get doesn't retrieve empty files.
        # Is it what we want?
        transport.gettree((remote_subfolder), (retrieved_subfolder))

        assert 'file.txt' in [p.name for p in retrieved_subfolder.iterdir()]


def test_gettree_nested_directory(custom_transport, tmp_path_remote, tmp_path_local):
    """Test `gettree` for a nested directory."""
    content = b'dummy\ncontent'
    dir_path = tmp_path_remote / 'sub' / 'path'
    dir_path.mkdir(parents=True)

    file_path = dir_path / 'filename.txt'

    with open(file_path, 'wb') as handle:
        handle.write(content)

    with custom_transport as transport:
        transport.gettree((tmp_path_remote), (tmp_path_local))

    assert (tmp_path_local / 'sub' / 'path' / 'filename.txt').is_file


def test_exec_pwd(custom_transport, tmp_path_remote):
    """I create a strange subfolder with a complicated name and
    then see if I can run ``ls``. This also checks the correct
    escaping of funny characters, both in the directory
    creation (which should be done by paramiko) and in the command
    execution (done in this module, in the _exec_command_internal function).

    Note: chdir() & getcwd() is no longer an abstract method, therefore this test is skipped for AsyncSshTransport.
    """
    # Start value
    if not hasattr(custom_transport, 'chdir'):
        return

    with custom_transport as transport:
        # To compare with: getcwd uses the normalized ('realpath') path
        location = transport.normalize('/tmp')
        subfolder = """_'s f"#"""  # A folder with characters to escape
        subfolder_fullpath = os.path.join(location, subfolder)

        with pytest.warns(AiidaDeprecationWarning, match=CHDIR_WARNING):
            transport.chdir(location)
        if not transport.isdir(subfolder):
            # Since I created the folder, I will remember to
            # delete it at the end of this test
            transport.mkdir(subfolder)

            assert transport.isdir(subfolder)
            with pytest.warns(AiidaDeprecationWarning, match=CHDIR_WARNING):
                transport.chdir(subfolder)

            assert subfolder_fullpath == transport.getcwd()
            retcode, stdout, stderr = transport.exec_command_wait('pwd')
            assert retcode == 0
            # I have to strip it because 'pwd' returns a trailing \n
            assert stdout.strip() == subfolder_fullpath
            assert stderr == ''


def test_exec_with_stdin_string(custom_transport):
    """Test command execution with a stdin string."""
    test_string = 'some_test String'
    with custom_transport as transport:
        retcode, stdout, stderr = transport.exec_command_wait('cat', stdin=test_string)
        assert retcode == 0
        assert stdout == test_string
        assert stderr == ''


def test_exec_with_stdin_bytes(custom_transport):
    """Test command execution with a stdin bytes.

    I test directly the exec_command_wait_bytes function; I also pass some non-unicode
    bytes to check that there is no internal implicit encoding/decoding in the code.
    """

    # Skip this test for AsyncSshTransport
    if 'AsyncSshTransport' in custom_transport.__str__():
        return

    test_string = b'some_test bytes with non-unicode -> \xfa'
    with custom_transport as transport:
        retcode, stdout, stderr = transport.exec_command_wait_bytes('cat', stdin=test_string)
        assert retcode == 0
        assert stdout == test_string
        assert stderr == b''


def test_exec_with_stdin_filelike(custom_transport):
    """Test command execution with a stdin from filelike."""

    # Skip this test for AsyncSshTransport
    if 'AsyncSshTransport' in custom_transport.__str__():
        return

    test_string = 'some_test String'
    stdin = io.StringIO(test_string)
    with custom_transport as transport:
        retcode, stdout, stderr = transport.exec_command_wait('cat', stdin=stdin)
        assert retcode == 0
        assert stdout == test_string
        assert stderr == ''


def test_exec_with_stdin_filelike_bytes(custom_transport):
    """Test command execution with a stdin from filelike of type bytes.

    I test directly the exec_command_wait_bytes function; I also pass some non-unicode
    bytes to check that there is no place in the code where this non-unicode string is
    implicitly converted to unicode (temporarily, and then converted back) -
    if this happens somewhere, that code would fail (as the test_string
    cannot be decoded to UTF8). (Note: we cannot test for all encodings, we test for
    unicode hoping that this would already catch possible issues.)
    """
    # Skip this test for AsyncSshTransport
    if 'AsyncSshTransport' in custom_transport.__str__():
        return

    test_string = b'some_test bytes with non-unicode -> \xfa'
    stdin = io.BytesIO(test_string)
    with custom_transport as transport:
        retcode, stdout, stderr = transport.exec_command_wait_bytes('cat', stdin=stdin)
        assert retcode == 0
        assert stdout == test_string
        assert stderr == b''


def test_exec_with_stdin_filelike_bytes_decoding(custom_transport):
    """Test command execution with a stdin from filelike of type bytes, trying to decode.

    I test directly the exec_command_wait_bytes function; I also pass some non-unicode
    bytes to check that there is no place in the code where this non-unicode string is
    implicitly converted to unicode (temporarily, and then converted back) -
    if this happens somewhere, that code would fail (as the test_string
    cannot be decoded to UTF8). (Note: we cannot test for all encodings, we test for
    unicode hoping that this would already catch possible issues.)
    """
    # Skip this test for AsyncSshTransport
    if 'AsyncSshTransport' in custom_transport.__str__():
        return

    test_string = b'some_test bytes with non-unicode -> \xfa'
    stdin = io.BytesIO(test_string)
    with custom_transport as transport:
        with pytest.raises(UnicodeDecodeError):
            transport.exec_command_wait('cat', stdin=stdin, encoding='utf-8')


def test_exec_with_wrong_stdin(custom_transport):
    """Test command execution with incorrect stdin string."""
    # Skip this test for AsyncSshTransport
    if 'AsyncSshTransport' in custom_transport.__str__():
        return

    # I pass a number
    with custom_transport as transport:
        with pytest.raises(ValueError):
            transport.exec_command_wait('cat', stdin=1)


def test_transfer_big_stdout(custom_transport, tmp_path_remote):
    """Test the transfer of a large amount of data on stdout."""
    # Create a "big" file of > 2MB (10MB here; in general, larger than the buffer size)
    min_file_size_bytes = 5 * 1024 * 1024
    # The file content will be a sequence of these lines, until the size
    # is > MIN_FILE_SIZE_BYTES
    file_line = 'This is a Unicødê štring\n'
    fname = 'test.dat'
    script_fname = 'script.py'

    # I create a large content of the file (as a string)
    file_line_binary = file_line.encode('utf8')
    line_repetitions = min_file_size_bytes // len(file_line_binary) + 1
    fcontent = (file_line_binary * line_repetitions).decode('utf8')

    with custom_transport as transport:
        # We cannot use tempfile.mkdtemp because we're on a remote folder
        directory_name = 'temp_dir_test_transfer_big_stdout'
        directory_path = tmp_path_remote / directory_name
        transport.mkdir(directory_path)

        with tempfile.NamedTemporaryFile(mode='wb') as tmpf:
            tmpf.write(fcontent.encode('utf8'))
            tmpf.flush()

            # I put a file with specific content there at the right file name
            transport.putfile(tmpf.name, directory_path / fname)

        python_code = r"""import sys

# disable buffering is only allowed in binary
#stdout = open(sys.stdout.fileno(), mode="wb", buffering=0)
#stderr = open(sys.stderr.fileno(), mode="wb", buffering=0)
# Use these lines instead if you want to use buffering
# I am leaving these in as most programs typically are buffered
stdout = open(sys.stdout.fileno(), mode="wb")
stderr = open(sys.stderr.fileno(), mode="wb")

line = '''{}'''.encode('utf-8')

for i in range({}):
    stdout.write(line)
    stderr.write(line)
""".format(file_line, line_repetitions)

        with tempfile.NamedTemporaryFile(mode='w') as tmpf:
            tmpf.write(python_code)
            tmpf.flush()

            # I put a file with specific content there at the right file name
            transport.putfile(tmpf.name, directory_path / script_fname)

        # I get its content via the stdout; emulate also network slowness (note I cat twice)
        retcode, stdout, stderr = transport.exec_command_wait(
            f'cat {fname} ; sleep 1 ; cat {fname}', workdir=directory_path
        )
        assert stderr == ''
        assert stdout == fcontent + fcontent
        assert retcode == 0

        # I get its content via the stderr; emulate also network slowness (note I cat twice)
        retcode, stdout, stderr = transport.exec_command_wait(
            f'cat {fname} >&2 ; sleep 1 ; cat {fname} >&2', workdir=directory_path
        )
        assert stderr == fcontent + fcontent
        assert stdout == ''
        assert retcode == 0

        # This time, I cat one one on each of the two streams intermittently, to check
        # that this does not hang.

        # Initially I was using a command like
        #        'i=0; while [ "$i" -lt {} ] ; do let i=i+1; echo -n "{}" ; echo -n "{}" >&2 ; done'.format(
        #        line_repetitions, file_line, file_line))
        # However this is pretty slow (and using 'cat' of a file containing only one line is even slower)

        retcode, stdout, stderr = transport.exec_command_wait(f'python3 {script_fname}', workdir=directory_path)

        assert stderr == fcontent
        assert stdout == fcontent
        assert retcode == 0


def test_asynchronous_execution(custom_transport, tmp_path):
    """Test that the execution of a long(ish) command via the direct scheduler does not block.

    This is a regression test for #3094, where running a long job on the direct scheduler
    (via SSH) would lock the interpreter until the job was done.
    """
    # Use a unique name, using a UUID, to avoid concurrent tests (or very rapid
    # tests that follow each other) to overwrite the same destination
    import os

    script_fname = f'sleep-submit-{uuid.uuid4().hex}-{custom_transport.__class__.__name__}.sh'

    scheduler = SchedulerFactory('core.direct')()
    scheduler.set_transport(custom_transport)
    with custom_transport as transport:
        try:
            with tempfile.NamedTemporaryFile() as tmpf:
                # Put a submission script that sleeps 10 seconds
                tmpf.write(b'#!/bin/bash\nsleep 10\n')
                tmpf.flush()

                transport.putfile(tmpf.name, tmp_path / script_fname)

            timestamp_before = time.time()
            job_id_string = scheduler.submit_job(tmp_path, script_fname)

            elapsed_time = time.time() - timestamp_before
            # We want to get back control. If it takes < 5 seconds, it means that it is not blocking
            # as the job is taking at least 10 seconds. I put 5 as the machine could be slow (including the
            # SSH connection etc.) and I don't want to have false failures.
            # Actually, if the time is short, it could mean also that the execution failed!
            # So I double check later that the execution was successful.
            assert (
                elapsed_time < 5
            ), 'Getting back control after remote execution took more than 5 seconds! Probably submission blocks'

            # Check that the job is still running
            # Wait 0.2 more seconds, so that I don't do a super-quick check that might return True
            # even if it's not sleeping
            time.sleep(0.2)
            # Check that the job is still running - IMPORTANT, I'm assuming that all transports actually act
            # on the *same* local machine, and that the job_id is actually the process PID.
            # This needs to be adapted if:
            #    - a new transport plugin is tested and this does not test the same machine
            #    - a new scheduler is used and does not use the process PID, or the job_id of the 'direct' scheduler
            #      is not anymore simply the job PID
            job_id = int(job_id_string)
            assert psutil.pid_exists(job_id), 'The job is not there after a bit more than 1 second! Probably it failed'
        finally:
            # Clean up by killing the remote job.
            # This assumes it's on the same machine; if we add tests on a different machine,
            # we need to call 'kill' via the transport instead.
            # In reality it's not critical to remove it since it will end after 10 seconds of
            # sleeping, but this might avoid warnings (e.g. ResourceWarning)
            try:
                os.kill(job_id, signal.SIGTERM)
            except ProcessLookupError:
                # If the process is already dead (or has never run), I just ignore the error
                pass


def test_rename(custom_transport, tmp_path_remote):
    """Test the rename function of the transport plugin."""
    with custom_transport as transport:
        old_file = tmp_path_remote / 'oldfile.txt'
        new_file = tmp_path_remote / 'newfile.txt'
        another_file = tmp_path_remote / 'anotherfile.txt'

        # Create a test file to rename
        old_file.touch()
        another_file.touch()
        assert old_file.exists()
        assert another_file.exists()

        # Perform rename operation
        transport.rename(old_file, new_file)

        # Verify rename was successful
        assert not old_file.exists()
        assert new_file.exists()

        # Perform rename operation if new file already exists
        with pytest.raises(OSError, match='already exist|destination exists'):
            transport.rename(new_file, another_file)


def test_compress_error_handling(custom_transport: Transport, tmp_path_remote: Path, monkeypatch: pytest.MonkeyPatch):
    """Test that the compress method raises an error according to instructions given in the abstract method."""
    with custom_transport as transport:
        # if the format is not supported
        with pytest.raises(ValueError, match='Unsupported compression format'):
            transport.compress('unsupported_format', tmp_path_remote, tmp_path_remote / 'archive.tar', '/')

        # if the remotesource does not exist
        with pytest.raises(OSError, match=f"{tmp_path_remote / 'non_existing'} does not exist"):
            transport.compress('tar', tmp_path_remote / 'non_existing', tmp_path_remote / 'archive.tar', '/')

        # if a matching pattern of the remote source is not found
        with pytest.raises(OSError, match='does not exist, or a matching file/folder not found'):
            transport.compress('tar', tmp_path_remote / 'non_existing*', tmp_path_remote / 'archive.tar', '/')

        # if the remotedestination already exists
        Path(tmp_path_remote / 'already_exist.tar').touch()
        with pytest.raises(
            OSError, match=f"The remote destination {tmp_path_remote / 'already_exist.tar'} already exists."
        ):
            transport.compress('tar', tmp_path_remote, tmp_path_remote / 'already_exist.tar', '/', overwrite=False)

        # if the remotedestination is a directory, raise a sensible error.
        with pytest.raises(OSError, match=' is a directory, should include a filename.'):
            transport.compress('tar', tmp_path_remote, tmp_path_remote, '/')

        # if the root_dir is not a directory
        with pytest.raises(
            OSError,
            match=f"The relative root {tmp_path_remote / 'non_existing_folder'} does not exist, or is not a directory.",
        ):
            transport.compress(
                'tar', tmp_path_remote, tmp_path_remote / 'archive.tar', tmp_path_remote / 'non_existing_folder'
            )

        # if creating the tar file fails should raise an OSError
        # I do this by monkey patching transport.mock_exec_command_wait and transport.exec_command_wait_async
        def mock_exec_command_wait(*args, **kwargs):
            return 1, b'', b''

        async def mock_exec_command_wait_async(*args, **kwargs):
            return 1, b'', b''

        monkeypatch.setattr(transport, 'exec_command_wait', mock_exec_command_wait)
        monkeypatch.setattr(transport, 'exec_command_wait_async', mock_exec_command_wait_async)

        with pytest.raises(OSError, match='Error while creating the tar archive.'):
            Path(tmp_path_remote / 'file').touch()
            transport.compress('tar', tmp_path_remote, tmp_path_remote / 'archive.tar', '/')


@pytest.mark.parametrize('format', ['tar', 'tar.gz', 'tar.bz2', 'tar.xz'])
@pytest.mark.parametrize('dereference', [True, False])
@pytest.mark.parametrize('file_hierarchy', [{'file.txt': 'file', 'folder': {'file_1': '1'}}])
def test_compress_basic(
    custom_transport: Transport,
    format: str,
    dereference: bool,
    create_file_hierarchy: callable,
    file_hierarchy: dict,
    tmp_path_remote: Path,
    tmp_path_local: Path,
) -> None:
    """Test the basic functionality of the compress method.
    This test will create a file hierarchy on the remote machine, compress and download it,
    and then extract it on the local machine. The content of the files will be checked
    to ensure that the compression and extraction was successful."""
    remote = tmp_path_remote / 'root'
    remote.mkdir()
    create_file_hierarchy(file_hierarchy, remote)
    Path(remote / 'symlink').symlink_to(remote / 'file.txt')

    archive_name = 'archive.' + format

    # 1) basic functionality
    with custom_transport as transport:
        transport.compress(format, remote, tmp_path_remote / archive_name, root_dir=remote, dereference=dereference)

        transport.get(tmp_path_remote / archive_name, tmp_path_local / archive_name)

        shutil.unpack_archive(tmp_path_local / archive_name, tmp_path_local / 'extracted', filter='tar')

        extracted = [
            str(path.relative_to(tmp_path_local / 'extracted')) for path in (tmp_path_local / 'extracted').rglob('*')
        ]

        assert sorted(extracted) == sorted(['file.txt', 'folder', 'folder/file_1', 'symlink'])

        # test that the content of the files is the same
        assert Path(tmp_path_local / 'extracted' / 'file.txt').read_text() == 'file'
        assert Path(tmp_path_local / 'extracted' / 'folder' / 'file_1').read_text() == '1'

        # test the symlink
        if dereference:
            assert not os.path.islink(tmp_path_local / 'extracted' / 'symlink')
            assert Path(tmp_path_local / 'extracted' / 'symlink').read_text() == 'file'
        else:
            assert os.path.islink(tmp_path_local / 'extracted' / 'symlink')
            assert os.readlink(tmp_path_local / 'extracted' / 'symlink') == str(remote / 'file.txt')


@pytest.mark.parametrize('format', ['tar', 'tar.gz', 'tar.bz2', 'tar.xz'])
@pytest.mark.parametrize(
    'file_hierarchy',
    [
        {
            'file.txt': 'file',
            'folder_1': {'file_1': '1', 'file_11': '11', 'file_2': '2'},
            'folder_2': {'file_1': '1', 'file_11': '11', 'file_2': '2'},
        }
    ],
)
def test_compress_glob(
    custom_transport: Transport,
    create_file_hierarchy: callable,
    file_hierarchy: dict,
    format: str,
    tmp_path_remote: Path,
    tmp_path_local: Path,
) -> None:
    """Test the glob functionality of the compress method.

    It is similar to :func:`test_compress_basic` but specifies a glob pattern for the remote source allowing us to test
    the resolving mechanism separately."""

    remote = tmp_path_remote / 'root'
    remote.mkdir()
    create_file_hierarchy(file_hierarchy, remote)

    archive_name = 'archive_glob.' + format

    with custom_transport as transport:
        transport.compress(
            format,
            remote / 'folder*' / 'file_1*',
            tmp_path_remote / archive_name,
            root_dir=remote,
        )

        transport.get(tmp_path_remote / archive_name, tmp_path_local / archive_name)

        shutil.unpack_archive(tmp_path_local / archive_name, tmp_path_local / 'extracted_glob', filter='data')

        extracted = [
            str(path.relative_to(tmp_path_local / 'extracted_glob'))
            for path in (tmp_path_local / 'extracted_glob').rglob('*')
        ]
        assert sorted(extracted) == sorted(
            ['folder_1', 'folder_2', 'folder_1/file_1', 'folder_1/file_11', 'folder_2/file_1', 'folder_2/file_11']
        )


@pytest.mark.parametrize('format', ['tar', 'tar.gz', 'tar.bz2', 'tar.xz'])
@pytest.mark.parametrize('file_hierarchy', [{'file.txt': 'file', 'folder_1': {'file_1': '1'}}])
def test_extract(
    custom_transport: Transport,
    create_file_hierarchy: callable,
    file_hierarchy: dict,
    format: str,
    tmp_path_remote: Path,
    tmp_path_local: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    local = tmp_path_local / 'root'
    local.mkdir()
    create_file_hierarchy(file_hierarchy, local)

    shutil_mapping_format = {'tar': 'tar', 'tar.gz': 'gztar', 'tar.bz2': 'bztar', 'tar.xz': 'xztar'}

    archive_path = shutil.make_archive(str(tmp_path_local / 'archive'), shutil_mapping_format[format], root_dir=local)

    archive_name = archive_path.split('/')[-1]
    with custom_transport as transport:
        transport.put(archive_path, tmp_path_remote / archive_name)

        transport.extract(tmp_path_remote / archive_name, tmp_path_remote / 'extracted')

        transport.get(tmp_path_remote / 'extracted', tmp_path_local / 'extracted')

    extracted = [
        str(path.relative_to(tmp_path_local / 'extracted')) for path in (tmp_path_local / 'extracted').rglob('*')
    ]

    assert sorted(extracted) == sorted(['file.txt', 'folder_1', 'folder_1/file_1'])

    assert Path(tmp_path_local / 'extracted' / 'file.txt').read_text() == 'file'
    assert Path(tmp_path_local / 'extracted' / 'folder_1' / 'file_1').read_text() == '1'

    # should raise if remotesource does not exist
    with pytest.raises(OSError, match='does not exist'):
        with custom_transport as transport:
            transport.extract(tmp_path_remote / 'non_existing', tmp_path_remote / 'extracted')

    # should raise OSError in case extraction fails
    # I do this by monkey patching transport.exec_command_wait and transport.exec_command_wait_async
    def mock_exec_command_wait(*args, **kwargs):
        return 1, b'', b''

    async def mock_exec_command_wait_async(*args, **kwargs):
        return 1, b'', b''

    monkeypatch.setattr(transport, 'exec_command_wait', mock_exec_command_wait)
    monkeypatch.setattr(transport, 'exec_command_wait_async', mock_exec_command_wait_async)

    with pytest.raises(OSError, match='Error while extracting the tar archive.'):
        with custom_transport as transport:
            transport.extract(tmp_path_remote / archive_name, tmp_path_remote / 'extracted_1')


def test_glob(custom_transport, tmp_path_local):
    """Test the glob method of the transport plugin.
    This tests mainly the implementation, doesn't need to run on remote
    """

    for subpath in [
        'i.txt',
        'j.txt',
        'folder1/a/b.txt',
        'folder1/a/c.txt',
        'folder1/a/c.in',
        'folder1/c.txt',
        'folder1/e/f/g.txt',
        'folder2/x',
        'folder2/y/z',
    ]:
        tmp_path_local.joinpath(subpath).parent.mkdir(parents=True, exist_ok=True)
        tmp_path_local.joinpath(subpath).write_text('touch')

    with custom_transport as transport:
        # do not raise an error if the path does not exist
        g_list = transport.glob(str(tmp_path_local) + '/non_existing/*.txt')
        assert g_list == []

        g_list = transport.glob(str(tmp_path_local) + '/*.txt')
        paths = [str(tmp_path_local.joinpath(item)) for item in ['i.txt', 'j.txt']]
        assert sorted(paths) == sorted(g_list)

        g_list = transport.glob(str(tmp_path_local) + '/folder1/*.txt')
        paths = [str(tmp_path_local.joinpath(item)) for item in ['folder1/c.txt']]
        assert sorted(paths) == sorted(g_list)

        g_list = transport.glob(str(tmp_path_local) + '/folder1/*/*.txt')
        paths = [str(tmp_path_local.joinpath(item)) for item in ['folder1/a/b.txt', 'folder1/a/c.txt']]
        assert sorted(paths) == sorted(g_list)

        g_list = transport.glob(str(tmp_path_local) + '/folder*/*')
        paths = [
            str(tmp_path_local.joinpath(item))
            for item in ['folder1/a', 'folder1/c.txt', 'folder2/x', 'folder2/y', 'folder1/e']
        ]
        assert sorted(paths) == sorted(g_list)

        g_list = transport.glob(str(tmp_path_local) + '/folder1/*/*/*.txt')
        paths = [str(tmp_path_local.joinpath(item)) for item in ['folder1/e/f/g.txt']]
        assert sorted(paths) == sorted(g_list)
