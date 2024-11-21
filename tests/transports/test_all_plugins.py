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
import pathlib
import random
import shutil
import signal
import string
import tempfile
import time
import uuid

import psutil
import pytest
from aiida.plugins import SchedulerFactory, TransportFactory, entry_point
from aiida.transports import Transport

# TODO : test for copy with pattern
# TODO : test for copy with/without patterns, overwriting folder
# TODO : test for exotic cases of copy with source = destination
# TODO : silly cases of copy/put/get from self to self


@pytest.fixture(scope='function')
def remote_tmp_path(tmp_path_factory):
    """Mock the remote tmp path using tmp_path_factory to create folder start with 'remote'"""
    return tmp_path_factory.mktemp('remote')


@pytest.fixture(scope='function', params=entry_point.get_entry_point_names('aiida.transports'))
def custom_transport(request, tmp_path_factory, monkeypatch) -> Transport:
    """Fixture that parametrizes over all the registered implementations of the ``CommonRelaxWorkChain``."""
    plugin = TransportFactory(request.param)

    if request.param == 'core.ssh':
        kwargs = {'machine': 'localhost', 'timeout': 30, 'load_system_host_keys': True, 'key_policy': 'AutoAddPolicy'}
    elif request.param == 'core.ssh_auto':
        kwargs = {'machine': 'localhost'}
        filepath_config = tmp_path_factory.mktemp('transport') / 'config'
        monkeypatch.setattr(plugin, 'FILEPATH_CONFIG', filepath_config)
        if not filepath_config.exists():
            filepath_config.write_text('Host localhost')
    else:
        kwargs = {}

    return plugin(**kwargs)


def test_is_open(custom_transport):
    """Test that the is_open property works."""
    assert not custom_transport.is_open

    with custom_transport:
        assert custom_transport.is_open

    assert not custom_transport.is_open


def test_deprecate_chdir_and_getcwd(custom_transport, remote_tmp_path):
    """Test to be deprecated ``chdir``/``getcwd`` methods still work."""
    with custom_transport as transport:
        location = str(remote_tmp_path)
        transport.chdir(location)

        assert location == transport.getcwd()


def test_chdir_to_empty_string(custom_transport, remote_tmp_path):
    """I check that if I pass an empty string to chdir, the cwd does
    not change (this is a paramiko default behavior), but getcwd()
    is still correctly defined.
    """
    with custom_transport as transport:
        new_dir = str(remote_tmp_path)
        transport.chdir(new_dir)
        transport.chdir('')
        assert new_dir == transport.getcwd()


def test_makedirs(custom_transport, remote_tmp_path):
    """Verify the functioning of makedirs command"""
    with custom_transport as transport:
        # define folder structure
        dir_tree = str(remote_tmp_path / '1' / '2')
        # I create the tree
        transport.makedirs(dir_tree)
        # verify the existence
        assert transport.isdir(str(remote_tmp_path / '1'))
        assert dir_tree

        # try to recreate the same folder
        with pytest.raises(OSError):
            transport.makedirs(dir_tree)

        # recreate but with ignore flag
        transport.makedirs(dir_tree, True)

        transport.rmdir(dir_tree)
        transport.rmdir(str(remote_tmp_path / '1'))


def test_rmtree(custom_transport, remote_tmp_path):
    """Verify the functioning of rmtree command"""
    with custom_transport as transport:
        # define folder structure
        dir_tree = str(remote_tmp_path / '1' / '2')
        # I create the tree
        transport.makedirs(dir_tree)
        # remove it
        transport.rmtree(str(remote_tmp_path / '1'))
        # verify the removal
        assert not transport.isdir(str(remote_tmp_path / '1'))

        # also tests that it works with a single file
        # create file
        local_file_name = 'file.txt'
        text = 'Viva Verdi\n'
        single_file_path = str(remote_tmp_path / local_file_name)
        with open(single_file_path, 'w', encoding='utf8') as fhandle:
            fhandle.write(text)
        # remove it
        transport.rmtree(single_file_path)
        # verify the removal
        assert not transport.isfile(single_file_path)


