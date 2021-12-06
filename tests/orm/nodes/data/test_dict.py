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
"""Tests for :class:`aiida.orm.nodes.data.dict.Dict` class."""
import pytest

from aiida.orm import Dict


@pytest.fixture
def dictionary():
    return {'value': 1, 'nested': {'dict': 'ionary'}}


@pytest.mark.usefixtures('clear_database_before_test')
def test_keys(dictionary):
    """Test the ``keys`` method."""
    node = Dict(dictionary)
    assert sorted(node.keys()) == sorted(dictionary.keys())


@pytest.mark.usefixtures('clear_database_before_test')
def test_get_dict(dictionary):
    """Test the ``get_dict`` method."""
    node = Dict(dictionary)
    assert node.get_dict() == dictionary


@pytest.mark.usefixtures('clear_database_before_test')
def test_dict_property(dictionary):
    """Test the ``dict`` property."""
    node = Dict(dictionary)
    assert node.dict.value == dictionary['value']
    assert node.dict.nested == dictionary['nested']


@pytest.mark.usefixtures('clear_database_before_test')
def test_get_item(dictionary):
    """Test the ``__getitem__`` method."""
    node = Dict(dictionary)
    assert node['value'] == dictionary['value']
    assert node['nested'] == dictionary['nested']


@pytest.mark.usefixtures('clear_database_before_test')
def test_set_item(dictionary):
    """Test the methods for setting the item.

    * ``__setitem__`` directly on the node
    * ``__setattr__`` through the ``AttributeManager`` returned by the ``dict`` property
    """
    node = Dict(dictionary)

    node['value'] = 2
    assert node['value'] == 2

    node.dict.value = 3
    assert node['value'] == 3


@pytest.mark.usefixtures('clear_database_before_test')
def test_correct_raises(dictionary):
    """Test that the methods for accessing the item raise the correct error.

    * ``node['inexistent']`` should raise ``KeyError``
    * ``node.dict.inexistent`` should raise ``AttributeError``
    """
    node = Dict(dictionary)

    with pytest.raises(KeyError):
        _ = node['inexistent_key']

    with pytest.raises(AttributeError):
        _ = node.dict.inexistent_key


@pytest.mark.usefixtures('clear_database_before_test')
def test_eq(dictionary):
    """Test the ``__eq__`` method.

    A node should compare equal to itself and to the plain dictionary that represents its value. However, it should not
    compare equal to another node that has the same content. This is a hot issue and is being discussed in the following
    ticket: https://github.com/aiidateam/aiida-core/issues/1917
    """
    node = Dict(dictionary)
    clone = Dict(dictionary)

    assert node is node  # pylint: disable=comparison-with-itself
    assert node == dictionary
    assert node != clone

    # To test the fallback, where two ``Dict`` nodes are equal if their UUIDs are even if the content is different, we
    # create a different node with other content, but artificially give it the same UUID as ``node``. In practice this
    # wouldn't happen unless, by accident, two different nodes get the same UUID, the probability of which is minimal.
    # Note that we have to set the UUID directly through the database model instance of the backend entity, since it is
    # forbidden to change it through the front-end or backend entity instance, for good reasons.
    other = Dict({})
    other.backend_entity._dbmodel.uuid = node.uuid  # pylint: disable=protected-access
    assert other.uuid == node.uuid
    assert other.dict != node.dict
    assert node == other


@pytest.mark.usefixtures('clear_database_before_test')
def test_initialise_with_dict_kwarg(dictionary):
    """Test that the ``Dict`` node can be initialized with the ``dict`` keyword argument for backwards compatibility."""
    node = Dict(dict=dictionary)
    assert sorted(node.keys()) == sorted(dictionary.keys())
