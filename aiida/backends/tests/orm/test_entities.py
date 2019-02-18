# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test for general backend entities"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida import orm


class TestBackendEntitiesAndCollections(AiidaTestCase):
    """Test backend entities and their collections"""

    def test_collections_cache(self):
        """Make sure that we're not recreating collections each time .objects is called"""
        # Check directly
        user_collection = orm.User.objects
        self.assertIs(user_collection, orm.User.objects)

        # Now check passing an explicit backend
        backend = user_collection.backend
        self.assertIs(user_collection, user_collection(backend))
