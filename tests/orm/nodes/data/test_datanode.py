###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Regression tests for the shared :class:`~aiida.orm.DataNode` base class.

``Data`` and ``Container`` (``DataList``/``DataDict``) share node identity but keep separate storage
implementations. These tests pin the common contract: the hierarchy and imports, the class/type-string
resolution, the ``QueryBuilder`` semantics of the three bases, the process/port/link boundaries that accept
any data node, and the launcher-equivalent output filtering.
"""

import pytest

from aiida.common.exceptions import IncompatibleStorageSchema, StoringNotAllowed
from aiida.orm import (
    CalcJobNode,
    Container,
    Data,
    DataDict,
    DataList,
    DataNode,
    Dict,
    Int,
    Node,
    ProcessNode,
    QueryBuilder,
    Str,
)


def test_hierarchy_and_imports():
    """``Data`` and ``Container`` share ``DataNode``; ``ProcessNode`` stays separate."""
    assert issubclass(Data, DataNode)
    assert issubclass(Container, DataNode)
    assert issubclass(DataList, Container)
    assert issubclass(DataDict, Container)
    assert issubclass(DataNode, Node)
    assert not issubclass(ProcessNode, DataNode)
    assert not issubclass(DataNode, ProcessNode)
    # Containers are not ``Data`` and data is not a container, but both are data nodes.
    assert not issubclass(Container, Data)
    assert not issubclass(Data, Container)

    import aiida.orm
    import aiida.orm.nodes
    import aiida.orm.nodes.data

    assert aiida.orm.DataNode is aiida.orm.nodes.DataNode is aiida.orm.nodes.data.DataNode is DataNode


def test_datanode_abstract_contract():
    """``DataNode`` is abstract: no entry point, not storable, clone contract only."""
    assert DataNode._storable is False
    assert DataNode.entry_point is None
    with pytest.raises(StoringNotAllowed):
        DataNode().store()
    with pytest.raises(NotImplementedError):
        DataNode().clone()
    # Concrete branches keep their own storage implementations and clone semantics.
    assert Data._storable is True
    assert Container._storable is True


def test_load_node_class():
    """Type-string resolution keeps legacy strings and resolves the new base."""
    from aiida.orm.utils.node import load_node_class

    assert load_node_class(DataList.class_node_type) is DataList
    assert load_node_class(DataDict.class_node_type) is DataDict
    assert load_node_class(DataNode.class_node_type) is DataNode
    assert load_node_class('data.Data.') is Data
    assert load_node_class('data.core.int.Int.') is Int
    # The removed ``Code`` plugin still raises instead of silently falling back.
    with pytest.raises(IncompatibleStorageSchema):
        load_node_class('data.core.code.Code.')
    # Unknown ``data.`` type strings keep the legacy ``Data`` fallback without warning.
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter('error')
        assert load_node_class('data.core.unknown.Unknown.') is Data


def test_querybuilder_three_bases(aiida_profile_clean):
    """``DataNode`` matches both branches, ``Data`` excludes containers, ``Container`` matches both concretes."""
    Int(1).store()
    DataList([Int(2)]).store()
    DataDict({'a': Int(3)}).store()

    # Owned children are ``DbNode`` rows too, so they match data queries as well: one standalone ``Int`` plus
    # two containers plus their two owned ``Int`` children.
    assert QueryBuilder().append(DataNode).count() == 5
    assert QueryBuilder().append(Data).count() == 3
    assert QueryBuilder().append(Container).count() == 2
    assert QueryBuilder().append(DataList).count() == 1
    assert QueryBuilder().append(DataDict).count() == 1
    assert QueryBuilder().append(DataList, subclassing=False).count() == 1
    assert {type(node) for (node,) in QueryBuilder().append(DataNode, project='*').all()} == {
        Int,
        DataList,
        DataDict,
    }
    # Stored type strings are unchanged legacy identifiers.
    assert DataList.class_node_type == 'data.core.data_list.DataList.'
    assert DataDict.class_node_type == 'data.core.data_dict.DataDict.'
    assert Data.class_node_type == 'data.Data.'


def test_querybuilder_data_subclass_excludes_containers(aiida_profile_clean):
    """A ``Data`` subclass query never returns containers sharing the ``data.`` prefix."""
    Int(1).store()
    DataList([Int(2)]).store()

    # The owned ``Int`` child matches too, but no container ever matches a ``Data`` subclass query.
    assert QueryBuilder().append(Int).count() == 2
    assert {type(node) for (node,) in QueryBuilder().append(Int, project='*').all()} == {Int}
    assert QueryBuilder().append(Str).count() == 0
    assert QueryBuilder().append(Dict).count() == 0


def test_process_ports_accept_datanode():
    """Process ports declared with ``DataNode`` accept data and containers alike."""
    from aiida.engine.processes.ports import InputPort

    port = InputPort('port', valid_type=DataNode)
    assert port.validate(Int(1)) is None
    assert port.validate(DataList([Int(1)])) is None
    assert port.validate(DataDict({'a': Int(1)})) is None


def test_infer_node_types_keeps_data_narrow():
    """Type inference still distinguishes generic data nodes from ``Data``-only declarations."""
    from aiida.engine.processes.ports import _infer_node_types

    assert _infer_node_types(DataNode) == (DataNode,)
    assert _infer_node_types(Data) == (Data,)
    assert _infer_node_types(Int) == (Int,)
    assert _infer_node_types(Container) == (Container,)


def test_links_accept_containers():
    """Provenance link validation treats containers like data at the boundary."""
    from aiida.common.links import LinkType
    from aiida.orm.utils.links import validate_link

    source = CalcJobNode()
    target = DataList([Int(1)])
    validate_link(source, target, LinkType.CREATE, 'result')
    validate_link(target, source, LinkType.INPUT_CALC, 'input')


def test_calcfunction_container_output(aiida_profile_clean):
    """A ``calcfunction`` can return a container and the launcher-equivalent filter finds it."""
    from aiida.engine import calcfunction, run_get_node

    @calcfunction
    def make_list():
        return DataList([Int(1), Int(2)])

    results, node = run_get_node(make_list)
    assert isinstance(results, DataList)
    assert results.is_stored

    # This mirrors ``ProcessLauncher`` for finished processes: outputs are collected as data nodes.
    outputs = {entry.link_label: entry.node for entry in node.base.links.get_outgoing(node_class=DataNode)}
    assert set(outputs) == {'result'}
    assert isinstance(outputs['result'], DataList)
    assert outputs['result'].uuid == results.uuid
    # The stored container plus its two owned children are all data-node rows.
    assert QueryBuilder().append(DataNode).count() == 3


def test_calcfunction_owned_child_output(aiida_profile_clean):
    """Returning an owned container child records a standalone copy; the caller handle stays usable."""
    from aiida.engine import calcfunction, run_get_node
    from aiida.orm.nodes.data.container import is_owned

    @calcfunction
    def take_first(container: DataList):
        child = container[0]
        assert is_owned(child)
        return child

    source = DataList([Int(1), Int(2)])
    results, node = run_get_node(take_first, container=source)
    recorded = node.base.links.get_outgoing().get_node_by_label('result')

    assert recorded.is_stored
    assert not is_owned(recorded)
    assert not is_owned(results)
    assert recorded.value == 1
    # The recorded node is exactly what the process output link points to.
    assert recorded.uuid == node.base.links.get_outgoing().get_node_by_label('result').uuid
    assert results.uuid == recorded.uuid
