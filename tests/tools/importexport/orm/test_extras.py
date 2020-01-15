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
import shutil
import tempfile

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.tools.importexport import import_data, export


class TestExtras(AiidaTestCase):
    """Test ex-/import cases related to Extras"""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """Only run to prepare an export file"""
        super().setUpClass()

        data = orm.Data()
        data.label = 'my_test_data_node'
        data.store()
        data.set_extra_many({'b': 2, 'c': 3})
        cls.tmp_folder = tempfile.mkdtemp()
        cls.export_file = os.path.join(cls.tmp_folder, 'export.aiida')
        export([data], outfile=cls.export_file, silent=True)

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        """Remove tmp_folder"""
        super().tearDownClass()

        shutil.rmtree(cls.tmp_folder, ignore_errors=True)

    def setUp(self):
        """This function runs before every test execution"""
        self.clean_db()
        self.insert_data()

    def import_extras(self, mode_new='import'):
        """Import an aiida database"""
        import_data(self.export_file, silent=True, extras_mode_new=mode_new)

        builder = orm.QueryBuilder().append(orm.Data, filters={'label': 'my_test_data_node'})

        self.assertEqual(builder.count(), 1)
        self.imported_node = builder.all()[0][0]

    def modify_extras(self, mode_existing):
        """Import the same aiida database again"""
        self.imported_node.set_extra('a', 1)
        self.imported_node.set_extra('b', 1000)
        self.imported_node.delete_extra('c')

        import_data(self.export_file, silent=True, extras_mode_existing=mode_existing)

        # Query again the database
        builder = orm.QueryBuilder().append(orm.Data, filters={'label': 'my_test_data_node'})
        self.assertEqual(builder.count(), 1)
        return builder.all()[0][0]

    def tearDown(self):
        pass

    def test_import_of_extras(self):
        """Check if extras are properly imported"""
        self.import_extras()
        self.assertEqual(self.imported_node.get_extra('b'), 2)
        self.assertEqual(self.imported_node.get_extra('c'), 3)

    def test_absence_of_extras(self):
        """Check whether extras are not imported if the mode is set to 'none'"""
        self.import_extras(mode_new='none')
        with self.assertRaises(AttributeError):
            # the extra 'b' should not exist
            self.imported_node.get_extra('b')
        with self.assertRaises(AttributeError):
            # the extra 'c' should not exist
            self.imported_node.get_extra('c')

    def test_extras_import_mode_keep_existing(self):
        """Check if old extras are not modified in case of name collision"""
        self.import_extras()
        imported_node = self.modify_extras(mode_existing='kcl')

        # Check that extras are imported correctly
        self.assertEqual(imported_node.get_extra('a'), 1)
        self.assertEqual(imported_node.get_extra('b'), 1000)
        self.assertEqual(imported_node.get_extra('c'), 3)

    def test_extras_import_mode_update_existing(self):
        """Check if old extras are modified in case of name collision"""
        self.import_extras()
        imported_node = self.modify_extras(mode_existing='kcu')

        # Check that extras are imported correctly
        self.assertEqual(imported_node.get_extra('a'), 1)
        self.assertEqual(imported_node.get_extra('b'), 2)
        self.assertEqual(imported_node.get_extra('c'), 3)

    def test_extras_import_mode_mirror(self):
        """Check if old extras are fully overwritten by the imported ones"""
        self.import_extras()
        imported_node = self.modify_extras(mode_existing='ncu')

        # Check that extras are imported correctly
        with self.assertRaises(AttributeError):  # the extra
            # 'a' should not exist, as the extras were fully mirrored with respect to
            # the imported node
            imported_node.get_extra('a')
        self.assertEqual(imported_node.get_extra('b'), 2)
        self.assertEqual(imported_node.get_extra('c'), 3)

    def test_extras_import_mode_none(self):
        """Check if old extras are fully overwritten by the imported ones"""
        self.import_extras()
        imported_node = self.modify_extras(mode_existing='knl')

        # Check if extras are imported correctly
        self.assertEqual(imported_node.get_extra('b'), 1000)
        self.assertEqual(imported_node.get_extra('a'), 1)
        with self.assertRaises(AttributeError):  # the extra
            # 'c' should not exist, as the extras were keept untached
            imported_node.get_extra('c')

    def test_extras_import_mode_strange(self):
        """Check a mode that is probably does not make much sense but is still available"""
        self.import_extras()
        imported_node = self.modify_extras(mode_existing='kcd')

        # Check if extras are imported correctly
        self.assertEqual(imported_node.get_extra('a'), 1)
        self.assertEqual(imported_node.get_extra('c'), 3)
        with self.assertRaises(AttributeError):  # the extra
            # 'b' should not exist, as the collided extras are deleted
            imported_node.get_extra('b')

    def test_extras_import_mode_correct(self):
        """Test all possible import modes except 'ask' """
        self.import_extras()
        for mode1 in ['k', 'n']:  # keep or not keep old extras
            for mode2 in ['n', 'c']:  # create or not create new extras
                for mode3 in ['l', 'u', 'd']:  # leave old, update or delete collided extras
                    mode = mode1 + mode2 + mode3
                    import_data(self.export_file, silent=True, extras_mode_existing=mode)

    def test_extras_import_mode_wrong(self):
        """Check a mode that is wrong"""
        from aiida.tools.importexport.common.exceptions import ImportValidationError

        self.import_extras()
        with self.assertRaises(ImportValidationError):
            import_data(self.export_file, silent=True, extras_mode_existing='xnd')  # first letter is wrong
        with self.assertRaises(ImportValidationError):
            import_data(self.export_file, silent=True, extras_mode_existing='nxd')  # second letter is wrong
        with self.assertRaises(ImportValidationError):
            import_data(self.export_file, silent=True, extras_mode_existing='nnx')  # third letter is wrong
        with self.assertRaises(ImportValidationError):
            import_data(self.export_file, silent=True, extras_mode_existing='n')  # too short
        with self.assertRaises(ImportValidationError):
            import_data(self.export_file, silent=True, extras_mode_existing='nndnn')  # too long
        with self.assertRaises(ImportValidationError):
            import_data(self.export_file, silent=True, extras_mode_existing=5)  # wrong type
