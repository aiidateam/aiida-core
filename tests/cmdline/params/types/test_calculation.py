###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `CalculationParamType`."""

import uuid

import pytest

from aiida.cmdline.params.types import CalculationParamType
from aiida.orm import CalculationNode
from aiida.orm.utils.loaders import OrmEntityLoader


@pytest.fixture(scope='module')
def entities():
    """Create three ``CalculationNode``s."""
    entity_01 = CalculationNode().store()
    entity_02 = CalculationNode().store()
    entity_03 = CalculationNode().store()

    entity_01.label = f'calculation-{uuid.uuid4().hex}'
    entity_02.label = str(entity_01.pk)
    entity_03.label = str(entity_01.uuid)

    return entity_01, entity_02, entity_03


def test_get_by_id(entities):
    """Verify that using the ID will retrieve the correct entity."""
    entity_01, entity_02, entity_03 = entities
    identifier = str(entity_01.pk)
    result = CalculationParamType().convert(identifier, None, None)
    assert result.uuid == entity_01.uuid


def test_get_by_uuid(entities):
    """Verify that using the UUID will retrieve the correct entity."""
    entity_01, entity_02, entity_03 = entities
    identifier = str(entity_01.uuid)
    result = CalculationParamType().convert(identifier, None, None)
    assert result.uuid == entity_01.uuid


def test_get_by_label(entities):
    """Verify that using the LABEL will retrieve the correct entity."""
    entity_01, entity_02, entity_03 = entities
    identifier = str(entity_01.label)
    result = CalculationParamType().convert(identifier, None, None)
    assert result.uuid == entity_01.uuid


def test_ambiguous_label_pk(entities):
    """Situation: LABEL of entity_02 is exactly equal to ID of entity_01

    Verify that using an ambiguous identifier gives precedence to the ID interpretation
    Appending the special ambiguity breaker character will force the identifier to be treated as a LABEL
    """
    entity_01, entity_02, entity_03 = entities
    identifier = str(entity_02.label)
    result = CalculationParamType().convert(identifier, None, None)
    assert result.uuid == entity_01.uuid

    identifier = f'{entity_02.label}{OrmEntityLoader.label_ambiguity_breaker}'
    result = CalculationParamType().convert(identifier, None, None)
    assert result.uuid == entity_02.uuid


def test_ambiguous_label_uuid(entities):
    """Situation: LABEL of entity_03 is exactly equal to UUID of entity_01

    Verify that using an ambiguous identifier gives precedence to the UUID interpretation
    Appending the special ambiguity breaker character will force the identifier to be treated as a LABEL
    """
    entity_01, entity_02, entity_03 = entities
    identifier = str(entity_03.label)
    result = CalculationParamType().convert(identifier, None, None)
    assert result.uuid == entity_01.uuid

    identifier = f'{entity_03.label}{OrmEntityLoader.label_ambiguity_breaker}'
    result = CalculationParamType().convert(identifier, None, None)
    assert result.uuid == entity_03.uuid
