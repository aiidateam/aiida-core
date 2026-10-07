###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Characterization tests for transaction, rollback and repository failure behavior.

These tests pin down the exact guarantees the storage layer provides today so that atomic ownership-subtree storage
(container nodes) can be built on top of them. They run against every supported database backend (SQLite and
PostgreSQL) through the generic ``backend`` fixture.

Background: a database transaction does not roll back repository (file) writes, and rolled-back ORM objects keep
stale in-memory state. Future subtree storage must therefore treat in-memory objects touched by a failed transaction
as discarded, retry with fresh objects, and rely on the existing unreferenced-object maintenance to clean up orphaned
repository content.
"""

from io import BytesIO

import pytest
from sqlalchemy.exc import InvalidRequestError

from aiida import orm
from aiida.common import exceptions
from aiida.common.links import LinkType


@pytest.mark.usefixtures('aiida_profile_clean')
def test_multi_node_store_rolls_back_together(backend):
    """Storing multiple nodes in one transaction is all-or-nothing at the database level."""
    first = orm.Data()
    second = orm.Data()
    uuids = (first.uuid, second.uuid)

    with pytest.raises(RuntimeError, match='boom'):
        with backend.transaction():
            first.store()
            second.store()
            assert first.is_stored and second.is_stored
            raise RuntimeError('boom')

    for uuid in uuids:
        with pytest.raises(exceptions.NotExistent):
            orm.load_node(uuid=uuid)
    assert orm.QueryBuilder().append(orm.Data).count() == 0


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_transaction_inner_failure_caught_by_outer(backend):
    """An inner failure caught by the outer caller rolls back only the inner work."""
    outer = orm.Data()
    inner = orm.Data()

    with backend.transaction():
        outer.store()
        with pytest.raises(RuntimeError, match='inner'):
            with backend.transaction():
                inner.store()
                raise RuntimeError('inner')

    orm.load_node(uuid=outer.uuid)
    with pytest.raises(exceptions.NotExistent):
        orm.load_node(uuid=inner.uuid)


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.xfail(reason='nested transaction() commits the outer transaction early', strict=True)
def test_nested_transaction_outer_failure_rolls_back_inner(backend):
    """A successful nested transaction must still roll back if the outer transaction fails."""
    outer = orm.Data()
    inner = orm.Data()

    with pytest.raises(RuntimeError, match='outer'):
        with backend.transaction():
            outer.store()
            with backend.transaction():
                inner.store()
            raise RuntimeError('outer')

    for uuid in (outer.uuid, inner.uuid):
        with pytest.raises(exceptions.NotExistent):
            orm.load_node(uuid=uuid)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_store_inside_transaction_does_not_commit(backend):
    """`Node.store` composed inside a transaction only flushes and is rolled back on failure."""
    node = orm.Data()

    with pytest.raises(RuntimeError, match='boom'):
        with backend.transaction():
            node.store()
            assert node.is_stored
            raise RuntimeError('boom')

    with pytest.raises(exceptions.NotExistent):
        orm.load_node(uuid=node.uuid)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_rolled_back_nodes_must_be_discarded(backend):
    """Objects touched by a rolled-back transaction are unusable and must be discarded.

    The in-memory object keeps a stale ``is_stored`` flag and primary key, any attribute access fails because the
    underlying row was never committed, and calling ``store()`` again is a silent no-op. Retrying storage therefore
    requires fresh objects, which the content-addressed repository deduplicates automatically.
    """
    node = orm.Data()
    node.base.attributes.set('a', 1)

    with pytest.raises(RuntimeError, match='boom'):
        with backend.transaction():
            node.store()
            raise RuntimeError('boom')

    # Stale in-memory state: the object claims to be stored but its row does not exist.
    assert node.is_stored
    assert node.pk is not None
    with pytest.raises(exceptions.NotExistent):
        orm.load_node(uuid=node.uuid)
    # The detached model can no longer be read ...
    with pytest.raises(InvalidRequestError):
        node.base.attributes.get('a')
    # ... nor edited ...
    with pytest.raises(exceptions.ModificationNotAllowed):
        node.base.attributes.set('b', 2)
    # ... and re-storing is a silent no-op that still leaves nothing in the database.
    node.store()
    with pytest.raises(exceptions.NotExistent):
        orm.load_node(uuid=node.uuid)

    # A fresh object with identical content stores and reads back fine.
    retry = orm.Data()
    retry.base.attributes.set('a', 1)
    retry.store()
    assert orm.load_node(uuid=retry.uuid).base.attributes.get('a') == 1


@pytest.mark.usefixtures('aiida_profile_clean')
def test_repository_writes_are_not_rolled_back(backend):
    """Repository content written before a database rollback survives as unreferenced objects.

    A database transaction cannot roll back repository writes, so a failed store leaves the prepared content behind.
    The existing maintenance machinery must be able to identify it.
    """
    assert backend.get_unreferenced_keyset() == set()

    node = orm.Data()
    node.base.repository.put_object_from_filelike(BytesIO(b'content'), 'file.txt')

    with pytest.raises(RuntimeError, match='boom'):
        with backend.transaction():
            node.store()
            raise RuntimeError('boom')

    with pytest.raises(exceptions.NotExistent):
        orm.load_node(uuid=node.uuid)
    assert len(backend.get_unreferenced_keyset(check_consistency=False)) == 1


@pytest.mark.usefixtures('aiida_profile_clean')
def test_unreferenced_cleanup_preserves_live_content(backend):
    """Maintenance removes orphaned repository content without touching referenced files."""
    live = orm.Data()
    live.base.repository.put_object_from_filelike(BytesIO(b'live'), 'file.txt')
    live.store()

    orphan = orm.Data()
    orphan.base.repository.put_object_from_filelike(BytesIO(b'orphan'), 'file.txt')
    with pytest.raises(RuntimeError, match='boom'):
        with backend.transaction():
            orphan.store()
            raise RuntimeError('boom')

    assert len(backend.get_unreferenced_keyset(check_consistency=False)) == 1
    backend.maintain(full=False)
    assert backend.get_unreferenced_keyset(check_consistency=False) == set()
    assert orm.load_node(uuid=live.uuid).base.repository.get_object_content('file.txt') == 'live'


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.xfail(reason='backend link creation commits instead of joining the ambient transaction', strict=True)
def test_add_incoming_joins_ambient_transaction(backend):
    """Creating a link inside a transaction must roll back together with the transaction.

    Backend-level link creation currently commits unconditionally, which would break atomic subtree storage that
    composes link writes inside a transaction. Note this test uses the backend API directly on purpose: ownership
    validation must hold for low-level write paths as well, not just ORM convenience methods.
    """
    source = orm.Data().store()
    target = orm.Data().store()

    with pytest.raises(RuntimeError, match='boom'):
        with backend.transaction():
            target.backend_entity.add_incoming(source.backend_entity, LinkType.INPUT_WORK, 'input')
            raise RuntimeError('boom')

    assert target.base.links.get_incoming().all() == []


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.xfail(reason='store_all stores inputs sequentially without a transaction', strict=True)
def test_store_all_is_atomic(backend, monkeypatch):
    """`Node.store_all` must not leave partially stored inputs behind when a later store fails."""
    parent = orm.Data()
    child = orm.CalcJobNode()
    child.base.links.add_incoming(parent, link_type=LinkType.INPUT_CALC, link_label='input')

    def fail_store(self):
        raise RuntimeError('child store fails')

    monkeypatch.setattr(orm.CalcJobNode, 'store', fail_store)
    with pytest.raises(RuntimeError, match='child store fails'):
        child.store_all()

    with pytest.raises(exceptions.NotExistent):
        orm.load_node(uuid=parent.uuid)
