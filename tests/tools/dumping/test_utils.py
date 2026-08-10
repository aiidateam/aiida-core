###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the helpers in :mod:`aiida.tools._dumping.utils`."""

import functools

import pytest

from aiida import orm
from aiida.tools._dumping.utils import registry_name_for


class PluginWorkGraphNode(orm.WorkChainNode):
    """Plugin-style ``WorkChainNode`` subclass, standing in for ``aiida-workgraph``'s ``WorkGraphNode``.

    Such subclasses are not registered in :data:`~aiida.tools._dumping.utils.ORM_TYPE_TO_REGISTRY`
    directly but must still classify as workflows via their MRO, so that ``verdi profile dump`` picks
    them up.
    """


@pytest.mark.usefixtures('aiida_profile')
@pytest.mark.parametrize(
    'entity_factory, expected',
    (
        pytest.param(orm.CalculationNode, 'calculations', id='calculation'),
        pytest.param(orm.CalcFunctionNode, 'calculations', id='calcfunction'),
        pytest.param(orm.CalcJobNode, 'calculations', id='calcjob'),
        pytest.param(orm.WorkflowNode, 'workflows', id='workflow'),
        pytest.param(orm.WorkFunctionNode, 'workflows', id='workfunction'),
        pytest.param(orm.WorkChainNode, 'workflows', id='workchain'),
        pytest.param(PluginWorkGraphNode, 'workflows', id='plugin-subclass'),
        pytest.param(functools.partial(orm.Group, label='some-group'), 'groups', id='group'),
    ),
)
def test_registry_name_for(entity_factory, expected):
    """Registered types, plugin subclasses and groups all resolve to their registry.

    The entity is constructed inside the test body rather than passed as a parametrize value, because
    parametrize arguments are evaluated at collection time, before ``aiida_profile`` has loaded a
    profile.
    """
    assert registry_name_for(entity_factory()) == expected


@pytest.mark.usefixtures('aiida_profile')
def test_registry_name_for_unregistered_raises():
    """A node type with no registered base class raises a clear error."""
    with pytest.raises(NotImplementedError, match='No dump registry'):
        registry_name_for(orm.Int(1))


@pytest.mark.usefixtures('aiida_profile_clean')
def test_dump_plugin_subclass_node(entry_points, tmp_path):
    """A plugin ``WorkChainNode`` subclass is dumped as a workflow, not skipped with a ``KeyError``.

    Regression test for the actual dump call sites in
    :mod:`aiida.tools._dumping.executors.process`: dumping must resolve the registry through
    :func:`~aiida.tools._dumping.utils.registry_name_for` rather than an exact-type dict lookup.
    """
    entry_points.add(PluginWorkGraphNode, 'aiida.node:process.workflow.workchain.workgraph')

    node = PluginWorkGraphNode()
    node.label = 'my-workgraph'
    node.store()
    node.seal()

    dump_path = node.dump(output_path=tmp_path / 'dump')
    assert (dump_path / 'aiida_node_metadata.yaml').is_file()
