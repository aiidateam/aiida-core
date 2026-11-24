###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Focused tests for the owned-container scaffolding: :class:`DataList` and :class:`DataDict`.

Covers copy-on-insert, mixed member types, pre-storage mutation/ordering/keys, atomic freeze-on-store with
rollback/retry, and UUID identity equality/hashing.
"""

from uuid import UUID

import pytest
from sqlalchemy.exc import DataError

from aiida.common.exceptions import IntegrityError, ModificationNotAllowed
from aiida.orm import DataDict, DataList, Dict, Int, List, QueryBuilder, Str, load_node


def test_entry_points():
    """The new types are registered without changing existing ``List``/``Dict`` behavior."""
    from aiida.plugins import entry_point

    assert entry_point.load_entry_point('aiida.container', 'core.data_list') is DataList
    assert entry_point.load_entry_point('aiida.container', 'core.data_dict') is DataDict
    plain_list = List([1, 2])
    plain_dict = Dict({'a': 1})
    assert plain_list.get_list() == [1, 2]
    assert plain_dict.get_dict() == {'a': 1}


@pytest.mark.parametrize('store_inner_first', [False, True])
def test_store_rejects_multiple_owners(aiida_profile_clean, store_inner_first):
    """Drafts retain the same nodes, and storing a conflicting tree commits nothing."""
    node = Int(1)
    inner = DataList([node])
    outer = DataList([node, inner])
    assert inner[0] is outer[0] is node
    assert outer[1] is inner

    if store_inner_first:
        inner.store()

    message = 'already owned' if store_inner_first else 'multiple memberships'
    with pytest.raises(IntegrityError, match=message):
        outer.store()

    assert not outer.is_stored
    assert inner.is_stored is store_inner_first
    assert node.is_stored is store_inner_first
    assert QueryBuilder().append(DataList).count() == int(store_inner_first)
    assert QueryBuilder().append(Int).count() == int(store_inner_first)

    outer[0] = node.clone()
    if store_inner_first:
        outer[1] = inner.clone()
    outer.store()
    assert outer[0].uuid != outer[1][0].uuid


def test_insert_retains_explicit_clone():
    """Members retain the identities supplied by the caller, including explicit copies."""
    source = Int(5)
    explicit = source.clone()
    container = DataList([source, explicit]).store()
    assert container[0] is source
    assert container[1] is explicit
    assert source.uuid != explicit.uuid
    assert [child.uuid for child in load_node(container.pk)] == [source.uuid, explicit.uuid]


def test_remove_draft_member():
    """Removing a draft member returns the same node without storing it."""
    node = Int(1)
    container = DataList([node])
    removed = container.pop(0)
    assert removed is node
    assert len(container) == 0
    assert not node.is_stored

    node.store()
    container.append(node)
    container.store()
    assert load_node(container.pk)[0].pk == node.pk


def test_nested_detach_root_only_and_recursive_copy():
    """Detaching a nested container keeps its descendants; copying is recursive with new identities."""
    inner = DataList([Int(1), Int(2)])
    outer = DataList()
    outer.append(inner)
    nested = outer[0]
    assert nested[0].value == 1

    detached = outer.pop(0)
    assert len(outer) == 0
    assert detached is inner
    assert not detached[0].is_stored

    clone = detached.clone()
    assert clone.uuid != detached.uuid
    assert [child.uuid for child in clone] != [child.uuid for child in detached]
    assert [child.value for child in clone] == [1, 2]
    # No source-copy tracking: no provenance links and no source UUID recorded on the copy.
    assert not clone.base.links.get_incoming().all()
    assert clone.uuid != detached.uuid
    for attribute in clone.base.attributes.all.values():
        assert detached.uuid not in str(attribute)


def test_clone_metadata_independence():
    """Container cloning follows ``Data.clone()`` metadata behavior with independent mutable metadata."""
    node = DataList([Int(1)])
    node.label = 'label'
    node.description = 'description'
    node.base.extras.set('extra', {'nested': [1]})
    import copy as copy_module

    clone = node.clone()
    assert [child.uuid for child in copy_module.deepcopy(node)] != [child.uuid for child in node]
    assert clone.label == 'label'
    assert clone.description == 'description'
    assert clone.base.extras.get('extra') == {'nested': [1]}
    node.base.extras.set('extra', {'nested': [2]})
    node.label = 'changed'
    assert clone.base.extras.get('extra') == {'nested': [1]}
    assert clone.label == 'label'


def test_copy_usable_after_source_deletion():
    """Copies outlive their source, but a referenced node is protected from deletion."""
    source = Int(7).store()
    container = DataList([source.clone()])
    referencing_list = DataList([source]).store()
    backend = source.backend
    with pytest.raises(IntegrityError, match='still references it'), backend.transaction():
        backend.delete_nodes_and_connections([source.pk])
    with backend.transaction():
        backend.delete_nodes_and_connections([referencing_list.pk])
    backend.nodes.delete(source.pk)
    assert [child.value for child in container] == [7]
    container.store()
    assert container[0].value == 7


def test_stored_nested_container_requires_explicit_clone():
    """A stored container cannot be adopted; an explicit clone can be."""
    nested = DataList([Int(1)]).store()
    outer = DataList([nested])
    assert outer[0] is nested
    with pytest.raises(IntegrityError, match='insert an explicit clone'):
        outer.store()

    clone = nested.clone()
    outer[0] = clone
    outer.store()
    copied = load_node(outer.pk)[0]
    assert copied.uuid == clone.uuid != nested.uuid
    assert copied[0].uuid == clone[0].uuid != nested[0].uuid
    assert copied[0].value == nested[0].value


def test_store_rejects_membership_cycle(aiida_profile_clean):
    """Cycles can exist in drafts but cannot be stored or recursively cloned."""
    outer = DataList()
    inner = DataDict({'outer': outer})
    outer.append(inner)
    with pytest.raises(IntegrityError, match='cycle'):
        outer.store()
    with pytest.raises(IntegrityError, match='cycle'):
        outer.clone()
    assert QueryBuilder().append(DataList).count() == 0
    assert QueryBuilder().append(DataDict).count() == 0

    del inner['outer']
    outer.store()
    assert load_node(outer.pk)[0].uuid == inner.uuid


def test_heterogeneous_list_round_trip():
    """Owned and referenced entries reload in order and can be used as process inputs."""
    from aiida.engine import calcfunction

    @calcfunction
    def produce():
        return Int(3)

    @calcfunction
    def consume(numbers):
        return Int(numbers[2].value)

    source = produce()
    container = DataList([Int(1)])
    container.append(Int(2))
    container[0] = Str('first')
    container.append(source)
    container.store()

    reloaded = load_node(container.pk)
    assert [type(child) for child in reloaded] == [Str, Int, Int]
    assert [child.value for child in reloaded] == ['first', 2, 3]
    assert reloaded[2].uuid == source.uuid
    assert reloaded[2].creator.uuid == source.creator.uuid
    assert consume(reloaded).value == 3
    builder = QueryBuilder().append(DataList, filters={'id': reloaded.pk}, tag='owner')
    builder.append(Int, with_members='owner', project='id')
    assert set(builder.all(flat=True)) == {reloaded[1].pk, source.pk}

    other = DataList()
    other.append(source)
    with pytest.raises(IntegrityError, match='already has a membership row'):
        other.store()


def test_heterogeneous_nested_dict_round_trip():
    """A mapping can contain leaf data and both kinds of nested container."""
    container = DataDict(
        {'sample_name': Str('sample'), 'values': DataList([Int(1), Str('two')]), 'metadata': DataDict()}
    )
    container.store()

    reloaded = load_node(container.pk)
    assert list(reloaded) == ['sample_name', 'values', 'metadata']
    assert reloaded['sample_name'].value == 'sample'
    assert [child.value for child in reloaded['values']] == [1, 'two']
    assert isinstance(reloaded['metadata'], DataDict)


def test_non_data_rejected():
    """Process nodes and non-data nodes are rejected."""
    from aiida.orm import CalcJobNode

    container = DataList()
    with pytest.raises(TypeError):
        container.append(CalcJobNode())
    mapping = DataDict()
    with pytest.raises(TypeError):
        mapping['key'] = 'not-a-node'


def test_list_mutation_and_order():
    """Pre-storage list mutation: replace, remove, reorder."""
    container = DataList([Int(1), Int(2), Int(3)])
    container[1] = Int(20)
    assert [child.value for child in container] == [1, 20, 3]
    container.move(0, 2)
    assert [child.value for child in container] == [20, 3, 1]
    container.insert(1, Int(15))
    assert [child.value for child in container] == [20, 15, 3, 1]
    assert len(container) == 4
    with pytest.raises(TypeError):
        container[1:2]  # type: ignore[index]


def test_dict_keys_order_and_strings_only():
    """Dict keys are strings-only with insertion-order semantics."""
    mapping = DataDict({'a': Int(1), 'b': Int(2)})
    with pytest.raises(TypeError):
        mapping[1] = Int(3)
    with pytest.raises(TypeError):
        mapping[None] = Int(3)
    with pytest.raises(TypeError):
        _ = mapping[1]
    with pytest.raises(KeyError):
        _ = mapping['missing']

    # Replacement preserves position.
    mapping['a'] = Int(10)
    assert list(mapping.keys()) == ['a', 'b']
    assert mapping['a'].value == 10
    # Remove plus reinsert moves the key to the end.
    del mapping['a']
    mapping['a'] = Int(11)
    assert list(mapping.keys()) == ['b', 'a']
    assert list(mapping.items())[1][1].value == 11
    assert 'b' in mapping
    assert mapping.get('missing') is None


def test_dict_keys_are_literal_strings() -> None:
    """Keys are stored verbatim, including strings that would be invalid process ports."""
    keys = ['', '_hidden', 'suffix_', 'nested__name', 'with.dot', 'énergie', '1st', 'class', 'sample-name', 'é' * 255]
    mapping = DataDict({key: Int(index) for index, key in enumerate(keys)}).store()
    reloaded = load_node(mapping.pk)
    assert [(key, node.value) for key, node in reloaded.items()] == list(zip(keys, range(len(keys)), strict=True))


@pytest.mark.parametrize(
    ('key', 'message'),
    [('x' * 256, '255'), ('before\x00after', 'NUL')],
    ids=['too-long', 'nul'],
)
def test_dict_rejects_unstorable_keys(backend, key: str, message: str) -> None:
    """Storage errors propagate without freezing the dictionary or its children."""
    mapping = DataDict({key: Int(1)})
    child = mapping[key]
    error = IntegrityError if backend.get_session().get_bind().dialect.name == 'sqlite' else DataError
    with pytest.raises(error, match=message):
        mapping.store()

    assert not mapping.is_stored
    assert not child.is_stored
    del mapping[key]
    mapping['valid'] = Int(2)
    mapping.store()


def test_store_freezes_subtree_and_reloads_in_order():
    """Storing the root freezes the subtree; reloading preserves content, order and type metadata."""
    container = DataList([Int(1), Int(2), Int(3)])
    container.move(0, 2)
    mapping = DataDict({'b': Int(2), 'a': Int(1)})
    mapping.store()

    assert mapping.is_stored
    for child in mapping.values():
        assert child.is_stored
    with pytest.raises(ModificationNotAllowed):
        mapping['c'] = Int(3)
    with pytest.raises(ModificationNotAllowed):
        mapping['a'] = Int(3)
    with pytest.raises(ModificationNotAllowed):
        del mapping['a']
    # Stored children are immutable like any stored node; re-storing is a harmless no-op.
    stored_child = next(iter(mapping.values()))
    with pytest.raises(ModificationNotAllowed):
        stored_child.base.attributes.set('new_attribute', 1)
    assert stored_child.store() is stored_child
    # Extras stay mutable after freezing (immutable subtree modulo extras).
    mapping.base.extras.set('post_store', True)
    assert mapping.base.extras.get('post_store') is True
    stored_child.base.extras.set('post_store', 1)
    assert stored_child.base.extras.get('post_store') == 1

    reloaded = load_node(mapping.pk)
    assert isinstance(reloaded, DataDict)
    assert list(reloaded.keys()) == ['b', 'a']
    assert [child.value for child in reloaded.values()] == [2, 1]

    container.store()
    reloaded_list = load_node(container.pk)
    assert [child.value for child in reloaded_list] == [2, 3, 1]
    with pytest.raises(ModificationNotAllowed):
        reloaded_list.append(Int(4))


def test_empty_container_stores_with_unset_type():
    """A container that never held an element stores with unset type and accepts any type afterwards."""
    container = DataList()
    container.store()
    reloaded = load_node(container.pk)
    assert len(reloaded) == 0


def test_store_failure_leaves_no_partial_graph_and_retryable():
    """A mid-transaction failure recovers the same retained objects, editable and retryable."""
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

    # Nothing was partially stored: the same retained objects are unstored and editable.
    assert not container.is_stored
    for child in children:
        assert not child.is_stored
    assert [child.value for child in container] == [1, 2]
    assert list(container) == children
    container.append(Int(3))
    assert [child.value for child in container] == [1, 2, 3]

    # Retry without fresh objects succeeds and stores the complete subtree atomically.
    container.store()
    assert container.is_stored
    assert [child.value for child in container] == [1, 2, 3]
    assert list(container)[:2] == children


def test_enclosing_transaction_rollback_recovers_and_retries():
    """Rollback of an enclosing transaction after successful storage restores editable retained objects."""
    container = DataDict({'a': Int(1), 'b': Int(2)})
    backend = container.backend
    with pytest.raises(RuntimeError, match='outer failure'):
        with backend.transaction():
            container.store()
            assert container.is_stored
            raise RuntimeError('outer failure')

    assert not container.is_stored
    assert not any(child.is_stored for child in container.values())
    assert list(container.keys()) == ['a', 'b']
    assert [child.value for child in container.values()] == [1, 2]

    container['c'] = Int(3)
    container.store()
    assert container.is_stored
    assert list(container.keys()) == ['a', 'b', 'c']


def test_equality_and_hash_are_uuid_identity():
    """Independent copies are unequal even with matching content; hashing is UUID-based."""
    container = DataList([Int(1)])
    clone = container.clone()
    same = clone
    assert clone == same
    assert container != clone
    assert container.__hash__() == int(UUID(container.uuid))
    assert hash(container) == hash(UUID(container.uuid))
    assert hash(container) != hash(clone)
    container.store()
    assert load_node(container.pk) == container
    assert hash(load_node(container.pk)) == hash(container)


def test_store_membership_failure_leaves_no_partial_graph_and_retryable():
    """A membership failure during storage recovers the retained subtree, editable and retryable."""
    outer = DataList([DataList([Int(1)]), DataList([Int(2)])])
    nested = list(outer)

    backend = outer.backend
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
            outer.store()

    assert len(calls) == 2
    # Nothing was partially stored: the same retained objects are unstored and editable.
    assert not outer.is_stored
    assert not any(child.is_stored for child in outer)
    assert [[child.value for child in nested] for nested in outer] == [[1], [2]]
    assert list(outer) == nested
    outer.append(DataList([Int(3)]))
    assert len(outer) == 3

    # Retry without fresh objects stores the complete nested subtree atomically.
    outer.store()
    assert outer.is_stored
    assert [[child.value for child in nested] for nested in outer] == [[1], [2], [3]]
    assert list(outer)[:2] == nested
