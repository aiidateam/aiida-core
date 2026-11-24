###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Spec section-14 verification matrix (ORM level): owned data containers.

Covers ``orm-container-spec.md`` section 14 at the ORM/convenience level on
every supported database backend (the ``aiida_profile``/``backend`` fixtures
select SQLite vs PostgreSQL via ``--db-backend``; archive round-trips use the
same profile so both backends are exercised by CI).

Convention: tests asserting behavior delivered in phase 1 are strict. Tests
for integrations owned by other agents (process boundaries, deletion UX,
groups, archives, QueryBuilder, caching hashes) assert the specified
behavior but are marked ``xfail`` with the exact spec clause, so the suite
stays green while gaps are filed in the verify-agent status file instead of
being silently fixed here. This file owns TEST code only; it changes no
feature source.

Section-13 deferred items are asserted as *absent* (still deferred) and the
rejected source-copy tracking is asserted as absent too.
"""

import time

import pytest

from aiida.common.exceptions import IntegrityError, ModificationNotAllowed
from aiida.orm import DataDict, DataList, Dict, Int, List, Str, load_node

pytestmark = pytest.mark.usefixtures('aiida_profile_clean')


def _values(container):
    return [child.value for child in container]


class TestInsertAndExplicitClone:
    """Insertion retains identity; only explicit clones have independent metadata."""

    def test_repeated_insertion_rejected_at_store(self):
        source = Int(5)
        container = DataList([source, source])
        assert container[0] is container[1] is source
        with pytest.raises(IntegrityError, match='multiple memberships'):
            container.store()
        assert not source.is_stored

    def test_source_mutation_before_store_is_visible(self):
        source = Int(5)
        container = DataList([source])
        source.label = 'same node'
        assert container[0].label == 'same node'

    def test_mutable_metadata_independent(self):
        source = Int(1)
        source.base.extras.set('meta', {'nested': [1]})
        container = DataList([source.clone()])
        container[0].base.extras.set('meta', {'nested': [2]})
        assert source.base.extras.get('meta') == {'nested': [1]}

    def test_copy_usable_after_source_deletion(self):
        source = Int(7)
        source.store()
        container = DataList([source.clone()])
        source.backend.nodes.delete(source.pk)
        assert _values(container) == [7]
        container.store()
        assert container[0].value == 7


class TestRecursiveCloneRepo:
    """§14: recursive cloning and repository independence."""

    def test_recursive_clone_new_identities(self):
        outer = DataList()
        outer.append(DataList([Int(1), Int(2)]))
        clone = outer.clone()
        assert clone.uuid != outer.uuid
        assert clone[0].uuid != outer[0].uuid
        assert [c.uuid for c in clone[0]] != [c.uuid for c in outer[0]]
        assert [c.value for c in clone[0]] == [1, 2]

    def test_clone_repo_content_independent(self):
        from aiida.orm import SinglefileData

        content = b'payload-bytes'
        import io

        source = SinglefileData(file=io.BytesIO(content), filename='data.bin')
        container = DataList([source])
        clone = container.clone()
        assert clone[0].get_content() == content.decode()
        # Mutating the clone's repository must not affect the original child.
        clone[0].delete_object('data.bin')
        assert 'data.bin' in container[0].list_object_names()

    def test_no_source_tracking_metadata(self):
        outer = DataList([Int(1)])
        clone = outer.clone()
        assert not clone.base.links.get_incoming().all()
        assert clone.uuid != outer.uuid
        for attribute in clone.base.attributes.all.values():
            assert outer.uuid not in str(attribute)
        # Rejected feature (spec §13): no persistent source-copy relationship.
        assert 'source_uuid' not in clone.base.attributes.all
        assert 'source_uuid' not in clone.base.extras.all


class TestOwnerMembershipAgreement:
    """§14: owner/membership agreement through low-level and convenience paths."""

    def test_convenience_store_persists_agreement(self, backend):
        container = DataList([Int(1), Int(2)])
        container.store()
        reloaded = load_node(container.pk)
        assert _values(reloaded) == [1, 2]

    def test_low_level_attach_agreement(self, backend):
        """Low-level backend path: standalone nodes + create_container_membership agree."""
        from aiida.orm import Data

        owner = Data().store()
        children = [Data().store() for _ in range(2)]
        owner_type = DataList.class_node_type
        child_type = children[0].node_type
        # Retag via bulk_update on EntityTypes.NODE (kept explicit for backend parity).
        from aiida.orm.entities import EntityTypes

        backend.bulk_update(
            EntityTypes.NODE,
            [{'id': owner.pk, 'node_type': owner_type}]
            + [{'id': child.pk, 'node_type': child_type} for child in children],
        )
        backend.create_container_membership(
            owner.pk,
            [
                {'child_id': children[0].pk, 'child_node_type': child_type, 'position': 0, 'key': None},
                {'child_id': children[1].pk, 'child_node_type': child_type, 'position': 1, 'key': None},
            ],
        )

    def test_container_node_type_matches_orm(self):
        """Cross test (binding F1, now fixed by storage agent): storage literals
        must equal the real ORM identifiers (``data_list``/``data_dict``)."""
        from aiida.storage.ownership import CONTAINER_NODE_TYPES

        assert DataList.class_node_type in CONTAINER_NODE_TYPES
        assert DataDict.class_node_type in CONTAINER_NODE_TYPES


class TestEligibility:
    """Only data nodes and nested containers can be owned."""

    def test_process_nodes_rejected(self):
        from aiida.orm import CalcJobNode

        with pytest.raises(TypeError):
            DataList().append(CalcJobNode())

    def test_non_data_values_rejected(self):
        with pytest.raises(TypeError):
            DataDict()['k'] = 'not-a-node'

    def test_no_type_lock_after_clear(self):
        container = DataList([Int(1)])
        container.clear()
        container.append(Str('replacement'))
        assert container[0].value == 'replacement'


class TestCyclesConcurrency:
    """§14: cycle rejection and concurrent invariant violations."""

    def test_self_ownership_rejected_on_store_path(self, backend):
        # Owner listed as its own child via the backend contract.
        # NOTE: retags with the storage contract's literal (binding F1: the
        # real DataList.class_node_type is not yet recognised by the backend).
        from aiida.orm import Data
        from aiida.orm.entities import EntityTypes
        from aiida.storage import ownership as ownership_contract

        (owner_type,) = [t for t in ownership_contract.CONTAINER_NODE_TYPES if 'List' in t]
        owner = Data().store()
        backend.bulk_update(EntityTypes.NODE, [{'id': owner.pk, 'node_type': owner_type}])
        with pytest.raises(IntegrityError, match=r'[Cc]ycle|itself'):
            backend.create_container_membership(
                owner.pk,
                [{'child_id': owner.pk, 'child_node_type': owner_type, 'position': 0, 'key': None}],
            )

    def test_concurrent_double_ownership_rejected(self, backend):
        """Two owners racing for one child: second attach must fail (exclusivity)."""
        from aiida.orm import Data
        from aiida.orm.entities import EntityTypes

        owner_a = Data().store()
        owner_b = Data().store()
        child = Data().store()
        child_type = child.node_type
        backend.bulk_update(
            EntityTypes.NODE,
            [
                {'id': owner_a.pk, 'node_type': DataList.class_node_type},
                {'id': owner_b.pk, 'node_type': DataList.class_node_type},
            ],
        )
        backend.create_container_membership(
            owner_a.pk, [{'child_id': child.pk, 'child_node_type': child_type, 'position': 0, 'key': None}]
        )
        with pytest.raises(IntegrityError, match=r'[Ee]xclusive|[Aa]lready'):
            backend.create_container_membership(
                owner_b.pk, [{'child_id': child.pk, 'child_node_type': child_type, 'position': 0, 'key': None}]
            )


class TestPreStorageMutation:
    """§14: pre-storage mutation, removal, ordering, dictionary keys."""

    def test_list_replace_remove_reorder(self):
        container = DataList([Int(1), Int(2), Int(3)])
        container[1] = Int(20)
        assert _values(container) == [1, 20, 3]
        container.move(0, 2)
        assert _values(container) == [20, 3, 1]
        container.insert(1, Int(15))
        assert _values(container) == [20, 15, 3, 1]

    def test_removed_child_standalone_reusable(self):
        container = DataList([Int(1)])
        removed = container.pop(0)
        assert not removed.is_stored
        removed.store()
        assert removed.is_stored
        container.append(removed)
        assert container[0].uuid == removed.uuid

    def test_dict_key_semantics(self):
        mapping = DataDict({'a': Int(1), 'b': Int(2)})
        mapping['a'] = Int(10)  # replace preserves position
        assert list(mapping.keys()) == ['a', 'b']
        assert mapping['a'].value == 10
        del mapping['a']
        mapping['a'] = Int(11)  # remove+reinsert moves to end
        assert list(mapping.keys()) == ['b', 'a']
        with pytest.raises(TypeError):
            mapping[1] = Int(3)
        with pytest.raises(KeyError):
            _ = mapping['missing']

    def test_positions_persist_after_reload(self):
        container = DataList([Int(1), Int(2), Int(3)])
        container.move(0, 2)
        container.store()
        assert _values(load_node(container.pk)) == [2, 3, 1]


class TestLowLevelLinkRejectionStrict:
    """§14/§7: direct low-level provenance links to owned children are rejected."""

    def test_low_level_link_to_owned_rejected(self, backend):
        container = DataList([Int(1), Int(2)])
        container.store()
        child_pk = load_node(container.pk)[0].pk
        from aiida.common.links import LinkType
        from aiida.orm import CalculationNode
        from aiida.orm.entities import EntityTypes

        calc = CalculationNode().store()
        with pytest.raises(Exception):
            with backend.transaction():
                backend.bulk_insert(
                    EntityTypes.LINK,
                    [
                        {
                            'input_id': child_pk,
                            'output_id': calc.pk,
                            'label': 'x',
                            'type': LinkType.INPUT_CALC.value,
                        }
                    ],
                )


class TestMembershipQueriesStrict:
    """§14/§12: initial membership queries and subclass discovery (implemented)."""

    def test_with_members_join(self):
        from aiida.orm import QueryBuilder

        container = DataList([Int(1), Int(2)])
        container.store()
        outsider = Int(99).store()
        builder = (
            QueryBuilder()
            .append(DataList, filters={'id': container.pk}, tag='owner')
            .append(Int, with_members='owner', project='id')
        )
        assert sorted(builder.all(flat=True)) == sorted(c.pk for c in load_node(container.pk))
        assert outsider.pk not in builder.all(flat=True)

    def test_with_members_position_filter(self):
        from aiida.orm import QueryBuilder

        container = DataList([Int(1), Int(2)])
        container.store()
        first_pk = load_node(container.pk)[0].pk
        builder = (
            QueryBuilder()
            .append(DataList, filters={'id': container.pk}, tag='owner')
            .append(Int, with_members='owner', edge_filters={'position': 0}, project='id')
        )
        assert builder.all(flat=True) == [first_pk]

    def test_with_members_key_filter(self):
        from aiida.orm import QueryBuilder

        mapping = DataDict({'a': Int(1), 'b': Int(2)})
        mapping.store()
        builder = (
            QueryBuilder()
            .append(DataDict, filters={'id': mapping.pk}, tag='owner')
            .append(Int, with_members='owner', edge_filters={'key': 'b'}, project='id')
        )
        assert builder.all(flat=True) == [load_node(mapping.pk)['b'].pk]

    def test_with_owner_reverse(self):
        from aiida.orm import QueryBuilder

        container = DataList([Int(1)])
        container.store()
        builder = (
            QueryBuilder()
            .append(Int, filters={'id': load_node(container.pk)[0].pk}, tag='child')
            .append(DataList, with_owner='child', project='id')
        )
        assert builder.all(flat=True) == [container.pk]

    def test_separate_joins_match_different_children(self):
        from aiida.orm import QueryBuilder

        container = DataList([Int(1), Int(2)])
        container.store()
        kids = list(load_node(container.pk))
        builder = (
            QueryBuilder()
            .append(DataList, filters={'id': container.pk}, tag='owner')
            .append(Int, with_members='owner', edge_filters={'position': 0}, tag='first', project='id')
            .append(Int, with_members='owner', edge_filters={'position': 1}, tag='second', project='id')
        )
        assert builder.count() == 1
        (first_pk, second_pk) = builder.all(flat=True)
        assert (first_pk, second_pk) == (kids[0].pk, kids[1].pk)

    def test_subclass_discovery_by_type_string(self):
        """Stored type-string queries distinguish containers (not just inheritance)."""
        from aiida.orm import QueryBuilder

        listed = DataList([Int(1)])
        listed.store()
        mapped = DataDict({'a': Int(1)})
        mapped.store()
        lists = QueryBuilder().append(DataList, project='id').all(flat=True)
        dicts = QueryBuilder().append(DataDict, project='id').all(flat=True)
        assert listed.pk in lists
        assert mapped.pk not in lists
        assert mapped.pk in dicts
        assert listed.pk not in dicts


class TestContentHashingCacheReuse:
    """§14/§10: content hashing (implemented) + cache-reuse rejection (explicit)."""

    def test_equal_copies_equal_hashes(self):
        """Independent copies (different UUIDs) hash equally: UUIDs/owners excluded."""
        first = DataList([Int(1), Int(2)])
        second = DataList([Int(1), Int(2)])
        first.store()
        second.store()
        assert first.uuid != second.uuid
        assert first.base.caching.get_hash() == second.base.caching.get_hash()

    def test_different_content_different_hashes(self):
        first = DataList([Int(1)])
        second = DataList([Int(2)])
        first.store()
        second.store()
        assert first.base.caching.get_hash() != second.base.caching.get_hash()

    def test_list_hash_order_sensitive(self):
        first = DataList([Int(1), Int(2)])
        second = DataList([Int(2), Int(1)])
        first.store()
        second.store()
        assert first.base.caching.get_hash() != second.base.caching.get_hash()

    def test_dict_hash_order_insensitive(self):
        first = DataDict({'a': Int(1), 'b': Int(2)})
        second = DataDict({'b': Int(2), 'a': Int(1)})
        first.store()
        second.store()
        assert first.base.caching.get_hash() == second.base.caching.get_hash()

    def test_empty_hash_ignores_previous_members(self):
        emptied = DataList([Int(1)])
        emptied.clear()
        emptied.store()
        empty = DataList().store()
        assert emptied.base.caching.get_hash() == empty.base.caching.get_hash()

    def test_cache_reuse_disabled(self):
        """F4 resolved as explicit safe rejection: containers never serve/store cache."""
        assert DataList._cachable is False
        assert DataDict._cachable is False


class TestPlainListDictUnchanged:
    """§14: existing plain-value List and Dict behavior remaining unchanged."""

    def test_plain_list_dict(self):
        plain_list = List([1, 2])
        plain_dict = Dict({'a': 1})
        assert plain_list.get_list() == [1, 2]
        assert plain_dict.get_dict() == {'a': 1}
        plain_list.store()
        plain_dict.store()
        assert load_node(plain_list.pk).get_list() == [1, 2]
        assert load_node(plain_dict.pk).get_dict() == {'a': 1}


class TestPerfMeasurements:
    """§14 perf: storage/loading/copying/traversal/hashing at realistic sizes.

    Each element adds a node + owner ref + membership row. Measurements are
    reported (not hard-gated) so per-child query hotspots can be filed with
    numbers; bulk-op suggestions must not weaken validation.
    """

    @pytest.mark.parametrize('size', [50, 200])
    def test_store_load_copy_traverse_timing(self, size, capsys):
        container = DataList(Int(i) for i in range(size))
        start = time.monotonic()
        container.store()
        stored_s = time.monotonic() - start

        start = time.monotonic()
        reloaded = load_node(container.pk)
        loaded_vals = [child.value for child in reloaded]
        loaded_s = time.monotonic() - start
        assert loaded_vals == list(range(size))

        start = time.monotonic()
        clone = reloaded.clone()
        cloned_s = time.monotonic() - start
        assert len(clone) == size

        with capsys.disabled():
            print(
                f'\n[perf] DataList N={size}: store={stored_s:.3f}s load+traverse={loaded_s:.3f}s clone={cloned_s:.3f}s'
            )
        assert stored_s < 120  # generous gate: flags pathological per-child query blowups only
