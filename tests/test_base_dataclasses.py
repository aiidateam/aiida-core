# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=no-self-use
"""Tests for AiiDA base data classes."""
import operator

import pytest

from aiida.common.exceptions import ModificationNotAllowed
from aiida.orm import load_node, List, Bool, Float, Int, Str, NumericType
from aiida.orm.nodes.data.bool import get_true_node, get_false_node


@pytest.mark.usefixtures('clear_database_before_test_class')
class TestList:
    """Test AiiDA List class."""

    def test_creation(self):
        node = List()
        assert len(node) == 0
        with pytest.raises(IndexError):
            node[0]  # pylint: disable=pointless-statement

    def test_append(self):
        """Test append() member function."""

        def do_checks(node):
            assert len(node) == 1
            assert node[0] == 4

        node = List()
        node.append(4)
        do_checks(node)

        # Try the same after storing
        node = List()
        node.append(4)
        node.store()
        do_checks(node)

    def test_extend(self):
        """Test extend() member function."""
        lst = [1, 2, 3]

        def do_checks(node):
            assert len(node) == len(lst)
            # Do an element wise comparison
            for lst_, node_ in zip(lst, node):
                assert lst_ == node_

        node = List()
        node.extend(lst)
        do_checks(node)
        # Further extend
        node.extend(lst)
        assert len(node) == len(lst) * 2

        # Do an element wise comparison
        for i, _ in enumerate(lst):
            assert lst[i] == node[i]
            assert lst[i] == node[i % len(lst)]

        # Now try after storing
        node = List()
        node.extend(lst)
        node.store()
        do_checks(node)

    def test_mutability(self):
        """Test list's mutability before and after storage."""
        node = List()
        node.append(5)
        node.store()

        # Test all mutable calls are now disallowed
        with pytest.raises(ModificationNotAllowed):
            node.append(5)
        with pytest.raises(ModificationNotAllowed):
            node.extend([5])
        with pytest.raises(ModificationNotAllowed):
            node.insert(0, 2)
        with pytest.raises(ModificationNotAllowed):
            node.remove(0)
        with pytest.raises(ModificationNotAllowed):
            node.pop()
        with pytest.raises(ModificationNotAllowed):
            node.sort()
        with pytest.raises(ModificationNotAllowed):
            node.reverse()

    @staticmethod
    def test_store_load():
        """Test load_node on just stored object."""
        node = List(list=[1, 2, 3])
        node.store()

        node_loaded = load_node(node.pk)
        assert node.get_list() == node_loaded.get_list()


