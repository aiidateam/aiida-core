###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for working out the type of a port from the annotation of a parameter."""

from __future__ import annotations

from enum import Enum

import pytest

from aiida.engine import Many
from aiida.engine.processes.containers import fields_of, is_a_plain_class
from aiida.engine.processes.ports import as_written, infer_valid_type_from_type_annotation
from aiida.orm import Data, Int, Str


class Spin(Enum):
    UP = 'up'


@pytest.mark.parametrize('annotation', [int, str, Data, Spin])
def test_a_class_is_a_plain_class(annotation):
    """What a port takes is read off a class, so the plain ones have to be recognised as such."""
    assert is_a_plain_class(annotation)


@pytest.mark.parametrize('annotation', [Many[int], list[int], dict[str, int]])
def test_a_class_with_type_arguments_is_not(annotation):
    """`issubclass` refuses one, and Python 3.10 calls it a class where later versions do not."""
    assert not is_a_plain_class(annotation)


@pytest.mark.parametrize(
    ('annotation', 'expected'),
    [(int, (Int,)), (str, (Str,)), (Many[int], ()), (list[int], ())],
    ids=['int', 'str', 'many', 'list'],
)
def test_what_a_port_takes_is_read_off_the_annotation(annotation, expected):
    """A parameter taking many values declares a namespace, so no single type is inferred for it."""
    assert infer_valid_type_from_type_annotation(annotation) == expected


@pytest.mark.parametrize('annotation', [Many[int], list[int]])
def test_a_class_with_type_arguments_reaches_a_function_as_it_was_given(annotation):
    """What a fan-out produced arrives as a mapping, and `as_written` has to hand it over rather than raise."""
    assert as_written(annotation, {'item_0': Int(1)}) == {'item_0': 1}


@pytest.mark.parametrize('annotation', [Many[int], list[int]])
def test_a_class_with_type_arguments_holds_no_fields(annotation):
    """A container names its fields; a subscripted class is not one, and asking must not raise."""
    assert fields_of(annotation) is None
