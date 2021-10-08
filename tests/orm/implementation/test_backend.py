# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the ORM Backend class."""
import pytest

from aiida import orm
from aiida.common import exceptions
from aiida.orm.entities import EntityTypes


@pytest.mark.usefixtures('clear_database_before_test')
class TestBackend:
    """Test backend."""

    @pytest.fixture(autouse=True)
    def init_test(self, backend):
        """Set up the backend."""
        self.backend = backend  # pylint: disable=attribute-defined-outside-init

    def test_transaction_nesting(self):
        """Test that transaction nesting works."""
        user = orm.User('initial@email.com').store()
        with self.backend.transaction():
            user.email = 'pre-failure@email.com'
            try:
                with self.backend.transaction():
                    user.email = 'failure@email.com'
                    assert user.email == 'failure@email.com'
                    raise RuntimeError
            except RuntimeError:
                pass
            assert user.email == 'pre-failure@email.com'
        assert user.email == 'pre-failure@email.com'

    def test_transaction(self):
        """Test that transaction nesting works."""
        user1 = orm.User('user1@email.com').store()
        user2 = orm.User('user2@email.com').store()

        try:
            with self.backend.transaction():
                user1.email = 'broken1@email.com'
                user2.email = 'broken2@email.com'
                raise RuntimeError
        except RuntimeError:
            pass
        assert user1.email == 'user1@email.com'
        assert user2.email == 'user2@email.com'

    def test_store_in_transaction(self):
        """Test that storing inside a transaction is correctly dealt with."""
        user1 = orm.User('user_store@email.com')
        with self.backend.transaction():
            user1.store()
        # the following shouldn't raise
        orm.User.objects.get(email='user_store@email.com')

        user2 = orm.User('user_store_fail@email.com')
        try:
            with self.backend.transaction():
                user2.store()
                raise RuntimeError
        except RuntimeError:
            pass

        with pytest.raises(exceptions.NotExistent):
            orm.User.objects.get(email='user_store_fail@email.com')

    def test_bulk_insert(self):
        """Test that bulk insert works."""
        rows = [{'email': 'user1@email.com'}, {'email': 'user2@email.com'}]
        with self.backend.transaction() as transaction:
            # should fail if all fields are not given and allow_defaults=False
            with pytest.raises(exceptions.IntegrityError, match='Incorrect fields'):
                self.backend.bulk_insert(EntityTypes.USER, rows, transaction)
            pks = self.backend.bulk_insert(EntityTypes.USER, rows, transaction, allow_defaults=True)
        assert len(pks) == len(rows)
        for pk, row in zip(pks, rows):
            assert isinstance(pk, int)
            user = orm.User.objects.get(id=pk)
            assert user.email == row['email']

    def test_bulk_update(self):
        """Test that bulk update works."""
        user1 = orm.User('user1@email.com').store()
        user2 = orm.User('user2@email.com').store()
        user3 = orm.User('user3@email.com').store()
        with self.backend.transaction() as transaction:
            # should raise if the 'id' field is not present
            with pytest.raises(exceptions.IntegrityError, match="'id' field not given"):
                self.backend.bulk_update(EntityTypes.USER, [{'email': 'other'}], transaction)
            # should raise if a non-existent field is present
            with pytest.raises(exceptions.IntegrityError, match='Incorrect fields'):
                self.backend.bulk_update(EntityTypes.USER, [{'id': user1.pk, 'x': 'other'}], transaction)
            self.backend.bulk_update(
                EntityTypes.USER, [{
                    'id': user1.pk,
                    'email': 'other1'
                }, {
                    'id': user2.pk,
                    'email': 'other2'
                }], transaction
            )
        assert user1.email == 'other1'
        assert user2.email == 'other2'
        assert user3.email == 'user3@email.com'
