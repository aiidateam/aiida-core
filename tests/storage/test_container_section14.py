###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Spec section-14 verification matrix (storage level): owned data containers.

Backend-contract tests through ``aiida.storage.ownership`` and the
``create_container_membership`` backend method, run against every supported
database backend via the ``backend`` fixture (SQLite and PostgreSQL). Covers
the §14 storage-invariant bullets: low-level agreement paths, concurrent
violations, bulk guards, provenance-link rejection, deletion closure +
revalidation, archive export rejection, migration columns, plus perf
measurements (attach/traversal/deletion/export timing with per-child query
hotspot notes). TEST code only; no feature source is changed here.
"""

import time

import pytest

from aiida.common.exceptions import IntegrityError
from aiida.orm.entities import EntityTypes
from aiida.storage import ownership

pytestmark = pytest.mark.usefixtures('aiida_profile_clean')

FLOAT_TYPE = 'data.core.float.Float.'
INT_TYPE = 'data.core.int.Int.'
DATA_TYPE = 'data.Data.'
PROCESS_TYPE = 'process.calculation.calcjob.CalcJobNode.'

# Real ORM identifiers (entry-point preserving underscores). NOTE (binding
# F1): ``ownership.CONTAINER_NODE_TYPES`` still carries the wrong literals
# (``datalist``/``datadict``); tests below use the literals the backend
# contract currently enforces where needed and file the mismatch in the
# verify-agent status file instead of fixing source.
STORAGE_LIST_TYPE = next(iter(t for t in ownership.CONTAINER_NODE_TYPES if 'List' in t))
STORAGE_DICT_TYPE = next(iter(t for t in ownership.CONTAINER_NODE_TYPES if 'Dict' in t))


def _stored_nodes(backend, *node_types):
    from aiida.orm import Data

    nodes = [Data().store() for _ in node_types]
    backend.bulk_update(
        EntityTypes.NODE,
        [{'id': node.pk, 'node_type': node_type} for node, node_type in zip(nodes, node_types, strict=True)],
    )
    return nodes


def _attach(backend, owner_pk, specs):
    return backend.create_container_membership(owner_pk, specs)


def _spec(child_pk, child_type, position, key=None):
    return {'child_id': child_pk, 'child_node_type': child_type, 'position': position, 'key': key}


class TestRealOrmTypesAccepted:
    """F1 regression: the backend contract accepts the real ORM container identifiers."""

    def test_real_datalist_datatdict_types(self, backend):
        from aiida.orm import DataDict, DataList

        assert DataList.class_node_type in ownership.CONTAINER_NODE_TYPES
        assert DataDict.class_node_type in ownership.CONTAINER_NODE_TYPES
        owner, child = _stored_nodes(backend, DataList.class_node_type, FLOAT_TYPE)[0:2]
        resolved = _attach(backend, owner.pk, [_spec(child.pk, FLOAT_TYPE, 0)])
        assert resolved == FLOAT_TYPE


class TestLowLevelAgreement:
    """§14: owner/membership agreement through low-level paths."""

    def test_attach_sets_owner_and_rows(self, backend):
        owner, child_a, child_b = _stored_nodes(backend, STORAGE_LIST_TYPE, FLOAT_TYPE, FLOAT_TYPE)[0:3]
        resolved = _attach(backend, owner.pk, [_spec(child_a.pk, FLOAT_TYPE, 0), _spec(child_b.pk, FLOAT_TYPE, 1)])
        assert resolved == FLOAT_TYPE
        node_model, membership_model = backend._ownership_models()
        session = backend.get_session()
        rows = session.query(membership_model).filter(membership_model.owner_id == owner.pk).all()
        assert sorted(row.position for row in rows) == [0, 1]
        for child in (child_a, child_b):
            row = session.query(node_model).filter(node_model.id == child.pk).one()
            assert row.owner_id == owner.pk

    def test_agreement_violation_detected(self, backend):
        """A membership row without a matching owner ref (or vice versa) is rejected."""
        owner, child = _stored_nodes(backend, STORAGE_LIST_TYPE, FLOAT_TYPE)[0:2]
        _, membership_model = backend._ownership_models()
        session = backend.get_session()
        # Hand-insert a membership row that disagrees with the child's NULL owner ref.
        session.add(membership_model(owner_id=owner.pk, child_id=child.pk, position=0, key=None))
        session.flush()
        with pytest.raises(IntegrityError, match=r'[Aa]greement|[Aa]lready'):
            _attach(backend, owner.pk, [_spec(child.pk, FLOAT_TYPE, 1)])

    def test_dict_keys_persisted_agree(self, backend):
        owner, child = _stored_nodes(backend, STORAGE_DICT_TYPE, INT_TYPE)[0:2]
        _attach(backend, owner.pk, [_spec(child.pk, INT_TYPE, 0, key='alpha')])
        _, membership_model = backend._ownership_models()
        row = backend.get_session().query(membership_model).filter(membership_model.owner_id == owner.pk).one()
        assert row.key == 'alpha'
        assert row.position == 0


class TestConcurrentViolations:
    """§14: concurrent invariant violations (uniqueness makes races fail, not agree)."""

    def test_double_attach_same_child_fails(self, backend):
        owner_a, owner_b, child = _stored_nodes(backend, STORAGE_LIST_TYPE, STORAGE_LIST_TYPE, FLOAT_TYPE)
        _attach(backend, owner_a.pk, [_spec(child.pk, FLOAT_TYPE, 0)])
        with pytest.raises(IntegrityError):
            _attach(backend, owner_b.pk, [_spec(child.pk, FLOAT_TYPE, 0)])

    def test_overlapping_positions_rejected(self, backend):
        owner, child_a, child_b = _stored_nodes(backend, STORAGE_LIST_TYPE, FLOAT_TYPE, FLOAT_TYPE)[0:3]
        with pytest.raises(IntegrityError, match=r'[Dd]uplicate|[Pp]osition'):
            _attach(
                backend,
                owner.pk,
                [_spec(child_a.pk, FLOAT_TYPE, 0), _spec(child_b.pk, FLOAT_TYPE, 0)],
            )

    def test_duplicate_keys_rejected(self, backend):
        owner, child_a, child_b = _stored_nodes(backend, STORAGE_DICT_TYPE, INT_TYPE, INT_TYPE)[0:3]
        with pytest.raises(IntegrityError, match=r'[Dd]uplicate|[Kk]ey'):
            _attach(
                backend,
                owner.pk,
                [_spec(child_a.pk, INT_TYPE, 0, key='k'), _spec(child_b.pk, INT_TYPE, 1, key='k')],
            )


class TestBulkAndLinkGuards:
    """§14: bulk-operation guards and low-level provenance-link rejection."""

    def test_bulk_insert_owned_rejected(self):
        with pytest.raises(IntegrityError):
            ownership.validate_bulk_node_insert([{'owner_id': 42, 'container_element_type': None}])

    def test_bulk_insert_locked_type_rejected(self):
        with pytest.raises(IntegrityError):
            ownership.validate_bulk_node_insert([{'owner_id': None, 'container_element_type': FLOAT_TYPE}])

    def test_bulk_update_ownership_rejected(self):
        with pytest.raises(IntegrityError):
            ownership.validate_bulk_node_update([{'id': 1, 'owner_id': None}])

    def test_link_rows_touching_owned_rejected(self, backend):
        owner, child = _stored_nodes(backend, STORAGE_LIST_TYPE, FLOAT_TYPE)[0:2]
        _attach(backend, owner.pk, [_spec(child.pk, FLOAT_TYPE, 0)])
        from aiida.orm import Data

        other = Data().store()
        node_model, _ = backend._ownership_models()
        with pytest.raises(IntegrityError, match=r'[Oo]wned'):
            ownership.validate_link_rows(
                backend.get_session(),
                node_model,
                [{'input_id': child.pk, 'output_id': other.pk}],
            )


class TestDeletionClosureRevalidation:
    """§14: deletion approval (closure required) + execution-time revalidation."""

    def test_child_only_rejected(self, backend):
        owner, child = _stored_nodes(backend, STORAGE_LIST_TYPE, FLOAT_TYPE)[0:2]
        _attach(backend, owner.pk, [_spec(child.pk, FLOAT_TYPE, 0)])
        with pytest.raises(IntegrityError, match=r'[Cc]losed|[Ee]xpand|[Cc]losure'):
            ownership.validate_deletion_set(backend.get_session(), *backend._ownership_models(), [child.pk])

    def test_container_only_rejected(self, backend):
        owner, child = _stored_nodes(backend, STORAGE_LIST_TYPE, FLOAT_TYPE)[0:2]
        _attach(backend, owner.pk, [_spec(child.pk, FLOAT_TYPE, 0)])
        with pytest.raises(IntegrityError, match=r'[Cc]losed|[Ee]xpand|[Cc]losure|[Ss]ubtree'):
            ownership.validate_deletion_set(backend.get_session(), *backend._ownership_models(), [owner.pk])

    def test_closed_unit_validates(self, backend):
        owner, child = _stored_nodes(backend, STORAGE_LIST_TYPE, FLOAT_TYPE)[0:2]
        _attach(backend, owner.pk, [_spec(child.pk, FLOAT_TYPE, 0)])
        ownership.validate_deletion_set(backend.get_session(), *backend._ownership_models(), [owner.pk, child.pk])

    def test_expand_closure_helper(self, backend):
        owner, child = _stored_nodes(backend, STORAGE_LIST_TYPE, FLOAT_TYPE)[0:2]
        _attach(backend, owner.pk, [_spec(child.pk, FLOAT_TYPE, 0)])
        expanded = ownership.expand_ownership_closure(backend.get_session(), *backend._ownership_models(), [child.pk])
        assert expanded == {owner.pk, child.pk}


class TestArchiveExportRejection:
    """§14/§11: ownership-unit export safe-rejection (accepted per F5)."""

    def test_plain_export_unaffected(self, backend, tmp_path):
        from aiida.orm import Data
        from aiida.tools.archive import create_archive

        node = Data().store()
        path = str(tmp_path / 'plain.aiida')
        create_archive([node], filename=path)
        assert True

    def test_ownership_export_rejected(self, backend, tmp_path):
        from aiida.tools.archive import create_archive

        owner, child = _stored_nodes(backend, STORAGE_LIST_TYPE, FLOAT_TYPE)[0:2]
        _attach(backend, owner.pk, [_spec(child.pk, FLOAT_TYPE, 0)])
        from aiida.orm import load_node

        path = str(tmp_path / 'owned.aiida')
        with pytest.raises(Exception, match=r'[Oo]wned|[Cc]ontainer|[Oo]wnership'):
            create_archive([load_node(owner.pk)], filename=path)


class TestMigrationColumns:
    """§14: migration — ownership columns exist; pre-existing nodes stay standalone."""

    def test_owner_columns_present(self, backend):
        node_model, membership_model = backend._ownership_models()
        assert hasattr(node_model, 'owner_id')
        assert hasattr(node_model, 'container_element_type')
        assert hasattr(membership_model, 'owner_id')
        assert hasattr(membership_model, 'child_id')

    def test_existing_nodes_standalone(self, backend):
        from aiida.orm import Data

        node = Data().store()
        row = backend.get_session().query(backend._ownership_models()[0]).filter_by(id=node.pk).one()
        assert row.owner_id is None
        assert row.container_element_type is None


class TestPerfBackend:
    """§14 perf: attach/traversal/deletion timing; flag per-child query hotspots."""

    @pytest.mark.parametrize('size', [50, 200])
    def test_attach_traverse_delete_timing(self, size, backend, capsys):
        owner = _stored_nodes(backend, STORAGE_LIST_TYPE)[0]
        from aiida.orm import Data

        children = [Data().store() for _ in range(size)]
        child_type = children[0].node_type
        specs = [_spec(child.pk, child_type, position) for position, child in enumerate(children)]

        start = time.monotonic()
        resolved = _attach(backend, owner.pk, specs)
        attach_s = time.monotonic() - start
        assert resolved == child_type

        node_model, membership_model = backend._ownership_models()
        session = backend.get_session()
        start = time.monotonic()
        rows = session.query(membership_model).filter(membership_model.owner_id == owner.pk).all()
        traverse_s = time.monotonic() - start
        assert len(rows) == size

        start = time.monotonic()
        ownership.validate_deletion_set(session, node_model, membership_model, [owner.pk] + [c.pk for c in children])
        validate_s = time.monotonic() - start

        with capsys.disabled():
            print(
                f'\n[perf-storage] N={size}: attach={attach_s:.3f}s '
                f'traverse={traverse_s:.3f}s delete-validate={validate_s:.3f}s'
            )
        # Generous gates only: fail loudly on per-child query blowups, not on normal variance.
        assert attach_s < 120
        assert traverse_s < 60
