###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Transaction-aware rollback recovery for owned container subtrees.

Regression tests for the storage rollback-hook mechanism
(``StorageBackend.add_rollback_callback``, driven by ``backend.transaction``) and its container
integration (``Container.store`` registers eager subtree recovery when joining an enclosing
transaction).

Recovery happens at rollback time, so the same retained objects are restored to an unstored, editable,
retryable state regardless of whether a retained leaf child or the ownership root is inspected first
afterwards. Collaborators: the SQL transaction implementations (``psql_dos``, ``sqlite_dos`` via
inheritance, ``sqlite_temp``) and the owned-container ORM (``DataList``/``DataDict``).
"""

import pytest

from aiida.orm import DataDict, DataList, Int, Str, load_node

pytestmark = pytest.mark.usefixtures('aiida_profile_clean')


def _assert_no_leaked_scopes(backend):
    """Assert no rollback-callback scope leaked past its transaction."""
    assert getattr(backend, '_rollback_callback_scopes', []) == []


def test_rollback_hook_fires_on_rollback_and_discards_on_commit(backend):
    """Rollback hooks fire when their scope rolls back and are discarded on commit."""
    calls: list[str] = []

    with pytest.raises(RuntimeError, match='boom'):
        with backend.transaction():
            backend.add_rollback_callback(lambda: calls.append('rolled back'))
            raise RuntimeError('boom')
    assert calls == ['rolled back']
    _assert_no_leaked_scopes(backend)

    with backend.transaction():
        backend.add_rollback_callback(lambda: calls.append('rolled back'))
    assert calls == ['rolled back']
    _assert_no_leaked_scopes(backend)

    # Registering outside any transaction scope is a no-op: nothing could roll back.
    backend.add_rollback_callback(lambda: calls.append('no scope'))
    assert calls == ['rolled back']


def test_rollback_hook_nested_savepoint_fires_inner_only(backend):
    """An inner savepoint rollback fires only its own hooks; the outer scope survives and commits."""
    calls: list[str] = []

    with backend.transaction():
        backend.add_rollback_callback(lambda: calls.append('outer'))
        with pytest.raises(RuntimeError, match='inner boom'):
            with backend.transaction():
                backend.add_rollback_callback(lambda: calls.append('inner'))
                raise RuntimeError('inner boom')
        assert calls == ['inner']

    assert calls == ['inner']
    _assert_no_leaked_scopes(backend)


def test_outer_rollback_leaf_checked_first_recovers_subtree(backend):
    """Outer rollback restores the subtree even when a retained leaf is checked before the root."""
    container = DataDict({'a': Int(1), 'b': Str('two')})
    leaf = container['b']

    with pytest.raises(RuntimeError, match='outer failure'):
        with backend.transaction():
            container.store()
            assert container.is_stored
            raise RuntimeError('outer failure')

    # The leaf is inspected first: no root check may be required for recovery.
    assert not leaf.is_stored
    assert not container['a'].is_stored
    assert not container.is_stored
    assert container['b'] is leaf
    assert list(container.keys()) == ['a', 'b']
    assert [child.value for child in container.values()] == [1, 'two']
    _assert_no_leaked_scopes(backend)

    # The same retained objects stay editable and retryable.
    container['c'] = Int(3)
    container.store()
    assert container.is_stored
    assert list(container.keys()) == ['a', 'b', 'c']
    reloaded = load_node(container.pk)
    assert isinstance(reloaded, DataDict)
    assert [child.value for child in reloaded.values()] == [1, 'two', 3]


def test_outer_rollback_nested_leaf_checked_first(backend):
    """Outer rollback restores nested subtrees when a deeply owned leaf is checked before any container."""
    outer = DataList([DataList([Int(1), Int(2)]), DataList([Int(3)])])
    nested = outer[0]
    deep_leaf = outer[0][0]

    with pytest.raises(RuntimeError, match='outer failure'):
        with backend.transaction():
            outer.store()
            assert outer.is_stored
            raise RuntimeError('outer failure')

    # Deepest-first inspection order: leaf, then nested container, then root.
    assert not deep_leaf.is_stored
    assert not outer[0][1].is_stored
    assert not nested.is_stored
    assert not outer.is_stored
    assert outer[0] is nested
    assert outer[0][0] is deep_leaf
    assert [[child.value for child in owned] for owned in outer] == [[1, 2], [3]]
    _assert_no_leaked_scopes(backend)

    outer.append(DataList([Int(4)]))
    outer.store()
    assert outer.is_stored
    assert [[child.value for child in nested] for nested in load_node(outer.pk)] == [[1, 2], [3], [4]]


def test_nested_savepoint_rollback_caught_outer_continues(backend):
    """A savepoint rollback caught inside the outer transaction recovers the subtree; outer work commits."""
    container = DataList([Int(1), Int(2)])
    leaf = container[0]
    witness = Int(99)

    with backend.transaction():
        witness.store()
        assert witness.is_stored
        with pytest.raises(RuntimeError, match='inner failure'):
            with backend.transaction():
                container.store()
                assert container.is_stored
                raise RuntimeError('inner failure')
        # The subtree recovered while the outer transaction is still active; outer work is intact.
        assert not leaf.is_stored
        assert not container.is_stored
        assert witness.is_stored
        # The session remains usable for further writes inside the same outer transaction.
        followup = Int(100)
        followup.store()
        assert followup.is_stored

    assert witness.is_stored
    assert followup.is_stored
    assert not container.is_stored
    _assert_no_leaked_scopes(backend)

    # Retry the same retained objects after the outer transaction committed.
    container.store()
    assert container.is_stored
    assert [child.value for child in container] == [1, 2]
    assert container[0] is leaf


def test_successful_outer_commit_keeps_subtree_stored(backend):
    """A committed enclosing transaction persists the subtree: no recovery runs afterwards."""
    container = DataDict({'a': Int(1)})

    with backend.transaction():
        container.store()
        assert container.is_stored

    assert container.is_stored
    assert container['a'].is_stored
    assert container._container_guard_armed is False  # asserting guard disarm
    assert container._container_recovery_snapshot is None  # asserting snapshot release
    _assert_no_leaked_scopes(backend)

    reloaded = load_node(container.pk)
    assert isinstance(reloaded, DataDict)
    assert [child.value for child in reloaded.values()] == [1]


def test_immediate_failure_recovers_without_outer_transaction(backend):
    """A mid-storage failure with no enclosing transaction recovers the retained subtree."""
    container = DataList([Int(1), Int(2)])
    children = list(container)

    real_store = type(children[0].backend_entity).store

    def fail_on_second(self, links=None, clean=True):
        if getattr(self, '_fail_store', False):
            raise RuntimeError('simulated storage failure')
        return real_store(self, links, clean=clean)

    children[1].backend_entity._fail_store = True  # type: ignore[attr-defined]
    from unittest import mock

    with mock.patch.object(type(children[0].backend_entity), 'store', fail_on_second):
        with pytest.raises(RuntimeError, match='simulated storage failure'):
            container.store()

    # Child-first checks: recovery is synchronous, no root check required.
    for child in children:
        assert not child.is_stored
    assert not container.is_stored
    assert list(container) == children
    assert [child.value for child in container] == [1, 2]
    _assert_no_leaked_scopes(backend)

    container.store()
    assert container.is_stored
    assert list(container) == children
