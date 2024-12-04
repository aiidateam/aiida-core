###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `GroupParamType`."""

import uuid

import click
import pytest

from aiida.cmdline.params.types import GroupParamType
from aiida.orm import AutoGroup, Group, ImportGroup
from aiida.orm.utils.loaders import OrmEntityLoader


@pytest.fixture
def parameter_type():
    """Return an instance of the `GroupParamType`."""
    return GroupParamType()


@pytest.fixture
def setup_groups():
    """Create some groups to test the `GroupParamType` parameter type for the command line infrastructure.

    We create an initial group with a random name and then on purpose create two groups with a name that matches exactly
    the ID and UUID, respectively, of the first one. This allows us to test the rules implemented to solve ambiguities
    that arise when determing the identifier type.
    """
    entity_01 = Group(label=f'group-{uuid.uuid4()}').store()
    entity_02 = AutoGroup(label=str(entity_01.pk)).store()
    entity_03 = ImportGroup(label=str(entity_01.uuid)).store()
    return entity_01, entity_02, entity_03


def test_get_by_id(setup_groups, parameter_type):
    """Verify that using the ID will retrieve the correct entity."""
    entity_01, entity_02, entity_03 = setup_groups
    identifier = f'{entity_01.pk}'
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid


def test_get_by_uuid(setup_groups, parameter_type):
    """Verify that using the UUID will retrieve the correct entity."""
    entity_01, entity_02, entity_03 = setup_groups
    identifier = f'{entity_01.uuid}'
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid


def test_get_by_label(setup_groups, parameter_type):
    """Verify that using the LABEL will retrieve the correct entity."""
    entity_01, entity_02, entity_03 = setup_groups
    identifier = f'{entity_01.label}'
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid


def test_ambiguous_label_pk(setup_groups, parameter_type):
    """Situation: LABEL of entity_02 is exactly equal to ID of entity_01.

    Verify that using an ambiguous identifier gives precedence to the ID interpretation. Appending the special ambiguity
    breaker character will force the identifier to be treated as a LABEL.
    """
    entity_01, entity_02, entity_03 = setup_groups
    identifier = f'{entity_02.label}'
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid

    identifier = f'{entity_02.label}{OrmEntityLoader.label_ambiguity_breaker}'
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_02.uuid


def test_ambiguous_label_uuid(setup_groups, parameter_type):
    """Situation: LABEL of entity_03 is exactly equal to UUID of entity_01.

    Verify that using an ambiguous identifier gives precedence to the UUID interpretation. Appending the special
    ambiguity breaker character will force the identifier to be treated as a LABEL.
    """
    entity_01, entity_02, entity_03 = setup_groups
    identifier = f'{entity_03.label}'
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_01.uuid

    identifier = f'{entity_03.label}{OrmEntityLoader.label_ambiguity_breaker}'
    result = parameter_type.convert(identifier, None, None)
    assert result.uuid == entity_03.uuid


def test_create_if_not_exist():
    """Test the `create_if_not_exist` constructor argument."""
    label = 'non-existing-label-01'
    parameter_type = GroupParamType(create_if_not_exist=True)
    result = parameter_type.convert(label, None, None)
    assert isinstance(result, Group)
    assert result.is_stored

    label = 'non-existing-label-02'
    parameter_type = GroupParamType(create_if_not_exist=True, sub_classes=('aiida.groups:core.auto',))
    result = parameter_type.convert(label, None, None)
    assert isinstance(result, AutoGroup)

    # Specifying more than one subclass when `create_if_not_exist=True` is not allowed.
    with pytest.raises(ValueError):
        GroupParamType(create_if_not_exist=True, sub_classes=('aiida.groups:core.auto', 'aiida.groups:core.import'))


@pytest.mark.parametrize(
    ('sub_classes', 'expected'),
    (
        (None, (True, True, True)),
        (('aiida.groups:core.auto',), (False, True, False)),
        (('aiida.groups:core.auto', 'aiida.groups:core.import'), (False, True, True)),
    ),
)
def test_sub_classes(setup_groups, sub_classes, expected):
    """Test the `sub_classes` constructor argument."""
    entity_01, entity_02, entity_03 = setup_groups
    parameter_type = GroupParamType(sub_classes=sub_classes)

    results = []

    for group in [entity_01, entity_02, entity_03]:
        try:
            parameter_type.convert(str(group.pk), None, None)
        except click.BadParameter:
            results.append(False)
        else:
            results.append(True)

    assert tuple(results) == expected


@pytest.mark.usefixtures('aiida_profile_clean')
def test_shell_complete(setup_groups, parameter_type):
    """Test the `shell_complete` method that provides auto-complete functionality."""
    entity_01, entity_02, entity_03 = setup_groups
    entity_04 = Group(label='xavier').store()

    options = [item.value for item in parameter_type.shell_complete(None, None, '')]
    assert sorted(options) == sorted([entity_01.label, entity_02.label, entity_03.label, entity_04.label])

    options = [item.value for item in parameter_type.shell_complete(None, None, 'xa')]
    assert sorted(options) == sorted([entity_04.label])
