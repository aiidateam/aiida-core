# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name
"""Tests for :class:`aiida.orm.nodes.data.list.List` class."""
import pytest

from aiida.common.exceptions import ModificationNotAllowed
from aiida.orm import List, load_node


@pytest.fixture
def listing():
    return ['a', 2, True]


@pytest.fixture
def int_listing():
    return [2, 1, 3]


@pytest.mark.usefixtures('clear_database_before_test')
def test_creation():
    """Test the creation of an empty ``List`` node."""
    node = List()
    assert len(node) == 0
    with pytest.raises(IndexError):
        node[0]  # pylint: disable=pointless-statement


@pytest.mark.usefixtures('clear_database_before_test')
def test_mutability():
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
        node.remove(5)
    with pytest.raises(ModificationNotAllowed):
        node.pop()
    with pytest.raises(ModificationNotAllowed):
        node.sort()
    with pytest.raises(ModificationNotAllowed):
        node.reverse()


@pytest.mark.usefixtures('clear_database_before_test')
def test_store_load(listing):
    """Test load_node on just stored object."""
    node = List(listing)
    node.store()

    node_loaded = load_node(node.pk)
    assert node.get_list() == node_loaded.get_list()


@pytest.mark.usefixtures('clear_database_before_test')
def test_special_methods(listing):
    """Test the special methods of the ``List`` class."""
    node = List(list=listing)

    # __getitem__
    for i, value in enumerate(listing):
        assert node[i] == value

    # __setitem__
    node[0] = 'b'
    assert node[0] == 'b'

    # __delitem__
    del node[0]
    assert node.get_list() == listing[1:]

    # __len__
    assert len(node) == 2


@pytest.mark.usefixtures('clear_database_before_test')
def test_equality(listing):
    """Test that two ``List`` nodes with equal content compare equal."""
    node1 = List(list=listing)
    node2 = List(list=listing)

    assert node1 == node2


@pytest.mark.usefixtures('clear_database_before_test')
def test_append(listing):
    """Test the ``List.append()`` method."""

    def do_checks(node):
        assert len(node) == 1
        assert node[0] == 4

    node = List()
    node.append(4)
    do_checks(node)

    # Try the same after storing
    node.store()
    do_checks(node)

    node = List(list=listing)
    node.append('more')
    assert node[-1] == 'more'


@pytest.mark.usefixtures('clear_database_before_test')
def test_extend(listing):
    """Test extend() member function."""

    def do_checks(node, lst):
        assert len(node) == len(lst)
        # Do an element wise comparison
        for lst_el, node_el in zip(lst, node):
            assert lst_el == node_el

    node = List()
    node.extend(listing)
    do_checks(node, listing)

    # Further extend
    node.extend(listing)
    do_checks(node, listing * 2)

    # Now try after storing
    node.store()
    do_checks(node, listing * 2)


@pytest.mark.usefixtures('clear_database_before_test')
def test_insert(listing):
    """Test the ``List.insert()`` method."""
    node = List(list=listing)
    node.insert(1, 'new')
    assert node[1] == 'new'
    assert len(node) == 4


@pytest.mark.usefixtures('clear_database_before_test')
def test_remove(listing):
    """Test the ``List.remove()`` method."""
    node = List(list=listing)
    node.remove(1)
    listing.remove(1)
    assert node.get_list() == listing

    with pytest.raises(ValueError, match=r'list.remove\(x\): x not in list'):
        node.remove('non-existent')


@pytest.mark.usefixtures('clear_database_before_test')
def test_pop(listing):
    """Test the ``List.pop()`` method."""
    node = List(list=listing)
    node.pop()
    assert node.get_list() == listing[:-1]


@pytest.mark.usefixtures('clear_database_before_test')
def test_index(listing):
    """Test the ``List.index()`` method."""
    node = List(list=listing)

    assert node.index(True) == listing.index(True)


@pytest.mark.usefixtures('clear_database_before_test')
def test_count(listing):
    """Test the ``List.count()`` method."""
    node = List(list=listing)
    for value in listing:
        assert node.count(value) == listing.count(value)


@pytest.mark.usefixtures('clear_database_before_test')
def test_sort(listing, int_listing):
    """Test the ``List.sort()`` method."""
    node = List(list=int_listing)
    node.sort()
    int_listing.sort()
    assert node.get_list() == int_listing

    node = List(list=listing)
    with pytest.raises(TypeError, match=r"'<' not supported between instances of 'int' and 'str'"):
        node.sort()


@pytest.mark.usefixtures('clear_database_before_test')
def test_reverse(listing):
    """Test the ``List.reverse()`` method."""
    node = List(list=listing)
    node.reverse()
    listing.reverse()
    assert node.get_list() == listing


@pytest.mark.usefixtures('clear_database_before_test')
def test_initialise_with_list_kwarg(listing):
    """Test that the ``List`` node can be initialized with the ``list`` keyword argument for backwards compatibility."""
    node = List(list=listing)
    assert node.get_list() == listing