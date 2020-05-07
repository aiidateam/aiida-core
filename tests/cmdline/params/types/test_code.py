# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name,unused-variable,unused-argument
"""Tests for the `CodeParamType`."""
import click
import pytest

from aiida.cmdline.params.types import CodeParamType
from aiida.orm import Code
from aiida.orm.utils.loaders import OrmEntityLoader


@pytest.fixture
def parameter_type():
    """Return an instance of the `CodeParamType`."""
    return CodeParamType()


@pytest.fixture
def setup_codes(clear_database_before_test, aiida_localhost):
    """Create some `Code` instances to test the `CodeParamType` parameter type for the command line infrastructure.

    We create an initial code with a random name and then on purpose create two code with a name that matches exactly
    the ID and UUID, respectively, of the first one. This allows us to test the rules implemented to solve ambiguities
    that arise when determing the identifier type.
    """
    entity_01 = Code(remote_computer_exec=(aiida_localhost, '/bin/true')).store()
    entity_02 = Code(remote_computer_exec=(aiida_localhost, '/bin/true'), input_plugin_name='arithmetic.add').store()
    entity_03 = Code(remote_computer_exec=(aiida_localhost, '/bin/true'), input_plugin_name='templatereplacer').store()

    entity_01.label = 'computer_01'
    entity_02.label = str(entity_01.pk)
    entity_03.label = str(entity_01.uuid)

    return entity_01, entity_02, entity_03


def test_get_by_id(setup_codes, parameter_type):
    """Verify that using the ID will retrieve the correct entity."""
    entity_01, entity_02, entity_03 = setup_codes
    identifier = '{}'.format(entity_01.pk)
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid


def test_get_by_uuid(setup_codes, parameter_type):
    """Verify that using the UUID will retrieve the correct entity."""
    entity_01, entity_02, entity_03 = setup_codes
    identifier = '{}'.format(entity_01.uuid)
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid


def test_get_by_label(setup_codes, parameter_type):
    """Verify that using the LABEL will retrieve the correct entity."""
    entity_01, entity_02, entity_03 = setup_codes
    identifier = '{}'.format(entity_01.label)
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid


def test_get_by_fullname(setup_codes, parameter_type):
    """Verify that using the LABEL@machinename will retrieve the correct entity."""
    entity_01, entity_02, entity_03 = setup_codes
    identifier = '{}@{}'.format(entity_01.label, entity_01.computer.name)
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid


def test_ambiguous_label_pk(setup_codes, parameter_type):
    """Situation: LABEL of entity_02 is exactly equal to ID of entity_01.

    Verify that using an ambiguous identifier gives precedence to the ID interpretation
    Appending the special ambiguity breaker character will force the identifier to be treated as a LABEL
    """
    entity_01, entity_02, entity_03 = setup_codes
    identifier = '{}'.format(entity_02.label)
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid

    identifier = '{}{}'.format(entity_02.label, OrmEntityLoader.label_ambiguity_breaker)
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_02.uuid


def test_ambiguous_label_uuid(setup_codes, parameter_type):
    """Situation: LABEL of entity_03 is exactly equal to UUID of entity_01.

    Verify that using an ambiguous identifier gives precedence to the UUID interpretation
    Appending the special ambiguity breaker character will force the identifier to be treated as a LABEL
    """
    entity_01, entity_02, entity_03 = setup_codes
    identifier = '{}'.format(entity_03.label)
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid

    identifier = '{}{}'.format(entity_03.label, OrmEntityLoader.label_ambiguity_breaker)
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_03.uuid


def test_entry_point_validation(setup_codes):
    """Verify that when an `entry_point` is defined in the constructor, it is respected in the validation."""
    entity_01, entity_02, entity_03 = setup_codes
    parameter_type = CodeParamType(entry_point='arithmetic.add')
    identifier = '{}'.format(entity_02.pk)
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_02.uuid

    with pytest.raises(click.BadParameter):
        identifier = '{}'.format(entity_03.pk)
        result = parameter_type.convert(identifier, None, None)


def test_complete(setup_codes, parameter_type, aiida_localhost):
    """Test the `complete` method that provides auto-complete functionality."""
    entity_01, entity_02, entity_03 = setup_codes
    entity_04 = Code(label='xavier', remote_computer_exec=(aiida_localhost, '/bin/true')).store()

    options = [item[0] for item in parameter_type.complete(None, '')]
    assert sorted(options) == sorted([entity_01.label, entity_02.label, entity_03.label, entity_04.label])

    options = [item[0] for item in parameter_type.complete(None, 'xa')]
    assert sorted(options) == sorted([entity_04.label])
