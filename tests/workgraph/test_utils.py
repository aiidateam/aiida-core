###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for :mod:`aiida.workgraph.utils`."""

import pytest

from aiida.workgraph.utils import (
    get_nested_dict,
    resolve_node_link_managers,
    update_nested_dict,
    update_nested_dict_with_special_keys,
)


def test_get_nested_dict_returns_leaf():
    assert get_nested_dict({'base': {'pw': {'parameters': 2}}}, 'base.pw.parameters') == 2


def test_get_nested_dict_default_when_missing():
    assert get_nested_dict({'base': {'pw': {}}}, 'base.pw.parameters', default=None) is None


def test_get_nested_dict_raises_without_default():
    with pytest.raises(ValueError, match='not exist'):
        get_nested_dict({'base': {'pw': {}}}, 'base.pw.parameters')


def test_update_nested_dict_creates_path_from_none():
    assert update_nested_dict(None, 'scf.pw.parameters', 2) == {'scf': {'pw': {'parameters': 2}}}


def test_update_nested_dict_merges_into_existing_branch():
    base = {'scf': {'pw': {'a': 1}}}
    assert update_nested_dict(base, 'scf.pw', {'b': 2}) == {'scf': {'pw': {'a': 1, 'b': 2}}}


def test_update_nested_dict_overwrites_non_dict_leaf():
    assert update_nested_dict({'x': 1}, 'x', 2) == {'x': 2}


def test_update_nested_dict_with_special_keys_expands_and_drops_none():
    data = {'base.pw.parameters': 2, 'plain': 'keep', 'gone': None}
    assert update_nested_dict_with_special_keys(data) == {
        'base': {'pw': {'parameters': 2}},
        'plain': 'keep',
    }


def test_resolve_node_link_managers_passes_through_plain_data():
    """Values that are not ``NodeLinksManager`` are returned unchanged, recursing into dicts. The manager
    conversion itself is exercised end to end by every work graph run."""
    data = {'a': 1, 'nested': {'b': [1, 2], 'c': 'str'}}
    assert resolve_node_link_managers(data) == data
