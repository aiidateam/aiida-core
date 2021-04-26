# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the various node managers (.inputs, .outputs, .dict, ...)."""
# pylint: disable=unused-argument
import pytest

from aiida import orm
from aiida.common.exceptions import NotExistent, NotExistentAttributeError, NotExistentKeyError
from aiida.common import LinkType, AttributeDict


def test_dot_dict_manager(clear_database_before_test):
    """Verify that the Dict.dict manager behaves as intended."""
    dict_content = {'a': True, 'b': 1, 'c': 'Some string'}
    dict_node = orm.Dict(dict=dict_content)

    # Check that dir() return all keys and nothing else, important
    # for tab competion
    assert len(dir(dict_node.dict)) == len(dict_content)
    assert set(dir(dict_node.dict)) == set(dict_content)
    # Check that it works also as an iterator
    assert len(list(dict_node.dict)) == len(dict_content)
    assert set(dict_node.dict) == set(dict_content)

    for key, val in dict_content.items():
        # dict_node.dict.a == True, ...
        assert getattr(dict_node.dict, key) == val
        # dict_node.dict['a'] == True, ...
        assert dict_node.dict[key] == val

    # I check the attribute fetching directly
    assert dict_node.dict.b == 1

    # Must raise a AttributeError, otherwise tab competion will not work
    with pytest.raises(AttributeError):
        getattr(dict_node.dict, 'NotExistentKey')

    # Must raise a KeyError
    with pytest.raises(KeyError):
        _ = dict_node.dict['NotExistentKey']


def test_link_manager(clear_database_before_test):
    """Test the LinkManager via .inputs and .outputs from a ProcessNode."""
    # I first create a calculation with two inputs and two outputs

    # Create inputs
    inp1 = orm.Data()
    inp1.store()
    inp2 = orm.Data()
    inp2.store()
    inp3 = orm.Data()
    inp3.store()

    # Create calc with inputs
    calc = orm.CalculationNode()
    calc.add_incoming(inp1, link_type=LinkType.INPUT_CALC, link_label='inp1label')
    calc.add_incoming(inp2, link_type=LinkType.INPUT_CALC, link_label='inp2label')
    calc.store()

    # Attach outputs
    out1 = orm.Data()
    out2 = orm.Data()
    out1.add_incoming(calc, link_type=LinkType.CREATE, link_label='out1label')
    out1.store()
    out2.add_incoming(calc, link_type=LinkType.CREATE, link_label='out2label')
    out2.store()

    expected_inputs = {'inp1label': inp1.uuid, 'inp2label': inp2.uuid}
    expected_outputs = {'out1label': out1.uuid, 'out2label': out2.uuid}

    #### Check the 'inputs' manager ###
    # Check that dir() return all keys and nothing else, important
    # for tab competion (we skip anything that starts with an underscore)
    assert len([key for key in dir(calc.inputs) if not key.startswith('_')]) == len(expected_inputs)
    assert set(key for key in dir(calc.inputs) if not key.startswith('_')) == set(expected_inputs)
    # Check that it works also as an iterator
    assert len(list(calc.inputs)) == len(expected_inputs)
    assert set(calc.inputs) == set(expected_inputs)

    for key, val in expected_inputs.items():
        # calc.inputs.a.uuid == ..., ...
        assert getattr(calc.inputs, key).uuid == val
        # calc.inputs['a'].uuid == ..., ...
        assert calc.inputs[key].uuid == val

    # I check the attribute fetching directly
    assert calc.inputs.inp1label.uuid == expected_inputs['inp1label']

    ## Check for not-existing links
    # - Must raise a AttributeError, otherwise tab competion will not work
    # - Actually raises a NotExistentAttributeError
    # - NotExistentAttributeError should also be caught by NotExistent,
    #   for backwards-compatibility for AiiDA 1.0, 1.1, 1.2
    for exception in [AttributeError, NotExistent, NotExistentAttributeError]:
        with pytest.raises(exception):
            getattr(calc.inputs, 'NotExistentLabel')

    # - Must raise a KeyError to behave like a dictionary
    # - Actually raises a NotExistentKeyError
    # - NotExistentKeyError should also be caught by NotExistent,
    #   for backwards-compatibility for AiiDA 1.0, 1.1, 1.2
    for exception in [KeyError, NotExistent, NotExistentKeyError]:
        with pytest.raises(exception):
            _ = calc.inputs['NotExistentLabel']

    #### Check the 'outputs' manager ###
    # Check that dir() return all keys and nothing else, important
    # for tab competion (we skip anything that starts with an underscore)
    assert len([key for key in dir(calc.outputs) if not key.startswith('_')]) == len(expected_outputs)
    assert set(key for key in dir(calc.outputs) if not key.startswith('_')) == set(expected_outputs)
    # Check that it works also as an iterator
    assert len(list(calc.outputs)) == len(expected_outputs)
    assert set(calc.outputs) == set(expected_outputs)

    for key, val in expected_outputs.items():
        # calc.outputs.a.uuid == ..., ...
        assert getattr(calc.outputs, key).uuid == val
        # calc.outputs['a'].uuid == ..., ...
        assert calc.outputs[key].uuid == val

    # I check the attribute fetching directly
    assert calc.outputs.out1label.uuid == expected_outputs['out1label']

    # Must raise a AttributeError, otherwise tab competion will not work
    with pytest.raises(AttributeError):
        getattr(calc.outputs, 'NotExistentLabel')

    # Must raise a KeyError
    with pytest.raises(KeyError):
        _ = calc.outputs['NotExistentLabel']


def test_link_manager_with_nested_namespaces(clear_database_before_test):
    """Test the ``LinkManager`` works with nested namespaces."""
    inp1 = orm.Data()
    inp1.store()

    calc = orm.CalculationNode()
    calc.add_incoming(inp1, link_type=LinkType.INPUT_CALC, link_label='nested__sub__namespace')
    calc.store()

    # Attach outputs
    out1 = orm.Data()
    out1.add_incoming(calc, link_type=LinkType.CREATE, link_label='nested__sub__namespace')
    out1.store()

    # Check that the recommended way of dereferencing works
    assert calc.inputs.nested.sub.namespace.uuid == inp1.uuid
    assert calc.outputs.nested.sub.namespace.uuid == out1.uuid

    # Leafs will return an ``AttributeDict`` instance
    assert isinstance(calc.outputs.nested.sub, AttributeDict)

    # Check the legacy way still works
    with pytest.warns(Warning):
        assert calc.inputs.nested__sub__namespace.uuid == inp1.uuid
        assert calc.outputs.nested__sub__namespace.uuid == out1.uuid

    # Must raise a AttributeError, otherwise tab competion will not work
    with pytest.raises(AttributeError):
        _ = calc.outputs.nested.not_existent

    # Must raise a KeyError
    with pytest.raises(KeyError):
        _ = calc.outputs.nested['not_existent']
