###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi archive`."""

import shutil
import uuid
import zipfile

import pytest

from aiida.cmdline.commands import cmd_archive
from aiida.orm import Computer, Dict, Group, InstalledCode
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


def test_create_file_nested_directory(run_cli_command, tmp_path):
    """Test that output files that contains nested directories are created automatically."""
    filepath = tmp_path / 'some' / 'sub' / 'directory' / 'output.aiida'
    options = [str(filepath)]
    run_cli_command(cmd_archive.create, options)
    assert filepath.exists()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_create_all(run_cli_command, tmp_path, aiida_localhost):
    """Test that creating an archive for a set of various ORM entities works with the zip format."""
    computer = aiida_localhost
    code = InstalledCode(computer=computer, filepath_executable='/bin/true').store()
    group = Group(label=str(uuid.uuid4())).store()
    filename_output = tmp_path / 'archive.aiida'

    options = ['--all', filename_output]
    run_cli_command(cmd_archive.create, options, use_subprocess=True)
    assert filename_output.is_file()
    assert ArchiveFormatSqlZip().read_version(filename_output) == ArchiveFormatSqlZip().latest_version
    with ArchiveFormatSqlZip().open(filename_output, 'r') as archive:
        assert archive.querybuilder().append(Computer, project=['uuid']).all(flat=True) == [computer.uuid]
        assert archive.querybuilder().append(InstalledCode, project=['uuid']).all(flat=True) == [code.uuid]
        assert archive.querybuilder().append(Group, project=['uuid']).all(flat=True) == [group.uuid]


def test_create_basic(run_cli_command, tmp_path, aiida_localhost):
    """Test that creating an archive for a set of various ORM entities works with the zip format."""
    computer = aiida_localhost
    code = InstalledCode(computer=computer, filepath_executable='/bin/true').store()
    group = Group(label=str(uuid.uuid4())).store()
    node = Dict().store()
    filename_output = tmp_path / 'archive.aiida'

    options = ['-X', code.pk, '-Y', computer.pk, '-G', group.pk, '-N', node.pk, '--', filename_output]
    run_cli_command(cmd_archive.create, options)
    assert filename_output.is_file()
    assert ArchiveFormatSqlZip().read_version(filename_output) == ArchiveFormatSqlZip().latest_version
    with ArchiveFormatSqlZip().open(filename_output, 'r') as archive:
        assert archive.querybuilder().append(Computer, project=['uuid']).all(flat=True) == [computer.uuid]
        assert archive.querybuilder().append(InstalledCode, project=['uuid']).all(flat=True) == [code.uuid]
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
    assert ArchiveFormatSqlZip().read_version(filename_output) == target_version
    with zipfile.ZipFile(filename_output) as handle:
        assert handle.testzip() is None


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
    assert ArchiveFormatSqlZip().read_version(filename_clone) == target_version
    with zipfile.ZipFile(filename_clone) as handle:
        assert handle.testzip() is None


@pytest.mark.usefixtures('config_with_profile')
def test_migrate_low_verbosity(run_cli_command, tmp_path):
    """Test that the captured output is an empty string when the ``--verbosity WARNING`` option is passed.

    Note that we use the ``config_with_profile`` fixture to create a dummy profile, since the ``--verbosity`` option
    will change the profile configuration which could potentially influence the other tests.
    """
    filename_input = get_archive_file('export_0.6_simple.aiida', filepath='export/migrate')
    filename_output = tmp_path / 'archive.aiida'

    options = ['--verbosity', 'WARNING', filename_input, filename_output]
    result = run_cli_command(cmd_archive.migrate, options, suppress_warnings=True)
    assert result.output == ''
    assert filename_output.is_file()
    assert ArchiveFormatSqlZip().read_version(filename_output) == ArchiveFormatSqlZip().latest_version
    with zipfile.ZipFile(filename_output) as handle:
        assert handle.testzip() is None


@pytest.mark.parametrize('version', [v for v in list_versions() if v not in ('main_0000a', 'main_0000b')])
def test_version(run_cli_command, version):
    """Test the functionality of `verdi archive version`."""
    archive = f'export_{version}_simple.aiida'
    filename_input = get_archive_file(archive, filepath='export/migrate')
    options = [filename_input]
    result = run_cli_command(cmd_archive.archive_version, options)
    assert version in result.output


def test_info(run_cli_command):
    """Test the functionality of `verdi archive info`."""
    archive = f'export_{ArchiveFormatSqlZip().latest_version}_simple.aiida'
    filename_input = get_archive_file(archive, filepath='export/migrate')
    options = [filename_input]
    result = run_cli_command(cmd_archive.archive_info, options)
    assert 'export_version' in result.output


def test_info_detailed(run_cli_command):
    """Test the functionality of `verdi archive info --detailed`."""
    archive = f'export_{ArchiveFormatSqlZip().latest_version}_simple.aiida'
    filename_input = get_archive_file(archive, filepath='export/migrate')
    options = ['--detailed', filename_input]
    result = run_cli_command(cmd_archive.archive_info, options)
    assert 'Nodes:' in result.output


def test_info_empty_archive(run_cli_command):
    """Test the functionality of `verdi archive info` for an empty archive."""
    filename_input = get_archive_file('empty.aiida', filepath='export/migrate')
    result = run_cli_command(cmd_archive.archive_info, [filename_input], raises=True)
    assert 'archive file unreadable' in result.output


@pytest.mark.usefixtures('aiida_profile_clean')
def test_info_entities_starting_set_truncation(run_cli_command, tmp_path):
    """Test that entities_starting_set is truncated in non-detailed mode and shown fully with --detailed."""
    # Create 10 nodes to test truncation (should show 5 + message)
    nodes = [Dict().store() for _ in range(10)]
    filename_output = tmp_path / 'archive.aiida'

    # Create archive with 10 nodes
    options = ['-N'] + [str(node.pk) for node in nodes] + ['--', filename_output]
    run_cli_command(cmd_archive.create, options)

    # Test without --detailed (should be truncated)
    result = run_cli_command(cmd_archive.archive_info, [filename_output])
    assert '... and 5 more (use --detailed to show all)' in result.output

    # Test with --detailed (should show all)
    result_detailed = run_cli_command(cmd_archive.archive_info, ['--detailed', filename_output])
    assert '... and 5 more (use --detailed to show all)' not in result_detailed.output
    # All 10 UUIDs should be present in detailed mode
    for node in nodes:
        assert str(node.uuid) in result_detailed.output
