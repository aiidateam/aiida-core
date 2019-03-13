# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the ORM Backend class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.backends.testbase import AiidaTestCase
from aiida import orm
from aiida.common import exceptions


class TestBackend(AiidaTestCase):
    """Test backend."""

    def test_transaction_nesting(self):
        """Test that transaction nesting works."""
        user = orm.User('initial@email.com').store()
        with self.backend.transaction():
            user.email = 'pre-failure@email.com'
            try:
                with self.backend.transaction():
                    user.email = 'failure@email.com'
                    self.assertEqual(user.email, 'failure@email.com')
                    raise RuntimeError
            except RuntimeError:
                pass
            self.assertEqual(user.email, 'pre-failure@email.com')
        self.assertEqual(user.email, 'pre-failure@email.com')

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
        self.assertEqual(user1.email, 'user1@email.com')
        self.assertEqual(user2.email, 'user2@email.com')

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

        with self.assertRaises(exceptions.NotExistent):
            orm.User.objects.get(email='user_store_fail@email.com')
