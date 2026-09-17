###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test the :meth:`aiida.orm.data.base.to_aiida_type` serializer."""

from enum import Enum, IntEnum

import numpy
import pytest

from aiida import orm
from aiida.common.links import LinkType


@pytest.mark.parametrize(
    'expected_type, value',
    (
        (orm.Bool, True),
        (orm.Dict, {'foo': 'bar'}),
        (orm.Float, 5.0),
        (orm.Int, 5),
        (orm.List, [0, 1, 2]),
        (orm.Str, 'test-string'),
        (orm.EnumData, LinkType.RETURN),
        (orm.ArrayData, numpy.array([[0, 0, 0], [1, 1, 1]])),
    ),
)
def test_to_aiida_type(expected_type, value):
    """Test the ``to_aiida_type`` dispatch."""
    converted = orm.to_aiida_type(value)
    assert isinstance(converted, expected_type)
    if expected_type is orm.ArrayData:
        assert converted.get_array().all() == value.all()
    else:
        assert converted == value


class Spin(str, Enum):
    """An enum with a ``str`` mixin."""

    COLLINEAR = 'collinear'


class Mode(IntEnum):
    """An enum with an ``int`` mixin."""

    FAST = 1


@pytest.mark.parametrize(
    'member',
    (
        pytest.param(Spin.COLLINEAR, id='str-mixin'),
        pytest.param(Mode.FAST, id='int-enum'),
        pytest.param(LinkType.RETURN, id='plain'),
    ),
)
def test_member_keeps_the_enum_it_belongs_to(member):
    """Dispatch resolves by method resolution order, so a mixin would be stored as the type it is mixed with."""
    node = orm.to_aiida_type(member)

    assert isinstance(node, orm.EnumData)
    assert node.get_member() is member


class Custom:
    """A plain class only this test knows how to store."""


class CustomEnum(Enum):
    """An enum only this test knows how to store."""

    SOLE = 1


@pytest.mark.parametrize(
    'value',
    (pytest.param(Custom(), id='plain-class'), pytest.param(CustomEnum.SOLE, id='enum')),
)
def test_registered_conversion_is_still_reached(value):
    """Conversions are declared with ``to_aiida_type.register``, here and in every plugin that adds one.

    A registration for the enum itself is more specific than the one for ``Enum``, so it keeps its say.
    """

    @orm.to_aiida_type.register(type(value))
    def _(_):
        return orm.Str('custom')

    assert orm.to_aiida_type(value).value == 'custom'
