###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :class:`aiida.cmdline.params.types.profile.ProfileParamType`."""

import os
import re
import subprocess
import types

import click
import pytest

from aiida.cmdline.params.types.profile import ProfileParamType
from aiida.storage.sqlite_zip.backend import SqliteZipBackend


@pytest.fixture
def filepath_archive(tmp_path):
    """Return the filepath of an initialised, empty archive."""
    filepath = tmp_path / 'archive.aiida'
    SqliteZipBackend.initialise(SqliteZipBackend.create_profile(filepath))
    return filepath


@pytest.fixture
def ctx(aiida_config):
    """Return a ``click`` context with the config on the user defined object, as ``VerdiContext`` provides it."""
    context = click.Context(click.Command('test'))
    context.obj = types.SimpleNamespace(config=aiida_config, profile=None)
    return context


def test_convert_archive_file_url(ctx, filepath_archive, aiida_config):
    """Test that a ``file://`` value is converted to an ephemeral archive profile, without touching the config."""
    profile = ProfileParamType(accept_archive_location=True).convert(f'file://{filepath_archive}', None, ctx)

    assert profile.storage_backend == 'core.sqlite_zip'
    assert profile.storage_config['filepath'] == str(filepath_archive)
    assert ctx.obj.profile is profile
    assert profile.name not in [p.name for p in aiida_config.profiles]


def test_convert_archive_remote_url(ctx, aiida_config):
    """Test that an ``https://`` value is converted to an ephemeral archive profile, without network access."""
    url = 'https://example.com/some/path/export.aiida?download=1'
    profile = ProfileParamType(accept_archive_location=True).convert(url, None, ctx)

    assert profile.storage_backend == 'core.sqlite_zip'
    assert profile.storage_config['filepath'] == url
    assert re.fullmatch(r'export_aiida_[0-9a-f]{8}', profile.name)
    assert profile.name not in [p.name for p in aiida_config.profiles]

    # The name is deterministic: converting the same location again yields the same name
    assert ProfileParamType(accept_archive_location=True).convert(url, None, ctx).name == profile.name

    # ... but a different location with the same filename yields a different name
    other = ProfileParamType(accept_archive_location=True).convert(f'{url}&other=1', None, ctx)
    assert other.name != profile.name


def test_convert_archive_file_url_localhost(ctx, filepath_archive):
    """Test that the ``file://localhost/absolute/path`` form is accepted."""
    profile = ProfileParamType(accept_archive_location=True).convert(f'file://localhost{filepath_archive}', None, ctx)
    assert profile.storage_config['filepath'] == str(filepath_archive)


def test_convert_archive_file_url_percent_encoded(ctx, tmp_path):
    """Test that percent-encoded characters in a ``file://`` URL are decoded."""
    filepath_archive = tmp_path / 'some archive.aiida'
    SqliteZipBackend.initialise(SqliteZipBackend.create_profile(filepath_archive))

    value = f'file://{str(filepath_archive).replace(" ", "%20")}'
    profile = ProfileParamType(accept_archive_location=True).convert(value, None, ctx)
    assert profile.storage_config['filepath'] == str(filepath_archive)


def test_convert_archive_file_url_invalid_host(ctx):
    """Test that a ``file://`` URL with a non-local host is rejected with a clear error."""
    with pytest.raises(click.BadParameter, match=r'.*unsupported host `example.com`.*'):
        ProfileParamType(accept_archive_location=True).convert('file://example.com/path/export.aiida', None, ctx)


def test_convert_archive_file_url_non_existent(ctx, tmp_path):
    """Test that a ``file://`` value pointing to a non-existent file raises."""
    with pytest.raises(click.BadParameter, match=r'.*does not exist.*'):
        ProfileParamType(accept_archive_location=True).convert(f'file://{tmp_path / "non-existent.aiida"}', None, ctx)


def test_convert_archive_location_not_accepted_by_default(ctx):
    """Test that archive locations are rejected unless ``accept_archive_location=True``.

    This ensures that e.g. ``verdi profile delete <URL>`` fails label validation instead of silently creating an
    ephemeral profile; only parameters that explicitly opt in (the ``verdi -p/--profile`` option) convert locations.
    """
    with pytest.raises(click.BadParameter):
        ProfileParamType().convert('https://example.com/export.aiida', None, ctx)

    with pytest.raises(click.BadParameter):
        ProfileParamType().convert('file:///some/path/export.aiida', None, ctx)


def test_convert_archive_url_cannot_exist(ctx):
    """Test that URL values are not converted to archive profiles when ``cannot_exist=True``.

    In that case the value is supposed to be the name for a new profile, so it should fail label validation.
    """
    with pytest.raises(click.BadParameter):
        ProfileParamType(cannot_exist=True).convert('https://example.com/export.aiida', None, ctx)


def test_verdi_ephemeral_archive_profile(filepath_archive, tmp_path):
    """Test ``verdi -p file://<archive> <command>`` end-to-end in a subprocess.

    The command should succeed without the profile being added to the configuration file and without leaving the
    temporary database file behind after the process exits.
    """
    tmp_dir = tmp_path / 'tmpdir'
    tmp_dir.mkdir()

    env = os.environ.copy()
    env['TMPDIR'] = str(tmp_dir)

    filepath_config = tmp_path / 'aiida_config'
    env['AIIDA_PATH'] = str(filepath_config)

    result = subprocess.run(
        ['verdi', '-p', f'file://{filepath_archive}', 'user', 'list'],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    # The command queried the storage, so the database was extracted to ``TMPDIR``: check it was cleaned up at exit.
    # Only consider plain temporary files as created by ``tempfile.mkstemp``, to be robust against anything else in
    # the subprocess writing to ``TMPDIR``.
    leftovers = [path for path in tmp_dir.iterdir() if path.is_file() and path.name.startswith('tmp')]
    assert leftovers == []

    # The ephemeral profile was not added to the configuration file
    config_file = filepath_config / '.aiida' / 'config.json'
    assert config_file.exists(), 'the configuration file was not created'
    assert 'archive' not in config_file.read_text()