def test_listdir(custom_transport, remote_tmp_path):
    """Create directories, verify listdir, delete a folder with subfolders"""
    with custom_transport as transport:
        list_of_dir = ['1', '-f a&', 'as', 'a2', 'a4f']
        list_of_files = ['a', 'b']
        for this_dir in list_of_dir:
            transport.mkdir(str(remote_tmp_path / this_dir))

        for fname in list_of_files:
            with tempfile.NamedTemporaryFile() as tmpf:
                # Just put an empty file there at the right file name
                transport.putfile(tmpf.name, str(remote_tmp_path / fname))

        list_found = transport.listdir(str(remote_tmp_path))

        assert sorted(list_found) == sorted(list_of_dir + list_of_files)

        assert sorted(transport.listdir(str(remote_tmp_path), 'a*')), sorted(['as', 'a2', 'a4f'])
        assert sorted(transport.listdir(str(remote_tmp_path), 'a?')), sorted(['as', 'a2'])
        assert sorted(transport.listdir(str(remote_tmp_path), 'a[2-4]*')), sorted(['a2', 'a4f'])


def test_listdir_withattributes(custom_transport, remote_tmp_path):
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
        list_of_files = ['a', 'b']
        for this_dir in list_of_dir:
            transport.mkdir(str(remote_tmp_path / this_dir))

        for fname in list_of_files:
            with tempfile.NamedTemporaryFile() as tmpf:
                # Just put an empty file there at the right file name
                transport.putfile(tmpf.name, str(remote_tmp_path / fname))

        comparison_list = {k: True for k in list_of_dir}
        for k in list_of_files:
            comparison_list[k] = False

        assert simplify_attributes(transport.listdir_withattributes(str(remote_tmp_path))), comparison_list
        assert simplify_attributes(transport.listdir_withattributes(str(remote_tmp_path), 'a*')), {
            'as': True,
            'a2': True,
            'a4f': True,
            'a': False,
        }
        assert simplify_attributes(transport.listdir_withattributes(str(remote_tmp_path), 'a?')), {
            'as': True,
            'a2': True,
        }
        assert simplify_attributes(transport.listdir_withattributes(str(remote_tmp_path), 'a[2-4]*')), {
            'a2': True,
            'a4f': True,
        }


def test_dir_creation_deletion(custom_transport, remote_tmp_path):
    """Test creating and deleting directories."""
    with custom_transport as transport:
        new_dir = str(remote_tmp_path / 'new')
        transport.mkdir(new_dir)

        with pytest.raises(OSError):
            # I create twice the same directory
            transport.mkdir(new_dir)

        transport.isdir(new_dir)
        assert not transport.isfile(new_dir)


def test_dir_copy(custom_transport, remote_tmp_path):
    """Verify if in the copy of a directory also the protection bits
    are carried over
    """
    with custom_transport as transport:
        # Create a src dir
        src_dir = str(remote_tmp_path / 'copy_src')
        transport.mkdir(src_dir)

        dst_dir = str(remote_tmp_path / 'copy_dst')
        transport.copy(src_dir, dst_dir)

        with pytest.raises(ValueError):
            transport.copy(src_dir, '')

        with pytest.raises(ValueError):
            transport.copy('', dst_dir)


def test_dir_permissions_creation_modification(custom_transport, remote_tmp_path):
    """Verify if chmod raises OSError when trying to change bits on a
    non-existing folder
    """
    with custom_transport as transport:
        directory = str(remote_tmp_path / 'test')

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
        transport.chdir(directory)

        # change permissions of an empty string, non existing folder.
        fake_dir = ''
        with pytest.raises(OSError):
            transport.chmod(fake_dir, 0o777)

        fake_dir = 'pippo'
        with pytest.raises(OSError):
            # chmod to a non existing folder
            transport.chmod(fake_dir, 0o777)

        transport.chdir('..')
        transport.rmdir(directory)


def test_dir_reading_permissions(custom_transport, remote_tmp_path):
    """Try to enter a directory with no read permissions.
    Verify that the cwd has not changed after failed try.
    """
    with custom_transport as transport:
        directory = str(remote_tmp_path / 'test')

        # create directory with non default permissions
        transport.mkdir(directory)

        # change permissions to low ones
        transport.chmod(directory, 0)

        # test if the security bits have changed
        assert transport.get_mode(directory) == 0

        old_cwd = transport.getcwd()

        with pytest.raises(OSError):
            transport.chdir(directory)

        new_cwd = transport.getcwd()

        assert old_cwd == new_cwd


def test_isfile_isdir_to_empty_string(custom_transport):
    """I check that isdir or isfile return False when executed on an
    empty string
    """
    with custom_transport as transport:
        assert not transport.isdir('')
        assert not transport.isfile('')


