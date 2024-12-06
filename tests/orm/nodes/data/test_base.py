###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :class:`aiida.orm.nodes.data.base.BaseType` classes."""

import operator

import pytest

from aiida.orm import Bool, Float, Int, NumericType, Str, load_node


@pytest.mark.parametrize(
    'node_type, default, value',
    [
        (Bool, False, True),
        (Int, 0, 5),
        (Float, 0.0, 5.5),
        (Str, '', 'a'),
    ],
)
def test_create(node_type, default, value):
    """Test the creation of the ``BaseType`` nodes."""
    node = node_type()
    assert node.value == default

    node = node_type(value)
    assert node.value == value


@pytest.mark.parametrize('node_type', [Bool, Float, Int, Str])
def test_store_load(node_type):
    """Test ``BaseType`` node storing and loading."""
    node = node_type()
    node.store()
    loaded = load_node(node.pk)
    assert node.value == loaded.value


def test_modulo():
    """Test ``Int`` modulus operation."""
    term_a = Int(12)
    term_b = Int(10)

    assert term_a % term_b == 2
    assert isinstance(term_a % term_b, NumericType)
    assert term_a % 10 == 2
    assert isinstance(term_a % 10, NumericType)
    assert 12 % term_b == 2
    assert isinstance(12 % term_b, NumericType)


@pytest.mark.parametrize(
    'node_type, a, b',
    [
        (Int, 3, 5),
        (Float, 1.2, 5.5),
    ],
)
def test_add(node_type, a, b):
    """Test addition for ``Int`` and ``Float`` nodes."""
    node_a = node_type(a)
    node_b = node_type(b)

    result = node_a + node_b
    assert isinstance(result, node_type)
    assert result.value == a + b

    # Node and native (both ways)
    result = node_a + b
    assert isinstance(result, node_type)
    assert result.value == a + b

    result = a + node_b
    assert isinstance(result, node_type)
    assert result.value == a + b

    # Inplace
    result = node_type(a)
    result += node_b
    assert isinstance(result, node_type)
    assert result.value == a + b


@pytest.mark.parametrize(
    'node_type, a, b',
    [
        (Int, 3, 5),
        (Float, 1.2, 5.5),
    ],
)
def test_multiplication(node_type, a, b):
    """Test floats multiplication."""
    node_a = node_type(a)
    node_b = node_type(b)

    # Check multiplication
    result = node_a * node_b
    assert isinstance(result, node_type)
    assert result.value == a * b

    # Check multiplication Node and native (both ways)
    result = node_a * b
    assert isinstance(result, node_type)
    assert result.value == a * b

    result = a * node_b
    assert isinstance(result, node_type)
    assert result.value == a * b

    # Inplace
    result = node_type(a)
    result *= node_b
    assert isinstance(result, node_type)
    assert result.value == a * b


@pytest.mark.parametrize(
    'node_type, a, b',
    [
        (Int, 3, 5),
        (Float, 1.2, 5.5),
    ],
)
def test_division(node_type, a, b):
    """Test the ``BaseType`` normal division operator."""
    node_a = node_type(a)
    node_b = node_type(b)

    result = node_a / node_b
    assert result == a / b
    assert isinstance(result, Float)  # Should be a `Float` for both node types


@pytest.mark.parametrize(
    'node_type, a, b',
    [
        (Int, 3, 5),
        (Float, 1.2, 5.5),
    ],
)
def test_division_integer(node_type, a, b):
    """Test the ``Int`` integer division operator."""
    node_a = node_type(a)
    node_b = node_type(b)

    result = node_a // node_b
    assert result == a // b
    assert isinstance(result, node_type)


@pytest.mark.parametrize(
    'node_type, base, power',
    [
        (Int, 5, 2),
        (Float, 3.5, 3),
    ],
)
def test_power(node_type, base, power):
    """Test power operator."""
    node_base = node_type(base)
    node_power = node_type(power)

    result = node_base**node_power
    assert result == base**power
    assert isinstance(result, node_type)


@pytest.mark.parametrize(
    'node_type, a, b',
    [
        (Int, 5, 2),
        (Float, 3.5, 3),
    ],
)
def test_modulus(node_type, a, b):
    """Test modulus operator."""
    node_a = node_type(a)
    node_b = node_type(b)

    assert node_a % node_b == a % b
    assert isinstance(node_a % node_b, node_type)

    assert node_a % b == a % b
    assert isinstance(node_a % b, node_type)

    assert a % node_b == a % b
    assert isinstance(a % node_b, node_type)


@pytest.mark.parametrize(
    'opera',
    [
        operator.add,
        operator.mul,
        operator.pow,
        operator.lt,
        operator.le,
        operator.gt,
        operator.ge,
        operator.iadd,
        operator.imul,
    ],
)
def test_operator(opera):
    """Test operations between Int and Float objects."""
    node_a = Float(2.2)
    node_b = Int(3)

    for node_x, node_y in [(node_a, node_b), (node_b, node_a)]:
        res = opera(node_x, node_y)
        c_val = opera(node_x.value, node_y.value)
        assert res._type is type(c_val)
        assert res == opera(node_x.value, node_y.value)


@pytest.mark.parametrize(
    'node_type, a, b',
    [
        (Bool, False, True),
        (Int, 2, 5),
        (Float, 2.5, 5.5),
        (Str, 'a', 'b'),
    ],
)
def test_equality(node_type, a, b):
    """Test equality comparison for the base types."""
    node_a = node_type(a)
    node_a_clone = node_type(a)
    node_b = node_type(b)

    # Test equality comparison with Python base types
    assert node_a == a
    assert node_a != b

    # Test equality comparison with other `BaseType` nodes
    assert node_a == node_a_clone
    assert node_a != node_b


@pytest.mark.parametrize('numeric_type', (Float, Int))
def test_unary_pos(numeric_type):
    """Test the ``__pos__`` unary operator for all ``NumericType`` subclasses."""
    node_positive = numeric_type(1)
    node_negative = numeric_type(-1)

    assert +node_positive == node_positive
    assert +node_negative == node_negative


@pytest.mark.parametrize('numeric_type', (Float, Int))
def test_unary_neg(numeric_type):
    """Test the ``__neg__`` unary operator for all ``NumericType`` subclasses."""
    node_positive = numeric_type(1)
    node_negative = numeric_type(-1)

    assert -node_positive != node_positive
    assert -node_negative != node_negative
    assert -node_positive == node_negative
    assert -node_negative == node_positive
    assert -node_negative == node_positive


@pytest.mark.parametrize('numeric_type', (Float, Int))
def test_unary_abs(numeric_type):
    """Test the ``__abs__`` unary operator for all ``NumericType`` subclasses"""
    node_positive = numeric_type(1)
    node_negative = numeric_type(-1)

    # Test positive number
    abs_positive = abs(node_positive)
    assert abs_positive == node_positive

    # Test negative number
    abs_negative = abs(node_negative)
    assert abs_negative != node_negative
    assert abs_positive == abs_negative
