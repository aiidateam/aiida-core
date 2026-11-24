###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Storage-owned subtree persistence: ``store_container_subtree``.

Regression tests for the storage-layer orchestration of owned-container
subtree storage (node rows plus membership edges in a single transaction,
joining an enclosing transaction when present). Covers successful nested
storage (ordering and root-link forwarding) and
rollback on partial node/membership failure with no partial graph left
behind. Storage level only: inputs are backend entities plus explicit
:class:`~aiida.storage.ownership.OwnedContainerSpec` metadata, never ORM
container objects.
"""

import pytest

from aiida.common.exceptions import NotExistent
from aiida.orm import DataList, Int, load_node
from aiida.storage import ownership as ownership_contract

pytestmark = pytest.mark.usefixtures('aiida_profile_clean')

INT_TYPE = Int.class_node_type
LIST_TYPE = DataList.class_node_type


def _leaf(value):
    """Return an unstored ``Int`` node with the given value."""
    return Int(value)


def _empty_list():
    """Return an unstored empty ``DataList`` (correct node type and user, no ORM membership used)."""
    return DataList()


def _spec(owner, children, kind='list'):
    """Build an :class:`OwnedContainerSpec` for ``children`` in the given order."""
    return ownership_contract.OwnedContainerSpec(
        owner=owner.backend_entity,
        members=[
            ownership_contract.OwnedMemberSpec(entity=child.backend_entity, position=position, key=None)
            for position, child in enumerate(children)
        ],
        kind=kind,
    )


def _assert_no_rows(backend, entities):
    """Assert none of the backend entities has a persisted row."""
    for entity in entities:
        if entity.pk is not None:
            with pytest.raises(NotExistent):
                backend.nodes.get(pk=entity.pk)


def test_store_nested_subtree_success(backend):
    """Nested subtree stores atomically: order and root-link forwarding hold."""
    leaf_a, leaf_b, leaf_c = _leaf(1), _leaf(2), _leaf(3)
    inner, inner2, outer = _empty_list(), _empty_list(), _empty_list()

    entities = [
        leaf_a.backend_entity,
        leaf_b.backend_entity,
        inner.backend_entity,
        leaf_c.backend_entity,
        inner2.backend_entity,
        outer.backend_entity,
    ]
    specs = [
        _spec(inner, [leaf_a, leaf_b]),
        _spec(inner2, [leaf_c]),
        _spec(outer, [inner, inner2]),
    ]

    from unittest import mock

    from aiida.common.links import LinkType
    from aiida.orm.utils.links import LinkTriple

    link_source = _leaf(0)
    link_source.store()
    root_links = [LinkTriple(link_source, LinkType.CREATE, 'output')]
    seen_store = {}
    seen_store_container = {}
    leaf_cls = type(leaf_a.backend_entity)
    container_cls = type(outer.backend_entity)
    real_store = leaf_cls.store
    real_store_container = container_cls.store_container

    def recording_store(self, links=None, clean=True):
        seen_store[self.uuid] = links
        return real_store(self, links, clean=clean)

    def recording_store_container(self, links=None, clean=True):
        seen_store_container[self.uuid] = links
        return real_store_container(self, links, clean=clean)

    with (
        mock.patch.object(leaf_cls, 'store', recording_store),
        mock.patch.object(container_cls, 'store_container', recording_store_container),
    ):
        backend.store_container_subtree(entities, specs, root_links=root_links, clean=True)

    # Leaf data rows go through ``BackendNode.store``; container rows go through the dedicated
    # ``BackendContainer.store_container`` and never ``BackendNode.store``.
    assert set(seen_store) == {leaf_a.backend_entity.uuid, leaf_b.backend_entity.uuid, leaf_c.backend_entity.uuid}
    assert set(seen_store_container) == {
        inner.backend_entity.uuid,
        inner2.backend_entity.uuid,
        outer.backend_entity.uuid,
    }
    # Only the ownership root (last entity) receives the incoming links.
    assert seen_store_container[outer.backend_entity.uuid] == root_links
    for entity in entities[:-1]:
        assert seen_store.get(entity.uuid) is None
        assert seen_store_container.get(entity.uuid) is None

    reloaded = load_node(outer.pk)
    assert isinstance(reloaded, DataList)
    assert [[child.value for child in nested] for nested in reloaded] == [[1, 2], [3]]
    assert [triple.node.uuid for triple in reloaded.base.links.get_incoming().all()] == [link_source.uuid]


def test_store_subtree_node_failure_rolls_back(backend):
    """A node-row failure rolls back the whole subtree: no partial graph remains."""
    leaf_a, leaf_b = _leaf(1), _leaf(2)
    owner = _empty_list()
    entities = [leaf_a.backend_entity, leaf_b.backend_entity, owner.backend_entity]
    specs = [_spec(owner, [leaf_a, leaf_b])]

    real_store = type(leaf_a.backend_entity).store

    def fail_on_second(self, links=None, clean=True):
        if getattr(self, '_fail_store', False):
            raise RuntimeError('simulated node storage failure')
        return real_store(self, links, clean=clean)

    leaf_b.backend_entity._fail_store = True  # type: ignore[attr-defined]
    from unittest import mock

    with mock.patch.object(type(leaf_a.backend_entity), 'store', fail_on_second):
        with pytest.raises(RuntimeError, match='simulated node storage failure'):
            backend.store_container_subtree(entities, specs)

    _assert_no_rows(backend, entities)


def test_store_subtree_membership_failure_rolls_back(backend):
    """A membership failure after node rows rolls everything back: no partial graph remains."""
    leaf_a, leaf_b = _leaf(1), _leaf(2)
    inner, inner2, outer = _empty_list(), _empty_list(), _empty_list()
    entities = [
        leaf_a.backend_entity,
        inner.backend_entity,
        leaf_b.backend_entity,
        inner2.backend_entity,
        outer.backend_entity,
    ]
    specs = [
        _spec(inner, [leaf_a]),
        _spec(inner2, [leaf_b]),
        _spec(outer, [inner, inner2]),
    ]

    real_create = backend.create_container_membership
    calls = []

    def fail_on_second(owner_id, members, **kwargs):
        calls.append(owner_id)
        if len(calls) == 2:
            raise RuntimeError('simulated membership failure')
        return real_create(owner_id, members, **kwargs)

    from unittest import mock

    with mock.patch.object(backend, 'create_container_membership', fail_on_second):
        with pytest.raises(RuntimeError, match='simulated membership failure'):
            backend.store_container_subtree(entities, specs)

    assert calls and len(calls) == 2
    _assert_no_rows(backend, entities)
