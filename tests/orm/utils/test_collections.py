###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.orm.utils.collections` module."""

import io

import pytest

from aiida import orm
from aiida.common.extendeddicts import AttributeDict
from aiida.orm.utils.collections import shallow_copy_nested_dict


def test_shallow_copy_nested_dict():
    """Test nested dictionaries are copied recursively while leaf values are preserved."""
    node = orm.Int(1)
    numbers = [1, 2, 3]
    original = {
        'metadata': {
            'options': {
                'resources': {
                    'num_machines': 1,
                },
            },
            'node': node,
        },
        'numbers': numbers,
    }

    copied = shallow_copy_nested_dict(original)

    assert copied is not original
    assert copied['metadata'] is not original['metadata']
    assert copied['metadata']['options'] is not original['metadata']['options']
    assert copied['metadata']['options']['resources'] is not original['metadata']['options']['resources']
    assert copied['metadata']['node'] is node
    assert copied['numbers'] is numbers

    copied['metadata']['options']['resources']['num_machines'] = 2

    assert original['metadata']['options']['resources']['num_machines'] == 1


@pytest.mark.parametrize('stored', [False, True])
@pytest.mark.parametrize('node_type', ['int', 'dict', 'singlefile'])
def test_node_identity(node_type, stored):
    """Preserve stored and unstored data nodes, including file-backed data used in process inputs."""
    if node_type == 'int':
        node = orm.Int(1)
    elif node_type == 'dict':
        node = orm.Dict({'value': 1})
    else:
        node = orm.SinglefileData(io.BytesIO(b'input data'), filename='input.dat')
    if stored:
        node.store()

    original = {'node': node, 'nested': {'same_node': node}}
    copied = shallow_copy_nested_dict(original)

    assert copied['node'] is node
    assert copied['nested']['same_node'] is node
    assert copied['node'].uuid == node.uuid
    assert copied['node'].is_stored is stored


def test_non_dictionary_containers_are_shared():
    """Lists and tuples remain shared, including any dictionaries they contain."""
    nested = {'value': 1}
    values = [nested]
    pair = (nested,)
    original = {'options': {'values': values, 'pair': pair}}

    copied = shallow_copy_nested_dict(original)

    assert copied['options'] is not original['options']
    assert copied['options']['values'] is values
    assert copied['options']['pair'] is pair
    copied['options']['values'][0]['value'] = 2
    assert original['options']['values'][0]['value'] == 2


def test_empty_dictionary():
    """Return a new container even when there are no values."""
    original = {}
    copied = shallow_copy_nested_dict(original)

    assert copied == {}
    assert copied is not original


def test_dictionary_subclass():
    """Accept AttributeDict input namespaces and return independent plain dictionaries."""
    original = AttributeDict({'options': AttributeDict({'num_machines': 1})})
    copied = shallow_copy_nested_dict(original)
    copied['options']['num_machines'] = 2

    assert type(copied) is dict
    assert type(copied['options']) is dict
    assert original.options.num_machines == 1


def test_public_imports():
    """Expose the helper through the ORM and utility import paths."""
    from aiida.orm.utils import shallow_copy_nested_dict as utility

    assert orm.shallow_copy_nested_dict is shallow_copy_nested_dict
    assert utility is shallow_copy_nested_dict
