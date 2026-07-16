###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the helpers in :mod:`aiida.tools._dumping.utils`."""

import pytest

from aiida import orm
from aiida.tools._dumping.utils import registry_name_for


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'node_cls, expected',
    (
        (orm.CalculationNode, 'calculations'),
        (orm.CalcFunctionNode, 'calculations'),
        (orm.CalcJobNode, 'calculations'),
        (orm.WorkflowNode, 'workflows'),
        (orm.WorkFunctionNode, 'workflows'),
        (orm.WorkChainNode, 'workflows'),
    ),
)
def test_registry_name_for_exact_types(node_cls, expected):
    """Exact registered node types resolve to their registry as before."""
    assert registry_name_for(node_cls()) == expected


@pytest.mark.usefixtures('aiida_profile_clean')
def test_registry_name_for_group():
    """Groups resolve to the ``groups`` registry."""
    assert registry_name_for(orm.Group(label='some-group')) == 'groups'


@pytest.mark.usefixtures('aiida_profile_clean')
def test_registry_name_for_subclass():
    """A plugin-style ``WorkChainNode`` subclass resolves via its MRO.

    This mirrors nodes such as ``aiida-workgraph``'s ``WorkGraphNode``, which are not
    registered in :data:`~aiida.tools._dumping.utils.ORM_TYPE_TO_REGISTRY` directly but
    must still be classified as workflows so that ``verdi profile dump`` picks them up.
    """

    class PluginWorkChainNode(orm.WorkChainNode):
        """Trivial subclass standing in for a plugin-provided process node."""

    assert registry_name_for(PluginWorkChainNode()) == 'workflows'


@pytest.mark.usefixtures('aiida_profile_clean')
def test_registry_name_for_unregistered_raises():
    """A node type with no registered base class raises a clear error."""
    with pytest.raises(KeyError, match='No dump registry'):
        registry_name_for(orm.Int(1))
