###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :class:`aiida.orm.nodes.data.datetime.DateTimeData`."""

import datetime

import pytest

from aiida import orm
from aiida.orm import DateTimeData, load_node


def test_value_roundtrip():
    value = datetime.datetime(2026, 7, 22, 13, 30, 15)
    node = DateTimeData(value).store()
    assert load_node(node.pk).value == value


def test_to_aiida_type_dispatches_datetime():
    value = datetime.datetime.now()
    node = orm.to_aiida_type(value)
    assert isinstance(node, DateTimeData)
    assert node.value == value


def test_invalid_type_raises():
    with pytest.raises(TypeError, match='expected a datetime.datetime'):
        DateTimeData('2026-07-22')


def test_str():
    value = datetime.datetime(2026, 7, 22)
    assert str(DateTimeData(value)) == str(value)
