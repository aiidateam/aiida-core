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
import zipfile

import pytest

from aiida.cmdline.commands import cmd_archive
from aiida.orm import Code, Computer, Dict, Group
from aiida.storage.sqlite_zip.migrator import list_versions
from aiida.tools.archive import ArchiveFormatSqlZip
from tests.utils.archives import get_archive_file

pytest.mark.usefixtures('chdir_tmp_path')


def test_create_file_already_exists(run_cli_command, tmp_path):
    """Test that using a file that already exists will raise."""
    tmp_path.joinpath('existing').touch()
    options = [tmp_path.joinpath('existing')]
    run_cli_command(cmd_archive.create, options, raises=True)


def test_create_force(run_cli_command, tmp_path):
    """Test that using a file that already exists will work when the ``-f/--force`` parameter is used."""
    tmp_path.joinpath('existing').touch()
    options = ['--force', tmp_path.joinpath('existing')]
    run_cli_command(cmd_archive.create, options)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_create_all(run_cli_command, tmp_path):
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
    filename_output = tmp_path / 'archive.aiida'

    options = ['--all', filename_output]
    run_cli_command(cmd_archive.create, options)
    assert filename_output.is_file()
    assert ArchiveFormatSqlZip().read_version(filename_output) == ArchiveFormatSqlZip().latest_version
    with ArchiveFormatSqlZip().open(filename_output, 'r') as archive:
        assert archive.querybuilder().append(Computer, project=['uuid']).all(flat=True) == [computer.uuid]
        assert archive.querybuilder().append(Code, project=['uuid']).all(flat=True) == [code.uuid]
        assert archive.querybuilder().append(Group, project=['uuid']).all(flat=True) == [group.uuid]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_create_basic(run_cli_command, tmp_path):
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
    node = Dict().store()
    filename_output = tmp_path / 'archive.aiida'

    options = ['-X', code.pk, '-Y', computer.pk, '-G', group.pk, '-N', node.pk, '--', filename_output]
    run_cli_command(cmd_archive.create, options)
    assert filename_output.is_file()
    assert ArchiveFormatSqlZip().read_version(filename_output) == ArchiveFormatSqlZip().latest_version
    with ArchiveFormatSqlZip().open(filename_output, 'r') as archive:
        assert archive.querybuilder().append(Computer, project=['uuid']).all(flat=True) == [computer.uuid]
        assert archive.querybuilder().append(Code, project=['uuid']).all(flat=True) == [code.uuid]
        assert archive.querybuilder().append(Group, project=['uuid']).all(flat=True) == [group.uuid]
        assert archive.querybuilder().append(Dict, project=['uuid']).all(flat=True) == [node.uuid]


@pytest.mark.parametrize('version', ('0.4', '0.5', '0.6', '0.7', '0.8', '0.9', '0.10', '0.11', '0.12'))
def test_migrate_versions_old(run_cli_command, tmp_path, version):
    """Migrating archives with a version older than the current should work."""
    archive = f'export_{version}_simple.aiida'
    filename_input = get_archive_file(archive, filepath='export/migrate')
    filename_output = tmp_path / 'archive.aiida'

    options = [filename_input, filename_output]
    run_cli_command(cmd_archive.migrate, options)
    assert filename_output.is_file()
    assert ArchiveFormatSqlZip().read_version(filename_output) == ArchiveFormatSqlZip().latest_version


def test_migrate_version_specific(run_cli_command, tmp_path):
    """Test the `-v/--version` option to migrate to a specific version instead of the latest."""
    archive = 'export_0.5_simple.aiida'
    target_version = '0.8'
    filename_input = get_archive_file(archive, filepath='export/migrate')
    filename_output = tmp_path / 'archive.aiida'

    options = [filename_input, filename_output, '--version', target_version]
    run_cli_command(cmd_archive.migrate, options)
    assert filename_output.is_file()
    assert zipfile.ZipFile(filename_output).testzip() is None  # pylint: disable=consider-using-with

    assert ArchiveFormatSqlZip().read_version(filename_output) == target_version


