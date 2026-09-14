###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `CalcJob` utils."""

import pytest

from aiida.common.links import LinkType
from aiida.orm import Dict
from aiida.orm.utils.calcjob import CalcJobResultManager


@pytest.fixture
def get_calcjob_node(generate_calculation_node):
    """Return a calculation node with `Dict` output with default output label and the dictionary it contains."""
    node = generate_calculation_node(entry_point='aiida.calculations:core.templatereplacer').store()
    dictionary = {
        'key_one': 'val_one',
        'key_two': 'val_two',
    }

    results = Dict(dict=dictionary).store()
    results.base.links.add_incoming(
        node, link_type=LinkType.CREATE, link_label=node.process_class.spec().default_output_node
    )

    return node, dictionary


def test_no_process_type(generate_calculation_node):
    """`get_results` should raise `ValueError` if `CalcJobNode` has no `process_type`"""
    node = generate_calculation_node()
    manager = CalcJobResultManager(node)

    with pytest.raises(ValueError):
        manager.get_results()


def test_invalid_process_type(generate_calculation_node):
    """`get_results` should raise `ValueError` if `CalcJobNode` has invalid `process_type`"""
    node = generate_calculation_node(entry_point='aiida.calculations:invalid')
    manager = CalcJobResultManager(node)

    with pytest.raises(ValueError):
        manager.get_results()


def test_process_class_no_default_node(generate_calculation_node):
    """`get_results` should raise `ValueError` if process class does not define default output node."""
    # This is a valid process class however ArithmeticAddCalculation does define a default output node
    node = generate_calculation_node(entry_point='aiida.calculations:core.arithmetic.add')
    manager = CalcJobResultManager(node)

    with pytest.raises(ValueError):
        manager.get_results()


def test_iterator(get_calcjob_node):
    """Test that the manager can be iterated over."""
    node, dictionary = get_calcjob_node
    manager = CalcJobResultManager(node)
    for key in manager:
        assert key in dictionary.keys()


def test_getitem(get_calcjob_node):
    """Test that the manager supports the getitem operator."""
    node, dictionary = get_calcjob_node
    manager = CalcJobResultManager(node)

    for key, value in dictionary.items():
        assert manager[key] == value

    with pytest.raises(KeyError):
        assert manager['non-existent-key']


def test_getitem_no_results(generate_calculation_node):
    """Test that `getitem` raises `KeyError` if no results can be retrieved whatsoever e.g. there is no output."""
    node = generate_calculation_node()
    manager = CalcJobResultManager(node)

    with pytest.raises(KeyError):
        assert manager['key']


def test_getattr(get_calcjob_node):
    """Test that the manager supports the getattr operator."""
    node, dictionary = get_calcjob_node
    manager = CalcJobResultManager(node)

    for key, value in dictionary.items():
        assert getattr(manager, key) == value

    with pytest.raises(AttributeError):
        assert getattr(manager, 'non-existent-key')


def test_getattr_no_results(generate_calculation_node):
    """Test that `getattr` raises `AttributeError` if no results can be retrieved whatsoever e.g. there is no output."""
    node = generate_calculation_node()
    manager = CalcJobResultManager(node)

    with pytest.raises(AttributeError):
        assert getattr(manager, 'key')


def test_dir(get_calcjob_node):
    """Test that `dir` returns all keys of the dictionary and nothing else."""
    node, dictionary = get_calcjob_node
    manager = CalcJobResultManager(node)

    assert len(dir(manager)) == len(dictionary)
    assert set(dir(manager)) == set(dictionary)

    # Check that it works also as an iterator
    assert len(list(manager)) == len(dictionary)
    assert set(manager) == set(dictionary)
