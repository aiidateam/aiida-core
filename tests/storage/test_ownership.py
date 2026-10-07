###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backend-level ownership invariant and failure-path tests.

Covers ``orm-container-spec.md`` sections 2, 3, and 12 (storage-first
iteration) at the storage-backend contract level, never through ORM
convenience methods:

- owner FK / membership table / element-type metadata layout parity
  between the PostgreSQL and SQLite models;
- field-level validation (eligibility, positions, keys);
- homogeneity (exact ``node_type`` comparison without plugin loading,
  outer-type-only nesting, NULL handling);
- atomic agreement of owner references with membership rows;
- exclusive, acyclic ownership;
- stored immutability;
- provenance-link rejection for owned nodes;
- ownership-closed deletion planning;
- archive-export rejection of ownership units.

Backend integration tests use the generic ``backend`` fixture and so run
against every supported database backend (SQLite and PostgreSQL).
"""

import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from aiida.common import exceptions
from aiida.common.links import LinkType
from aiida.orm import Data, Float
from aiida.orm.entities import EntityTypes
from aiida.storage import ownership
from aiida.storage.ownership import (
    expand_ownership_closure,
    is_container_node_type,
    is_data_node_type,
    resolve_element_type,
    validate_deletion_set,
    validate_membership_spec,
    validate_ownership_graph,
)

FLOAT_TYPE = 'data.core.float.Float.'
INT_TYPE = 'data.core.int.Int.'
LIST_OWNER_TYPE = 'data.core.data_list.DataList.'
DICT_OWNER_TYPE = 'data.core.data_dict.DataDict.'
PROCESS_TYPE = 'process.calculation.calcjob.CalcJobNode.'


def _make_graph(owner_type=LIST_OWNER_TYPE, child_types=(FLOAT_TYPE, FLOAT_TYPE)):
    """Return ``(owner, children)`` stored standalone nodes, owner retagged as container."""
    from aiida.orm import QueryBuilder  # noqa: F401  (keeps backend session settled)

    owner = Data().store()
    children = [Data().store() for _ in child_types]
    # Retag stored rows at the backend level: tests operate on stored
    # ``node_type`` identifier strings, never on ORM plugin classes.
    backend = owner.backend
    backend.bulk_update(
        EntityTypes.NODE,
        [
            {'id': owner.pk, 'node_type': owner_type},
            *(
                {'id': child.pk, 'node_type': child_type}
                for child, child_type in zip(children, child_types, strict=True)
            ),
        ],
    )
    return owner, children


def _specs(children, keys=None, start=0):
    return [
        {
            'child_id': child.pk,
            'child_node_type': FLOAT_TYPE,
            'position': position,
            'key': None if keys is None else keys[position - start],
        }
        for position, child in enumerate(children, start=start)
    ]


class TestEligibility:
    """Owner/child eligibility is decided from ``node_type`` strings only."""

    def test_data_types_eligible_as_children(self):
        assert is_data_node_type('data.Data.')
        assert is_data_node_type(FLOAT_TYPE)
        assert is_data_node_type(LIST_OWNER_TYPE)

    def test_non_data_rejected_as_children(self):
        assert not is_data_node_type(PROCESS_TYPE)
        assert not is_data_node_type('node.Node.')
        assert not is_data_node_type(None)
        assert not is_data_node_type('')

    def test_only_reserved_containers_own(self):
        assert is_container_node_type(LIST_OWNER_TYPE)
        assert is_container_node_type(DICT_OWNER_TYPE)
        assert not is_container_node_type(FLOAT_TYPE)
        assert not is_container_node_type('data.core.list.List.')
        assert not is_container_node_type('data.Data.')
        assert not is_container_node_type(None)

    def test_membership_spec_rejects_bad_owner(self):
        with pytest.raises(exceptions.IntegrityError, match='Ineligible owner'):
            validate_membership_spec(owner_node_type=FLOAT_TYPE, child_node_type=FLOAT_TYPE, position=0, key=None)

    def test_membership_spec_rejects_non_data_child(self):
        with pytest.raises(exceptions.IntegrityError, match='Ineligible child'):
            validate_membership_spec(
                owner_node_type=LIST_OWNER_TYPE, child_node_type=PROCESS_TYPE, position=0, key=None
            )

    def test_membership_spec_rejects_bad_position(self):
        for position in (-1, '0', 1.5, True):
            with pytest.raises(exceptions.IntegrityError, match='position'):
                validate_membership_spec(
                    owner_node_type=LIST_OWNER_TYPE, child_node_type=FLOAT_TYPE, position=position, key=None
                )

    def test_membership_spec_rejects_non_string_key(self):
        for key in (0, 1.5, b'a', ('a',)):
            with pytest.raises(exceptions.IntegrityError, match='key'):
                validate_membership_spec(
                    owner_node_type=LIST_OWNER_TYPE, child_node_type=FLOAT_TYPE, position=0, key=key
                )


class TestHomogeneity:
    """Exact ``node_type`` comparison without loading plugins; NULL means unset."""

    def test_unset_locks_to_first_type(self):
        assert resolve_element_type(None, FLOAT_TYPE) == FLOAT_TYPE

    def test_match_passes(self):
        assert resolve_element_type(FLOAT_TYPE, FLOAT_TYPE) == FLOAT_TYPE

    def test_mismatch_fails_even_for_base_class(self):
        # Sharing the `Data` base class is insufficient: `Int` != `Float`.
        with pytest.raises(exceptions.IntegrityError, match='Homogeneity'):
            resolve_element_type(FLOAT_TYPE, INT_TYPE)

    def test_subclass_does_not_match(self):
        with pytest.raises(exceptions.IntegrityError, match='Homogeneity'):
            resolve_element_type('data.Data.', FLOAT_TYPE)

    def test_nested_containers_compare_outer_type_only(self):
        outer_a = 'data.core.data_list.DataList.'
        outer_b = 'data.core.data_dict.DataDict.'
        assert resolve_element_type(outer_a, outer_a) == outer_a
        with pytest.raises(exceptions.IntegrityError, match='Homogeneity'):
            resolve_element_type(outer_a, outer_b)


class TestModelParity:
    """PostgreSQL and SQLite models carry the same ownership layout."""

    def test_node_columns_match(self):
        from aiida.storage.psql_dos.models import node as pg_node
        from aiida.storage.sqlite_zip import models as lite_models

        pg_cols = {column.name for column in pg_node.DbNode.__table__.columns}
        lite_cols = {column.name for column in lite_models.DbNode.__table__.columns}
        assert {'owner_id', 'container_element_type'} <= pg_cols
        assert {'owner_id', 'container_element_type'} <= lite_cols
        assert pg_cols == lite_cols

    def test_membership_tables_match(self):
        from aiida.storage.psql_dos.models import node as pg_node
        from aiida.storage.sqlite_zip import models as lite_models

        for table in (pg_node.DbMembership.__table__, lite_models.DbMembership.__table__):
            assert table.name == 'db_dbmembership'
            assert {column.name for column in table.columns} == {'id', 'owner_id', 'child_id', 'position', 'key'}
        pg_unique = sorted(
            tuple(sorted(constraint.columns.keys()))
            for constraint in pg_node.DbMembership.__table__.constraints
            if isinstance(constraint, sa.UniqueConstraint)
        )
        lite_unique = sorted(
            tuple(sorted(constraint.columns.keys()))
            for constraint in lite_models.DbMembership.__table__.constraints
            if isinstance(constraint, sa.UniqueConstraint)
        )
        assert pg_unique == lite_unique == [('child_id',), ('key', 'owner_id'), ('owner_id', 'position')]

    def test_heads_include_ownership_revision(self):
        from aiida.storage.psql_dos.migrator import PsqlDosMigrator
        from aiida.storage.sqlite_dos.backend import SqliteDosMigrator

        assert PsqlDosMigrator.get_schema_version_head() == 'main_0004'
        assert SqliteDosMigrator.get_schema_version_head() == 'main_0004'


@pytest.fixture
def memory_session():
    """An isolated in-memory SQLite session over the converted backend models."""
    from aiida.storage.sqlite_zip import models as lite_models

    engine = create_engine('sqlite:///:memory:')
    lite_models.SqliteBase.metadata.create_all(engine)
    with Session(engine) as session:
        yield session, lite_models.DbNode, lite_models.DbMembership


def _insert_node(session, node_model, node_type, owner_id=None, element_type=None):
    import uuid
    from datetime import datetime, timezone

    row = node_model(
        uuid=uuid.uuid4().hex,
        node_type=node_type,
        label='',
        description='',
        ctime=datetime.now(timezone.utc),
        mtime=datetime.now(timezone.utc),
        attributes={},
        extras={},
        repository_metadata={},
        user_id=1,
        owner_id=owner_id,
        container_element_type=element_type,
    )
    session.add(row)
    session.flush()
    return row


class TestGraphValidationSessionLevel:
    """Failure paths of graph validation that need no live backend."""

    def test_self_ownership_rejected(self, memory_session):
        session, node_model, membership_model = memory_session
        owner = _insert_node(session, node_model, LIST_OWNER_TYPE)
        with pytest.raises(exceptions.IntegrityError, match='itself'):
            validate_ownership_graph(
                session,
                node_model,
                membership_model,
                owner_id=owner.id,
                owner_node_type=LIST_OWNER_TYPE,
                owner_element_type=None,
                members=[{'child_id': owner.id, 'child_node_type': LIST_OWNER_TYPE, 'position': 0, 'key': None}],
            )

    def test_cycle_through_stored_edge_rejected(self, memory_session):
        session, node_model, membership_model = memory_session
        outer = _insert_node(session, node_model, LIST_OWNER_TYPE)
        inner = _insert_node(session, node_model, LIST_OWNER_TYPE, owner_id=outer.id)
        session.add(membership_model(owner_id=outer.id, child_id=inner.id, position=0, key=None))
        session.flush()
        # Attaching the ancestor as a child of its own descendant must fail.
        with pytest.raises(exceptions.IntegrityError, match='ancestor'):
            validate_ownership_graph(
                session,
                node_model,
                membership_model,
                owner_id=inner.id,
                owner_node_type=LIST_OWNER_TYPE,
                owner_element_type=None,
                members=[{'child_id': outer.id, 'child_node_type': LIST_OWNER_TYPE, 'position': 0, 'key': None}],
            )

    def test_missing_child_rejected(self, memory_session):
        session, node_model, membership_model = memory_session
        owner = _insert_node(session, node_model, LIST_OWNER_TYPE)
        with pytest.raises(exceptions.IntegrityError, match='does not exist'):
            validate_ownership_graph(
                session,
                node_model,
                membership_model,
                owner_id=owner.id,
                owner_node_type=LIST_OWNER_TYPE,
                owner_element_type=None,
                members=[{'child_id': owner.id + 999, 'child_node_type': FLOAT_TYPE, 'position': 0, 'key': None}],
            )

    def test_deletion_closure_helpers(self, memory_session):
        session, node_model, membership_model = memory_session
        root = _insert_node(session, node_model, LIST_OWNER_TYPE)
        child = _insert_node(session, node_model, FLOAT_TYPE, owner_id=root.id)
        grandchild = _insert_node(session, node_model, FLOAT_TYPE, owner_id=child.id)
        session.add(membership_model(owner_id=root.id, child_id=child.id, position=0, key=None))
        session.add(membership_model(owner_id=child.id, child_id=grandchild.id, position=0, key=None))
        session.flush()
        assert expand_ownership_closure(session, node_model, membership_model, [grandchild.id]) == {
            root.id,
            child.id,
            grandchild.id,
        }
        with pytest.raises(exceptions.IntegrityError, match='ownership-closed'):
            validate_deletion_set(session, node_model, membership_model, [child.id])
        validate_deletion_set(session, node_model, membership_model, [root.id, child.id, grandchild.id])


@pytest.mark.usefixtures('aiida_profile_clean')
class TestAtomicAttach:
    """Atomic owner/membership agreement through the backend contract."""

    def test_attach_success(self, backend):
        owner, children = _make_graph()
        node_model, membership_model = backend._ownership_models()
        resolved = backend.create_container_membership(owner.pk, _specs(children))
        assert resolved == FLOAT_TYPE
        session = backend.get_session()
        stored_owner = session.query(node_model).filter(node_model.id == owner.pk).one()
        assert stored_owner.container_element_type == FLOAT_TYPE
        for position, child in enumerate(children):
            stored_child = session.query(node_model).filter(node_model.id == child.pk).one()
            assert stored_child.owner_id == owner.pk
            edge = session.query(membership_model).filter(membership_model.child_id == child.pk).one()
            assert (edge.owner_id, edge.position, edge.key) == (owner.pk, position, None)

    def test_dict_keys_persisted(self, backend):
        owner, children = _make_graph(owner_type=DICT_OWNER_TYPE)
        backend.create_container_membership(owner.pk, _specs(children, keys=['b', 'a']))
        _, membership_model = backend._ownership_models()
        session = backend.get_session()
        edges = session.query(membership_model).filter(membership_model.owner_id == owner.pk).order_by('position').all()
        assert [(edge.position, edge.key) for edge in edges] == [(0, 'b'), (1, 'a')]

    def test_empty_attach_leaves_type_unset(self, backend):
        owner, _ = _make_graph(child_types=())
        assert backend.create_container_membership(owner.pk, []) is None
        node_model, _ = backend._ownership_models()
        stored = backend.get_session().query(node_model).filter(node_model.id == owner.pk).one()
        assert stored.container_element_type is None

    def test_mixed_types_rejected_atomically(self, backend):
        owner, children = _make_graph()
        other = Data().store()
        backend.bulk_update(EntityTypes.NODE, [{'id': other.pk, 'node_type': INT_TYPE}])
        node_model, membership_model = backend._ownership_models()
        session = backend.get_session()
        with pytest.raises(exceptions.IntegrityError, match='Homogeneity'):
            backend.create_container_membership(
                owner.pk,
                [
                    {'child_id': children[0].pk, 'child_node_type': FLOAT_TYPE, 'position': 0, 'key': None},
                    {'child_id': other.pk, 'child_node_type': INT_TYPE, 'position': 1, 'key': None},
                ],
            )
        # Atomicity: neither the owner reference nor any membership row was written.
        assert session.query(node_model).filter(node_model.id == owner.pk).one().container_element_type is None
        assert session.query(membership_model).filter(membership_model.owner_id == owner.pk).count() == 0

    def test_locked_type_enforced_on_later_inserts(self, backend):
        owner, children = _make_graph(child_types=(FLOAT_TYPE,))
        backend.create_container_membership(owner.pk, _specs(children))
        other = Data().store()
        backend.bulk_update(EntityTypes.NODE, [{'id': other.pk, 'node_type': INT_TYPE}])
        # A differently typed child violates the locked element type...
        with pytest.raises(exceptions.IntegrityError, match='Homogeneity'):
            backend.create_container_membership(
                owner.pk,
                [{'child_id': other.pk, 'child_node_type': INT_TYPE, 'position': 1, 'key': None}],
            )
        # ...while even a matching child is rejected: stored membership is immutable.
        backend.bulk_update(EntityTypes.NODE, [{'id': other.pk, 'node_type': FLOAT_TYPE}])
        with pytest.raises(exceptions.IntegrityError, match='immutable'):
            backend.create_container_membership(
                owner.pk,
                [{'child_id': other.pk, 'child_node_type': FLOAT_TYPE, 'position': 1, 'key': None}],
            )

    def test_exclusive_ownership(self, backend):
        owner_a, children = _make_graph()
        owner_b = Data().store()
        backend.bulk_update(EntityTypes.NODE, [{'id': owner_b.pk, 'node_type': LIST_OWNER_TYPE}])
        backend.create_container_membership(owner_a.pk, _specs(children))
        node_model, _ = backend._ownership_models()
        session = backend.get_session()
        with pytest.raises(exceptions.IntegrityError, match='already owned'):
            backend.create_container_membership(
                owner_b.pk,
                [
                    {
                        'child_id': children[0].pk,
                        'child_node_type': FLOAT_TYPE,
                        'position': 0,
                        'key': None,
                    }
                ],
            )
        assert session.query(node_model).filter(node_model.id == children[0].pk).one().owner_id == owner_a.pk

    def test_owner_must_be_container(self, backend):
        plain, children = _make_graph(owner_type=FLOAT_TYPE)
        with pytest.raises(exceptions.IntegrityError, match='Ineligible owner'):
            backend.create_container_membership(plain.pk, _specs(children))

    def test_process_child_rejected(self, backend):
        owner, _ = _make_graph(child_types=())
        proc = Data().store()
        backend.bulk_update(EntityTypes.NODE, [{'id': proc.pk, 'node_type': PROCESS_TYPE}])
        with pytest.raises(exceptions.IntegrityError, match='Ineligible child'):
            backend.create_container_membership(
                owner.pk, [{'child_id': proc.pk, 'child_node_type': PROCESS_TYPE, 'position': 0, 'key': None}]
            )

    def test_duplicate_positions_and_keys_rejected(self, backend):
        owner, children = _make_graph()
        with pytest.raises(exceptions.IntegrityError, match='position'):
            backend.create_container_membership(
                owner.pk,
                [
                    {'child_id': children[0].pk, 'child_node_type': FLOAT_TYPE, 'position': 0, 'key': None},
                    {'child_id': children[1].pk, 'child_node_type': FLOAT_TYPE, 'position': 0, 'key': None},
                ],
            )
        owner_d, children_d = _make_graph(owner_type=DICT_OWNER_TYPE)
        with pytest.raises(exceptions.IntegrityError, match='key'):
            backend.create_container_membership(
                owner_d.pk,
                [
                    {'child_id': children_d[0].pk, 'child_node_type': FLOAT_TYPE, 'position': 0, 'key': 'same'},
                    {'child_id': children_d[1].pk, 'child_node_type': FLOAT_TYPE, 'position': 1, 'key': 'same'},
                ],
            )

    def test_bulk_insert_rejects_owned_and_locked(self, backend):
        owned = Data()
        with pytest.raises(exceptions.IntegrityError, match='atomically'):
            backend.bulk_insert(
                EntityTypes.NODE,
                [
                    {
                        'uuid': owned.uuid,
                        'node_type': FLOAT_TYPE,
                        'process_type': None,
                        'label': '',
                        'description': '',
                        'ctime': owned.ctime,
                        'mtime': owned.mtime,
                        'attributes': {},
                        'extras': {},
                        'repository_metadata': {},
                        'dbcomputer_id': None,
                        'user_id': backend.default_user.pk,
                        'owner_id': 12345,
                        'container_element_type': None,
                    }
                ],
            )

    def test_bulk_update_rejects_ownership_mutation(self, backend):
        node = Data().store()
        with pytest.raises(exceptions.IntegrityError, match='immutable'):
            backend.bulk_update(EntityTypes.NODE, [{'id': node.pk, 'owner_id': node.pk}])
        with pytest.raises(exceptions.IntegrityError, match='immutable'):
            backend.bulk_update(EntityTypes.NODE, [{'id': node.pk, 'container_element_type': FLOAT_TYPE}])

    def test_store_rejects_owned_model(self, backend):
        node = Data().store()
        entity = backend.nodes.get(pk=node.pk)
        entity.bare_model.owner_id = node.pk
        with pytest.raises(exceptions.IntegrityError, match='independently'):
            entity.store()
        backend.get_session().rollback()

    def test_link_to_owned_rejected(self, backend):
        owner, children = _make_graph(child_types=(FLOAT_TYPE,))
        backend.create_container_membership(owner.pk, _specs(children))
        source = backend.nodes.get(pk=Data().store().pk)
        target = backend.nodes.get(pk=children[0].pk)
        with pytest.raises(exceptions.IntegrityError, match='owned'):
            target.add_incoming(source, LinkType.CREATE, 'label')
        with pytest.raises(exceptions.IntegrityError, match='owned'):
            backend.bulk_insert(
                EntityTypes.LINK,
                [{'input_id': source.pk, 'output_id': children[0].pk, 'label': 'x', 'type': 'create'}],
                allow_defaults=True,
            )


@pytest.mark.usefixtures('aiida_profile_clean')
class TestOwnershipDeletion:
    """Deletion sets must be ownership-closed; execution removes edges and nodes."""

    def test_child_only_deletion_rejected(self, backend):
        owner, children = _make_graph()
        backend.create_container_membership(owner.pk, _specs(children))
        with backend.transaction():
            with pytest.raises(exceptions.IntegrityError, match='ownership-closed'):
                backend.delete_nodes_and_connections([children[0].pk])

    def test_container_only_deletion_rejected(self, backend):
        owner, children = _make_graph()
        backend.create_container_membership(owner.pk, _specs(children))
        with backend.transaction():
            with pytest.raises(exceptions.IntegrityError, match='ownership-closed'):
                backend.delete_nodes_and_connections([owner.pk])

    def test_closed_unit_deletion_succeeds(self, backend):
        owner, children = _make_graph()
        backend.create_container_membership(owner.pk, _specs(children))
        node_model, membership_model = backend._ownership_models()
        session = backend.get_session()
        # Capture plain pks: the bulk delete detaches session instances, invalidating ORM attribute access.
        owner_pk = owner.pk
        child_pks = [child.pk for child in children]
        with backend.transaction():
            backend.delete_nodes_and_connections([owner_pk, *child_pks])
        session.expunge_all()
        assert session.query(node_model).filter(node_model.id.in_([owner_pk])).count() == 0
        assert session.query(membership_model).filter(membership_model.owner_id == owner_pk).count() == 0


@pytest.mark.usefixtures('aiida_profile_clean')
class TestArchiveExportGuard:
    """Archive export strips ownership columns and rejects ownership units."""

    def test_plain_export_unaffected(self, backend, tmp_path):
        from aiida.tools.archive.create import _assert_no_ownership_members

        node = Float(1.0).store()
        _assert_no_ownership_members(backend, {node.pk})

    def test_ownership_unit_export_rejected(self, backend):
        from aiida.tools.archive.create import _assert_no_ownership_members
        from aiida.tools.archive.exceptions import ExportValidationError

        owner, children = _make_graph()
        backend.create_container_membership(owner.pk, _specs(children))
        with pytest.raises(ExportValidationError, match='ownership'):
            _assert_no_ownership_members(backend, {owner.pk})
        with pytest.raises(ExportValidationError, match='ownership'):
            _assert_no_ownership_members(backend, {children[0].pk})


def test_integration_notes_present():
    """Deferred integrations are recorded at the contract module, not silently dropped."""
    assert 'QueryBuilder' in ownership.OWNERSHIP_INTEGRATION_NOTES


def test_container_node_types_match_orm():
    """Storage owner eligibility strings equal the real ORM container type strings (F1)."""
    from aiida.orm import DataDict, DataList

    assert set(ownership.CONTAINER_NODE_TYPES) == {DataList.class_node_type, DataDict.class_node_type}
    assert ownership.is_container_node_type(DataList.class_node_type)
    assert ownership.is_container_node_type(DataDict.class_node_type)
