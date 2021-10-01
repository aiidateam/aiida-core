# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi export`."""
import shutil
import tarfile
import zipfile

import pytest

from aiida.cmdline.commands import cmd_archive
from aiida.orm import Code, Computer, Data, Group
from aiida.tools.importexport import EXPORT_VERSION, ReaderJsonZip
from tests.utils.archives import get_archive_file

pytest.mark.usefixtures('chdir_tmp_path')


def test_create_file_already_exists(run_cli_command, tmp_path):
    """Test that using a file that already exists will raise."""
    assert tmp_path.exists()
    options = [tmp_path]
    run_cli_command(cmd_archive.create, options, raises=True)


def test_create_force(run_cli_command, tmp_path):
    """Test that using a file that already exists will work when the ``-f/--force`` parameter is used."""
    assert tmp_path.exists()
    options = ['--force', tmp_path]
    run_cli_command(cmd_archive.create, options)


@pytest.mark.parametrize('fmt', ('zip', 'zip-uncompressed', 'tar.gz'))
@pytest.mark.usefixtures('clear_database_before_test')
def test_create_compressed(run_cli_command, tmp_path, fmt):
    """Test that creating an archive for a set of various ORM entities works with the zip format."""
    computer = Computer(
        label='comp',
        hostname='localhost',
        transport_type='core.local',
        scheduler_type='core.direct',
        workdir='/tmp/aiida'
    ).store()
    code = Code(remote_computer_exec=(computer, '/bin/true')).store()
    group = Group(label='test_group').store()
    node = Data().store()
    filename_output = tmp_path / 'archive.aiida'

    options = ['-X', code.pk, '-Y', computer.pk, '-G', group.pk, '-N', node.pk, '-F', fmt, filename_output]
    run_cli_command(cmd_archive.create, options)
    assert filename_output.is_file()

    if fmt.startswith('zip'):
        assert zipfile.ZipFile(filename_output).testzip() is None  # pylint: disable=consider-using-with
    else:
        assert tarfile.is_tarfile(filename_output)


@pytest.mark.parametrize('version', range(1, int(EXPORT_VERSION.rsplit('.', maxsplit=1)[-1]) - 1))
def test_migrate_versions_old(run_cli_command, tmp_path, version):
    """Migrating archives with a version older than the current should work."""
    archive = f'export_v0.{version}_simple.aiida'
    filename_input = get_archive_file(archive, filepath='export/migrate')
    filename_output = tmp_path / 'archive.aiida'

    options = [filename_input, filename_output]
    run_cli_command(cmd_archive.migrate, options)
    assert filename_output.is_file()
    assert zipfile.ZipFile(filename_output).testzip() is None  # pylint: disable=consider-using-with


def test_migrate_version_specific(run_cli_command, tmp_path):
    """Test the `-v/--version` option to migrate to a specific version instead of the latest."""
    archive = 'export_v0.1_simple.aiida'
    target_version = '0.2'
    filename_input = get_archive_file(archive, filepath='export/migrate')
    filename_output = tmp_path / 'archive.aiida'

    options = [filename_input, filename_output, '--version', target_version]
    run_cli_command(cmd_archive.migrate, options)
    assert filename_output.is_file()
    assert zipfile.ZipFile(filename_output).testzip() is None  # pylint: disable=consider-using-with

    with ReaderJsonZip(filename_output) as archive_object:
        assert archive_object.metadata.export_version == target_version


def test_migrate_file_already_exists(run_cli_command, tmp_path):
    """Test that using a file that already exists will raise."""
    assert tmp_path.exists()
    filename_input = get_archive_file('export_v0.6_simple.aiida', filepath='export/migrate')
    options = [filename_input, tmp_path]
    run_cli_command(cmd_archive.migrate, options, raises=True)


def test_migrate_force(run_cli_command, tmp_path):
    """Test that using a file that already exists will work when the ``-f/--force`` parameter is used."""
    assert tmp_path.exists()
    filename_input = get_archive_file('export_v0.6_simple.aiida', filepath='export/migrate')
    options = ['--force', filename_input, tmp_path]
    run_cli_command(cmd_archive.migrate, options)


def test_migrate_in_place(run_cli_command, tmp_path):
    """Test that passing the -i/--in-place option will overwrite the passed file."""
    archive = 'export_v0.1_simple.aiida'
    target_version = '0.2'
    filename_input = get_archive_file(archive, filepath='export/migrate')
    filename_clone = tmp_path / 'archive.aiida'

    # copy file (don't want to overwrite test data)
    shutil.copy(filename_input, filename_clone)

    # specifying both output and in-place should except
    options = [filename_clone, '--in-place', '--output-file', 'test.aiida']
    run_cli_command(cmd_archive.migrate, options, raises=True)

    # specifying neither output nor in-place should except
    options = [filename_clone]
    run_cli_command(cmd_archive.migrate, options, raises=True)

    # check that in-place migration produces a valid archive in place of the old file
    options = [filename_clone, '--in-place', '--version', target_version]
    run_cli_command(cmd_archive.migrate, options)
    assert filename_clone.is_file()
    assert zipfile.ZipFile(filename_clone).testzip() is None  # pylint: disable=consider-using-with

    with ReaderJsonZip(filename_clone) as archive_object:
        assert archive_object.metadata.export_version == target_version


@pytest.mark.usefixtures('config_with_profile')
def test_migrate_low_verbosity(run_cli_command, tmp_path):
    """Test that the captured output is an empty string when the ``--verbosity WARNING`` option is passed.

    Note that we use the ``config_with_profile`` fixture to create a dummy profile, since the ``--verbosity`` option
    will change the profile configuration which could potentially influence the other tests.
    """
    filename_input = get_archive_file('export_v0.6_simple.aiida', filepath='export/migrate')
    filename_output = tmp_path / 'archive.aiida'

    options = ['--verbosity', 'WARNING', filename_input, filename_output]
    result = run_cli_command(cmd_archive.migrate, options)
    assert result.output == ''
    assert filename_output.is_file()
    assert zipfile.ZipFile(filename_output).testzip() is None  # pylint: disable=consider-using-with


def test_migrate_tar_gz(run_cli_command, tmp_path):
    """Test that -F/--archive-format option can be used to write a tar.gz instead."""
    filename_input = get_archive_file('export_v0.6_simple.aiida', filepath='export/migrate')
    filename_output = tmp_path / 'archive.aiida'

    options = ['--archive-format', 'tar.gz', filename_input, filename_output]
    run_cli_command(cmd_archive.migrate, options)
    assert filename_output.is_file()
    assert tarfile.is_tarfile(filename_output)


@pytest.mark.parametrize('version', range(1, int(EXPORT_VERSION.rsplit('.', maxsplit=1)[-1]) - 1))
def test_inspect(run_cli_command, version):
    """Test the functionality of `verdi export inspect`."""
    archive = f'export_v0.{version}_simple.aiida'
    filename_input = get_archive_file(archive, filepath='export/migrate')

    # Test the options that will print the meta data
    options = ['-m', filename_input]
    run_cli_command(cmd_archive.inspect, options)

    # Test the --version option which should print the archive format version
    options = ['--version', filename_input]
    result = run_cli_command(cmd_archive.inspect, options)
    assert result.output.strip() == f'0.{version}'


def test_inspect_empty_archive(run_cli_command):
    """Test the functionality of `verdi export inspect` for an empty archive."""
    filename_input = get_archive_file('empty.aiida', filepath='export/migrate')
    result = run_cli_command(cmd_archive.inspect, [filename_input], raises=True)
    assert 'corrupt archive' in result.output
