###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the ``verdi profile cache-refresh`` and ``verdi profile cache-clear`` commands."""

import os
import subprocess
import zipfile

import pytest

from aiida.cmdline.commands import cmd_profile
from aiida.storage.sqlite_zip.backend import SqliteZipBackend


@pytest.fixture
def cache_dirpath(tmp_path, monkeypatch):
    """Redirect the ``sqlite_zip`` database cache to a temporary directory and return its path."""
    dirpath = tmp_path / 'cache'
    monkeypatch.setattr('aiida.storage.sqlite_zip.cache.get_cache_dirpath', lambda: dirpath)
    return dirpath


def test_cache_clear(run_cli_command, cache_dirpath):
    """Test ``verdi profile cache-clear`` deletes the cached files."""
    cache_dirpath.mkdir(parents=True)
    (cache_dirpath / '00000000-1.sqlite3').write_bytes(b'database')

    result = run_cli_command(cmd_profile.profile_cache_clear, ['--force'], use_subprocess=False)
    assert 'Deleted 1 cached database file(s)' in result.output
    assert not list(cache_dirpath.iterdir())


def test_cache_clear_empty(run_cli_command, cache_dirpath):
    """Test ``verdi profile cache-clear`` when the cache is empty."""
    result = run_cli_command(cmd_profile.profile_cache_clear, ['--force'], use_subprocess=False)
    assert 'nothing to delete' in result.output


def test_cache_refresh(run_cli_command, cache_dirpath, tmp_path, config_with_profile_factory):
    """Test ``verdi profile cache-refresh`` populates the cache and records it in the configuration."""
    config = config_with_profile_factory()

    filepath_archive = tmp_path / 'archive.aiida'
    profile = SqliteZipBackend.create_profile(filepath_archive)
    SqliteZipBackend.initialise(profile)
    config.add_profile(profile)

    result = run_cli_command(cmd_profile.profile_cache_refresh, [profile.name], use_subprocess=False)
    assert 'Cached database' in result.output

    filename = config.get_profile(profile.name).storage_config['cached_database']
    assert (cache_dirpath / filename).is_file()


def test_cache_refresh_wrong_backend(run_cli_command, cache_dirpath, config_with_profile_factory):
    """Test ``verdi profile cache-refresh`` raises for profiles not using the ``core.sqlite_zip`` backend."""
    config = config_with_profile_factory()
    profile_name = config.default_profile_name

    result = run_cli_command(cmd_profile.profile_cache_refresh, [profile_name], use_subprocess=False, raises=True)
    assert 'does not use the `core.sqlite_zip` storage backend' in result.output


def test_cache_refresh_transient_flags_not_persisted(
    run_cli_command, cache_dirpath, tmp_path, config_with_profile_factory
):
    """Test that flags injected by ``verdi --use-cache/--force-cache`` are never persisted by ``cache-refresh``."""
    from aiida.cmdline.commands.cmd_verdi import verdi

    config = config_with_profile_factory()

    filepath_archive = tmp_path / 'archive.aiida'
    profile = SqliteZipBackend.create_profile(filepath_archive)
    SqliteZipBackend.initialise(profile)
    config.add_profile(profile)

    options = ['--use-cache', '--force-cache', 'profile', 'cache-refresh', profile.name]
    result = run_cli_command(verdi, options, use_subprocess=False)
    assert 'Cached database' in result.output

    storage_config = config.get_profile(profile.name).storage_config
    assert 'cached_database' in storage_config
    assert 'use_cache' not in storage_config
    assert 'force_cache' not in storage_config


def test_cache_refresh_deletes_stale_entry(run_cli_command, cache_dirpath, tmp_path, config_with_profile_factory):
    """Test that ``cache-refresh`` deletes the previously recorded cache entry when the archive changed."""
    config = config_with_profile_factory()

    filepath_archive = tmp_path / 'archive.aiida'
    profile = SqliteZipBackend.create_profile(filepath_archive)
    SqliteZipBackend.initialise(profile)
    config.add_profile(profile)

    run_cli_command(cmd_profile.profile_cache_refresh, [profile.name], use_subprocess=False)
    filename_old = config.get_profile(profile.name).storage_config['cached_database']

    # Rewrite the archive with a different database content, keeping the metadata intact
    with zipfile.ZipFile(filepath_archive) as zip_handle:
        metadata = zip_handle.read('metadata.json')
    with zipfile.ZipFile(filepath_archive, 'w') as zip_handle:
        zip_handle.writestr('metadata.json', metadata)
        zip_handle.writestr('db.sqlite3', b'different database content')

    result = run_cli_command(cmd_profile.profile_cache_refresh, [profile.name], use_subprocess=False)
    assert f'Deleted the previously cached database `{filename_old}`' in result.output

    filename_new = config.get_profile(profile.name).storage_config['cached_database']
    assert filename_new != filename_old
    assert not (cache_dirpath / filename_old).exists()
    assert (cache_dirpath / filename_new).is_file()


def test_verdi_force_cache(tmp_path):
    """Test ``verdi profile setup --use-cache`` followed by ``verdi --force-cache`` end-to-end in a subprocess.

    With ``--force-cache``, a profile with a recorded cached database must be usable without access to the archive,
    and the transient flag must not be persisted to the configuration file.
    """
    filepath_config = tmp_path / 'aiida_config'
    env = os.environ.copy()
    env['AIIDA_PATH'] = str(filepath_config)

    filepath_archive = tmp_path / 'archive.aiida'
    SqliteZipBackend.initialise(SqliteZipBackend.create_profile(filepath_archive))

    options = ['-n', '--profile-name', 'archive', '--filepath', str(filepath_archive), '--use-cache']
    result = subprocess.run(
        ['verdi', 'profile', 'setup', 'core.sqlite_zip', *options], capture_output=True, text=True, env=env, check=False
    )
    assert result.returncode == 0, result.stderr

    # Move the archive away: only ``--force-cache`` should still be able to use the profile
    filepath_archive.rename(tmp_path / 'moved-away.aiida')

    result = subprocess.run(
        ['verdi', '-p', 'archive', 'user', 'list'], capture_output=True, text=True, env=env, check=False
    )
    assert result.returncode != 0

    result = subprocess.run(
        ['verdi', '--force-cache', '-p', 'archive', 'user', 'list'],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    # The transient flag was not persisted to the configuration file
    import json

    config_file = filepath_config / '.aiida' / 'config.json'
    storage_config = json.loads(config_file.read_text())['profiles']['archive']['storage']['config']
    assert 'force_cache' not in storage_config
