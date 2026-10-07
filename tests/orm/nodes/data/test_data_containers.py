###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Focused tests for the owned-container scaffolding: :class:`DataList` and :class:`DataDict`.

Covers copy-on-insert, type locking, pre-storage mutation/ordering/keys, atomic freeze-on-store with
rollback/retry, and UUID identity equality/hashing.
"""

from uuid import UUID

import pytest

from aiida.common.exceptions import ModificationNotAllowed
from aiida.orm import DataDict, DataList, Dict, Int, List, Str, load_node


def test_entry_points():
    """The new types are registered without changing existing ``List``/``Dict`` behavior."""
    from aiida.plugins import entry_point

    assert entry_point.load_entry_point('aiida.data', 'core.data_list') is DataList
    assert entry_point.load_entry_point('aiida.data', 'core.data_dict') is DataDict
    plain_list = List([1, 2])
    plain_dict = Dict({'a': 1})
    assert plain_list.get_list() == [1, 2]
    assert plain_dict.get_dict() == {'a': 1}


def test_copy_on_insert():
    """Insertion always copies: source untouched, repeated inserts distinct, copies copy again."""
    container = DataList()
    source = Int(5)

    container.append(source)
    container.append(source)
    first, second = container[0], container[1]

    assert first.uuid != source.uuid
    assert second.uuid != source.uuid
    assert first.uuid != second.uuid
    assert first.value == second.value == 5
    # The source stays standalone and usable; it was not adopted or invalidated.
    assert not source.is_stored
    assert source.value == 5

    # Inserting an explicitly created copy copies it again.
    explicit = first.clone()
    assert explicit.uuid != first.uuid
    container.append(explicit)
    assert container[2].uuid != explicit.uuid
    assert container[2].value == 5


def test_owned_child_store_rejected_and_detach():
    """Owned children cannot be stored independently; removed children become standalone."""
    container = DataList([Int(1)])
    with pytest.raises(ModificationNotAllowed):
        container[0].store()

    removed = container.pop(0)
    assert len(container) == 0
    # Removal does not store or invalidate: the child is standalone, unstored and editable.
    assert not removed.is_stored
    removed.store()
    assert removed.is_stored

    # Reinserting the detached node copies it again.
    container.append(removed)
    assert container[0].uuid != removed.uuid


def test_nested_detach_root_only_and_recursive_copy():
    """Detaching a nested container keeps its descendants; copying is recursive with new identities."""
    inner = DataList([Int(1), Int(2)])
    outer = DataList()
    outer.append(inner)
    nested = outer[0]
    assert nested[0].value == 1

    detached = outer.pop(0)
    assert len(outer) == 0
    # Only the nested root is detached; its descendants remain owned by it.
    with pytest.raises(ModificationNotAllowed):
        detached[0].store()

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
    """Copies stay usable after deletion of their source."""
    source = Int(7)
    source.store()
    container = DataList([source])
    source_pk = source.pk
    source.backend.nodes.delete(source_pk)
    assert [child.value for child in container] == [7]
    container.store()
    assert container[0].value == 7


def test_type_locking():
    """Element type is inferred from the first element and stays locked, even when emptied."""
    container = DataList()
    assert container.element_type is None
    container.append(Int(1))
    assert container.element_type == Int.class_node_type
    with pytest.raises(TypeError):
        container.append(Str('nope'))
    with pytest.raises(TypeError):
        container[0] = Str('nope')
    container.clear()
    assert len(container) == 0
    with pytest.raises(TypeError):
        container.append(Str('still locked'))
    container.append(Int(2))
    assert container[0].value == 2


def test_nested_homogeneity_by_concrete_container_type():
    """Nested homogeneity compares only the concrete container type, each enforcing its own rule."""
    inner_ints = DataList([Int(1)])
    inner_strs = DataList([Str('a')])
    outer = DataList([inner_ints])
    outer.append(inner_strs)
    assert len(outer) == 2
    assert [child.value for child in outer[1]] == ['a']
    with pytest.raises(TypeError):
        outer.append(Int(1))


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
    assert reloaded.element_type == Int.class_node_type

    container.store()
    reloaded_list = load_node(container.pk)
    assert [child.value for child in reloaded_list] == [2, 3, 1]
    with pytest.raises(ModificationNotAllowed):
        reloaded_list.append(Int(4))


def test_empty_container_stores_with_unset_type():
    """A container that never held an element stores with unset type and accepts any type afterwards."""
    container = DataList()
    container.store()
    assert container.element_type is None
    reloaded = load_node(container.pk)
    assert len(reloaded) == 0
    assert reloaded.element_type is None


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
    assert container.element_type == Int.class_node_type
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
    assert container.element_type == Int.class_node_type

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