def test_isfile_isdir_to_non_existing_string(custom_transport, remote_tmp_path):
    """I check that isdir or isfile return False when executed on an
    empty string
    """
    with custom_transport as transport:
        fake_folder = str(remote_tmp_path / 'pippo')
        assert not transport.isfile(fake_folder)
        assert not transport.isdir(fake_folder)
        with pytest.raises(OSError):
            transport.chdir(fake_folder)


def test_put_and_get(custom_transport, tmp_path_factory):
    """Test putting and getting files."""
    local_dir = tmp_path_factory.mktemp('local')
    remote_dir = tmp_path_factory.mktemp('remote')

    directory = 'tmp_try'

    with custom_transport as transport:
        (local_dir / directory).mkdir()
        transport.mkdir(str(remote_dir / directory))

        local_file_name = 'file.txt'
        retrieved_file_name = 'file_retrieved.txt'

        remote_file_name = 'file_remote.txt'

        # here use full path in src and dst
        local_file_abs_path = str(local_dir / directory / local_file_name)
        retrieved_file_abs_path = str(local_dir / directory / retrieved_file_name)
        remote_file_abs_path = str(remote_dir / directory / remote_file_name)

        text = 'Viva Verdi\n'
        with open(local_file_abs_path, 'w', encoding='utf8') as fhandle:
            fhandle.write(text)

        transport.put(local_file_abs_path, remote_file_abs_path)
        transport.get(remote_file_abs_path, retrieved_file_abs_path)

        list_of_files = transport.listdir(str(remote_dir / directory))
        # it is False because local_file_name has the full path,
        # while list_of_files has not
        assert local_file_name not in list_of_files
        assert remote_file_name in list_of_files
        assert retrieved_file_name not in list_of_files


def test_putfile_and_getfile(custom_transport, tmp_path_factory):
    """Test putting and getting files."""
    local_dir = tmp_path_factory.mktemp('local')
    remote_dir = tmp_path_factory.mktemp('remote')

    directory = 'tmp_try'

    with custom_transport as transport:
        (local_dir / directory).mkdir()
        transport.mkdir(str(remote_dir / directory))

        local_file_name = 'file.txt'
        retrieved_file_name = 'file_retrieved.txt'

        remote_file_name = 'file_remote.txt'

        # here use full path in src and dst
        local_file_abs_path = str(local_dir / directory / local_file_name)
        retrieved_file_abs_path = str(local_dir / directory / retrieved_file_name)
        remote_file_abs_path = str(remote_dir / directory / remote_file_name)

        text = 'Viva Verdi\n'
        with open(local_file_abs_path, 'w', encoding='utf8') as fhandle:
            fhandle.write(text)

        transport.putfile(local_file_abs_path, remote_file_abs_path)
        transport.getfile(remote_file_abs_path, retrieved_file_abs_path)

        list_of_files = transport.listdir(str(remote_dir / directory))
        # it is False because local_file_name has the full path,
        # while list_of_files has not
        assert local_file_name not in list_of_files
        assert remote_file_name in list_of_files
        assert retrieved_file_name not in list_of_files


def test_put_get_abs_path_file(custom_transport, tmp_path_factory):
    """Test of exception for non existing files and abs path"""
    local_dir = tmp_path_factory.mktemp('local')
    remote_dir = tmp_path_factory.mktemp('remote')

    directory = 'tmp_try'

    with custom_transport as transport:
        (local_dir / directory).mkdir()
        transport.mkdir(str(remote_dir / directory))

        local_file_name = 'file.txt'
        retrieved_file_name = 'file_retrieved.txt'

        remote_file_name = 'file_remote.txt'

        local_file_rel_path = local_file_name
        local_file_abs_path = str(local_dir / directory / local_file_name)

        remote_file_rel_path = remote_file_name

        local_file_abs_path = str(local_dir / directory / local_file_name)
        retrieved_file_abs_path = str(local_dir / directory / retrieved_file_name)
        remote_file_abs_path = str(remote_dir / directory / remote_file_name)

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


