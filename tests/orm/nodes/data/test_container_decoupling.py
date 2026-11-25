###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Decoupling of owned containers from ``Data`` semantics and storage.

Covers the clarified requirement: containers behave like data nodes for
provenance (container-level process input/output links, no new link
tables, shared ``DbNode`` identity) but are decoupled from ``Data`` —
they subclass :class:`~aiida.orm.nodes.node.Node` via
:class:`~aiida.orm.nodes.data.container.Container`, persist through the
dedicated :class:`~aiida.orm.implementation.containers.BackendContainer`
entity (``store_container``), and never through ``BackendNode.store``.
"""

from unittest import mock

import pytest

from aiida.common.exceptions import IntegrityError
from aiida.common.links import LinkType
from aiida.orm import Container, Data, DataDict, DataList, Int, Node, load_node

INT_TYPE = Int.class_node_type
LIST_TYPE = DataList.class_node_type
DICT_TYPE = DataDict.class_node_type


def test_containers_are_not_data_but_share_node_identity():
    """Containers are ``Node``/``Container`` instances, never ``Data``; type strings are unchanged."""
    container = DataList([Int(1)])
    nested = DataDict({'inner': DataList([Int(2)])})

    assert isinstance(container, Node)
    assert isinstance(container, Container)
    assert not isinstance(container, Data)
    assert not isinstance(nested, Data)
    assert not isinstance(nested['inner'], Data)
    assert isinstance(nested['inner'], Container)

    # Provenance identity is preserved: stored ``node_type`` strings are unchanged, so no migration rewrites them.
    assert DataList.class_node_type == 'data.core.data_list.DataList.'
    assert DataDict.class_node_type == 'data.core.data_dict.DataDict.'
    assert container.node_type == LIST_TYPE

    container.store()
    reloaded = load_node(container.pk)
    assert isinstance(reloaded, DataList)
    assert not isinstance(reloaded, Data)
    assert [child.value for child in reloaded] == [1]

    # Containers are queryable by their concrete type through the shared node identity.
    from aiida.orm import QueryBuilder

    queried = QueryBuilder().append(DataList, filters={'id': container.pk}).first(flat=True)
    assert isinstance(queried, DataList)
    assert queried.uuid == container.uuid


def test_container_backend_entity_is_dedicated():
    """Container backend entities are ``BackendContainer`` with their own store path."""
    from aiida.orm.implementation.containers import BackendContainer
    from aiida.orm.implementation.nodes import BackendNode

    container = DataList([Int(1)])
    leaf = Int(2)
    container_entity = container.backend_entity
    leaf_entity = leaf.backend_entity

    # Common node identity: container entities remain ``BackendNode`` instances ...
    assert isinstance(container_entity, BackendNode)
    # ... but through the dedicated ``BackendContainer`` abstraction.
    assert isinstance(container_entity, BackendContainer)
    assert type(container_entity) is not type(leaf_entity)
    assert not hasattr(leaf_entity, 'store_container')

    # The generic data path loudly refuses containers instead of silently persisting them as plain data.
    with pytest.raises(IntegrityError, match='BackendContainer'):
        container_entity.store()

    # Leaf data still goes through ``BackendNode.store``.
    leaf_entity.store()
    assert leaf.is_stored


def test_container_store_never_calls_backend_node_store():
    """Storing a nested subtree never routes a container row through ``BackendNode.store``."""
    from aiida.storage.psql_dos.orm.nodes import SqlaNode

    inner = DataList([Int(1), Int(2)])
    inner2 = DataList([Int(3)])
    outer = DataList([inner, inner2])
    # Flatten in-memory: nested containers hold copies, so collect the owned subtree the store would persist.
    subtree = outer._collect_subtree()

    seen_node_types: list[str] = []
    real_store = SqlaNode.store

    def recording_store(self, links=None, clean=True):
        seen_node_types.append(self.node_type)
        return real_store(self, links, clean=clean)

    with mock.patch.object(SqlaNode, 'store', recording_store):
        outer.store()

    assert outer.is_stored
    # Only leaf data rows went through ``BackendNode.store``; container rows used ``store_container``.
    assert seen_node_types
    assert set(seen_node_types) == {INT_TYPE}
    assert [child.value for child in outer[0]] == [1, 2]
    assert [child.value for child in outer[1]] == [3]
    assert outer.element_type == LIST_TYPE
    assert all(node.is_stored for node in subtree)


def test_nested_failure_rolls_back_and_retries():
    """A nested membership failure stores nothing and the retained subtree stays editable/retryable."""
    outer = DataList([DataList([Int(1), Int(2)]), DataList([Int(3)])])
    backend = outer.backend
    subtree = outer._collect_subtree()

    real_create = backend.create_container_membership
    calls = []

    def fail_on_second(owner_id, members, assert_element_type=None, **kwargs):
        calls.append(owner_id)
        if len(calls) == 2:
            raise RuntimeError('simulated nested membership failure')
        return real_create(owner_id, members, assert_element_type, **kwargs)

    with mock.patch.object(backend, 'create_container_membership', fail_on_second):
        with pytest.raises(RuntimeError, match='simulated nested membership failure'):
            outer.store()

    assert calls and len(calls) == 2
    # No partial graph: every retained object is unstored, with content, order and locks intact.
    assert not outer.is_stored
    for node in subtree:
        assert not node.is_stored
    assert [[child.value for child in nested] for nested in outer] == [[1, 2], [3]]
    assert outer.element_type == LIST_TYPE
    assert outer[0].element_type == INT_TYPE

    # Retry without fresh objects succeeds and stores the complete subtree atomically.
    outer.store()
    assert outer.is_stored
    reloaded = load_node(outer.pk)
    assert [[child.value for child in nested] for nested in reloaded] == [[1, 2], [3]]


@pytest.mark.requires_broker
def test_process_container_io_retains_root_provenance():
    """Process container inputs/outputs link at the container root with values preserved."""
    from aiida.engine import calcfunction

    @calcfunction
    def wrap_in_list(value):
        """Wrap one value in a new container (returned as the process output)."""
        result = DataList()
        result.append(value)
        return result

    @calcfunction
    def unwrap_single(value):
        """Return the input itself (the engine re-copies recorded input copies)."""
        return value

    source = Int(7)
    result, calc_node = wrap_in_list.run_get_node(source)

    # The output is a stored container linked at the root; provenance is CREATE, values preserved.
    assert isinstance(result, DataList)
    assert not isinstance(result, Data)
    assert result.is_stored
    assert [child.value for child in result] == [7]
    assert result.element_type == INT_TYPE
    incoming = result.base.links.get_incoming(link_type=LinkType.CREATE).all()
    assert len(incoming) == 1
    assert incoming[0].node.uuid == calc_node.uuid
    assert calc_node.is_stored

    # Owned children passed as inputs are detached to standalone copies (new identity, same content).
    outer = DataList([Int(11)])
    owned = outer[0]
    assert owned._container_owner is outer
    echoed, echo_node = unwrap_single.run_get_node(owned)
    assert echoed.value == 11
    recorded = echo_node.base.links.get_incoming(link_type=LinkType.INPUT_CALC).all()
    assert len(recorded) == 1
    assert recorded[0].node.uuid != owned.uuid
    # Returning a recorded input copy re-copies it instead of closing a provenance cycle over the input.
    assert echoed.uuid != recorded[0].node.uuid
    # The original container is untouched and still unstored.
    assert not outer.is_stored
    assert outer[0].value == 11
