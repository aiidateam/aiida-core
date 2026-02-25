###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi archive import`."""

import pytest

from aiida.cmdline.commands import cmd_archive
from aiida.orm import Group
from aiida.storage.sqlite_zip.migrator import list_versions
from aiida.tools.archive.implementations.sqlite_zip.main import ArchiveFormatSqlZip
from tests.utils.archives import get_archive_file

ARCHIVE_PATH = 'export/migrate'


@pytest.fixture
def newest_archive():
    """Return the name of the export archive at the latest version."""
    return f'export_{ArchiveFormatSqlZip().latest_version}_simple.aiida'


def test_import_no_archives(run_cli_command):
    """Test that passing no valid archives will lead to command failure."""
    options = []
    result = run_cli_command(cmd_archive.import_archive, options, raises=True)
    assert 'Critical' in result.output


def test_import_non_existing_archives(run_cli_command):
    """Test that passing a non-existing archive will lead to command failure."""
    options = ['non-existing-archive.aiida']
    run_cli_command(cmd_archive.import_archive, options, raises=True)


def test_import_archive(run_cli_command, newest_archive):
    """Test import for archive files from disk"""
    archives = [
        get_archive_file('arithmetic.add.aiida', filepath='calcjob'),
        get_archive_file(newest_archive, filepath=ARCHIVE_PATH),
    ]

    options = [] + archives
    run_cli_command(cmd_archive.import_archive, options)


@pytest.mark.parametrize(
    'archive',
    (
        get_archive_file('arithmetic.add.aiida', filepath='calcjob'),
        get_archive_file('export_0.9_simple.aiida', filepath=ARCHIVE_PATH),
    ),
)
def test_import_dry_run(run_cli_command, archive):
    """Test import dry-run"""
    result = run_cli_command(cmd_archive.import_archive, [archive, '--dry-run'])
    assert f'import dry-run of archive {archive} completed' in result.output


def test_import_to_group(run_cli_command, newest_archive):
    """Test import to existing Group and that Nodes are added correctly for multiple imports of the same,
    as well as separate, archives.
    """
    archives = [
        get_archive_file('arithmetic.add.aiida', filepath='calcjob'),
        get_archive_file(newest_archive, filepath=ARCHIVE_PATH),
    ]

    group_label = 'import_madness'
    group = Group(group_label).store()

    assert group.is_empty, 'The Group should be empty.'

    # Invoke `verdi import`, making sure there are no exceptions
    options = ['-G', group.label] + [archives[0]]
    run_cli_command(cmd_archive.import_archive, options)
    assert not group.is_empty, 'The Group should no longer be empty.'

    nodes_in_group = group.count()

    # Invoke `verdi import` again, making sure Group count doesn't change
    options = ['-G', group.label] + [archives[0]]
    run_cli_command(cmd_archive.import_archive, options)
    assert (
        group.count() == nodes_in_group
    ), f'The Group count should not have changed from {nodes_in_group}. Instead it is now {group.count()}'

    # Invoke `verdi import` again with new archive, making sure Group count is upped
    options = ['-G', group.label] + [archives[1]]
    run_cli_command(cmd_archive.import_archive, options)
    assert (
        group.count() > nodes_in_group
    ), 'There should now be more than {} nodes in group {} , instead there are {}'.format(
        nodes_in_group, group_label, group.count()
    )


def test_import_make_new_group(run_cli_command, newest_archive):
    """Make sure imported entities are saved in new Group"""
    # Initialization
    group_label = 'new_group_for_verdi_import'
    archives = [get_archive_file(newest_archive, filepath=ARCHIVE_PATH)]

    # Check Group does not already exist
    group_search = Group.collection.find(filters={'label': group_label})
    assert len(group_search) == 0, f"A Group with label '{group_label}' already exists, this shouldn't be."

    # Invoke `verdi import`, making sure there are no exceptions
    options = ['-G', group_label] + archives
    run_cli_command(cmd_archive.import_archive, options, use_subprocess=True)

    # Make sure new Group was created
    (group, new_group) = Group.collection.get_or_create(group_label)
    assert not new_group, 'The Group should not have been created now, but instead when it was imported.'
    assert not group.is_empty, 'The Group should not be empty.'


@pytest.mark.usefixtures('aiida_profile_clean')
def test_no_import_group(run_cli_command, newest_archive):
    """Test '--import-group/--no-import-group' options."""
    archives = [get_archive_file(newest_archive, filepath=ARCHIVE_PATH)]

    assert Group.collection.count() == 0, 'There should be no Groups.'

    # Invoke `verdi import`
    options = archives
    run_cli_command(cmd_archive.import_archive, options)
    assert Group.collection.count() == 5

    # Invoke `verdi import` again, creating another import group
    options = ['--import-group'] + archives
    run_cli_command(cmd_archive.import_archive, options)
    assert Group.collection.count() == 6

    # Invoke `verdi import` again, but with no import group created
    options = ['--no-import-group'] + archives
    run_cli_command(cmd_archive.import_archive, options)
    assert Group.collection.count() == 6


