###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Savepoint isolation when backend operations hit real database failures.

While the transaction characterization tests use manually raised errors, these tests trigger actual database
constraint and flush failures inside a nested backend transaction through the existing backend write operations
and their error handlers. They run against every supported database backend through the generic ``backend``
fixture.

A nested failure caught by the outer caller must roll back only to its savepoint: earlier outer work survives,
the failed inner work is absent, and the session stays usable for further writes up to a successful outer commit.
"""

import pytest

from aiida import orm
from aiida.common import exceptions


@pytest.mark.usefixtures('aiida_profile_clean')
def test_integrity_error_in_nested_transaction_preserves_outer_work(backend):
    """A unique-constraint failure in a nested transaction must not take outer work down with it."""
    outer = orm.Data()

    with backend.transaction():
        outer.store()
        orm.User('duplicate@email.com').store()
        with pytest.raises(exceptions.IntegrityError, match=r'(?i)unique'):
            with backend.transaction():
                orm.User('duplicate@email.com').store()

        # The session remains usable: further writes succeed and the outer transaction commits.
        later = orm.Data()
        later.store()

    assert orm.load_node(uuid=outer.uuid).pk == outer.pk
    assert orm.load_node(uuid=later.uuid).pk == later.pk
    assert orm.QueryBuilder().append(orm.Data).count() == 2
    assert orm.QueryBuilder().append(orm.User, filters={'email': 'duplicate@email.com'}).count() == 1


@pytest.mark.usefixtures('aiida_profile_clean')
def test_bulk_failure_without_handler_rolls_back_to_savepoint(backend):
    """Without an error handler in the way, a flush failure already isolates to its savepoint.

    This baseline shows the savepoint mechanics are sound; the isolation bug is specific to error handlers that
    call ``session.rollback()``.
    """
    from sqlalchemy.exc import IntegrityError as SAIntegrityError

    from aiida.orm.entities import EntityTypes

    outer = orm.Data()

    with backend.transaction():
        outer.store()
        with pytest.raises(SAIntegrityError):
            with backend.transaction():
                backend.bulk_insert(
                    EntityTypes.USER,
                    [{'email': 'bulk-dup@email.com'}, {'email': 'bulk-dup@email.com'}],
                    allow_defaults=True,
                )

        later = orm.Data()
        later.store()

    orm.load_node(uuid=outer.uuid)
    orm.load_node(uuid=later.uuid)
    assert orm.QueryBuilder().append(orm.User, filters={'email': 'bulk-dup@email.com'}).count() == 0


@pytest.mark.usefixtures('aiida_profile_clean')
def test_integrity_error_without_transaction_keeps_session_usable(backend):
    """A constraint failure outside any explicit transaction still raises and leaves a clean session."""
    orm.User('duplicate@email.com').store()

    with pytest.raises(exceptions.IntegrityError, match=r'(?i)unique'):
        orm.User('duplicate@email.com').store()

    node = orm.Data()
    node.store()
    orm.load_node(uuid=node.uuid)
    assert orm.QueryBuilder().append(orm.User, filters={'email': 'duplicate@email.com'}).count() == 1
