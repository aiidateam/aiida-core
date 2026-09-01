###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.orm.utils.collections` module."""

from aiida import orm
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
