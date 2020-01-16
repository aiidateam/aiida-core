# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Extras tests for the export and import routines"""
# pylint: disable=attribute-defined-outside-init

import os

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.tools.importexport import import_data, export

from tests.utils.configuration import with_temp_dir


class TestAttributes(AiidaTestCase):
    """Test ex-/import cases related to Attributes"""

    def create_data_with_attr(self):
        self.data = orm.Data()
        self.data.label = 'my_test_data_node'
        self.data.set_attribute_many({'b': 2, 'c': 3})
        self.data.store()

    def import_attributes(self):
        """Import an AiiDA database"""
        import_data(self.export_file, silent=True)

        builder = orm.QueryBuilder().append(orm.Data, filters={'label': 'my_test_data_node'})

        self.assertEqual(builder.count(), 1)
        self.imported_node = builder.all()[0][0]

    @with_temp_dir
    def test_import_of_attributes(self, temp_dir):
        """Check if attributes are properly imported"""
        # Create Data with attributes
        self.create_data_with_attr()

        self.assertEqual(self.data.get_attribute('b'), 2)
        self.assertEqual(self.data.get_attribute('c'), 3)

        # Export
        self.export_file = os.path.join(temp_dir, 'export.aiida')
        export([self.data], outfile=self.export_file, silent=True)

        # Clean db
        self.reset_database()

        self.import_attributes()

        self.assertEqual(self.imported_node.get_attribute('b'), 2)
        self.assertEqual(self.imported_node.get_attribute('c'), 3)
