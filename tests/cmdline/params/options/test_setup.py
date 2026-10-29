###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for setup command line options."""

import uuid

import click
import pytest

from aiida.cmdline.params.options.commands.setup import SETUP_PROFILE_UUID, validate_profile_uuid


@pytest.mark.parametrize(
    'valid_uuid',
    (
        'c02e1fd7-1bf1-42ec-a059-86cbff2eb87c',
        'c02e1fd71bf142eca05986cbff2eb87c',
        '00000000-0000-0000-0000-000000000000',
    ),
)
def test_validate_profile_uuid_valid(valid_uuid):
    """Test ``validate_profile_uuid`` callback with valid UUIDs."""
    assert validate_profile_uuid(None, None, valid_uuid) == valid_uuid


def test_validate_profile_uuid_none():
    """Test ``validate_profile_uuid`` callback with None (not specified)."""
    assert validate_profile_uuid(None, None, None) is None


@pytest.mark.parametrize(
    'invalid_uuid',
    (
        'invalid-uuid',
        '',
        '12345',
        'c02e1fd7-1bf1-42ec-a059-86cbff2eb87g',
    ),
)
def test_validate_profile_uuid_invalid(invalid_uuid):
    """Test ``validate_profile_uuid`` callback with invalid UUIDs raises click.BadParameter."""
    with pytest.raises(click.BadParameter, match='is not a valid UUID'):
        validate_profile_uuid(None, None, invalid_uuid)


def test_setup_profile_uuid_option(run_cli_command):
    """Test ``SETUP_PROFILE_UUID`` option attached to a click command."""

    @click.command()
    @SETUP_PROFILE_UUID()
    def test_cmd(profile_uuid):
        click.echo(f'UUID: {profile_uuid}')

    test_uuid = str(uuid.uuid4())
    result = run_cli_command(test_cmd, ['--profile-uuid', test_uuid])
    assert result.exit_code == 0
    assert f'UUID: {test_uuid}' in result.output

    # When not supplied, should default to None
    result = run_cli_command(test_cmd, [])
    assert result.exit_code == 0
    assert 'UUID: None' in result.output

    # When invalid, should fail with BadParameter
    result = run_cli_command(test_cmd, ['--profile-uuid', 'invalid-uuid'], raises=True)
    assert result.exit_code != 0
    assert 'is not a valid UUID' in result.output
