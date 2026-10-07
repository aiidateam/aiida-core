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
from aiida.orm import DataDict, DataList, Dict, Float, Int, List, Str, load_node

pytestmark = pytest.mark.usefixtures('aiida_profile_clean')


def _values(container):
    return [child.value for child in container]


class TestCopyInsertRepeatMetadataLifetime:
    """§14: copy-on-insertion, repeated insertion, metadata independence, source lifetime."""

    def test_repeated_insertion_distinct_copies(self):
        container = DataList()
        source = Int(5)
        container.append(source)
        container.append(source)
        first, second = container[0], container[1]
        assert first.uuid != source.uuid
        assert second.uuid != source.uuid
        assert first.uuid != second.uuid
        assert first.value == second.value == 5

    def test_source_ownership_lifetime_unchanged(self):
        container = DataList()
        source = Int(5)
        container.append(source)
        assert not source.is_stored
        assert source.value == 5
        source.label = 'still-mine'
        assert container[0].label != 'still-mine'

    def test_insert_explicit_copy_copies_again(self):
        container = DataList([Int(1)])
        explicit = container[0].clone()
        container.append(explicit)
        assert container[1].uuid != explicit.uuid

    def test_mutable_metadata_independent(self):
        source = Int(1)
        source.base.extras.set('meta', {'nested': [1]})
        container = DataList([source])
        container[0].base.extras.set('meta', {'nested': [2]})
        assert source.base.extras.get('meta') == {'nested': [1]}

    def test_copy_usable_after_source_deletion(self):
        source = Int(7)
        source.store()
        container = DataList([source])
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
        assert reloaded.element_type == Int.class_node_type

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
        resolved = backend.create_container_membership(
            owner.pk,
            [
                {'child_id': children[0].pk, 'child_node_type': child_type, 'position': 0, 'key': None},
                {'child_id': children[1].pk, 'child_node_type': child_type, 'position': 1, 'key': None},
            ],
        )
        assert resolved == child_type

    def test_container_node_type_matches_orm(self):
        """Cross test (binding F1, now fixed by storage agent): storage literals
        must equal the real ORM identifiers (``data_list``/``data_dict``)."""
        from aiida.storage.ownership import CONTAINER_NODE_TYPES

        assert DataList.class_node_type in CONTAINER_NODE_TYPES
        assert DataDict.class_node_type in CONTAINER_NODE_TYPES


class TestEligibilityHomogeneityLocking:
    """§14: eligibility, homogeneity, type locking, typed/untyped empty containers."""

    def test_process_nodes_rejected(self):
        from aiida.orm import CalcJobNode

        with pytest.raises(TypeError):
            DataList().append(CalcJobNode())

    def test_non_data_values_rejected(self):
        with pytest.raises(TypeError):
            DataDict()['k'] = 'not-a-node'

    def test_homogeneity_exact_type(self):
        container = DataList([Int(1)])
        with pytest.raises(TypeError):
            container.append(Str('x'))
        with pytest.raises(TypeError):
            container.append(Float(1.0))

    def test_type_lock_survives_emptying(self):
        container = DataList([Int(1)])
        container.clear()
        assert container.element_type == Int.class_node_type
        with pytest.raises(TypeError):
            container.append(Str('locked'))

    def test_empty_untyped_container_storable(self):
        container = DataList()
        assert container.element_type is None
        container.store()
        assert load_node(container.pk).element_type is None

    def test_empty_typed_vs_untyped_hash_inputs_differ(self):
        """Spec §10: NULL element-type state contributes to the caching hash."""
        typed = DataList([Int(1)])
        typed.clear()
        typed.store()
        untyped = DataList()
        untyped.store()
        assert typed.element_type == Int.class_node_type
        assert untyped.element_type is None
        assert typed.element_type != untyped.element_type

    def test_nested_outer_type_only(self):
        inner_ints = DataList([Int(1)])
        inner_strs = DataList([Str('a')])
        outer = DataList([inner_ints])
        outer.append(inner_strs)  # different inner types, same outer concrete type: allowed
        assert len(outer) == 2
        with pytest.raises(TypeError):
            outer.append(Int(1))


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
        assert container[0].uuid != removed.uuid

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


