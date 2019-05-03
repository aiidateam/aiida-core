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
from unittest import skip


class TestQueryBuilderDjango(AiidaTestCase):

    @skip("This test passes but we should see it is still valid under Django JSONB")
    def test_clsf_django(self):
        """
        This tests the classifications of the QueryBuilder u. the django backend.
        """
        import aiida.backends.djsite.db.models as djmodels
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
            self.assertTrue(issubclass(cls, djmodels.DbNode.sa))

        for cls, classifiers in (
                qb._get_ormclass(djmodels.DbNode.sa, None),
        ):
            self.assertEqual(classifiers['ormclass_type_string'], Node._plugin_type_string)
            self.assertTrue(issubclass(cls, djmodels.DbNode.sa))

        for cls, classifiers in (
                qb._get_ormclass(djmodels.DbGroup.sa, None),
                qb._get_ormclass(Group, None),
                qb._get_ormclass(None, 'group'),
                qb._get_ormclass(None, 'Group'),
        ):
            self.assertEqual(classifiers['ormclass_type_string'], 'group')
            self.assertTrue(issubclass(cls, djmodels.DbGroup.sa))

        for cls, classifiers in (
                qb._get_ormclass(djmodels.DbUser.sa, None),
                qb._get_ormclass(djmodels.DbUser.sa, None),
                qb._get_ormclass(None, "user"),
                qb._get_ormclass(None, "User"),
        ):
            self.assertEqual(classifiers['ormclass_type_string'], 'user')
            self.assertTrue(issubclass(cls, djmodels.DbUser.sa))

        for cls, classifiers in (
                qb._get_ormclass(djmodels.DbComputer.sa, None),
                qb._get_ormclass(Computer, None),
                qb._get_ormclass(None, 'computer'),
                qb._get_ormclass(None, 'Computer'),
        ):
            self.assertEqual(classifiers['ormclass_type_string'], 'computer')
            self.assertTrue(issubclass(cls, djmodels.DbComputer.sa))

        for cls, classifiers in (
                qb._get_ormclass(Data, None),
                qb._get_ormclass(None, 'data.Data.'),
        ):
            self.assertEqual(classifiers['ormclass_type_string'], Data._plugin_type_string)
            self.assertTrue(issubclass(cls, djmodels.DbNode.sa))