def test_put_get_empty_string_file(custom_transport, tmp_path_factory):
    """Test of exception put/get of empty strings"""
    local_dir = tmp_path_factory.mktemp('local')
    remote_dir = tmp_path_factory.mktemp('remote')

    directory = 'tmp_try'

    with custom_transport as transport:
        (local_dir / directory).mkdir()
        transport.mkdir(str(remote_dir / directory))

        local_file_name = 'file.txt'
        retrieved_file_name = 'file_retrieved.txt'

        remote_file_name = 'file_remote.txt'

        # here use full path in src and dst
        local_file_abs_path = str(local_dir / directory / local_file_name)
        retrieved_file_abs_path = str(local_dir / directory / retrieved_file_name)
        remote_file_abs_path = str(remote_dir / directory / remote_file_name)

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
        # overwrite retrieved_file_name
        transport.getfile(remote_file_abs_path, retrieved_file_abs_path)


def test_put_and_get_tree(custom_transport):
    """Test putting and getting files."""
    local_dir = os.path.join('/', 'tmp')
    remote_dir = local_dir
    directory = 'tmp_try'

    with custom_transport as transport:
        transport.chdir(remote_dir)

        while os.path.exists(os.path.join(local_dir, directory)):
            # I append a random letter/number until it is unique
            directory += random.choice(string.ascii_uppercase + string.digits)

        local_subfolder = os.path.join(local_dir, directory, 'tmp1')
        remote_subfolder = 'tmp2'
        retrieved_subfolder = os.path.join(local_dir, directory, 'tmp3')

        os.mkdir(os.path.join(local_dir, directory))
        os.mkdir(os.path.join(local_dir, directory, local_subfolder))

        transport.chdir(directory)

        local_file_name = os.path.join(local_subfolder, 'file.txt')

        text = 'Viva Verdi\n'
        with open(local_file_name, 'w', encoding='utf8') as fhandle:
            fhandle.write(text)

        # here use full path in src and dst
        for i in range(2):
            if i == 0:
                transport.put(local_subfolder, remote_subfolder)
                transport.get(remote_subfolder, retrieved_subfolder)
            else:
                transport.puttree(local_subfolder, remote_subfolder)
                transport.gettree(remote_subfolder, retrieved_subfolder)

            # Here I am mixing the local with the remote fold
            list_of_dirs = transport.listdir('.')
            # # it is False because local_file_name has the full path,
            # # while list_of_files has not
            assert local_subfolder not in list_of_dirs
            assert remote_subfolder in list_of_dirs
            assert retrieved_subfolder not in list_of_dirs
            assert 'tmp1' in list_of_dirs
            assert 'tmp3' in list_of_dirs

            list_pushed_file = transport.listdir('tmp2')
            list_retrieved_file = transport.listdir('tmp3')
            assert 'file.txt' in list_pushed_file
            assert 'file.txt' in list_retrieved_file

        shutil.rmtree(local_subfolder)
        shutil.rmtree(retrieved_subfolder)
        transport.rmtree(remote_subfolder)

        transport.chdir('..')
        transport.rmdir(directory)


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


def test_copy(custom_transport):
    """Test copying."""
    local_dir = os.path.join('/', 'tmp')
    remote_dir = local_dir
    directory = 'tmp_try'

    with custom_transport as transport:
        transport.chdir(remote_dir)

        while os.path.exists(os.path.join(local_dir, directory)):
            # I append a random letter/number until it is unique
            directory += random.choice(string.ascii_uppercase + string.digits)

        transport.mkdir(directory)
        transport.chdir(directory)

        local_base_dir = os.path.join(local_dir, directory, 'local')
        os.mkdir(local_base_dir)

        # first test put: I create three files in local
        file_1 = os.path.join(local_base_dir, 'a.txt')
        file_2 = os.path.join(local_base_dir, 'b.tmp')
        file_3 = os.path.join(local_base_dir, 'c.txt')
        text = 'Viva Verdi\n'
        for filename in [file_1, file_2, file_3]:
            with open(filename, 'w', encoding='utf8') as fhandle:
                fhandle.write(text)

        # first test the copy. Copy of two files matching patterns, into a folder
        transport.copy(os.path.join('local', '*.txt'), '.')
        assert set(['a.txt', 'c.txt', 'local']) == set(transport.listdir('.'))
        transport.remove('a.txt')
        transport.remove('c.txt')
        # second test copy. Copy of two folders
        transport.copy('local', 'prova')
        assert set(['prova', 'local']) == set(transport.listdir('.'))
        assert set(['a.txt', 'b.tmp', 'c.txt']) == set(transport.listdir('prova'))
        transport.rmtree('prova')
        # third test copy. Can copy one file into a new file
        transport.copy(os.path.join('local', '*.tmp'), 'prova')
        assert set(['prova', 'local']) == set(transport.listdir('.'))
        transport.remove('prova')
        # fourth test copy: can't copy more than one file on the same file,
        # i.e., the destination should be a folder
        with pytest.raises(OSError):
            transport.copy(os.path.join('local', '*.txt'), 'prova')
        # fifth test, copying one file into a folder
        transport.mkdir('prova')
        transport.copy(os.path.join('local', 'a.txt'), 'prova')
        assert set(transport.listdir('prova')) == set(['a.txt'])
        transport.rmtree('prova')
        # sixth test, copying one file into a file
        transport.copy(os.path.join('local', 'a.txt'), 'prova')
        assert transport.isfile('prova')
        transport.remove('prova')
        # copy of folder into an existing folder
        # NOTE: the command cp has a different behavior on Mac vs Ubuntu
        # tests performed locally on a Mac may result in a failure.
        transport.mkdir('prova')
        transport.copy('local', 'prova')
        assert set(['local']) == set(transport.listdir('prova'))
        assert set(['a.txt', 'b.tmp', 'c.txt']) == set(transport.listdir(os.path.join('prova', 'local')))
        transport.rmtree('prova')
        # exit
        transport.chdir('..')
        transport.rmtree(directory)