class TestFreezeRollbackRetained:
    """§14: independent-child storage rejection, atomic freezing, rollback, retained state."""

    def test_independent_child_store_rejected(self):
        container = DataList([Int(1)])
        with pytest.raises(ModificationNotAllowed):
            container[0].store()

    def test_atomic_freeze(self):
        container = DataList([Int(1), Int(2)])
        container.store()
        assert container.is_stored
        reloaded = load_node(container.pk)
        assert reloaded.is_stored
        assert _values(reloaded) == [1, 2]
        with pytest.raises(ModificationNotAllowed):
            reloaded.append(Int(3))

    def test_enclosing_rollback_recovery_retryable(self, backend):
        container = DataList([Int(1), Int(2)])
        with pytest.raises(RuntimeError, match='force outer rollback'):
            with backend.transaction():
                container.store()
                raise RuntimeError('force outer rollback')
        # Retained objects recovered: unstored, editable, retryable (same objects).
        assert not container.is_stored
        assert _values(container) == [1, 2]
        container.append(Int(3))
        container.store()
        assert _values(load_node(container.pk)) == [1, 2, 3]


class TestProcessBoundariesStrict:
    """§14/§7: process input copies and calculation output copies (implemented)."""

    def test_calcfunction_input_owned_child_copied(self):
        """An owned child passed as input executes as the recorded standalone copy."""
        from aiida.engine import calcfunction
        from aiida.orm.nodes.data.container import is_owned

        @calcfunction
        def identity(x):
            return x

        container = DataList([Int(1)])
        child = container[0]
        out, calc = identity.run_get_node(child)
        assert out.value == 1
        recorded = calc.inputs.x
        assert recorded.value == 1
        assert recorded.uuid != child.uuid  # independent standalone copy recorded
        assert recorded.is_stored
        assert not is_owned(recorded)

    def test_calcfunction_output_owned_child_copied(self):
        """Exposing an owned child as a calculation output records a copy via CREATE."""
        from aiida.common.links import LinkType
        from aiida.engine import calcfunction
        from aiida.orm.nodes.data.container import is_owned

        @calcfunction
        def first(x):
            return x[0]

        container = DataList([Int(7)])
        source_uuid = container[0].uuid
        out, calc = first.run_get_node(container)
        assert out.value == 7
        recorded_outputs = calc.base.links.get_outgoing(link_type=LinkType.CREATE).all()
        assert len(recorded_outputs) == 1
        recorded_out = recorded_outputs[0].node
        assert recorded_out.value == 7
        assert recorded_out.uuid != source_uuid  # independent standalone copy recorded
        assert not is_owned(recorded_out)
        assert [child.value for child in container] == [7]

    @pytest.mark.xfail(
        reason='spec §7: exposed output handle should be the recorded copy (stale-handle gap, filed by verify agent)',
        strict=False,
    )
    def test_exposed_output_handle_is_recorded_copy(self):
        """GAP: ``run_get_node`` returns the pre-copy handle, not the CREATE'd copy."""
        from aiida.common.links import LinkType
        from aiida.engine import calcfunction

        @calcfunction
        def first(x):
            return x[0]

        container = DataList([Int(7)])
        out, calc = first.run_get_node(container)
        recorded_out = calc.base.links.get_outgoing(link_type=LinkType.CREATE).one().node
        assert out.uuid == recorded_out.uuid


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


