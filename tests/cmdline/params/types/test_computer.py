# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name
"""Tests for the `ComputerParamType`."""
import pytest

from aiida import orm
from aiida.cmdline.params.types import ComputerParamType
from aiida.orm.utils.loaders import OrmEntityLoader


@pytest.fixture
def parameter_type():
    """Return an instance of the `ComputerParamType`."""
    return ComputerParamType()


@pytest.fixture
def setup_computers(clear_database_before_test):  # pylint: disable=unused-argument
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
        'workdir': '/tmp/aiida'
    }

    entity_01 = orm.Computer(label='computer_01', **kwargs).store()
    entity_02 = orm.Computer(label=str(entity_01.pk), **kwargs).store()
    entity_03 = orm.Computer(label=str(entity_01.uuid), **kwargs).store()

    return entity_01, entity_02, entity_03


def test_complete(setup_computers, parameter_type):
    """Test the `complete` method that provides auto-complete functionality."""
    kwargs = {
        'hostname': 'localhost',
        'transport_type': 'core.local',
        'scheduler_type': 'core.direct',
        'workdir': '/tmp/aiida'
    }
    entity_01, entity_02, entity_03 = setup_computers
    entity_04 = orm.Computer(label='xavier', **kwargs).store()

    options = [item[0] for item in parameter_type.complete(None, '')]
    assert sorted(options) == sorted([entity_01.label, entity_02.label, entity_03.label, entity_04.label])

    options = [item[0] for item in parameter_type.complete(None, 'xa')]
    assert sorted(options) == sorted([entity_04.label])


def test_get_by_id(setup_computers, parameter_type):
    """
    Verify that using the ID will retrieve the correct entity
    """
    entity_01, _, _ = setup_computers
    identifier = f'{entity_01.pk}'
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid


def test_get_by_uuid(setup_computers, parameter_type):
    """
    Verify that using the UUID will retrieve the correct entity
    """
    entity_01, _, _ = setup_computers
    identifier = f'{entity_01.uuid}'
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid


def test_get_by_label(setup_computers, parameter_type):
    """
    Verify that using the LABEL will retrieve the correct entity
    """
    entity_01, _, _ = setup_computers
    identifier = f'{entity_01.label}'
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid


def test_ambiguous_label_pk(setup_computers, parameter_type):
    """
    Situation: LABEL of entity_02 is exactly equal to ID of entity_01

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
    """
    Situation: LABEL of entity_03 is exactly equal to UUID of entity_01

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