def test_put(custom_transport):
    """Test putting files."""
    # exactly the same tests of copy, just with the put function
    # and therefore the local path must be absolute
    local_dir = os.path.join('/', 'tmp')
    remote_dir = local_dir
    directory = 'tmp_try'

    with custom_transport as transport:
        transport.chdir(remote_dir)

        while os.path.exists(os.path.join(local_dir, directory)):
            # I append a random letter/number until it is unique
            directory += random.choice(string.ascii_uppercase + string.digits)

        transport.mkdir(directory)
        transport.chdir(directory)

        local_base_dir = os.path.join(local_dir, directory, 'local')
        os.mkdir(local_base_dir)

        # first test put: I create three files in local
        file_1 = os.path.join(local_base_dir, 'a.txt')
        file_2 = os.path.join(local_base_dir, 'b.tmp')
        file_3 = os.path.join(local_base_dir, 'c.txt')
        text = 'Viva Verdi\n'
        for filename in [file_1, file_2, file_3]:
            with open(filename, 'w', encoding='utf8') as fhandle:
                fhandle.write(text)

        # first test putransport. Copy of two files matching patterns, into a folder
        transport.put(os.path.join(local_base_dir, '*.txt'), '.')
        assert set(['a.txt', 'c.txt', 'local']) == set(transport.listdir('.'))
        transport.remove('a.txt')
        transport.remove('c.txt')
        # second. Copy of folder into a non existing folder
        transport.put(local_base_dir, 'prova')
        assert set(['prova', 'local']) == set(transport.listdir('.'))
        assert set(['a.txt', 'b.tmp', 'c.txt']) == set(transport.listdir('prova'))
        transport.rmtree('prova')
        # third. copy of folder into an existing folder
        transport.mkdir('prova')
        transport.put(local_base_dir, 'prova')
        assert set(['prova', 'local']) == set(transport.listdir('.'))
        assert set(['local']) == set(transport.listdir('prova'))
        assert set(['a.txt', 'b.tmp', 'c.txt']) == set(transport.listdir(os.path.join('prova', 'local')))
        transport.rmtree('prova')
        # third test copy. Can copy one file into a new file
        transport.put(os.path.join(local_base_dir, '*.tmp'), 'prova')
        assert set(['prova', 'local']) == set(transport.listdir('.'))
        transport.remove('prova')
        # fourth test copy: can't copy more than one file on the same file,
        # i.e., the destination should be a folder
        with pytest.raises(OSError):
            transport.put(os.path.join(local_base_dir, '*.txt'), 'prova')
        # copy of folder into file
        with open(os.path.join(local_dir, directory, 'existing.txt'), 'w', encoding='utf8') as fhandle:
            fhandle.write(text)
        with pytest.raises(OSError):
            transport.put(os.path.join(local_base_dir), 'existing.txt')
        transport.remove('existing.txt')
        # fifth test, copying one file into a folder
        transport.mkdir('prova')
        transport.put(os.path.join(local_base_dir, 'a.txt'), 'prova')
        assert set(transport.listdir('prova')) == set(['a.txt'])
        transport.rmtree('prova')
        # sixth test, copying one file into a file
        transport.put(os.path.join(local_base_dir, 'a.txt'), 'prova')
        assert transport.isfile('prova')
        transport.remove('prova')

        # exit
        transport.chdir('..')
        transport.rmtree(directory)