@pytest.mark.usefixtures('clear_database_before_test_class')
class TestFloat:
    """Test Float class."""

    def setup_method(self):
        # pylint: disable=attribute-defined-outside-init
        self.value = Float()
        self.all_types = [Int, Float, Bool, Str]

    def test_create(self):
        """Creating basic data objects."""
        term_a = Float()
        # Check that initial value is zero
        assert round(abs(term_a.value - 0.0), 7) == 0

        float_ = Float(6.0)
        assert round(abs(float_.value - 6.), 7) == 0
        assert round(abs(float_ - Float(6.0)), 7) == 0

        int_ = Int()
        assert round(abs(int_.value - 0), 7) == 0
        int_ = Int(6)
        assert round(abs(int_.value - 6), 7) == 0
        assert round(abs(float_ - int_), 7) == 0

        bool_ = Bool()
        assert round(abs(bool_.value - False), 7) == 0
        bool_ = Bool(False)
        assert bool_.value is False
        assert bool_.value == get_false_node()
        bool_ = Bool(True)
        assert bool_.value is True
        assert bool_.value == get_true_node()

        str_ = Str()
        assert str_.value == ''
        str_ = Str('Hello')
        assert str_.value == 'Hello'

    def test_load(self):
        """Test object loading."""
        for typ in self.all_types:
            node = typ()
            node.store()
            loaded = load_node(node.pk)
            assert node == loaded

    def test_add(self):
        """Test addition."""
        term_a = Float(4)
        term_b = Float(5)
        # Check adding two db Floats
        res = term_a + term_b
        assert isinstance(res, NumericType)
        assert round(abs(res - 9.0), 7) == 0

        # Check adding db Float and native (both ways)
        res = term_a + 5.0
        assert isinstance(res, NumericType)
        assert round(abs(res - 9.0), 7) == 0

        res = 5.0 + term_a
        assert isinstance(res, NumericType)
        assert round(abs(res - 9.0), 7) == 0

        # Inplace
        term_a = Float(4)
        term_a += term_b
        assert round(abs(term_a - 9.0), 7) == 0

        term_a = Float(4)
        term_a += 5
        assert round(abs(term_a - 9.0), 7) == 0

    def test_mul(self):
        """Test floats multiplication."""
        term_a = Float(4)
        term_b = Float(5)
        # Check adding two db Floats
        res = term_a * term_b
        assert isinstance(res, NumericType)
        assert round(abs(res - 20.0), 7) == 0

        # Check adding db Float and native (both ways)
        res = term_a * 5.0
        assert isinstance(res, NumericType)
        assert round(abs(res - 20), 7) == 0

        res = 5.0 * term_a
        assert isinstance(res, NumericType)
        assert round(abs(res - 20.0), 7) == 0

        # Inplace
        term_a = Float(4)
        term_a *= term_b
        assert round(abs(term_a - 20), 7) == 0

        term_a = Float(4)
        term_a *= 5
        assert round(abs(term_a - 20), 7) == 0

    def test_power(self):
        """Test power operator."""
        term_a = Float(4)
        term_b = Float(2)

        res = term_a**term_b
        assert round(abs(res.value - 16.), 7) == 0

    def test_division(self):
        """Test the normal division operator."""
        term_a = Float(3)
        term_b = Float(2)

        assert round(abs(term_a / term_b - 1.5), 7) == 0
        assert isinstance(term_a / term_b, Float)

    def test_division_integer(self):
        """Test the integer division operator."""
        term_a = Float(3)
        term_b = Float(2)

        assert round(abs(term_a // term_b - 1.0), 7) == 0
        assert isinstance(term_a // term_b, Float)

    def test_modulus(self):
        """Test modulus operator."""
        term_a = Float(12.0)
        term_b = Float(10.0)

        assert round(abs(term_a % term_b - 2.0), 7) == 0
        assert isinstance(term_a % term_b, NumericType)
        assert round(abs(term_a % 10.0 - 2.0), 7) == 0
        assert isinstance(term_a % 10.0, NumericType)
        assert round(abs(12.0 % term_b - 2.0), 7) == 0
        assert isinstance(12.0 % term_b, NumericType)


@pytest.mark.usefixtures('clear_database_before_test_class')
class TestFloatIntMix:
    """Test operations between Int and Float objects."""

    def test_operator(self):
        """Test all binary operators."""
        term_a = Float(2.2)
        term_b = Int(3)

        for oper in [
            operator.add, operator.mul, operator.pow, operator.lt, operator.le, operator.gt, operator.ge, operator.iadd,
            operator.imul
        ]:
            for term_x, term_y in [(term_a, term_b), (term_b, term_a)]:
                res = oper(term_x, term_y)
                c_val = oper(term_x.value, term_y.value)
                assert res._type == type(c_val)  # pylint: disable=protected-access
                assert res == oper(term_x.value, term_y.value)


@pytest.mark.usefixtures('clear_database_before_test_class')
class TestInt:
    """Test Int class."""

    def test_division(self):
        """Test the normal division operator."""
        term_a = Int(3)
        term_b = Int(2)

        assert round(abs(term_a / term_b - 1.5), 7) == 0
        assert isinstance(term_a / term_b, Float)

    def test_division_integer(self):
        """Test the integer division operator."""
        term_a = Int(3)
        term_b = Int(2)

        assert round(abs(term_a // term_b - 1), 7) == 0
        assert isinstance(term_a // term_b, Int)

    def test_modulo(self):
        """Test modulus operation."""
        term_a = Int(12)
        term_b = Int(10)

        assert term_a % term_b == 2
        assert isinstance(term_a % term_b, NumericType)
        assert term_a % 10 == 2
        assert isinstance(term_a % 10, NumericType)
        assert 12 % term_b == 2
        assert isinstance(12 % term_b, NumericType)
