# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""orm.Computer tests for the export and import routines"""
# pylint: disable=too-many-statements,no-member

import os

from aiida import orm
from aiida.tools.importexport import import_data, export

from tests.utils.configuration import with_temp_dir
from .. import AiidaArchiveTestCase


class TestComputer(AiidaArchiveTestCase):
    """Test ex-/import cases related to Computers"""

    @with_temp_dir
    def test_same_computer_import(self, temp_dir):
        """
        Test that you can import nodes in steps without any problems. In this
        test we will import a first calculation and then a second one. The
        import should work as expected and have in the end two job
        calculations.

        Each calculation is related to the same computer. In the end we should
        have only one computer
        """
        # Use local computer
        comp = self.computer

        # Store two job calculation related to the same computer
        calc1_label = 'calc1'
        calc1 = orm.CalcJobNode()
        calc1.computer = comp
        calc1.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        calc1.label = calc1_label
        calc1.store()
        calc1.seal()

        calc2_label = 'calc2'
        calc2 = orm.CalcJobNode()
        calc2.computer = comp
        calc2.set_option('resources', {'num_machines': 2, 'num_mpiprocs_per_machine': 2})
        calc2.label = calc2_label
        calc2.store()
        calc2.seal()

        # Store locally the computer name
        comp_name = str(comp.label)
        comp_uuid = str(comp.uuid)

        # Export the first job calculation
        filename1 = os.path.join(temp_dir, 'export1.aiida')
        export([calc1], filename=filename1)

        # Export the second job calculation
        filename2 = os.path.join(temp_dir, 'export2.aiida')
        export([calc2], filename=filename2)

        # Clean the local database
        self.refurbish_db()

        # Check that there are no computers
        builder = orm.QueryBuilder()
        builder.append(orm.Computer, project=['*'])
        self.assertEqual(builder.count(), 0, 'There should not be any computers in the database at this point.')

        # Check that there are no calculations
        builder = orm.QueryBuilder()
        builder.append(orm.CalcJobNode, project=['*'])
        self.assertEqual(builder.count(), 0, 'There should not be any calculations in the database at this point.')

        # Import the first calculation
        import_data(filename1)

        # Check that the calculation computer is imported correctly.
        builder = orm.QueryBuilder()
        builder.append(orm.CalcJobNode, project=['label'])
        self.assertEqual(builder.count(), 1, 'Only one calculation should be found.')
        self.assertEqual(str(builder.first()[0]), calc1_label, 'The calculation label is not correct.')

        # Check that the referenced computer is imported correctly.
        builder = orm.QueryBuilder()
        builder.append(orm.Computer, project=['label', 'uuid', 'id'])
        self.assertEqual(builder.count(), 1, 'Only one computer should be found.')
        self.assertEqual(str(builder.first()[0]), comp_name, 'The computer name is not correct.')
        self.assertEqual(str(builder.first()[1]), comp_uuid, 'The computer uuid is not correct.')

        # Store the id of the computer
        comp_id = builder.first()[2]

        # Import the second calculation
        import_data(filename2)

        # Check that the number of computers remains the same and its data
        # did not change.
        builder = orm.QueryBuilder()
        builder.append(orm.Computer, project=['label', 'uuid', 'id'])
        self.assertEqual(builder.count(), 1, f'Found {builder.count()} computersbut only one computer should be found.')
        self.assertEqual(str(builder.first()[0]), comp_name, 'The computer name is not correct.')
        self.assertEqual(str(builder.first()[1]), comp_uuid, 'The computer uuid is not correct.')
        self.assertEqual(builder.first()[2], comp_id, 'The computer id is not correct.')

        # Check that now you have two calculations attached to the same
        # computer.
        builder = orm.QueryBuilder()
        builder.append(orm.Computer, tag='comp')
        builder.append(orm.CalcJobNode, with_computer='comp', project=['label'])
        self.assertEqual(builder.count(), 2, 'Two calculations should be found.')
        ret_labels = set(_ for [_] in builder.all())
        self.assertEqual(ret_labels, set([calc1_label, calc2_label]), 'The labels of the calculations are not correct.')

    @with_temp_dir
    def test_same_computer_different_name_import(self, temp_dir):
        """
        This test checks that if the computer is re-imported with a different
        name to the same database, then the original computer will not be
        renamed. It also checks that the names were correctly imported (without
        any change since there is no computer name collision)
        """
        # Get computer
        comp1 = self.computer

        # Store a calculation
        calc1_label = 'calc1'
        calc1 = orm.CalcJobNode()
        calc1.computer = self.computer
        calc1.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        calc1.label = calc1_label
        calc1.store()
        calc1.seal()

        # Store locally the computer name
        comp1_name = str(comp1.label)

        # Export the first job calculation
        filename1 = os.path.join(temp_dir, 'export1.aiida')
        export([calc1], filename=filename1)

        # Rename the computer
        comp1.label = f'{comp1_name}_updated'

        # Store a second calculation
        calc2_label = 'calc2'
        calc2 = orm.CalcJobNode()
        calc2.computer = self.computer
        calc2.set_option('resources', {'num_machines': 2, 'num_mpiprocs_per_machine': 2})
        calc2.label = calc2_label
        calc2.store()
        calc2.seal()

        # Export the second job calculation
        filename2 = os.path.join(temp_dir, 'export2.aiida')
        export([calc2], filename=filename2)

        # Clean the local database
        self.refurbish_db()

        # Check that there are no computers
        builder = orm.QueryBuilder()
        builder.append(orm.Computer, project=['*'])
        self.assertEqual(builder.count(), 0, 'There should not be any computers in the database at this point.')

        # Check that there are no calculations
        builder = orm.QueryBuilder()
        builder.append(orm.CalcJobNode, project=['*'])
        self.assertEqual(builder.count(), 0, 'There should not be any calculations in the database at this point.')

        # Import the first calculation
        import_data(filename1)

        # Check that the calculation computer is imported correctly.
        builder = orm.QueryBuilder()
        builder.append(orm.CalcJobNode, project=['label'])
        self.assertEqual(builder.count(), 1, 'Only one calculation should be found.')
        self.assertEqual(str(builder.first()[0]), calc1_label, 'The calculation label is not correct.')

        # Check that the referenced computer is imported correctly.
        builder = orm.QueryBuilder()
        builder.append(orm.Computer, project=['label', 'uuid', 'id'])
        self.assertEqual(builder.count(), 1, 'Only one computer should be found.')
        self.assertEqual(str(builder.first()[0]), comp1_name, 'The computer name is not correct.')

        # Import the second calculation
        import_data(filename2)

        # Check that the number of computers remains the same and its data
        # did not change.
        builder = orm.QueryBuilder()
        builder.append(orm.Computer, project=['label'])
        self.assertEqual(builder.count(), 1, f'Found {builder.count()} computersbut only one computer should be found.')
        self.assertEqual(str(builder.first()[0]), comp1_name, 'The computer name is not correct.')

    @with_temp_dir
    def test_different_computer_same_name_import(self, temp_dir):
        """
        This test checks that if there is a name collision, the imported
        computers are renamed accordingly.
        """
        from aiida.tools.importexport.common.config import DUPL_SUFFIX

        # Set the computer name
        comp1_name = 'localhost_1'
        self.computer.label = comp1_name

        # Store a calculation
        calc1_label = 'calc1'
        calc1 = orm.CalcJobNode()
        calc1.computer = self.computer
        calc1.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        calc1.label = calc1_label
        calc1.store()
        calc1.seal()

        # Export the first job calculation
        filename1 = os.path.join(temp_dir, 'export1.aiida')
        export([calc1], filename=filename1)

        # Reset the database
        self.refurbish_db()

        # Set the computer name to the same name as before
        self.computer.label = comp1_name

        # Store a second calculation
        calc2_label = 'calc2'
        calc2 = orm.CalcJobNode()
        calc2.computer = self.computer
        calc2.set_option('resources', {'num_machines': 2, 'num_mpiprocs_per_machine': 2})
        calc2.label = calc2_label
        calc2.store()
        calc2.seal()

        # Export the second job calculation
        filename2 = os.path.join(temp_dir, 'export2.aiida')
        export([calc2], filename=filename2)

        # Reset the database
        self.refurbish_db()

        # Set the computer name to the same name as before
        self.computer.label = comp1_name

        # Store a third calculation
        calc3_label = 'calc3'
        calc3 = orm.CalcJobNode()
        calc3.computer = self.computer
        calc3.set_option('resources', {'num_machines': 2, 'num_mpiprocs_per_machine': 2})
        calc3.label = calc3_label
        calc3.store()
        calc3.seal()

        # Export the third job calculation
        filename3 = os.path.join(temp_dir, 'export3.aiida')
        export([calc3], filename=filename3)

        # Clean the local database
        self.refurbish_db()

        # Check that there are no computers
        builder = orm.QueryBuilder()
        builder.append(orm.Computer, project=['*'])
        self.assertEqual(builder.count(), 0, 'There should not be any computers in the database at this point.')

        # Check that there are no calculations
        builder = orm.QueryBuilder()
        builder.append(orm.CalcJobNode, project=['*'])
        self.assertEqual(
            builder.count(), 0, 'There should not be any '
            'calculations in the database at '
            'this point.'
        )

        # Import all the calculations
        import_data(filename1)
        import_data(filename2)
        import_data(filename3)

        # Retrieve the calculation-computer pairs
        builder = orm.QueryBuilder()
        builder.append(orm.CalcJobNode, project=['label'], tag='jcalc')
        builder.append(orm.Computer, project=['label'], with_node='jcalc')
        self.assertEqual(builder.count(), 3, 'Three combinations expected.')
        res = builder.all()
        self.assertIn([calc1_label, comp1_name], res, 'Calc-Computer combination not found.')
        self.assertIn([calc2_label, comp1_name + DUPL_SUFFIX.format(0)], res, 'Calc-Computer combination not found.')
        self.assertIn([calc3_label, comp1_name + DUPL_SUFFIX.format(1)], res, 'Calc-Computer combination not found.')

    @with_temp_dir
    def test_import_of_computer_json_params(self, temp_dir):
        """
        This test checks that the metadata and transport params are exported and imported correctly in both backends.
        """
        # Set the computer name
        comp1_name = 'localhost_1'
        comp1_metadata = {'workdir': '/tmp/aiida'}
        self.computer.label = comp1_name
        self.computer.metadata = comp1_metadata

        # Store a calculation
        calc1_label = 'calc1'
        calc1 = orm.CalcJobNode()
        calc1.computer = self.computer
        calc1.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        calc1.label = calc1_label
        calc1.store()
        calc1.seal()

        # Export the first job calculation
        filename1 = os.path.join(temp_dir, 'export1.aiida')
        export([calc1], filename=filename1)

        # Clean the local database
        self.refurbish_db()

        # Import the data
        import_data(filename1)

        builder = orm.QueryBuilder()
        builder.append(orm.Computer, project=['metadata'], tag='comp')
        self.assertEqual(builder.count(), 1, 'Expected only one computer')

        res = builder.dict()[0]
        self.assertEqual(res['comp']['metadata'], comp1_metadata, 'Not the expected metadata were found')

    def test_import_of_django_sqla_export_file(self):
        """Check that sqla import manages to import the django archive file correctly"""
        from tests.utils.archives import import_archive

        for archive in ['django.aiida', 'sqlalchemy.aiida']:
            # Clean the database
            self.refurbish_db()

            # Import the needed data
            import_archive(archive, filepath='export/compare')

            # The expected metadata
            comp1_metadata = {'workdir': '/tmp/aiida'}

            # Check that we got the correct metadata
            # Make sure to exclude the default computer
            builder = orm.QueryBuilder()
            builder.append(
                orm.Computer, project=['metadata'], tag='comp', filters={'label': {
                    '!==': self.computer.label
                }}
            )
            self.assertEqual(builder.count(), 1, 'Expected only one computer')

            res = builder.dict()[0]

            self.assertEqual(res['comp']['metadata'], comp1_metadata)