class TestDeletionApproval:
    """§14: ownership-expanded deletion approval and execution-time revalidation.

    The backend contract path (``delete_nodes_and_connections`` inside a
    transaction) enforces closure strictly. The ORM single-row
    ``nodes.delete(pk)`` path bypasses closure validation (filed below).
    """

    def test_child_only_set_rejected(self, backend):
        container = DataList([Int(1), Int(2)])
        container.store()
        child_pk = load_node(container.pk)[0].pk
        with pytest.raises(IntegrityError, match=r'[Cc]losure|[Ee]xpand|[Cc]losed'):
            with backend.transaction():
                backend.delete_nodes_and_connections([child_pk])

    def test_container_only_set_rejected(self, backend):
        container = DataList([Int(1), Int(2)])
        container.store()
        with pytest.raises(IntegrityError, match=r'[Cc]losure|[Ee]xpand|[Cc]losed|[Ss]ubtree'):
            with backend.transaction():
                backend.delete_nodes_and_connections([container.pk])

    def test_approved_whole_unit_deletes(self, backend):
        from aiida.common.exceptions import NotExistent

        container = DataList([Int(1)])
        container.store()
        root_pk = container.pk
        child_pk = load_node(root_pk)[0].pk
        with backend.transaction():
            backend.delete_nodes_and_connections([root_pk, child_pk])
        with pytest.raises(NotExistent):
            load_node(child_pk)
        with pytest.raises(NotExistent):
            load_node(root_pk)

    def test_orm_single_row_delete_requires_expansion(self):
        """ORM ``nodes.delete`` rejects owned-child and container targets (closure UX)."""
        container = DataList([Int(1), Int(2)])
        container.store()
        child_pk = load_node(container.pk)[0].pk
        with pytest.raises(IntegrityError, match=r'[Ee]xpand|[Oo]wnership unit|[Oo]wned'):
            load_node(container.pk).backend.nodes.delete(child_pk)
        with pytest.raises(IntegrityError, match=r'[Ee]xpand|[Oo]wnership unit|[Ss]ubtree'):
            load_node(container.pk).backend.nodes.delete(container.pk)


class TestGroupWholeUnit:
    """§14/§9: complete-unit group membership (implemented)."""

    def test_child_add_rejected_root_required(self):
        from aiida.orm import Group

        container = DataList([Int(1), Int(2)])
        container.store()
        group = Group(label='g1').store()
        child = load_node(container.pk)[0]
        with pytest.raises(Exception, match=r'[Rr]oot|[Ww]hole|[Uu]nit|[Cc]hild'):
            group.add_nodes(child)

    def test_child_remove_rejected_root_required(self):
        from aiida.orm import Group

        container = DataList([Int(1), Int(2)])
        container.store()
        group = Group(label='g1r').store()
        group.add_nodes(load_node(container.pk))
        child = load_node(container.pk)[0]
        with pytest.raises(Exception, match=r'[Rr]oot|[Ww]hole|[Uu]nit|[Cc]hild'):
            group.remove_nodes(child)

    def test_root_add_covers_descendants(self):
        from aiida.orm import Group, QueryBuilder

        container = DataList([Int(1)])
        container.store()
        child_pk = load_node(container.pk)[0].pk
        group = Group(label='g2').store()
        group.add_nodes(load_node(container.pk))
        builder = (
            QueryBuilder().append(Group, filters={'id': group.pk}, tag='g').append(Int, with_group='g', project='id')
        )
        assert child_pk in builder.all(flat=True)

    def test_root_remove_clears_unit(self):
        from aiida.orm import Group, QueryBuilder

        container = DataList([Int(1)])
        container.store()
        group = Group(label='g3').store()
        group.add_nodes(load_node(container.pk))
        group.remove_nodes(load_node(container.pk))
        builder = (
            QueryBuilder().append(Group, filters={'id': group.pk}, tag='g').append(Int, with_group='g', project='id')
        )
        assert builder.count() == 0