def test_migrate_file_already_exists(run_cli_command, tmp_path):
    """Test that using a file that already exists will raise."""
    outpath = tmp_path / 'archive.aiida'
    outpath.touch()
    filename_input = get_archive_file('export_0.6_simple.aiida', filepath='export/migrate')
    options = [filename_input, outpath]
    run_cli_command(cmd_archive.migrate, options, raises=True)


def test_migrate_force(run_cli_command, tmp_path):
    """Test that using a file that already exists will work when the ``-f/--force`` parameter is used."""
    outpath = tmp_path / 'archive.aiida'
    outpath.touch()
    filename_input = get_archive_file('export_0.6_simple.aiida', filepath='export/migrate')
    options = ['--force', filename_input, outpath]
    run_cli_command(cmd_archive.migrate, options)
    assert ArchiveFormatSqlZip().read_version(outpath) == ArchiveFormatSqlZip().latest_version


def test_migrate_in_place(run_cli_command, tmp_path):
    """Test that passing the -i/--in-place option will overwrite the passed file."""
    archive = 'export_0.6_simple.aiida'
    target_version = '0.8'
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

    assert ArchiveFormatSqlZip().read_version(filename_clone) == target_version


@pytest.mark.usefixtures('config_with_profile')
def test_migrate_low_verbosity(run_cli_command, tmp_path):
    """Test that the captured output is an empty string when the ``--verbosity WARNING`` option is passed.

    Note that we use the ``config_with_profile`` fixture to create a dummy profile, since the ``--verbosity`` option
    will change the profile configuration which could potentially influence the other tests.
    """
    filename_input = get_archive_file('export_0.6_simple.aiida', filepath='export/migrate')
    filename_output = tmp_path / 'archive.aiida'

    options = ['--verbosity', 'WARNING', filename_input, filename_output]
    result = run_cli_command(cmd_archive.migrate, options)
    assert result.output == ''
    assert filename_output.is_file()
    assert zipfile.ZipFile(filename_output).testzip() is None  # pylint: disable=consider-using-with
    assert ArchiveFormatSqlZip().read_version(filename_output) == ArchiveFormatSqlZip().latest_version


@pytest.mark.parametrize('version', list_versions())
def test_inspect_version(run_cli_command, version):
    """Test the functionality of `verdi export inspect --version`."""
    archive = f'export_{version}_simple.aiida'
    filename_input = get_archive_file(archive, filepath='export/migrate')
    options = ['--version', filename_input]
    result = run_cli_command(cmd_archive.inspect, options)
    assert result.output.strip() == f'{version}'


def test_inspect_metadata(run_cli_command):
    """Test the functionality of `verdi export inspect --meta-data`."""
    archive = f'export_{ArchiveFormatSqlZip().latest_version}_simple.aiida'
    filename_input = get_archive_file(archive, filepath='export/migrate')
    options = ['--meta-data', filename_input]
    result = run_cli_command(cmd_archive.inspect, options)
    assert 'export_version' in result.output


def test_inspect_database(run_cli_command):
    """Test the functionality of `verdi export inspect --meta-data`."""
    archive = f'export_{ArchiveFormatSqlZip().latest_version}_simple.aiida'
    filename_input = get_archive_file(archive, filepath='export/migrate')
    options = ['--database', filename_input]
    result = run_cli_command(cmd_archive.inspect, options)
    assert 'Nodes:' in result.output


def test_inspect_empty_archive(run_cli_command):
    """Test the functionality of `verdi export inspect` for an empty archive."""
    filename_input = get_archive_file('empty.aiida', filepath='export/migrate')
    result = run_cli_command(cmd_archive.inspect, [filename_input], raises=True)
    assert 'archive file of unknown format' in result.output