def test_comment_mode(run_cli_command, newest_archive):
    """Test toggling comment mode flag"""
    archives = [get_archive_file(newest_archive, filepath=ARCHIVE_PATH)]
    for mode in ['leave', 'newest', 'overwrite']:
        options = ['--comment-mode', mode] + archives
        run_cli_command(cmd_archive.import_archive, options)


def test_import_old_url_archives(run_cli_command):
    """Test import of old URL archives

    Expected behavior: Automatically migrate to newest version and import correctly.
    """
    archive = 'export_v0.4_no_UPF.aiida'
    version = '0.4'
    url_path = (
        'https://raw.githubusercontent.com/aiidateam/aiida-core/'
        '0599dabf0887bee172a04f308307e99e3c3f3ff2/aiida/backends/tests/fixtures/export/migrate/'
    )
    options = [url_path + archive]
    result = run_cli_command(cmd_archive.import_archive, options)
    assert version in result.output, result.exception
    assert f'Success: imported archive {options[0]}' in result.output, result.exception


def test_import_url_and_local_archives(run_cli_command, newest_archive):
    """Test import of both a remote and local archive"""
    url_archive = 'export_v0.4_no_UPF.aiida'
    local_archive = newest_archive
    url_path = (
        'https://raw.githubusercontent.com/aiidateam/aiida-core/'
        '0599dabf0887bee172a04f308307e99e3c3f3ff2/aiida/backends/tests/fixtures/export/migrate/'
    )

    options = [
        get_archive_file(local_archive, filepath=ARCHIVE_PATH),
        url_path + url_archive,
        get_archive_file(local_archive, filepath=ARCHIVE_PATH),
    ]
    run_cli_command(cmd_archive.import_archive, options)


def test_raise_malformed_url(run_cli_command):
    """Test the correct error is raised when supplying a malformed URL"""
    malformed_url = 'htp://www.aiida.net'

    result = run_cli_command(cmd_archive.import_archive, [malformed_url], raises=True)
    assert 'could not be reached.' in result.output, result.exception


def test_migration(run_cli_command):
    """Test options `--migration`/`--no-migration`

    `migration` = True (default), Expected: No query, migrate
    `migration` = False, Expected: No query, no migrate
    """
    archive = get_archive_file('export_0.4_simple.aiida', filepath=ARCHIVE_PATH)
    success_message = f'Success: imported archive {archive}'

    # Import "normally", but explicitly specifying `--migration`, make sure confirm message is present
    # `migration` = True (default), `non_interactive` = False (default), Expected: Query user, migrate
    options = ['--migration', archive]
    result = run_cli_command(cmd_archive.import_archive, options)
    assert 'trying migration' in result.output, result.exception
    assert success_message in result.output, result.exception

    # Import using `--no-migration`, make sure confirm message has gone
    # `migration` = False, `non_interactive` = False (default), Expected: No query, no migrate
    options = ['--no-migration', archive]
    result = run_cli_command(cmd_archive.import_archive, options, raises=True)
    assert 'trying migration' not in result.output, result.exception
    assert success_message not in result.output, result.exception


@pytest.mark.parametrize('version', [v for v in list_versions() if v not in ('main_0000a', 'main_0000b')])
def test_import_old_local_archives(version, run_cli_command):
    """Test import of old local archives
    Expected behavior: Automatically migrate to newest version and import correctly.
    """
    archive, version = (f'export_{version}_simple.aiida', f'{version}')
    options = [get_archive_file(archive, filepath=ARCHIVE_PATH)]
    result = run_cli_command(cmd_archive.import_archive, options)
    assert version in result.output, result.exception
    assert f'Success: imported archive {options[0]}' in result.output, result.exception


def test_import_packed_flag(run_cli_command, newest_archive, aiida_profile_clean):
    """Test import with --packed flag streams directly to packed storage."""
    from aiida.manage import get_manager

    archive = get_archive_file(newest_archive, filepath=ARCHIVE_PATH)
    options = ['--packed', archive]
    result = run_cli_command(cmd_archive.import_archive, options)
    assert f'Success: imported archive {archive}' in result.output, result.exception

    # Verify objects are in packed storage (not loose)
    repo = get_manager().get_profile_storage().get_repository()
    with repo._container as container:
        counts = container.count_objects()
        # The archive should have some repository objects that end up packed
        # We just verify that loose is 0 when --packed is used
        assert counts.loose == 0, f'Expected 0 loose objects with --packed flag, got {counts.loose}'
