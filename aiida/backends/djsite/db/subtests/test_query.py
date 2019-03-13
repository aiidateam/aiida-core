# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.backends.testbase import AiidaTestCase


class TestQueryBuilderDjango(AiidaTestCase):

    def test_clsf_django(self):
        """
        This tests the classifications of the QueryBuilder u. the django backend.
        """
        from aiida.orm.implementation.django.dummy_model import (
            DbNode, DbUser, DbComputer,
            DbGroup,
        )
        from aiida.common.exceptions import DbContentError
        from aiida.orm import QueryBuilder, Group, Node, Computer, Data, StructureData
        qb = QueryBuilder()

        with self.assertRaises(DbContentError):
            qb._get_ormclass(None, 'data')
        with self.assertRaises(DbContentError):
            qb._get_ormclass(None, 'data.Data')
        with self.assertRaises(DbContentError):
            qb._get_ormclass(None, '.')

        for cls, classifiers in (
                qb._get_ormclass(StructureData, None),
                qb._get_ormclass(None, 'data.structure.StructureData.'),
        ):
            self.assertEqual(classifiers['ormclass_type_string'], 'data.structure.StructureData.')
            self.assertTrue(issubclass(cls, DbNode))

        for cls, classifiers in (
                qb._get_ormclass(DbNode, None),
        ):
            self.assertEqual(classifiers['ormclass_type_string'], Node._plugin_type_string)
            self.assertTrue(issubclass(cls, DbNode))

        for cls, classifiers in (
                qb._get_ormclass(DbGroup, None),
                qb._get_ormclass(Group, None),
                qb._get_ormclass(None, 'group'),
                qb._get_ormclass(None, 'Group'),
        ):
            self.assertEqual(classifiers['ormclass_type_string'], 'group')
            self.assertTrue(issubclass(cls, DbGroup))

        for cls, classifiers in (
                qb._get_ormclass(DbUser, None),
                qb._get_ormclass(DbUser, None),
                qb._get_ormclass(None, "user"),
                qb._get_ormclass(None, "User"),
        ):
            self.assertEqual(classifiers['ormclass_type_string'], 'user')
            self.assertTrue(issubclass(cls, DbUser))

        for cls, classifiers in (
                qb._get_ormclass(DbComputer, None),
                qb._get_ormclass(Computer, None),
                qb._get_ormclass(None, 'computer'),
                qb._get_ormclass(None, 'Computer'),
        ):
            self.assertEqual(classifiers['ormclass_type_string'], 'computer')
            self.assertTrue(issubclass(cls, DbComputer))

        for cls, classifiers in (
                qb._get_ormclass(Data, None),
                qb._get_ormclass(None, 'data.Data.'),
        ):
            self.assertEqual(classifiers['ormclass_type_string'], Data._plugin_type_string)
            self.assertTrue(issubclass(cls, DbNode))
