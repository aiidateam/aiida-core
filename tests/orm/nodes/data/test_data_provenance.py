###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Regression tests for data queries and container behavior at provenance boundaries."""

import pytest

from aiida.common.exceptions import IncompatibleStorageSchema
from aiida.orm import (
    CalcJobNode,
    Container,
    Data,
    DataDict,
    DataList,
    Dict,
    Int,
    QueryBuilder,
    Str,
)


def test_load_node_class():
    """Type-string resolution keeps legacy strings."""
    from aiida.orm.utils.node import load_node_class

    assert load_node_class(DataList.class_node_type) is DataList
    assert load_node_class(DataDict.class_node_type) is DataDict
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


def test_querybuilder_data_includes_containers(aiida_profile_clean):
    """``Data`` matches all data nodes and ``Container`` matches only containers."""
    Int(1).store()
    DataList([Int(2)]).store()
    DataDict({'a': Int(3)}).store()

    # Owned children are ``DbNode`` rows too, so they match data queries as well: one standalone ``Int`` plus
    # two containers plus their two owned ``Int`` children.
    assert QueryBuilder().append(Data).count() == 5
    assert QueryBuilder().append(Container).count() == 2
    assert QueryBuilder().append(DataList).count() == 1
    assert QueryBuilder().append(DataDict).count() == 1
    assert QueryBuilder().append(DataList, subclassing=False).count() == 1
    assert {type(node) for (node,) in QueryBuilder().append(Data, project='*').all()} == {
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


def test_process_ports_accept_data_and_containers():
    """Process ports declared with ``Data`` accept data and containers alike."""
    from aiida.engine.processes.ports import InputPort

    port = InputPort('port', valid_type=Data)
    assert port.validate(Int(1)) is None
    assert port.validate(DataList([Int(1)])) is None
    assert port.validate(DataDict({'a': Int(1)})) is None


def test_infer_data_node_types():
    """Type inference preserves the declared data class."""
    from aiida.engine.processes.ports import _infer_node_types

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
    outputs = {
        entry.link_label: entry.node
        for entry in node.base.links.get_outgoing(node_class=Data, include_container_members=False)
    }
    assert set(outputs) == {'result'}
    assert isinstance(outputs['result'], DataList)
    assert outputs['result'].uuid == results.uuid
    # The stored container plus its two owned children are all data-node rows.
    assert QueryBuilder().append(Data).count() == 3


def test_create_links_for_nested_members():
    """Every newly created member has its own CREATE link, but only the root is an output port."""
    from aiida.common.links import LinkType
    from aiida.engine import calcfunction, run_get_node
    from aiida.orm import load_node

    @calcfunction
    def make_summary():
        return DataDict({'numbers': DataList([Int(1)])})

    summary, calculation = run_get_node(make_summary)
    numbers = summary['numbers']
    leaf = load_node(numbers[0].pk)

    for node in (summary, numbers, leaf):
        assert node.base.links.get_incoming(link_type=LinkType.CREATE).one().node == calculation
        assert node.creator == calculation
    assert set(calculation.outputs) == {'result'}


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
    assert results.creator == node
