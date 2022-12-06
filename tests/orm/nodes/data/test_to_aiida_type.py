# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test the :meth:`aiida.orm.data.base.to_aiida_type` serializer."""
import pytest

from aiida import orm
from aiida.common.links import LinkType


#yapf: disable
@pytest.mark.usefixtures('aiida_profile')
@pytest.mark.parametrize(
    'expected_type, value', (
        (orm.Bool, True),
        (orm.Dict, {'foo': 'bar'}),
        (orm.Float, 5.0),
        (orm.Int, 5),
        (orm.List, [0, 1, 2]),
        (orm.Str, 'test-string'),
        (orm.EnumData, LinkType.RETURN),
    )
)
# yapf: enable
def test_to_aiida_type(expected_type, value):
    """Test the ``to_aiida_type`` dispatch."""
    converted = orm.to_aiida_type(value)
    assert isinstance(converted, expected_type)
    assert converted == value
