# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""orm.Code tests for the export and import routines"""

import os

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common.links import LinkType
from aiida.tools.importexport import import_data, export

from tests.utils.configuration import with_temp_dir
from tests.tools.importexport.utils import get_all_node_links


class TestCode(AiidaTestCase):
    """Test ex-/import cases related to Codes"""

    def setUp(self):
        self.reset_database()

    def tearDown(self):
        self.reset_database()

    @with_temp_dir
    def test_that_solo_code_is_exported_correctly(self, temp_dir):
        """
        This test checks that when a calculation is exported then the
        corresponding code is also exported.
        """
        code_label = 'test_code1'

        code = orm.Code()
        code.set_remote_computer_exec((self.computer, '/bin/true'))
        code.label = code_label
        code.store()

        code_uuid = code.uuid

        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([code], outfile=export_file, silent=True)

        self.reset_database()

        import_data(export_file, silent=True)

        self.assertEqual(orm.load_node(code_uuid).label, code_label)

    @with_temp_dir
    def test_input_code(self, temp_dir):
        """
        This test checks that when a calculation is exported then the
        corresponding code is also exported. It also checks that the links
        are also in place after the import.
        """
        code_label = 'test_code1'

        code = orm.Code()
        code.set_remote_computer_exec((self.computer, '/bin/true'))
        code.label = code_label
        code.store()

        code_uuid = code.uuid

        calc = orm.CalcJobNode()
        calc.computer = self.computer
        calc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})

        calc.add_incoming(code, LinkType.INPUT_CALC, 'code')
        calc.store()
        calc.seal()
        links_count = 1

        export_links = get_all_node_links()

        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([calc], outfile=export_file, silent=True)

        self.reset_database()

        import_data(export_file, silent=True)

        # Check that the code node is there
        self.assertEqual(orm.load_node(code_uuid).label, code_label)

        # Check that the link is in place
        import_links = get_all_node_links()
        self.assertListEqual(sorted(export_links), sorted(import_links))
        self.assertEqual(
            len(export_links), links_count, 'Expected to find only one link from code to '
            'the calculation node before export. {} found.'.format(len(export_links))
        )
        self.assertEqual(
            len(import_links), links_count, 'Expected to find only one link from code to '
            'the calculation node after import. {} found.'.format(len(import_links))
        )

    @with_temp_dir
    def test_solo_code(self, temp_dir):
        """
        This test checks that when a calculation is exported then the
        corresponding code is also exported.
        """
        code_label = 'test_code1'

        code = orm.Code()
        code.set_remote_computer_exec((self.computer, '/bin/true'))
        code.label = code_label
        code.store()

        code_uuid = code.uuid

        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([code], outfile=export_file, silent=True)

        self.clean_db()
        self.insert_data()

        import_data(export_file, silent=True)

        self.assertEqual(orm.load_node(code_uuid).label, code_label)