def test_get(custom_transport):
    """Test getting files."""
    # exactly the same tests of copy, just with the put function
    # and therefore the local path must be absolute
    local_dir = os.path.join('/', 'tmp')
    remote_dir = local_dir
    directory = 'tmp_try'

    with custom_transport as transport:
        transport.chdir(remote_dir)

        while os.path.exists(os.path.join(local_dir, directory)):
            # I append a random letter/number until it is unique
            directory += random.choice(string.ascii_uppercase + string.digits)

        transport.mkdir(directory)
        transport.chdir(directory)

        local_base_dir = os.path.join(local_dir, directory, 'local')
        local_destination = os.path.join(local_dir, directory)
        os.mkdir(local_base_dir)

        # first test put: I create three files in local
        file_1 = os.path.join(local_base_dir, 'a.txt')
        file_2 = os.path.join(local_base_dir, 'b.tmp')
        file_3 = os.path.join(local_base_dir, 'c.txt')
        text = 'Viva Verdi\n'
        for filename in [file_1, file_2, file_3]:
            with open(filename, 'w', encoding='utf8') as fhandle:
                fhandle.write(text)

        # first test put. Copy of two files matching patterns, into a folder
        transport.get(os.path.join('local', '*.txt'), local_destination)
        assert set(['a.txt', 'c.txt', 'local']) == set(os.listdir(local_destination))
        os.remove(os.path.join(local_destination, 'a.txt'))
        os.remove(os.path.join(local_destination, 'c.txt'))
        # second. Copy of folder into a non existing folder
        transport.get('local', os.path.join(local_destination, 'prova'))
        assert set(['prova', 'local']) == set(os.listdir(local_destination))
        assert set(['a.txt', 'b.tmp', 'c.txt']) == set(os.listdir(os.path.join(local_destination, 'prova')))
        shutil.rmtree(os.path.join(local_destination, 'prova'))
        # third. copy of folder into an existing folder
        os.mkdir(os.path.join(local_destination, 'prova'))
        transport.get('local', os.path.join(local_destination, 'prova'))
        assert set(['prova', 'local']) == set(os.listdir(local_destination))
        assert set(['local']) == set(os.listdir(os.path.join(local_destination, 'prova')))
        assert set(['a.txt', 'b.tmp', 'c.txt']) == set(os.listdir(os.path.join(local_destination, 'prova', 'local')))
        shutil.rmtree(os.path.join(local_destination, 'prova'))
        # third test copy. Can copy one file into a new file
        transport.get(os.path.join('local', '*.tmp'), os.path.join(local_destination, 'prova'))
        assert set(['prova', 'local']) == set(os.listdir(local_destination))
        os.remove(os.path.join(local_destination, 'prova'))
        # fourth test copy: can't copy more than one file on the same file,
        # i.e., the destination should be a folder
        with pytest.raises(OSError):
            transport.get(os.path.join('local', '*.txt'), os.path.join(local_destination, 'prova'))
        # copy of folder into file
        with open(os.path.join(local_destination, 'existing.txt'), 'w', encoding='utf8') as fhandle:
            fhandle.write(text)
        with pytest.raises(OSError):
            transport.get('local', os.path.join(local_destination, 'existing.txt'))
        os.remove(os.path.join(local_destination, 'existing.txt'))
        # fifth test, copying one file into a folder
        os.mkdir(os.path.join(local_destination, 'prova'))
        transport.get(os.path.join('local', 'a.txt'), os.path.join(local_destination, 'prova'))
        assert set(os.listdir(os.path.join(local_destination, 'prova'))) == set(['a.txt'])
        shutil.rmtree(os.path.join(local_destination, 'prova'))
        # sixth test, copying one file into a file
        transport.get(os.path.join('local', 'a.txt'), os.path.join(local_destination, 'prova'))
        assert os.path.isfile(os.path.join(local_destination, 'prova'))
        os.remove(os.path.join(local_destination, 'prova'))

        # exit
        transport.chdir('..')
        transport.rmtree(directory)


