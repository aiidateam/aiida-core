###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test for general backend entities"""

import pickle

import pytest

from aiida import orm
from aiida.common.exceptions import InvalidOperation


class TestBackendEntitiesAndCollections:
    """Test backend entities and their collections"""

    def test_get_collection(self, backend):
        """Test :meth:`aiida.orm.entities.Entity.get_collection`."""
        user_collection = orm.User.get_collection(backend)
        assert user_collection is orm.User.collection
        assert user_collection.backend is backend

    def test_collections_cache(self):
        """Make sure that we're not recreating collections each time .collection is called"""
        # Check directly
        user_collection = orm.User.collection
        assert user_collection is orm.User.collection

        # Now check passing an explicit backend
        backend = user_collection.backend
        assert user_collection is user_collection(backend)

    def test_collections_count(self):
        """Make sure count() works for collections"""
        user_collection_count = orm.User.collection.count()
        number_of_users = orm.QueryBuilder().append(orm.User).count()
        assert number_of_users > 0, 'There should be more than 0 Users in the DB'
        assert user_collection_count == number_of_users, (
            "{} User(s) was/were found using Collections' count() method, "
            'but {} User(s) was/were found using QueryBuilder directly'.format(user_collection_count, number_of_users)
        )

    def test_pickle(self):
        """Pickling is not supported and should raise."""
        with pytest.raises(InvalidOperation):
            pickle.dumps(orm.Entity({}))
