###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Issue 4: consistent leaf storability/validation during container subtree store.

Every leaf :class:`~aiida.orm.Data` in an owned-container subtree must receive the same
``_validate_storability`` and relevant ``_validate`` checks as a standalone store, before any
repository or database writes. Nested containers receive the same storability check without
redundant/exponential re-validation: the ownership-root ``_validate`` may only delegate to nested
container ``_validate`` and inspect leaves.

These regressions fail against the current ``Container.store`` (which validates only the root):
invalid/unregistered/unstorable leaves are persisted instead of rejected.
"""

from __future__ import annotations

from unittest import mock

import pytest

from aiida.common.datastructures import StashMode
from aiida.common.exceptions import StoringNotAllowed, ValidationError
from aiida.orm import Data, DataDict, DataList, Int, SinglefileData, load_node
from aiida.orm.nodes.data.container import Container
from aiida.orm.nodes.data.remote.stash.base import RemoteStashData
from aiida.orm.nodes.repository import NodeRepository

pytestmark = pytest.mark.usefixtures('aiida_profile_clean')


class UnregisteredData(Data):
    """Custom leaf with no entry point: standalone store raises ``StoringNotAllowed``."""


def _assert_nothing_persisted(container: Container):
    """Assert the failed store left no partial graph: root/leaves unstored, no DB rows."""
    assert not container.is_stored
    leaves = [node for node in container._collect_subtree() if not isinstance(node, Container)]
    for leaf in leaves:
        assert not leaf.is_stored
    # No database rows for any subtree node.
    from aiida.orm import QueryBuilder

    builder = QueryBuilder().append(Container, filters={'uuid': container.uuid}).all()
    assert builder == []
    for leaf in leaves:
        assert QueryBuilder().append(Data, filters={'uuid': leaf.uuid}).all() == []


def test_valid_registered_leaves_store():
    """Registered valid leaves store atomically through the ownership root."""
    container = DataList([Int(1), Int(2)])
    container.store()
    assert container.is_stored
    assert [child.value for child in container] == [1, 2]
    for child in container:
        assert child.is_stored
    reloaded = load_node(container.pk)
    assert [child.value for child in reloaded] == [1, 2]


def test_unregistered_leaf_rejected_before_writes():
    """Unregistered custom leaf is rejected like a standalone store, before any writes."""
    with pytest.raises(StoringNotAllowed):
        UnregisteredData().store()

    container = DataList([UnregisteredData()])
    backend = container.backend
    with (
        mock.patch.object(NodeRepository, '_store', autospec=True, side_effect=NodeRepository._store) as repo_store,
        mock.patch.object(backend, 'store_container_subtree', wraps=backend.store_container_subtree) as subtree_store,
    ):
        with pytest.raises(StoringNotAllowed):
            container.store()
        repo_store.assert_not_called()
        subtree_store.assert_not_called()
    _assert_nothing_persisted(container)
    # Retained objects stay unstored and editable: detaching and labelling still work, and a fresh
    # valid container stores (element type stays locked, so retry uses a new root).
    removed = container.pop(0)
    assert not removed.is_stored
    removed.label = 'still-editable'
    container.label = 'still-editable'
    assert len(container) == 0
    fresh = DataList([Int(1)])
    fresh.store()
    assert fresh.is_stored


def test_unstorable_leaf_rejected_before_writes():
    """Registered but non-storable leaf (``RemoteStashData``) is rejected before any writes."""
    with pytest.raises(StoringNotAllowed):
        RemoteStashData(stash_mode=StashMode.COPY).store()

    container = DataList([RemoteStashData(stash_mode=StashMode.COPY)])
    backend = container.backend
    with (
        mock.patch.object(NodeRepository, '_store', autospec=True, side_effect=NodeRepository._store) as repo_store,
        mock.patch.object(backend, 'store_container_subtree', wraps=backend.store_container_subtree) as subtree_store,
    ):
        with pytest.raises(StoringNotAllowed):
            container.store()
        repo_store.assert_not_called()
        subtree_store.assert_not_called()
    _assert_nothing_persisted(container)
    assert container.element_type == RemoteStashData.class_node_type
    # Editable after failure: replacement preserves position semantics once fixed.
    container[0] = RemoteStashData(stash_mode=StashMode.COPY)
    assert not container.is_stored


def test_invalid_leaf_rejected_before_writes():
    """Registered leaf failing ``_validate`` (empty ``SinglefileData``) is rejected before any writes."""
    with pytest.raises(ValidationError):
        SinglefileData().store()

    container = DataList([SinglefileData()])
    backend = container.backend
    with (
        mock.patch.object(NodeRepository, '_store', autospec=True, side_effect=NodeRepository._store) as repo_store,
        mock.patch.object(backend, 'store_container_subtree', wraps=backend.store_container_subtree) as subtree_store,
    ):
        with pytest.raises(ValidationError):
            container.store()
        repo_store.assert_not_called()
        subtree_store.assert_not_called()
    _assert_nothing_persisted(container)
    # Retained objects stay editable and retryable.
    container[0] = SinglefileData.from_string('fixed')
    container.store()
    assert container.is_stored


def test_nested_invalid_leaf_rejected_before_writes():
    """Invalid leaf inside a nested container aborts the whole subtree before any writes."""
    inner = DataList([SinglefileData()])
    outer = DataList([inner])
    backend = outer.backend
    with (
        mock.patch.object(NodeRepository, '_store', autospec=True, side_effect=NodeRepository._store) as repo_store,
        mock.patch.object(backend, 'store_container_subtree', wraps=backend.store_container_subtree) as subtree_store,
    ):
        with pytest.raises(ValidationError):
            outer.store()
        repo_store.assert_not_called()
        subtree_store.assert_not_called()
    assert not outer.is_stored
    nested = outer[0]
    assert not nested.is_stored
    assert not nested[0].is_stored
    _assert_nothing_persisted(outer)
    # Ordering/membership survive the failure; the subtree remains editable.
    assert len(outer) == 1
    assert len(nested) == 1


def test_nested_unregistered_leaf_rejected_before_writes():
    """Unregistered leaf inside a nested container aborts the whole subtree before any writes."""
    inner = DataList([UnregisteredData()])
    outer = DataDict({'nested': inner})
    backend = outer.backend
    with (
        mock.patch.object(NodeRepository, '_store', autospec=True, side_effect=NodeRepository._store) as repo_store,
        mock.patch.object(backend, 'store_container_subtree', wraps=backend.store_container_subtree) as subtree_store,
    ):
        with pytest.raises(StoringNotAllowed):
            outer.store()
        repo_store.assert_not_called()
        subtree_store.assert_not_called()
    assert not outer.is_stored
    assert not outer['nested'].is_stored
    assert not outer['nested'][0].is_stored


def test_root_validate_delegates_only_to_nested():
    """Root ``_validate`` inspects leaves without calling leaf ``_validate`` (no redundant recursion)."""
    container = DataList([Int(1), Int(2)])
    with mock.patch.object(Int, '_validate', autospec=True, side_effect=Int._validate) as leaf_validate:
        container._validate()
        leaf_validate.assert_not_called()

    inner = DataList([Int(1)])
    outer = DataList([inner])
    with mock.patch.object(
        Container, '_validate', autospec=True, side_effect=Container._validate
    ) as container_validate:
        outer._validate()
        # Root plus the single nested container: linear delegation, no exponential re-validation.
        assert container_validate.call_count == 2


def test_store_validates_each_leaf_once():
    """Subtree store invokes each leaf ``_validate`` exactly once (linear, not exponential)."""
    inner = DataList([Int(1), Int(2)])
    outer = DataList([inner])
    calls: list[str] = []
    real_validate = Int._validate

    def counting_validate(self):
        calls.append(self.uuid)
        return real_validate(self)

    with mock.patch.object(Int, '_validate', autospec=True, side_effect=counting_validate):
        outer.store()
    assert outer.is_stored
    assert sorted(calls) == sorted(child.uuid for child in outer[0])
    assert len(calls) == 2