def test_put_get_abs_path_tree(custom_transport):
    """Test of exception for non existing files and abs path"""
    local_dir = os.path.join('/', 'tmp')
    remote_dir = local_dir
    directory = 'tmp_try'

    with custom_transport as transport:
        transport.chdir(remote_dir)

        while os.path.exists(os.path.join(local_dir, directory)):
            # I append a random letter/number until it is unique
            directory += random.choice(string.ascii_uppercase + string.digits)

        local_subfolder = os.path.join(local_dir, directory, 'tmp1')
        remote_subfolder = 'tmp2'
        retrieved_subfolder = os.path.join(local_dir, directory, 'tmp3')

        os.mkdir(os.path.join(local_dir, directory))
        os.mkdir(os.path.join(local_dir, directory, local_subfolder))

        transport.chdir(directory)
        local_file_name = os.path.join(local_subfolder, 'file.txt')
        pathlib.Path(local_file_name).touch()

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

        os.remove(os.path.join(local_subfolder, 'file.txt'))
        os.rmdir(local_subfolder)
        transport.rmtree(remote_subfolder)

        transport.chdir('..')
        transport.rmdir(directory)


def test_put_get_empty_string_tree(custom_transport):
    """Test of exception put/get of empty strings"""
    # TODO : verify the correctness of \n at the end of a file
    local_dir = os.path.join('/', 'tmp')
    remote_dir = local_dir
    directory = 'tmp_try'

    with custom_transport as transport:
        transport.chdir(remote_dir)

        while os.path.exists(os.path.join(local_dir, directory)):
            # I append a random letter/number until it is unique
            directory += random.choice(string.ascii_uppercase + string.digits)

        local_subfolder = os.path.join(local_dir, directory, 'tmp1')
        remote_subfolder = 'tmp2'
        retrieved_subfolder = os.path.join(local_dir, directory, 'tmp3')

        os.mkdir(os.path.join(local_dir, directory))
        os.mkdir(os.path.join(local_dir, directory, local_subfolder))

        transport.chdir(directory)
        local_file_name = os.path.join(local_subfolder, 'file.txt')

        text = 'Viva Verdi\n'
        with open(local_file_name, 'w', encoding='utf8') as fhandle:
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
        transport.gettree(remote_subfolder, retrieved_subfolder)

        os.remove(os.path.join(local_subfolder, 'file.txt'))
        os.rmdir(local_subfolder)
        transport.remove(os.path.join(remote_subfolder, 'file.txt'))
        transport.rmdir(remote_subfolder)
        # If it couldn't end the copy, it leaves what he did on local file
        # here I am mixing local with remote
        assert 'file.txt' in transport.listdir('tmp3')
        os.remove(os.path.join(retrieved_subfolder, 'file.txt'))
        os.rmdir(retrieved_subfolder)

        transport.chdir('..')
        transport.rmdir(directory)


def test_gettree_nested_directory(custom_transport):
    """Test `gettree` for a nested directory."""
    with tempfile.TemporaryDirectory() as dir_remote, tempfile.TemporaryDirectory() as dir_local:
        content = b'dummy\ncontent'
        filepath = os.path.join(dir_remote, 'sub', 'path', 'filename.txt')
        os.makedirs(os.path.dirname(filepath))

        with open(filepath, 'wb') as handle:
            handle.write(content)

        with custom_transport as transport:
            transport.gettree(os.path.join(dir_remote, 'sub/path'), os.path.join(dir_local, 'sub/path'))


def test_exec_pwd(custom_transport):
    """I create a strange subfolder with a complicated name and
    then see if I can run pwd. This also checks the correct
    escaping of funny characters, both in the directory
    creation (which should be done by paramiko) and in the command
    execution (done in this module, in the _exec_command_internal function).
    """
    # Start value
    delete_at_end = False

    with custom_transport as transport:
        # To compare with: getcwd uses the normalized ('realpath') path
        location = transport.normalize('/tmp')
        subfolder = """_'s f"#"""  # A folder with characters to escape
        subfolder_fullpath = os.path.join(location, subfolder)

        transport.chdir(location)
        if not transport.isdir(subfolder):
            # Since I created the folder, I will remember to
            # delete it at the end of this test
            delete_at_end = True
            transport.mkdir(subfolder)

        assert transport.isdir(subfolder)
        transport.chdir(subfolder)

        assert subfolder_fullpath == transport.getcwd()
        retcode, stdout, stderr = transport.exec_command_wait('pwd')
        assert retcode == 0
        # I have to strip it because 'pwd' returns a trailing \n
        assert stdout.strip() == subfolder_fullpath
        assert stderr == ''

        if delete_at_end:
            transport.chdir(location)
            transport.rmdir(subfolder)


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
    test_string = b'some_test bytes with non-unicode -> \xfa'
    with custom_transport as transport:
        retcode, stdout, stderr = transport.exec_command_wait_bytes('cat', stdin=test_string)
        assert retcode == 0
        assert stdout == test_string
        assert stderr == b''