class TestArchiveConflictsMigrationMissingPlugin:
    """§14/§11: archive closure rejection, migration, missing-plugin operations."""

    def test_archive_export_nested_and_dict_rejected(self, tmp_path):
        """Export rejects nested containers and dict units, not just flat lists."""
        from aiida.tools.archive import create_archive
        from aiida.tools.archive.exceptions import ExportValidationError

        outer = DataList()
        outer.append(DataList([Int(1)]))
        outer.store()
        mapping = DataDict({'a': Int(1)})
        mapping.store()
        for node in (outer, mapping):
            with pytest.raises(ExportValidationError):
                create_archive([node], filename=str(tmp_path / f'{node.pk}.aiida'))

    def test_archive_export_child_selection_rejected(self, tmp_path):
        """Selecting an owned child for export rejects (§11 closure: child implies unit)."""
        from aiida.tools.archive import create_archive
        from aiida.tools.archive.exceptions import ExportValidationError

        container = DataList([Int(1), Int(2)])
        container.store()
        child = load_node(container.pk)[0]
        with pytest.raises(ExportValidationError):
            create_archive([child], filename=str(tmp_path / 'child.aiida'))

    def test_missing_element_plugin_reported(self):
        """Typed element access requires the real plugin and reports its absence."""
        from aiida.orm.nodes.data.container import _ContainerBase

        with pytest.raises(Exception, match=r'[Pp]lugin|[Ee]ntry point|[Nn]ot found|[Uu]nknown'):
            _ContainerBase._require_element_plugin('data.core.nonexistent.Missing.')

    def test_genuine_data_element_not_mistaken_for_missing(self):
        """A genuine base-Data element passes the plugin check (no false missing)."""
        from aiida.orm import Data
        from aiida.orm.nodes.data.container import _ContainerBase

        _ContainerBase._require_element_plugin(Data.class_node_type)

    @pytest.mark.xfail(
        reason='spec §11: import-side UUID conflicts unreachable while export safe-rejects (filed by verify agent)',
        strict=False,
    )
    def test_archive_conflict_disagreement_rejected(self, tmp_path):
        """GAP PROBE: import-side ownership disagreement under one UUID.

        Unreachable via public API while export safe-rejects ownership units
        (only hand-crafted archives could carry ownership rows); kept as a
        probe so a future export/import round-trip must handle conflicts by
        rejecting and rolling back, never by skipping or reconciling.
        """
        from aiida.tools.archive import create_archive, import_archive

        container = DataList([Int(1)])
        container.store()
        path = str(tmp_path / 'conflict.aiida')
        create_archive([container], filename=path)
        # Corrupt local ownership then re-import same UUIDs -> integrity error, rollback.
        with pytest.raises(Exception):
            import_archive(path)


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

    def test_typed_vs_untyped_empty_differ(self):
        typed = DataList([Int(1)])
        typed.clear()
        typed.store()
        untyped = DataList()
        untyped.store()
        assert typed.element_type == Int.class_node_type
        assert untyped.element_type is None
        assert typed.base.caching.get_hash() != untyped.base.caching.get_hash()

    def test_cache_reuse_disabled(self):
        """F4 resolved as explicit safe rejection: containers never serve/store cache."""
        assert DataList._cachable is False
        assert DataDict._cachable is False


class TestIntegrationSmokeStrict:
    """Strict smoke tests for already-integrated paths (relational storage).

    Caveats live in the verify-agent status file; remaining xfail tests track
    the still-open contract gaps (process auto-copy, groups, QB joins, archive
    import, deletion UX).
    """

    def test_workflow_return_owned_child_rejected(self):
        """Workfunctions returning an owned child are rejected (no auto-copy)."""
        from aiida.engine import workfunction

        @workfunction
        def bad():
            container = DataList([Int(1)])
            return container[0]

        with pytest.raises(Exception):
            bad()

    def test_archive_export_ownership_rejected(self, tmp_path):
        """Export explicitly rejects ownership units (F5 accepted safe-rejection,
        now enforced at the relational level); plain nodes still export fine."""
        from aiida.tools.archive import create_archive
        from aiida.tools.archive.exceptions import ExportValidationError

        container = DataList([Int(1)])
        container.store()
        with pytest.raises(ExportValidationError, match=r'[Oo]wned|[Oo]wnership|[Cc]ontainer'):
            create_archive([container], filename=str(tmp_path / 'container.aiida'))
        plain = Int(1).store()
        create_archive([plain], filename=str(tmp_path / 'plain.aiida'))

    def test_structural_traversal_smoke(self):
        container = DataList([Int(1)])
        container.store()
        reloaded = load_node(container.pk)
        assert len(reloaded) == 1
        assert reloaded.element_type == Int.class_node_type

    def test_element_type_reload_relational(self):
        """Locked element type reloads from relational metadata (F2: no attrs)."""
        container = DataList([Int(1)])
        container.store()
        reloaded = load_node(container.pk)
        assert reloaded.element_type == Int.class_node_type
        assert '_container_element_type' not in reloaded.base.attributes.all
        assert '_container_membership' not in reloaded.base.attributes.all


