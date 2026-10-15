###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for runtime preparation of `aiida.engine.processes.ports`."""

import pytest

from aiida import orm
from aiida.common.extendeddicts import AttributesFrozendict
from aiida.engine.processes.ports import InputPort, PortNamespace

pytestmark = pytest.mark.presto


def test_prepare_keeps_plain_values() -> None:
    """Values matching the declared runtime type pass through preparation."""
    port = InputPort('count', valid_type=int)
    assert port.prepare(2).runtime == 2
    assert port.prepare(2).runtime is not None


@pytest.mark.usefixtures('aiida_profile_clean')
def test_prepare_unwraps_matching_nodes() -> None:
    """Nodes convertible to the declared runtime type arrive as plain values."""
    port = InputPort('count', valid_type=int)
    assert port.prepare(orm.Int(2)).runtime == 2


@pytest.mark.usefixtures('aiida_profile_clean')
def test_prepare_keeps_nodes_for_node_ports() -> None:
    """Nodes matching a node-typed port are preserved for provenance."""
    port = InputPort('count', valid_type=orm.Int)
    node: orm.Int = orm.Int(2)
    resolved = port.prepare(node)
    assert resolved.runtime is node
    assert resolved.sources is node


@pytest.mark.usefixtures('aiida_profile_clean')
def test_prepare_keeps_unconvertible_values_for_validation() -> None:
    """Unconvertible values pass through preparation and fail validation."""
    port = InputPort('count', valid_type=int)
    node: orm.Str = orm.Str('wrong')
    assert port.prepare(node).runtime is node
    assert port.validate(node) is not None


@pytest.mark.usefixtures('aiida_profile_clean')
def test_namespace_prepare_returns_new_mapping() -> None:
    """Namespace preparation adapts leaves without changing the supplied mapping."""
    namespace = PortNamespace('values')
    namespace['count'] = InputPort('count', valid_type=int)
    node: orm.Int = orm.Int(2)
    mapping: dict[str, object] = {'count': node}
    prepared = namespace.prepare(mapping)
    assert isinstance(prepared.runtime, AttributesFrozendict)
    assert prepared.runtime['count'] == 2
    assert prepared.sources['count'] is node
    assert mapping == {'count': node}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_prepare_reports_converted_sources() -> None:
    """Converted values source from themselves; supplied nodes source from themselves."""
    port = InputPort('count', valid_type=int)
    node: orm.Int = orm.Int(2)
    resolved = port.prepare(node)
    assert (resolved.runtime, resolved.sources) == (2, node)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_serialize_converts_dynamic_leaves() -> None:
    """Undeclared values serialize to nodes for provenance."""
    namespace = PortNamespace('values', valid_type=int, dynamic=True)
    serialized = namespace.serialize({'extra': 3})
    assert isinstance(serialized['extra'], orm.Int)
