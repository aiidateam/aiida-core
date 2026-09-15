###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for a task taking an enum member."""

from __future__ import annotations

from enum import Enum

import pytest
from pydantic import BaseModel

from aiida.engine import run_get_node, task
from aiida.orm import EnumData


class Spin(str, Enum):
    """An enum mixed with ``str``, which is how one is usually written."""

    NONE = 'none'
    COLLINEAR = 'collinear'


class Plain(Enum):
    """And one that is not, so that both ways of writing it are covered."""

    FAST = 1
    SLOW = 2


class Settings(BaseModel):
    spin: Spin = Spin.NONE
    mode: Plain = Plain.FAST


@task(outputs=['seen'])
def reads_a_member(spin: Spin) -> str:
    return f'{type(spin).__name__}/{spin.value}'


@task(outputs=['seen'])
def reads_a_container(given: Settings) -> str:
    return f'{given.spin.value}/{given.mode.value}'


@pytest.mark.parametrize('member', (Spin.COLLINEAR, Plain.SLOW), ids=('mixed-in', 'plain'))
def test_a_member_is_stored_as_the_enum_it_belongs_to(member):
    """`to_aiida_type` dispatches on the type, so a member of a `str` enum would be stored as its `str()`."""
    results, node = run_get_node(reads_a_member, spin=member)

    assert isinstance(node.inputs.spin, EnumData)
    assert node.inputs.spin.get_member() is member
    assert results['seen'] == f'{type(member).__name__}/{member.value}'


def test_a_container_field_holds_a_member():
    """A field of a container is a port like any other, so it keeps the enum the same way."""
    results, node = run_get_node(reads_a_container, given={'spin': Spin.COLLINEAR, 'mode': Plain.SLOW})

    assert isinstance(node.inputs.given.spin, EnumData)
    assert results['seen'] == 'collinear/2'