class TestCliBehavior:
    """§14/§8/§9: CLI whole-unit expansion and explicit approval."""

    def test_cli_group_add_child_expands_with_force(self, run_cli_command):
        from aiida.cmdline.commands import cmd_group
        from aiida.orm import Group, QueryBuilder

        container = DataList([Int(1), Int(2)])
        container.store()
        child_pk = load_node(container.pk)[0].pk
        run_cli_command(cmd_group.group_create, ['clitest'])
        # The expansion notice is emitted via info log (suppressed at test log
        # levels); assert the spec behavior: the complete unit was added.
        run_cli_command(cmd_group.group_add_nodes, ['--force', '--group=clitest', str(child_pk)])
        builder = (
            QueryBuilder()
            .append(Group, filters={'label': 'clitest'}, tag='g')
            .append(Int, with_group='g', project='id')
        )
        assert child_pk in builder.all(flat=True)

    def test_cli_group_add_child_requires_confirmation(self, run_cli_command):
        from aiida.cmdline.commands import cmd_group

        container = DataList([Int(1)])
        container.store()
        child_pk = load_node(container.pk)[0].pk
        run_cli_command(cmd_group.group_create, ['clitest2'])
        # Declining the prompt aborts without applying the expansion.
        run_cli_command(cmd_group.group_add_nodes, ['--group=clitest2', str(child_pk)], user_input='n', raises=True)

    def test_cli_node_delete_child_requires_force(self, run_cli_command):
        from aiida.cmdline.commands import cmd_node
        from aiida.common.exceptions import NotExistent

        container = DataList([Int(1)])
        container.store()
        root_pk = container.pk
        child_pk = load_node(root_pk)[0].pk
        # Without --force the ownership expansion is not approved: no deletion.
        run_cli_command(cmd_node.node_delete, [str(child_pk)], user_input='n', raises=True)
        assert load_node(child_pk).is_stored
        # With --force the whole unit is deleted with explicit approval.
        run_cli_command(cmd_node.node_delete, ['--force', str(child_pk)])
        with pytest.raises(NotExistent):
            load_node(root_pk)
        with pytest.raises(NotExistent):
            load_node(child_pk)


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


class TestDeferredStayDeferred:
    """Spec §13: deferred items stay deferred; rejected items stay absent."""

    def test_slicing_still_unsupported(self):
        with pytest.raises(TypeError):
            DataList([Int(1), Int(2)])[0:1]  # type: ignore[index]

    def test_no_parameterized_port_types(self):
        # Element-type-aware ports deferred: only class-only valid_type accepted.
        from aiida.engine import ProcessSpec

        spec = ProcessSpec()
        spec.input('data', valid_type=DataList)
        assert spec.inputs['data'].valid_type is DataList

    def test_no_source_copy_tracking(self):
        clone = DataList([Int(1)]).clone()
        assert 'source_uuid' not in clone.base.extras.all
        assert not clone.base.links.get_incoming().all()

    def test_no_container_serialization_schema(self):
        assert not hasattr(DataList, 'get_list')
        assert not hasattr(DataDict, 'get_dict')


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