def test_exec_with_stdin_filelike(custom_transport):
    """Test command execution with a stdin from filelike."""
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
    test_string = b'some_test bytes with non-unicode -> \xfa'
    stdin = io.BytesIO(test_string)
    with custom_transport as transport:
        with pytest.raises(UnicodeDecodeError):
            transport.exec_command_wait('cat', stdin=stdin, encoding='utf-8')


def test_exec_with_wrong_stdin(custom_transport):
    """Test command execution with incorrect stdin string."""
    # I pass a number
    with custom_transport as transport:
        with pytest.raises(ValueError):
            transport.exec_command_wait('cat', stdin=1)


def test_transfer_big_stdout(custom_transport):
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

    with custom_transport as trans:
        # We cannot use tempfile.mkdtemp because we're on a remote folder
        location = trans.normalize(os.path.join('/', 'tmp'))
        trans.chdir(location)
        assert location == trans.getcwd()

        directory = 'temp_dir_test_transfer_big_stdout'
        while trans.isdir(directory):
            # I append a random letter/number until it is unique
            directory += random.choice(string.ascii_uppercase + string.digits)
        trans.mkdir(directory)
        trans.chdir(directory)

        with tempfile.NamedTemporaryFile(mode='wb') as tmpf:
            tmpf.write(fcontent.encode('utf8'))
            tmpf.flush()

            # I put a file with specific content there at the right file name
            trans.putfile(tmpf.name, fname)

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
            trans.putfile(tmpf.name, script_fname)

        # I get its content via the stdout; emulate also network slowness (note I cat twice)
        retcode, stdout, stderr = trans.exec_command_wait(f'cat {fname} ; sleep 1 ; cat {fname}')
        assert stderr == ''
        assert stdout == fcontent + fcontent
        assert retcode == 0

        # I get its content via the stderr; emulate also network slowness (note I cat twice)
        retcode, stdout, stderr = trans.exec_command_wait(f'cat {fname} >&2 ; sleep 1 ; cat {fname} >&2')
        assert stderr == fcontent + fcontent
        assert stdout == ''
        assert retcode == 0

        # This time, I cat one one on each of the two streams intermittently, to check
        # that this does not hang.

        # Initially I was using a command like
        #        'i=0; while [ "$i" -lt {} ] ; do let i=i+1; echo -n "{}" ; echo -n "{}" >&2 ; done'.format(
        #        line_repetitions, file_line, file_line))
        # However this is pretty slow (and using 'cat' of a file containing only one line is even slower)

        retcode, stdout, stderr = trans.exec_command_wait(f'python3 {script_fname}')

        assert stderr == fcontent
        assert stdout == fcontent
        assert retcode == 0

        # Clean-up
        trans.remove(fname)
        trans.remove(script_fname)
        trans.chdir('..')
        trans.rmdir(directory)


def test_asynchronous_execution(custom_transport):
    """Test that the execution of a long(ish) command via the direct scheduler does not block.

    This is a regression test for #3094, where running a long job on the direct scheduler
    (via SSH) would lock the interpreter until the job was done.
    """
    # Use a unique name, using a UUID, to avoid concurrent tests (or very rapid
    # tests that follow each other) to overwrite the same destination
    script_fname = f'sleep-submit-{uuid.uuid4().hex}-{custom_transport.__class__.__name__}.sh'

    scheduler = SchedulerFactory('core.direct')()
    scheduler.set_transport(custom_transport)
    with custom_transport as transport:
        try:
            with tempfile.NamedTemporaryFile() as tmpf:
                # Put a submission script that sleeps 10 seconds
                tmpf.write(b'#!/bin/bash\nsleep 10\n')
                tmpf.flush()

                transport.putfile(tmpf.name, os.path.join('/tmp', script_fname))

            timestamp_before = time.time()
            job_id_string = scheduler.submit_job('/tmp', script_fname)

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

            # Also remove the script
            try:
                transport.remove(f'/tmp/{script_fname}')
            except FileNotFoundError:
                # If the file wasn't even created, I just ignore this error
                pass
