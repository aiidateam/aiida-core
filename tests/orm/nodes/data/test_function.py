###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :class:`aiida.orm.nodes.data.function.FunctionData`."""

import pytest

from aiida import orm
from aiida.orm import FunctionData, load_node


def a_referenced_function():
    """A module-level function used as the target of a ``FunctionData`` reference."""
    return 42


def test_stores_module_and_qualname_and_resolves_value():
    node = FunctionData(a_referenced_function).store()
    loaded = load_node(node.pk)
    assert loaded.module_path == __name__
    assert loaded.qualname == 'a_referenced_function'
    assert loaded.path == f'{__name__}:a_referenced_function'
    assert loaded.value is a_referenced_function
    assert loaded.value() == 42


def test_to_aiida_type_dispatches_function():
    node = orm.to_aiida_type(a_referenced_function)
    assert isinstance(node, FunctionData)
    assert node.value is a_referenced_function


def test_invalid_object_raises():
    with pytest.raises(TypeError, match='expected a function-like object'):
        FunctionData(5)


def test_unresolvable_reference_raises_import_error():
    node = FunctionData(a_referenced_function)
    node.base.attributes.set('qualname', 'does_not_exist')
    with pytest.raises(ImportError, match="attribute 'does_not_exist' not found"):
        _ = node.value
