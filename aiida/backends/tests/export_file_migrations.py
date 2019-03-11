# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Generic tests that need the use of the DB."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida import orm


class TestExportFileMigration(AiidaTestCase):
    """
    Test the Code class.
    """

    def test_v3_to_v4(self):
        import os

        from aiida.common.folders import SandboxFolder
        from aiida.cmdline.commands.cmd_export import migrate
        from aiida.orm.importexport import import_data

        from aiida.orm.node import CalculationNode
        from aiida.orm.node.data.structure import StructureData
        from aiida.orm.node.data.remote import RemoteData
        from aiida.orm.node import Node
        from aiida.orm.querybuilder import QueryBuilder

        with SandboxFolder(sandbox_in_repo=False) as new_export_folder:
            # aiida/backends/tests/fixtures/calcjob/arithmetic.add.aiida
            input_file = 'fixtures/calcjob/arithmetic.add.aiida'
            output_file = os.join(new_export_folder, 'output_file.aiida')

            # Perform the migration
            migrate(input_file, output_file, True, True, 'tar.gz')

            # Load the migrated file
            import_data(output_file, silent=True)

            # Do the necessary checks
            self.assertEquals(QueryBuilder().append(Node).count(), 5)

            # Verify that CalculationNodes have non-empty attribute dictionaries
            qb = QueryBuilder().append(CalculationNode)
            for [calculation] in qb.iterall():
                self.assertIsInstance(calculation.get_attrs(), dict)
                self.assertNotEquals(len(calculation.get_attrs()), 0)

            # Verify that the structure data maintained its label, cell and kinds
            qb = QueryBuilder().append(StructureData)
            for [structure] in qb.iterall():
                self.assertEquals(structure.label, '')
                self.assertEquals(structure.cell, '')

            qb = QueryBuilder().append(StructureData, project=['attributes.kinds'])
            for [kinds] in qb.iterall():
                self.assertEqual(len(kinds), 2)
                for kind in kinds:
                    self.assertIn(kind, '')

            # Check that there is a StructureData that is an output of a CalculationNode
            qb = QueryBuilder()
            qb.append(CalculationNode, project=['uuid'], tag='calculation')
            qb.append(StructureData, with_incoming='calculation')
            self.assertGreater(len(qb.all()), 0)

            # Check that there is a RemoteData that is a child and parent of a CalculationNode
            qb = QueryBuilder()
            qb.append(CalculationNode, tag='parent')
            qb.append(RemoteData, project=['uuid'], with_incoming='parent', tag='remote')
            qb.append(CalculationNode, with_incoming='remote')
            self.assertGreater(len(qb.all()), 0)
