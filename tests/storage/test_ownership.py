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

- owner FK / membership table parity
  between the PostgreSQL and SQLite models;
- field-level validation (eligibility, positions, keys);
- atomic agreement of owner references with membership rows;
- exclusive, acyclic ownership;
- stored immutability;
- provenance-link rejection for owned nodes;
- ownership-closed deletion planning;

Backend integration tests use the generic ``backend`` fixture and so run
against every supported database backend (SQLite and PostgreSQL).
"""

import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from aiida.common import exceptions
from aiida.common.links import LinkType
from aiida.orm import Data
from aiida.orm.entities import EntityTypes
from aiida.storage import ownership
from aiida.storage.ownership import (
    expand_ownership_closure,
    is_container_node_type,
    is_data_node_type,
    is_ownable_node_type,
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
            'child_node_type': child.node_type,
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
        # Containers are ownable children via
        # ``is_ownable_node_type``, not leaf data.
        assert not is_data_node_type(LIST_OWNER_TYPE)
        assert is_ownable_node_type(LIST_OWNER_TYPE)
        assert is_ownable_node_type(DICT_OWNER_TYPE)
        assert is_ownable_node_type(FLOAT_TYPE)

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


class TestModelParity:
    """PostgreSQL and SQLite models carry the same ownership columns."""

    def test_node_columns_match(self):
        from aiida.storage.psql_dos.models import node as pg_node
        from aiida.storage.sqlite_zip import models as lite_models

        pg_cols = {column.name for column in pg_node.DbNode.__table__.columns}
        lite_cols = {column.name for column in lite_models.DbNode.__table__.columns}
        # `owner_id` stays on the base node.
        assert 'owner_id' in pg_cols
        assert 'container_element_type' not in pg_cols
        assert 'container_element_type' not in lite_cols
        assert pg_cols == lite_cols
        # No container marker tables exist at runtime.
        for table_name in ('db_dbcontainer', 'db_dblistcontainer', 'db_dbdictcontainer'):
            assert table_name not in pg_node.Base.metadata.tables
            assert table_name not in lite_models.SqliteBase.metadata.tables

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
        # Membership owners are containers: the FK points at the owner node row.
        owner_fk = next(fk for fk in pg_node.DbMembership.__table__.foreign_key_constraints if 'owner_id' in fk.columns)
        assert {fk.target_fullname for fk in owner_fk.elements} == {'db_dbnode.id'}
        child_fk = next(fk for fk in pg_node.DbMembership.__table__.foreign_key_constraints if 'child_id' in fk.columns)
        assert {fk.target_fullname for fk in child_fk.elements} == {'db_dbnode.id'}

    def test_heads_include_ownership_revision(self):
        from aiida.storage.psql_dos.migrator import PsqlDosMigrator
        from aiida.storage.sqlite_dos.backend import SqliteDosMigrator

        assert PsqlDosMigrator.get_schema_version_head() == 'main_0003'
        assert SqliteDosMigrator.get_schema_version_head() == 'main_0003'


@pytest.fixture
def memory_session():
    """An isolated in-memory SQLite session over the converted backend models."""
    from aiida.storage.sqlite_zip import models as lite_models

    engine = create_engine('sqlite:///:memory:')
    lite_models.SqliteBase.metadata.create_all(engine)
    with Session(engine) as session:
        yield session, lite_models.DbNode, lite_models.DbMembership


def _insert_node(session, node_model, node_type, owner_id=None):
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
        backend.create_container_membership(owner.pk, _specs(children))
        session = backend.get_session()
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

    def test_empty_attach_writes_no_rows(self, backend):
        owner, _ = _make_graph(child_types=())
        backend.create_container_membership(owner.pk, [])
        _, membership_model = backend._ownership_models()
        session = backend.get_session()
        assert session.query(membership_model).filter(membership_model.owner_id == owner.pk).count() == 0
        assert session.query(membership_model).count() == 0

    def test_mixed_types_persisted(self, backend):
        owner, children = _make_graph(child_types=(FLOAT_TYPE, INT_TYPE))
        backend.create_container_membership(owner.pk, _specs(children))

        node_model, membership_model = backend._ownership_models()
        session = backend.get_session()
        edges = session.query(membership_model).filter_by(owner_id=owner.pk).order_by('position').all()
        assert [edge.child_id for edge in edges] == [child.pk for child in children]
        assert [session.get(node_model, child.pk).node_type for child in children] == [FLOAT_TYPE, INT_TYPE]

    def test_stored_membership_cannot_be_extended(self, backend):
        owner, children = _make_graph(child_types=(FLOAT_TYPE,))
        backend.create_container_membership(owner.pk, _specs(children))
        other = Data().store()
        with pytest.raises(exceptions.IntegrityError, match='immutable'):
            backend.create_container_membership(
                owner.pk,
                [{'child_id': other.pk, 'child_node_type': other.node_type, 'position': 1, 'key': None}],
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
                    }
                ],
            )

    def test_bulk_update_rejects_ownership_mutation(self, backend):
        node = Data().store()
        with pytest.raises(exceptions.IntegrityError, match='immutable'):
            backend.bulk_update(EntityTypes.NODE, [{'id': node.pk, 'owner_id': node.pk}])

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
class TestContainerKindDiscipline:
    """List-vs-dict key discipline and kind-scoped access (ADR-01 §3, §7)."""

    def test_list_rejects_keyed_members(self, backend):
        owner, children = _make_graph()
        with pytest.raises(exceptions.IntegrityError, match='key NULL'):
            backend.create_container_membership(
                owner.pk,
                [{'child_id': children[0].pk, 'child_node_type': FLOAT_TYPE, 'position': 0, 'key': 'a'}],
            )

    def test_dict_rejects_keyless_members(self, backend):
        owner, children = _make_graph(owner_type=DICT_OWNER_TYPE)
        with pytest.raises(exceptions.IntegrityError, match='NOT NULL'):
            backend.create_container_membership(
                owner.pk,
                [{'child_id': children[0].pk, 'child_node_type': FLOAT_TYPE, 'position': 0, 'key': None}],
            )

    def test_explicit_kind_mismatch_rejected(self, backend):
        owner, children = _make_graph()
        with pytest.raises(exceptions.IntegrityError, match=r'[Kk]ind'):
            backend.create_container_membership(owner.pk, _specs(children), kind='dict')
        owner_d, children_d = _make_graph(owner_type=DICT_OWNER_TYPE)
        with pytest.raises(exceptions.IntegrityError, match=r'[Kk]ind'):
            backend.create_dict_membership(owner.pk, _specs(children))
        with pytest.raises(exceptions.IntegrityError, match=r'[Kk]ind'):
            backend.create_list_membership(
                owner_d.pk,
                [
                    {'child_id': children_d[0].pk, 'child_node_type': FLOAT_TYPE, 'position': 0, 'key': 'a'},
                    {'child_id': children_d[1].pk, 'child_node_type': FLOAT_TYPE, 'position': 1, 'key': 'b'},
                ],
            )

    def test_kind_authoritative_via_node_type(self, backend):
        from aiida.storage import ownership as ownership_contract

        assert ownership_contract.container_kind_for(LIST_OWNER_TYPE) == 'list'
        assert ownership_contract.container_kind_for(DICT_OWNER_TYPE) == 'dict'
        assert ownership_contract.container_kind_for(FLOAT_TYPE) is None
        # No container marker models are exposed by the backend.
        assert not hasattr(backend, '_container_models')

    def test_wrong_kind_is_atomic(self, backend):
        owner, children = _make_graph()
        node_model, membership_model = backend._ownership_models()
        session = backend.get_session()
        with pytest.raises(exceptions.IntegrityError, match=r'[Kk]ind'):
            backend.create_container_membership(owner.pk, _specs(children), kind='dict')
        # Atomic: nothing was written.
        assert session.query(membership_model).filter(membership_model.owner_id == owner.pk).count() == 0
        for child in children:
            assert session.query(node_model).filter(node_model.id == child.pk).one().owner_id is None


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
        owner_pk = owner.pk
        child_pks = [child.pk for child in children]
        with backend.transaction():
            # Keep an ORM instance alive: a bulk delete must update the active backend's identity map.
            stored_owner = session.get(node_model, owner_pk)
            backend.delete_nodes_and_connections([owner_pk, *child_pks])
            assert sa.inspect(stored_owner).deleted
        assert session.query(node_model).filter(node_model.id.in_([owner_pk])).count() == 0
        assert session.query(membership_model).filter(membership_model.owner_id == owner_pk).count() == 0


def test_integration_notes_present():
    """Deferred integrations are recorded at the contract module, not silently dropped."""
    assert 'QueryBuilder' in ownership.OWNERSHIP_INTEGRATION_NOTES


def test_container_node_types_match_orm():
    """Storage owner eligibility strings equal the real ORM container type strings (F1)."""
    from aiida.orm import DataDict, DataList

    assert set(ownership.CONTAINER_NODE_TYPES) == {DataList.class_node_type, DataDict.class_node_type}
    assert ownership.is_container_node_type(DataList.class_node_type)
    assert ownership.is_container_node_type(DataDict.class_node_type)
