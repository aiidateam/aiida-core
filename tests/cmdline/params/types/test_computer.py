###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `ComputerParamType`."""

import uuid

import click
import pytest

from aiida import orm
from aiida.cmdline.params.types import ComputerParamType, MpirunCommandParamType
from aiida.orm.utils.loaders import OrmEntityLoader


@pytest.fixture
def parameter_type():
    """Return an instance of the `ComputerParamType`."""
    return ComputerParamType()


@pytest.fixture
def setup_computers():
    """Create some `Computer` instances to test the `ComputerParamType` parameter type for the command line
    infrastructure.

    We create an initial computer with name computer_01 and then on purpose create two computer with a name that matches
    exactly the ID and UUID, respectively, of the first one. This allows us to test the rules implemented to solve
    ambiguities that arise when determing the identifier type.
    """
    kwargs = {
        'hostname': 'localhost',
        'transport_type': 'core.local',
        'scheduler_type': 'core.direct',
        'workdir': '/tmp/aiida',
    }

    entity_01 = orm.Computer(label=f'computer-{uuid.uuid4().hex}', **kwargs).store()
    entity_02 = orm.Computer(label=str(entity_01.pk), **kwargs).store()
    entity_03 = orm.Computer(label=str(entity_01.uuid), **kwargs).store()

    return entity_01, entity_02, entity_03


@pytest.mark.usefixtures('aiida_profile_clean')
def test_shell_complete(setup_computers, parameter_type):
    """Test the `shell_complete` method that provides auto-complete functionality."""
    kwargs = {
        'hostname': 'localhost',
        'transport_type': 'core.local',
        'scheduler_type': 'core.direct',
        'workdir': '/tmp/aiida',
    }
    entity_01, entity_02, entity_03 = setup_computers
    entity_04 = orm.Computer(label='xavier', **kwargs).store()

    options = [item.value for item in parameter_type.shell_complete(None, None, '')]
    assert sorted(options) == sorted([entity_01.label, entity_02.label, entity_03.label, entity_04.label])

    options = [item.value for item in parameter_type.shell_complete(None, None, 'xa')]
    assert sorted(options) == sorted([entity_04.label])


def test_get_by_id(setup_computers, parameter_type):
    """Verify that using the ID will retrieve the correct entity"""
    entity_01, _, _ = setup_computers
    identifier = f'{entity_01.pk}'
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid


def test_get_by_uuid(setup_computers, parameter_type):
    """Verify that using the UUID will retrieve the correct entity"""
    entity_01, _, _ = setup_computers
    identifier = f'{entity_01.uuid}'
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid


def test_get_by_label(setup_computers, parameter_type):
    """Verify that using the LABEL will retrieve the correct entity"""
    entity_01, _, _ = setup_computers
    identifier = f'{entity_01.label}'
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid


def test_ambiguous_label_pk(setup_computers, parameter_type):
    """Situation: LABEL of entity_02 is exactly equal to ID of entity_01

    Verify that using an ambiguous identifier gives precedence to the ID interpretation
    Appending the special ambiguity breaker character will force the identifier to be treated as a LABEL
    """
    entity_01, entity_02, _ = setup_computers
    identifier = f'{entity_02.label}'
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid

    identifier = f'{entity_02.label}{OrmEntityLoader.label_ambiguity_breaker}'
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_02.uuid


def test_ambiguous_label_uuid(setup_computers, parameter_type):
    """Situation: LABEL of entity_03 is exactly equal to UUID of entity_01

    Verify that using an ambiguous identifier gives precedence to the UUID interpretation
    Appending the special ambiguity breaker character will force the identifier to be treated as a LABEL
    """
    entity_01, _, entity_03 = setup_computers
    identifier = f'{entity_03.label}'
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid

    identifier = f'{entity_03.label}{OrmEntityLoader.label_ambiguity_breaker}'
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_03.uuid


def test_mpirun_command_param_type_ctx_none():
    """Test that `MpirunCommandParamType.convert` raises BadParameter when `ctx` is None."""
    param_type = MpirunCommandParamType()
    with pytest.raises(click.BadParameter, match='Scheduler not specified for this computer!'):
        param_type.convert('mpirun -np {tot_num_mpiprocs}', None, None)


def test_mpirun_command_param_type_ctx_missing_scheduler():
    """Test that `MpirunCommandParamType.convert` raises BadParameter when `ctx.params` lacks 'scheduler'."""
    param_type = MpirunCommandParamType()
    ctx = click.Context(click.Command('test'))
    ctx.params = {}
    with pytest.raises(click.BadParameter, match='Scheduler not specified for this computer!'):
        param_type.convert('mpirun -np {tot_num_mpiprocs}', None, ctx)


def test_mpirun_command_param_type_valid_ctx():
    """Test `MpirunCommandParamType.convert` with a valid scheduler context."""
    from aiida.plugins.entry_point import get_entry_point_from_string

    param_type = MpirunCommandParamType()
    ctx = click.Context(click.Command('test'))
    ctx.params = {'scheduler': get_entry_point_from_string('aiida.schedulers:core.direct')}

    # Valid command with known replacement field
    result = param_type.convert('mpirun -np {tot_num_mpiprocs}', None, ctx)
    assert result == 'mpirun -np {tot_num_mpiprocs}'

    # Invalid command with unknown replacement field
    with pytest.raises(click.BadParameter, match="In workdir there is an unknown replacement field 'unknown_field'"):
        param_type.convert('mpirun -np {unknown_field}', None, ctx)

    # Malformed format string
    with pytest.raises(click.BadParameter, match='Error in the string'):
        param_type.convert('mpirun -np {unclosed', None, ctx)
