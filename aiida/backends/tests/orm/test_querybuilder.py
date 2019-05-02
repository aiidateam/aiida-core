# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the QueryBuilder ORM class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from aiida import orm
from aiida.backends.testbase import AiidaTestCase


class TestQueryBuilder(AiidaTestCase):
    """Unit tests for the QueryBuilder ORM class."""

    def test_first_multiple_projections(self):
        """Test `first()` returns correct types and numbers for multiple projections."""
        orm.Data().store()
        orm.Data().store()

        result = orm.QueryBuilder().append(
            orm.User, tag='user', project=['email']).append(
                orm.Data, with_user='user', project=['*']).first()

        self.assertEqual(type(result), list)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], six.string_types)
        self.assertIsInstance(result[1], orm.Data)
