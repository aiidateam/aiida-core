# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Tests for specific subclasses of Data
"""
from aiida.orm import load_node
from aiida.common.exceptions import ModificationNotAllowed
from aiida.backends.testbase import AiidaTestCase
import unittest



def simplify(string):
    """
    Takes a string, strips spaces in each line and returns it
    Useful to compare strings when different versions of a code give
    different spaces.
    """
    return "\n".join(s.strip() for s in string.split())


class TestCalcStatus(AiidaTestCase):
    """
    Test the functionality of calculation states.
    """

    def test_state(self):
        from aiida.orm import JobCalculation
        from aiida.common.datastructures import calc_states

        # Use the AiidaTestCase test computer

        c = JobCalculation(computer=self.computer,
                           resources={
                               'num_machines': 1,
                               'num_mpiprocs_per_machine': 1}
                           )
        # Should be in the NEW state before storing
        self.assertEquals(c.get_state(), calc_states.NEW)

        with self.assertRaises(ModificationNotAllowed):
            c._set_state(calc_states.TOSUBMIT)

        c.store()
        # Should be in the NEW state right after storing
        self.assertEquals(c.get_state(), calc_states.NEW)

        # Set a different state and check
        c._set_state(calc_states.TOSUBMIT)
        self.assertEquals(c.get_state(), calc_states.TOSUBMIT)

        # Set a different state and check
        c._set_state(calc_states.SUBMITTING)
        self.assertEquals(c.get_state(), calc_states.SUBMITTING)

        # Try to reset a state and check that the proper exception is raised
        with self.assertRaises(ModificationNotAllowed):
            c._set_state(calc_states.SUBMITTING)

        # Set a different state and check
        c._set_state(calc_states.FINISHED)
        self.assertEquals(c.get_state(), calc_states.FINISHED)

        # Try to set a previous state (that is, going backward from
        # FINISHED to WITHSCHEDULER, for instance)
        # and check that this is not allowed
        with self.assertRaises(ModificationNotAllowed):
            c._set_state(calc_states.WITHSCHEDULER)


class TestSinglefileData(AiidaTestCase):
    """
    Test the SinglefileData class.
    """

    def test_reload_singlefiledata(self):
        import os
        import tempfile

        from aiida.orm.data.singlefile import SinglefileData

        file_content = 'some text ABCDE'
        with tempfile.NamedTemporaryFile() as f:
            filename = f.name
            basename = os.path.split(filename)[1]
            f.write(file_content)
            f.flush()
            a = SinglefileData(file=filename)

        the_uuid = a.uuid

        self.assertEquals(a.get_folder_list(), [basename])

        with open(a.get_abs_path(basename)) as f:
            self.assertEquals(f.read(), file_content)

        a.store()

        with open(a.get_abs_path(basename)) as f:
            self.assertEquals(f.read(), file_content)
        self.assertEquals(a.get_folder_list(), [basename])

        b = load_node(the_uuid)

        # I check the retrieved object
        self.assertTrue(isinstance(b, SinglefileData))
        self.assertEquals(b.get_folder_list(), [basename])
        with open(b.get_abs_path(basename)) as f:
            self.assertEquals(f.read(), file_content)


class TestCifData(AiidaTestCase):
    """
    Tests for CifData class.
    """
    from aiida.orm.data.cif import has_pycifrw
    from aiida.orm.data.structure import has_ase, has_pymatgen, has_spglib, \
        get_pymatgen_version
    from distutils.version import StrictVersion

    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_reload_cifdata(self):
        import os
        import tempfile

        from aiida.orm.data.cif import CifData

        file_content = "data_test _cell_length_a 10(1)"
        with tempfile.NamedTemporaryFile() as f:
            filename = f.name
            basename = os.path.split(filename)[1]
            f.write(file_content)
            f.flush()
            a = CifData(file=filename,
                        source={'version': '1234',
                                'db_name': 'COD',
                                'id': '0000001'})

        # Key 'db_kind' is not allowed in source description:
        with self.assertRaises(KeyError):
            a.source = {'db_kind': 'small molecule'}

        the_uuid = a.uuid

        self.assertEquals(a.get_folder_list(), [basename])

        with open(a.get_abs_path(basename)) as f:
            self.assertEquals(f.read(), file_content)

        a.store()

        self.assertEquals(a.source, {
            'db_name': 'COD',
            'id': '0000001',
            'version': '1234',
        })

        with open(a.get_abs_path(basename)) as f:
            self.assertEquals(f.read(), file_content)
        self.assertEquals(a.get_folder_list(), [basename])

        b = load_node(the_uuid)

        # I check the retrieved object
        self.assertTrue(isinstance(b, CifData))
        self.assertEquals(b.get_folder_list(), [basename])
        with open(b.get_abs_path(basename)) as f:
            self.assertEquals(f.read(), file_content)

        # Checking the get_or_create() method:
        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content)
            f.flush()
            c, created = CifData.get_or_create(f.name, store_cif=False)

        self.assertTrue(isinstance(c, CifData))
        self.assertTrue(not created)

        with open(c.get_file_abs_path()) as f:
            self.assertEquals(f.read(), file_content)

        other_content = "data_test _cell_length_b 10(1)"
        with tempfile.NamedTemporaryFile() as f:
            f.write(other_content)
            f.flush()
            c, created = CifData.get_or_create(f.name, store_cif=False)

        self.assertTrue(isinstance(c, CifData))
        self.assertTrue(created)

        with open(c.get_file_abs_path()) as f:
            self.assertEquals(f.read(), other_content)

    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_parse_cifdata(self):
        import tempfile

        from aiida.orm.data.cif import CifData

        file_content = "data_test _cell_length_a 10(1)"
        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content)
            f.flush()
            a = CifData(file=f.name)

        self.assertEquals(a.values.keys(), ['test'])

    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_change_cifdata_file(self):
        import tempfile

        from aiida.orm.data.cif import CifData

        file_content_1 = "data_test _cell_length_a 10(1)"
        file_content_2 = "data_test _cell_length_a 11(1)"
        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content_1)
            f.flush()
            a = CifData(file=f.name)

        self.assertEquals(a.values['test']['_cell_length_a'], '10(1)')

        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content_2)
            f.flush()
            a.set_file(f.name)

        self.assertEquals(a.values['test']['_cell_length_a'], '11(1)')

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_get_aiida_structure(self):
        import tempfile

        from aiida.orm.data.cif import CifData

        with tempfile.NamedTemporaryFile() as f:
            f.write('''
data_test
_cell_length_a    10
_cell_length_b    10
_cell_length_c    10
_cell_angle_alpha 90
_cell_angle_beta  90
_cell_angle_gamma 90
loop_
_atom_site_label
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
C 0 0 0
O 0.5 0.5 0.5
            ''')
            f.flush()
            a = CifData(file=f.name)

        with self.assertRaises(ValueError):
            a._get_aiida_structure(converter='none')

        c = a._get_aiida_structure()

        self.assertEquals(c.get_kind_names(), ['C', 'O'])

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_ase_primitive_and_conventional_cells_ase(self):
        """
        Checking the number of atoms per primitive/conventional cell
        returned by ASE ase.io.read() method. Test input is
        adapted from http://www.crystallography.net/cod/9012064.cif@120115
        """
        import tempfile
        import ase

        from aiida.orm.data.cif import CifData

        with tempfile.NamedTemporaryFile() as f:
            f.write('''
                data_9012064
                _space_group_IT_number           166
                _symmetry_space_group_name_H-M   'R -3 m :H'
                _cell_angle_alpha                90
                _cell_angle_beta                 90
                _cell_angle_gamma                120
                _cell_length_a                   4.395
                _cell_length_b                   4.395
                _cell_length_c                   30.440
                _cod_database_code               9012064
                loop_
                _atom_site_label
                _atom_site_fract_x
                _atom_site_fract_y
                _atom_site_fract_z
                _atom_site_U_iso_or_equiv
                Bi 0.00000 0.00000 0.40046 0.02330
                Te1 0.00000 0.00000 0.00000 0.01748
                Te2 0.00000 0.00000 0.79030 0.01912
            ''')
            f.flush()
            c = CifData(file=f.name)

        ase = c._get_aiida_structure(converter='ase',
                                     primitive_cell=False).get_ase()
        self.assertEquals(ase.get_number_of_atoms(), 15)

        ase = c._get_aiida_structure(converter='ase').get_ase()
        self.assertEquals(ase.get_number_of_atoms(), 15)

        ase = c._get_aiida_structure(converter='ase',
                                     primitive_cell=True, subtrans_included=False).get_ase()
        self.assertEquals(ase.get_number_of_atoms(), 5)

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    @unittest.skipIf(not has_pymatgen(), "Unable to import pymatgen")
    @unittest.skipIf(has_pymatgen() and
                     StrictVersion(get_pymatgen_version()) !=
                     StrictVersion('4.5.3'),
                     "Mismatch in the version of pymatgen (expected 4.5.3)")
    def test_ase_primitive_and_conventional_cells_pymatgen(self):
        """
        Checking the number of atoms per primitive/conventional cell
        returned by ASE ase.io.read() method. Test input is
        adapted from http://www.crystallography.net/cod/9012064.cif@120115
        """
        import tempfile

        from aiida.orm.data.cif import CifData

        with tempfile.NamedTemporaryFile() as f:
            f.write('''
data_9012064
_space_group_IT_number           166
_symmetry_space_group_name_H-M   'R -3 m :H'
_cell_angle_alpha                90
_cell_angle_beta                 90
_cell_angle_gamma                120
_cell_length_a                   4.395
_cell_length_b                   4.395
_cell_length_c                   30.440
_cod_database_code               9012064
loop_
_atom_site_label
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_site_U_iso_or_equiv
Bi 0.00000 0.00000 0.40046 0.02330
Te1 0.00000 0.00000 0.00000 0.01748
Te2 0.00000 0.00000 0.79030 0.01912
            ''')
            f.flush()
            c = CifData(file=f.name)

        ase = c._get_aiida_structure(converter='pymatgen',
                                     primitive_cell=False).get_ase()
        self.assertEquals(ase.get_number_of_atoms(), 15)

        ase = c._get_aiida_structure(converter='pymatgen').get_ase()
        self.assertEquals(ase.get_number_of_atoms(), 15)

        ase = c._get_aiida_structure(converter='pymatgen',
                                     primitive_cell=True).get_ase()
        self.assertEquals(ase.get_number_of_atoms(), 5)

    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_pycifrw_from_datablocks(self):
        """
        Tests CifData.pycifrw_from_cif()
        """
        from aiida.orm.data.cif import pycifrw_from_cif
        import re

        datablocks = [
            {
                '_atom_site_label': ['A', 'B', 'C'],
                '_atom_site_occupancy': [1.0, 0.5, 0.5],
                '_publ_section_title': 'Test CIF'
            }
        ]
        lines = pycifrw_from_cif(datablocks).WriteOut().split('\n')
        non_comments = []
        for line in lines:
            if not re.search('^#', line):
                non_comments.append(line)
        self.assertEquals(simplify("\n".join(non_comments)),
                          simplify('''
data_0
loop_
  _atom_site_label
   A
   B
   C

loop_
  _atom_site_occupancy
   1.0
   0.5
   0.5

_publ_section_title                     'Test CIF'
'''))

        loops = {'_atom_site': ['_atom_site_label', '_atom_site_occupancy']}
        lines = pycifrw_from_cif(datablocks, loops).WriteOut().split('\n')
        non_comments = []
        for line in lines:
            if not re.search('^#', line):
                non_comments.append(line)
        self.assertEquals(simplify("\n".join(non_comments)),
                          simplify('''
data_0
loop_
  _atom_site_label
  _atom_site_occupancy
   A  1.0
   B  0.5
   C  0.5

_publ_section_title                     'Test CIF'
'''))

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_cif_roundtrip(self):
        import tempfile
        from aiida.orm.data.cif import CifData

        with tempfile.NamedTemporaryFile() as f:
            f.write('''
                data_test
                _cell_length_a    10
                _cell_length_b    10
                _cell_length_c    10
                _cell_angle_alpha 90
                _cell_angle_beta  90
                _cell_angle_gamma 90
                loop_
                _atom_site_label
                _atom_site_fract_x
                _atom_site_fract_y
                _atom_site_fract_z
                C 0 0 0
                O 0.5 0.5 0.5
                _cod_database_code 0000001
                _[local]_flags     ''
            ''')
            f.flush()
            a = CifData(file=f.name)

        b = CifData(values=a.values)
        c = CifData(values=b.values)
        self.assertEquals(b._prepare_cif(), c._prepare_cif())

        b = CifData(ase=a.ase)
        c = CifData(ase=b.ase)
        self.assertEquals(b._prepare_cif(), c._prepare_cif())

    def test_symop_string_from_symop_matrix_tr(self):
        from aiida.orm.data.cif import symop_string_from_symop_matrix_tr

        self.assertEquals(
            symop_string_from_symop_matrix_tr(
                [[1, 0, 0], [0, 1, 0], [0, 0, 1]]), "x,y,z")

        self.assertEquals(
            symop_string_from_symop_matrix_tr(
                [[1, 0, 0], [0, -1, 0], [0, 1, 1]]), "x,-y,y+z")

        self.assertEquals(
            symop_string_from_symop_matrix_tr(
                [[-1, 0, 0], [0, 1, 0], [0, 0, 1]], [1, -1, 0]), "-x+1,y-1,z")

    def test_parse_formula(self):
        from aiida.orm.data.cif import parse_formula

        self.assertEqual(parse_formula("C H"),
                         {'C': 1, 'H': 1})

        self.assertEqual(parse_formula("C5 H1"),
                         {'C': 5, 'H': 1})

        self.assertEqual(parse_formula("Ca5 Ho"),
                         {'Ca': 5, 'Ho': 1})

        self.assertEqual(parse_formula("H0.5 O"),
                         {'H': 0.5, 'O': 1})

        self.assertEqual(parse_formula("C0 O0"),
                         {'C': 0, 'O': 0})

        # Invalid literal for float()
        with self.assertRaises(ValueError):
            parse_formula("H0.5.2 O")

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_attached_hydrogens(self):
        import tempfile
        from aiida.orm.data.cif import CifData

        with tempfile.NamedTemporaryFile() as f:
            f.write('''
                data_test
                _cell_length_a    10
                _cell_length_b    10
                _cell_length_c    10
                _cell_angle_alpha 90
                _cell_angle_beta  90
                _cell_angle_gamma 90
                loop_
                _atom_site_label
                _atom_site_fract_x
                _atom_site_fract_y
                _atom_site_fract_z
                _atom_site_attached_hydrogens
                C 0 0 0 ?
                O 0.5 0.5 0.5 .
                H 0.75 0.75 0.75 0
            ''')
            f.flush()
            a = CifData(file=f.name)

        self.assertEqual(a.has_attached_hydrogens(), False)

        with tempfile.NamedTemporaryFile() as f:
            f.write('''
                data_test
                _cell_length_a    10
                _cell_length_b    10
                _cell_length_c    10
                _cell_angle_alpha 90
                _cell_angle_beta  90
                _cell_angle_gamma 90
                loop_
                _atom_site_label
                _atom_site_fract_x
                _atom_site_fract_y
                _atom_site_fract_z
                _atom_site_attached_hydrogens
                C 0 0 0 ?
                O 0.5 0.5 0.5 1
                H 0.75 0.75 0.75 0
            ''')
            f.flush()
            a = CifData(file=f.name)

        self.assertEqual(a.has_attached_hydrogens(), True)

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    @unittest.skipIf(not has_spglib(), "Unable to import spglib")
    def test_refine(self):
        """
        Test case for refinement (space group determination) for a
        CifData object.
        """
        from aiida.orm.data.cif import CifData, refine_inline
        import tempfile

        with tempfile.NamedTemporaryFile() as f:
            f.write('''
                data_test
                _cell_length_a    10
                _cell_length_b    10
                _cell_length_c    10
                _cell_angle_alpha 90
                _cell_angle_beta  90
                _cell_angle_gamma 90
                loop_
                _atom_site_label
                _atom_site_fract_x
                _atom_site_fract_y
                _atom_site_fract_z
                C 0.5 0.5 0.5
                O 0.25 0.5 0.5
                O 0.75 0.5 0.5
            ''')
            f.flush()
            a = CifData(file=f.name)

        ret_dict = refine_inline(a)
        b = ret_dict['cif']
        self.assertEqual(b.values.keys(), ['test'])
        self.assertEqual(b.values['test']['_chemical_formula_sum'], 'C O2')
        self.assertEqual(b.values['test']['_symmetry_equiv_pos_as_xyz'], [
            'x,y,z',
            '-x,-y,-z',
            '-y,x,z',
            'y,-x,-z',
            '-x,-y,z',
            'x,y,-z',
            'y,-x,z',
            '-y,x,-z',
            'x,-y,-z',
            '-x,y,z',
            '-y,-x,-z',
            'y,x,z',
            '-x,y,-z',
            'x,-y,z',
            'y,x,-z',
            '-y,-x,z'])

        with tempfile.NamedTemporaryFile() as f:
            f.write('''
                data_a
                data_b
            ''')
            f.flush()
            c = CifData(file=f.name)

        with self.assertRaises(ValueError):
            ret_dict = refine_inline(c)

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    @unittest.skipIf(not has_spglib(), "Unable to import spglib")
    def test_parse_formula(self):
        from aiida.orm.data.cif import parse_formula

        self.assertEqual(parse_formula("C H"),
                         {'C': 1, 'H': 1})

        self.assertEqual(parse_formula("C5 H1"),
                         {'C': 5, 'H': 1})

        self.assertEqual(parse_formula("Ca5 Ho"),
                         {'Ca': 5, 'Ho': 1})

        self.assertEqual(parse_formula("H0.5 O"),
                         {'H': 0.5, 'O': 1})

        # Invalid literal for float()
        with self.assertRaises(ValueError):
            parse_formula("H0.5.2 O")


class TestKindValidSymbols(AiidaTestCase):
    """
    Tests the symbol validation of the
    aiida.orm.data.structure.Kind class.
    """

    def test_bad_symbol(self):
        """
        Should not accept a non-existing symbol.
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols='Hxx')

    def test_empty_list_symbols(self):
        """
        Should not accept an empty list
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols=[])

    def test_valid_list(self):
        """
        Should not raise any error.
        """
        from aiida.orm.data.structure import Kind

        _ = Kind(symbols=['H', 'He'], weights=[0.5, 0.5])


class TestSiteValidWeights(AiidaTestCase):
    """
    Tests valid weight lists.
    """

    def test_isnot_list(self):
        """
        Should not accept a non-list, non-number weight
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols='Ba', weights='aaa')

    def test_empty_list_weights(self):
        """
        Should not accept an empty list
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols='Ba', weights=[])

    def test_symbol_weight_mismatch(self):
        """
        Should not accept a size mismatch of the symbols and weights
        list.
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols=['Ba', 'C'], weights=[1.])

        with self.assertRaises(ValueError):
            _ = Kind(symbols=['Ba'], weights=[0.1, 0.2])

    def test_negative_value(self):
        """
        Should not accept a negative weight
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols=['Ba', 'C'], weights=[-0.1, 0.3])

    def test_sum_greater_one(self):
        """
        Should not accept a sum of weights larger than one
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols=['Ba', 'C'],
                     weights=[0.5, 0.6])

    def test_sum_one_weights(self):
        """
        Should accept a sum equal to one
        """
        from aiida.orm.data.structure import Kind

        _ = Kind(symbols=['Ba', 'C'],
                 weights=[1. / 3., 2. / 3.])

    def test_sum_less_one_weights(self):
        """
        Should accept a sum equal less than one
        """
        from aiida.orm.data.structure import Kind

        _ = Kind(symbols=['Ba', 'C'],
                 weights=[1. / 3., 1. / 3.])

    def test_none(self):
        """
        Should accept None.
        """
        from aiida.orm.data.structure import Kind

        _ = Kind(symbols='Ba', weights=None)


class TestKindTestGeneral(AiidaTestCase):
    """
    Tests the creation of Kind objects and their methods.
    """

    def test_sum_one_general(self):
        """
        Should accept a sum equal to one
        """
        from aiida.orm.data.structure import Kind

        a = Kind(symbols=['Ba', 'C'],
                 weights=[1. / 3., 2. / 3.])
        self.assertTrue(a.is_alloy())
        self.assertFalse(a.has_vacancies())

    def test_sum_less_one_general(self):
        """
        Should accept a sum equal less than one
        """
        from aiida.orm.data.structure import Kind

        a = Kind(symbols=['Ba', 'C'],
                 weights=[1. / 3., 1. / 3.])
        self.assertTrue(a.is_alloy())
        self.assertTrue(a.has_vacancies())

    def test_no_position(self):
        """
        Should not accept a 'positions' parameter
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(position=[0., 0., 0.], symbols=['Ba'],
                     weights=[1.])

    def test_simple(self):
        """
        Should recognize a simple element.
        """
        from aiida.orm.data.structure import Kind

        a = Kind(symbols='Ba')
        self.assertFalse(a.is_alloy())
        self.assertFalse(a.has_vacancies())

        b = Kind(symbols='Ba', weights=1.)
        self.assertFalse(b.is_alloy())
        self.assertFalse(b.has_vacancies())

        c = Kind(symbols='Ba', weights=None)
        self.assertFalse(c.is_alloy())
        self.assertFalse(c.has_vacancies())

    def test_automatic_name(self):
        """
        Check the automatic name generator.
        """
        from aiida.orm.data.structure import Kind

        a = Kind(symbols='Ba')
        self.assertEqual(a.name, 'Ba')

        a = Kind(symbols=('Si', 'Ge'), weights=(1. / 3., 2. / 3.))
        self.assertEqual(a.name, 'GeSi')

        a = Kind(symbols=('Si', 'Ge'), weights=(0.4, 0.5))
        self.assertEqual(a.name, 'GeSiX')

        # Manually setting the name of the species
        a.name = 'newstring'
        self.assertEqual(a.name, 'newstring')


class TestKindTestMasses(AiidaTestCase):
    """
    Tests the management of masses during the creation of Kind objects.
    """

    def test_auto_mass_one(self):
        """
        mass for elements with sum one
        """
        from aiida.orm.data.structure import Kind, _atomic_masses

        a = Kind(symbols=['Ba', 'C'],
                 weights=[1. / 3., 2. / 3.])
        self.assertAlmostEqual(a.mass,
                               (_atomic_masses['Ba'] +
                                2. * _atomic_masses['C']) / 3.)

    def test_sum_less_one_masses(self):
        """
        mass for elements with sum less than one
        """
        from aiida.orm.data.structure import Kind, _atomic_masses

        a = Kind(symbols=['Ba', 'C'],
                 weights=[1. / 3., 1. / 3.])
        self.assertAlmostEqual(a.mass,
                               (_atomic_masses['Ba'] +
                                _atomic_masses['C']) / 2.)

    def test_sum_less_one_singleelem(self):
        """
        mass for a single element
        """
        from aiida.orm.data.structure import Kind, _atomic_masses

        a = Kind(symbols=['Ba'])
        self.assertAlmostEqual(a.mass,
                               _atomic_masses['Ba'])

    def test_manual_mass(self):
        """
        mass set manually
        """
        from aiida.orm.data.structure import Kind

        a = Kind(symbols=['Ba', 'C'],
                 weights=[1. / 3., 1. / 3.],
                 mass=1000.)
        self.assertAlmostEqual(a.mass, 1000.)


class TestStructureDataInit(AiidaTestCase):
    """
    Tests the creation of StructureData objects (cell and pbc).
    """

    def test_cell_wrong_size_1(self):
        """
        Wrong cell size (not 3x3)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            _ = StructureData(cell=((1., 2., 3.),))

    def test_cell_wrong_size_2(self):
        """
        Wrong cell size (not 3x3)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            _ = StructureData(cell=((1., 0., 0.), (0., 0., 3.), (0., 3.)))

    def test_cell_zero_vector(self):
        """
        Wrong cell (one vector has zero length)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            _ = StructureData(cell=((0., 0., 0.), (0., 1., 0.), (0., 0., 1.)))

    def test_cell_zero_volume(self):
        """
        Wrong cell (volume is zero)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            _ = StructureData(cell=((1., 0., 0.), (0., 1., 0.), (1., 1., 0.)))

    def test_cell_ok_init(self):
        """
        Correct cell
        """
        from aiida.orm.data.structure import StructureData

        cell = ((1., 0., 0.), (0., 2., 0.), (0., 0., 3.))
        a = StructureData(cell=cell)
        out_cell = a.cell

        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(cell[i][j], out_cell[i][j])

    def test_volume(self):
        """
        Check the volume calculation
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((1., 0., 0.), (0., 2., 0.), (0., 0., 3.)))
        self.assertAlmostEqual(a.get_cell_volume(), 6.)

    def test_wrong_pbc_1(self):
        """
        Wrong pbc parameter (not bool or iterable)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            cell = ((1., 0., 0.), (0., 2., 0.), (0., 0., 3.))
            _ = StructureData(cell=cell, pbc=1)

    def test_wrong_pbc_2(self):
        """
        Wrong pbc parameter (iterable but with wrong len)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            cell = ((1., 0., 0.), (0., 2., 0.), (0., 0., 3.))
            _ = StructureData(cell=cell, pbc=[True, True])

    def test_wrong_pbc_3(self):
        """
        Wrong pbc parameter (iterable but with wrong len)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            cell = ((1., 0., 0.), (0., 2., 0.), (0., 0., 3.))
            _ = StructureData(cell=cell, pbc=[])

    def test_ok_pbc_1(self):
        """
        Single pbc value
        """
        from aiida.orm.data.structure import StructureData

        cell = ((1., 0., 0.), (0., 2., 0.), (0., 0., 3.))
        a = StructureData(cell=cell, pbc=True)
        self.assertEquals(a.pbc, tuple([True, True, True]))

        a = StructureData(cell=cell, pbc=False)
        self.assertEquals(a.pbc, tuple([False, False, False]))

    def test_ok_pbc_2(self):
        """
        One-element list
        """
        from aiida.orm.data.structure import StructureData

        cell = ((1., 0., 0.), (0., 2., 0.), (0., 0., 3.))
        a = StructureData(cell=cell, pbc=[True])
        self.assertEqual(a.pbc, tuple([True, True, True]))

        a = StructureData(cell=cell, pbc=[False])
        self.assertEqual(a.pbc, tuple([False, False, False]))

    def test_ok_pbc_3(self):
        """
        Three-element list
        """
        from aiida.orm.data.structure import StructureData

        cell = ((1., 0., 0.), (0., 2., 0.), (0., 0., 3.))
        a = StructureData(cell=cell, pbc=[True, False, True])
        self.assertEqual(a.pbc, tuple([True, False, True]))


class TestStructureData(AiidaTestCase):
    """
    Tests the creation of StructureData objects (cell and pbc).
    """
    from aiida.orm.data.structure import has_ase, has_spglib

    def test_cell_ok_and_atoms(self):
        """
        Test the creation of a cell and the appending of atoms
        """
        from aiida.orm.data.structure import StructureData

        cell = [[2., 0., 0.], [0., 2., 0.], [0., 0., 2.]]

        a = StructureData(cell=cell)
        out_cell = a.cell
        self.assertAlmostEquals(cell, out_cell)

        a.append_atom(position=(0., 0., 0.), symbols=['Ba'])
        a.append_atom(position=(1., 1., 1.), symbols=['Ti'])
        a.append_atom(position=(1.2, 1.4, 1.6), symbols=['Ti'])
        self.assertFalse(a.is_alloy())
        self.assertFalse(a.has_vacancies())
        # There should be only two kinds! (two atoms of kind Ti should
        # belong to the same kind)
        self.assertEquals(len(a.kinds), 2)

        a.append_atom(position=(0.5, 1., 1.5), symbols=['O', 'C'],
                      weights=[0.5, 0.5])
        self.assertTrue(a.is_alloy())
        self.assertFalse(a.has_vacancies())

        a.append_atom(position=(0.5, 1., 1.5), symbols=['O'], weights=[0.5])
        self.assertTrue(a.is_alloy())
        self.assertTrue(a.has_vacancies())

        a.clear_kinds()
        a.append_atom(position=(0.5, 1., 1.5), symbols=['O'], weights=[0.5])
        self.assertFalse(a.is_alloy())
        self.assertTrue(a.has_vacancies())

    def test_kind_1(self):
        """
        Test the management of kinds (automatic detection of kind of
        simple atoms).
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2., 0., 0.), (0., 2., 0.), (0., 0., 2.)))

        a.append_atom(position=(0., 0., 0.), symbols=['Ba'])
        a.append_atom(position=(0.5, 0.5, 0.5), symbols=['Ba'])
        a.append_atom(position=(1., 1., 1.), symbols=['Ti'])

        self.assertEqual(len(a.kinds), 2)  # I should only have two types
        # I check for the default names of kinds
        self.assertEqual(set(k.name for k in a.kinds),
                         set(('Ba', 'Ti')))

    def test_kind_2(self):
        """
        Test the management of kinds (manual specification of kind name).
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2., 0., 0.), (0., 2., 0.), (0., 0., 2.)))

        a.append_atom(position=(0., 0., 0.), symbols=['Ba'], name='Ba1')
        a.append_atom(position=(0.5, 0.5, 0.5), symbols=['Ba'], name='Ba2')
        a.append_atom(position=(1., 1., 1.), symbols=['Ti'])

        kind_list = a.kinds
        self.assertEqual(len(kind_list), 3)  # I should have now three kinds
        self.assertEqual(set(k.name for k in kind_list),
                         set(('Ba1', 'Ba2', 'Ti')))

    def test_kind_3(self):
        """
        Test the management of kinds (adding an atom with different mass).
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2., 0., 0.), (0., 2., 0.), (0., 0., 2.)))

        a.append_atom(position=(0., 0., 0.), symbols=['Ba'], mass=100.)
        with self.assertRaises(ValueError):
            # Shouldn't allow, I am adding two sites with the same name 'Ba'
            a.append_atom(position=(0.5, 0.5, 0.5), symbols=['Ba'],
                          mass=101., name='Ba')

            # now it should work because I am using a different kind name
        a.append_atom(position=(0.5, 0.5, 0.5),
                      symbols=['Ba'], mass=101., name='Ba2')

        a.append_atom(position=(1., 1., 1.), symbols=['Ti'])

        self.assertEqual(len(a.kinds), 3)  # I should have now three types
        self.assertEqual(len(a.sites), 3)  # and 3 sites
        self.assertEqual(set(k.name for k in a.kinds), set(('Ba', 'Ba2', 'Ti')))

    def test_kind_4(self):
        """
        Test the management of kind (adding an atom with different symbols
        or weights).
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2., 0., 0.), (0., 2., 0.), (0., 0., 2.)))

        a.append_atom(position=(0., 0., 0.), symbols=['Ba', 'Ti'],
                      weights=(1., 0.), name='mytype')

        with self.assertRaises(ValueError):
            # Shouldn't allow, different weights
            a.append_atom(position=(0.5, 0.5, 0.5), symbols=['Ba', 'Ti'],
                          weights=(0.9, 0.1), name='mytype')

        with self.assertRaises(ValueError):
            # Shouldn't allow, different weights (with vacancy)
            a.append_atom(position=(0.5, 0.5, 0.5), symbols=['Ba', 'Ti'],
                          weights=(0.8, 0.1), name='mytype')

        with self.assertRaises(ValueError):
            # Shouldn't allow, different symbols list
            a.append_atom(position=(0.5, 0.5, 0.5), symbols=['Ba'],
                          name='mytype')

        with self.assertRaises(ValueError):
            # Shouldn't allow, different symbols list
            a.append_atom(position=(0.5, 0.5, 0.5), symbols=['Si', 'Ti'],
                          weights=(1., 0.), name='mytype')

            # should allow because every property is identical
        a.append_atom(position=(0., 0., 0.), symbols=['Ba', 'Ti'],
                      weights=(1., 0.), name='mytype')

        self.assertEquals(len(a.kinds), 1)

    def test_kind_5(self):
        """
        Test the management of kinds (automatic creation of new kind
        if name is not specified and properties are different).
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2., 0., 0.), (0., 2., 0.), (0., 0., 2.)))

        a.append_atom(position=(0., 0., 0.), symbols='Ba', mass=100.)
        a.append_atom(position=(0., 0., 0.), symbols='Ti')
        # The name does not exist
        a.append_atom(position=(0., 0., 0.), symbols='Ti', name='Ti2')
        # The name already exists, but the properties are identical => OK
        a.append_atom(position=(1., 1., 1.), symbols='Ti', name='Ti2')
        # The name already exists, but the properties are different!
        with self.assertRaises(ValueError):
            a.append_atom(position=(1., 1., 1.), symbols='Ti', mass=100.,
                          name='Ti2')
        # Should not complain, should create a new type
        a.append_atom(position=(0., 0., 0.), symbols='Ba', mass=150.)

        # There should be 4 kinds, the automatic name for the last one
        # should be Ba1
        self.assertEquals([k.name for k in a.kinds],
                          ['Ba', 'Ti', 'Ti2', 'Ba1'])
        self.assertEquals(len(a.sites), 5)

    def test_kind_5_bis(self):
        """
        Test the management of kinds (automatic creation of new kind
        if name is not specified and properties are different).
        This test was failing in, e.g., commit f6a8f4b.
        """
        from aiida.orm.data.structure import StructureData
        from aiida.common.constants import elements

        s = StructureData(cell=((6., 0., 0.), (0., 6., 0.), (0., 0., 6.)))

        s.append_atom(symbols='Fe', position=[0, 0, 0], mass=12)
        s.append_atom(symbols='Fe', position=[1, 0, 0], mass=12)
        s.append_atom(symbols='Fe', position=[2, 0, 0], mass=12)
        s.append_atom(symbols='Fe', position=[2, 0, 0])
        s.append_atom(symbols='Fe', position=[4, 0, 0])

        # I expect only two species, the first one with name 'Fe', mass 12,
        # and referencing the first three atoms; the second with name
        # 'Fe1', mass = elements[26]['mass'], and referencing the last two atoms
        self.assertEquals(
            set([(k.name, k.mass) for k in s.kinds]),
            set([('Fe', 12.0), ('Fe1', elements[26]['mass'])]))

        kind_of_each_site = [site.kind_name for site in s.sites]
        self.assertEquals(kind_of_each_site,
                          ['Fe', 'Fe', 'Fe', 'Fe1', 'Fe1'])

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    def test_kind_5_bis_ase(self):
        """
        Same test as test_kind_5_bis, but using ase
        """
        from aiida.orm.data.structure import StructureData
        import ase

        asecell = ase.Atoms('Fe5',
                            cell=((6., 0., 0.), (0., 6., 0.), (0., 0., 6.)))
        asecell.set_positions([
            [0, 0, 0],
            [1, 0, 0],
            [2, 0, 0],
            [3, 0, 0],
            [4, 0, 0],
        ])

        asecell[0].mass = 12.
        asecell[1].mass = 12.
        asecell[2].mass = 12.

        s = StructureData(ase=asecell)

        # I expect only two species, the first one with name 'Fe', mass 12,
        # and referencing the first three atoms; the second with name
        # 'Fe1', mass = elements[26]['mass'], and referencing the last two atoms
        self.assertEquals(
            set([(k.name, k.mass) for k in s.kinds]),
            set([('Fe', 12.0), ('Fe1', asecell[3].mass)]))

        kind_of_each_site = [site.kind_name for site in s.sites]
        self.assertEquals(kind_of_each_site,
                          ['Fe', 'Fe', 'Fe', 'Fe1', 'Fe1'])

    def test_kind_6(self):
        """
        Test the returning of kinds from the string name (most of the code
        copied from :py:meth:`.test_kind_5`).
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2., 0., 0.), (0., 2., 0.), (0., 0., 2.)))

        a.append_atom(position=(0., 0., 0.), symbols='Ba', mass=100.)
        a.append_atom(position=(0., 0., 0.), symbols='Ti')
        # The name does not exist
        a.append_atom(position=(0., 0., 0.), symbols='Ti', name='Ti2')
        # The name already exists, but the properties are identical => OK
        a.append_atom(position=(1., 1., 1.), symbols='Ti', name='Ti2')
        # Should not complain, should create a new type
        a.append_atom(position=(0., 0., 0.), symbols='Ba', mass=150.)
        # There should be 4 kinds, the automatic name for the last one
        # should be Ba1 (same check of test_kind_5
        self.assertEquals([k.name for k in a.kinds],
                          ['Ba', 'Ti', 'Ti2', 'Ba1'])
        #############################
        # Here I start the real tests
        # No such kind
        with self.assertRaises(ValueError):
            a.get_kind('Ti3')
        k = a.get_kind('Ba1')
        self.assertEqual(k.symbols, ('Ba',))
        self.assertAlmostEqual(k.mass, 150.)

    def test_kind_7(self):
        """
        Test the functions returning the list of kinds, symbols, ...
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2., 0., 0.), (0., 2., 0.), (0., 0., 2.)))

        a.append_atom(position=(0., 0., 0.), symbols='Ba', mass=100.)
        a.append_atom(position=(0., 0., 0.), symbols='Ti')
        # The name does not exist
        a.append_atom(position=(0., 0., 0.), symbols='Ti', name='Ti2')
        # The name already exists, but the properties are identical => OK
        a.append_atom(position=(0., 0., 0.), symbols=['O', 'H'],
                      weights=[0.9, 0.1], mass=15.)

        self.assertEquals(a.get_symbols_set(), set(['Ba', 'Ti', 'O', 'H']))

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    @unittest.skipIf(not has_spglib(), "Unable to import spglib")
    def test_kind_8(self):
        """
        Test the ase_refine_cell() function
        """
        from aiida.orm.data.structure import ase_refine_cell
        import ase
        import math
        import numpy

        a = ase.Atoms(cell=[10, 10, 10])
        a.append(ase.Atom('C', [0, 0, 0]))
        a.append(ase.Atom('C', [5, 0, 0]))
        b, sym = ase_refine_cell(a)
        sym.pop('rotations')
        sym.pop('translations')
        self.assertEquals(b.get_chemical_symbols(), ['C'])
        self.assertEquals(b.cell.tolist(), [[10, 0, 0], [0, 10, 0], [0, 0, 5]])
        self.assertEquals(sym,
                          {'hall': '-P 4 2', 'hm': 'P4/mmm', 'tables': 123})

        a = ase.Atoms(cell=[10, 2 * math.sqrt(75), 10])
        a.append(ase.Atom('C', [0, 0, 0]))
        a.append(ase.Atom('C', [5, math.sqrt(75), 0]))
        b, sym = ase_refine_cell(a)
        sym.pop('rotations')
        sym.pop('translations')
        self.assertEquals(b.get_chemical_symbols(), ['C'])
        self.assertEquals(numpy.round(b.cell, 2).tolist(),
                          [[10, 0, 0], [-5, 8.66, 0], [0, 0, 10]])
        self.assertEquals(sym,
                          {'hall': '-P 6 2', 'hm': 'P6/mmm', 'tables': 191})

        a = ase.Atoms(cell=[[10, 0, 0], [-10, 10, 0], [0, 0, 10]])
        a.append(ase.Atom('C', [5, 5, 5]))
        a.append(ase.Atom('F', [0, 0, 0]))
        b, sym = ase_refine_cell(a)
        sym.pop('rotations')
        sym.pop('translations')
        self.assertEquals(b.get_chemical_symbols(), ['C', 'F'])
        self.assertEquals(b.cell.tolist(), [[10, 0, 0], [0, 10, 0], [0, 0, 10]])
        self.assertEquals(b.get_scaled_positions().tolist(),
                          [[0.5, 0.5, 0.5], [0, 0, 0]])
        self.assertEquals(sym,
                          {'hall': '-P 4 2 3', 'hm': 'Pm-3m', 'tables': 221})

        a = ase.Atoms(cell=[[10, 0, 0], [-10, 10, 0], [0, 0, 10]])
        a.append(ase.Atom('C', [0, 0, 0]))
        a.append(ase.Atom('F', [5, 5, 5]))
        b, sym = ase_refine_cell(a)
        sym.pop('rotations')
        sym.pop('translations')
        self.assertEquals(b.get_chemical_symbols(), ['C', 'F'])
        self.assertEquals(b.cell.tolist(), [[10, 0, 0], [0, 10, 0], [0, 0, 10]])
        self.assertEquals(b.get_scaled_positions().tolist(),
                          [[0, 0, 0], [0.5, 0.5, 0.5]])
        self.assertEquals(sym,
                          {'hall': '-P 4 2 3', 'hm': 'Pm-3m', 'tables': 221})

        a = ase.Atoms(cell=[[12.132, 0, 0], [0, 6.0606, 0], [0, 0, 8.0956]])
        a.append(ase.Atom('Ba', [1.5334848, 1.3999986, 2.00042276]))
        b, sym = ase_refine_cell(a)
        sym.pop('rotations')
        sym.pop('translations')
        self.assertEquals(b.cell.tolist(),
                          [[6.0606, 0, 0], [0, 8.0956, 0], [0, 0, 12.132]])
        self.assertEquals(b.get_scaled_positions().tolist(), [[0, 0, 0]])

        a = ase.Atoms(cell=[10, 10, 10])
        a.append(ase.Atom('C', [5, 5, 5]))
        a.append(ase.Atom('O', [2.5, 5, 5]))
        a.append(ase.Atom('O', [7.5, 5, 5]))
        b, sym = ase_refine_cell(a)
        sym.pop('rotations')
        sym.pop('translations')
        self.assertEquals(b.get_chemical_symbols(), ['C', 'O'])
        self.assertEquals(sym,
                          {'hall': '-P 4 2', 'hm': 'P4/mmm', 'tables': 123})

        # Generated from COD entry 1507756
        # (http://www.crystallography.net/cod/1507756.cif@87343)
        from ase.lattice.spacegroup import crystal
        a = crystal(['Ba', 'Ti', 'O', 'O'],
                    [
                        [0, 0, 0],
                        [0.5, 0.5, 0.482],
                        [0.5, 0.5, 0.016],
                        [0.5, 0, 0.515]
                    ],
                    cell=[3.9999, 3.9999, 4.0170],
                    spacegroup=99)
        b, sym = ase_refine_cell(a)
        sym.pop('rotations')
        sym.pop('translations')
        self.assertEquals(b.get_chemical_symbols(), ['Ba', 'Ti', 'O', 'O'])
        self.assertEquals(sym, {'hall': 'P 4 -2', 'hm': 'P4mm', 'tables': 99})

    def test_get_formula(self):
        """
        Tests the generation of formula
        """
        from aiida.orm.data.structure import get_formula

        self.assertEquals(get_formula(['Ba', 'Ti'] + ['O'] * 3),
                          'BaO3Ti')
        self.assertEquals(get_formula(['Ba', 'Ti', 'C'] + ['O'] * 3,
                                      separator=" "),
                          'C Ba O3 Ti')
        self.assertEquals(get_formula(['H'] * 6 + ['C'] * 6),
                          'C6H6')
        self.assertEquals(get_formula(['H'] * 6 + ['C'] * 6,
                                      mode="hill_compact"),
                          'CH')
        self.assertEquals(get_formula((['Ba', 'Ti'] + ['O'] * 3) * 2 + \
                                      ['Ba'] + ['Ti'] * 2 + ['O'] * 3,
                                      mode="group"),
                          '(BaTiO3)2BaTi2O3')
        self.assertEquals(get_formula((['Ba', 'Ti'] + ['O'] * 3) * 2 + \
                                      ['Ba'] + ['Ti'] * 2 + ['O'] * 3,
                                      mode="group", separator=" "),
                          '(Ba Ti O3)2 Ba Ti2 O3')
        self.assertEquals(get_formula((['Ba', 'Ti'] + ['O'] * 3) * 2 + \
                                      ['Ba'] + ['Ti'] * 2 + ['O'] * 3,
                                      mode="reduce"),
                          'BaTiO3BaTiO3BaTi2O3')
        self.assertEquals(get_formula((['Ba', 'Ti'] + ['O'] * 3) * 2 + \
                                      ['Ba'] + ['Ti'] * 2 + ['O'] * 3,
                                      mode="reduce", separator=", "),
                          'Ba, Ti, O3, Ba, Ti, O3, Ba, Ti2, O3')
        self.assertEquals(get_formula((['Ba', 'Ti'] + ['O'] * 3) * 2,
                                      mode="count"),
                          'Ba2Ti2O6')
        self.assertEquals(get_formula((['Ba', 'Ti'] + ['O'] * 3) * 2,
                                      mode="count_compact"),
                          'BaTiO3')

    def test_get_cif(self):
        """
        Tests the conversion to CifData
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2., 0., 0.), (0., 2., 0.), (0., 0., 2.)))

        a.append_atom(position=(0., 0., 0.), symbols=['Ba'])
        a.append_atom(position=(0.5, 0.5, 0.5), symbols=['Ba'])
        a.append_atom(position=(1., 1., 1.), symbols=['Ti'])

        try:
            c = a._get_cif()
        # Exception thrown if ase can't be found
        except ImportError:
            return
        self.assertEquals(simplify(c._prepare_cif()[0]),
                          simplify("""#\#CIF1.1
##########################################################################
#               Crystallographic Information Format file
#               Produced by PyCifRW module
#
#  This is a CIF file.  CIF has been adopted by the International
#  Union of Crystallography as the standard for data archiving and
#  transmission.
#
#  For information on this file format, follow the CIF links at
#  http://www.iucr.org
##########################################################################

data_0
loop_
  _atom_site_label
  _atom_site_fract_x
  _atom_site_fract_y
  _atom_site_fract_z
  _atom_site_type_symbol
   Ba1  0.0  0.0  0.0  Ba
   Ba2  0.25  0.25  0.25  Ba
   Ti1  0.5  0.5  0.5  Ti

_cell_angle_alpha                       90.0
_cell_angle_beta                        90.0
_cell_angle_gamma                       90.0
_cell_length_a                          2.0
_cell_length_b                          2.0
_cell_length_c                          2.0
loop_
  _symmetry_equiv_pos_as_xyz
   'x, y, z'

_symmetry_Int_Tables_number             1
_symmetry_space_group_name_H-M          'P 1'
_symmetry_space_group_name_Hall         'P 1'
_cell_formula_units_Z                   1
_chemical_formula_sum                   'Ba2 Ti'
"""))

    def test_xyz_parser(self):
        from aiida.orm.data.structure import StructureData
        import numpy as np
        xyz_string1 = """
3

Li      0.00000000       0.00000000       0.00000000       6.94100000        3 
Si      4.39194796       0.00000000      10.10068356      28.08550000       14 
Si      4.39194796       0.00000000       3.79747116      28.08550000       14 
"""
        xyz_string2 = """
2
Silver dimer;
Ag 0 0 0
Ag 0 0 2.5335
"""

        xyz_string3 = """
2
Shifted Silver dimer;
Ag 0 0 -.5
Ag 0 0 2.0335
"""

        for xyz_string in (xyz_string1, xyz_string2, xyz_string3):
            s = StructureData()
            # Parsing the string:
            s._parse_xyz(xyz_string)
            # Making sure that the periodic boundary condition are not True
            # because I cannot parse a cell!
            self.assertTrue(not (any(s.pbc)))
            # Making sure that the structure has sites, kinds and a cell
            self.assertTrue(s.sites)
            self.assertTrue(s.kinds)
            self.assertTrue(s.cell)
            # The default cell is given in these cases:
            self.assertEqual(s.cell, np.diag([1, 1, 1]).tolist())

        # Testing a case where 1
        xyz_string4 = """
1

Li      0.00000000       0.00000000       0.00000000       6.94100000        3 
Si      4.39194796       0.00000000      10.10068356      28.08550000       14 
Si      4.39194796       0.00000000       3.79747116      28.08550000       14 
"""
        xyz_string5 = """
10

Li      0.00000000       0.00000000       0.00000000       6.94100000        3 
Si      4.39194796       0.00000000      10.10068356      28.08550000       14 
Si      4.39194796       0.00000000       3.79747116      28.08550000       14 
"""
        xyz_string6 = """
2
Shifted Silver dimer;
Ag 0 0 -.5
Ag 0 0
"""

        # The above cases have to fail because the number of atoms is wrong
        for xyz_string in (xyz_string4, xyz_string5, xyz_string6):
            with self.assertRaises(TypeError):
                StructureData()._parse_xyz(xyz_string)


class TestStructureDataLock(AiidaTestCase):
    """
    Tests that the structure is locked after storage
    """

    def test_lock(self):
        """
        Start from a StructureData object, convert to raw and then back
        """
        from aiida.orm.data.structure import StructureData, Kind, Site

        cell = ((1., 0., 0.), (0., 2., 0.), (0., 0., 3.))
        a = StructureData(cell=cell)

        a.pbc = [False, True, True]

        k = Kind(symbols='Ba', name='Ba')
        s = Site(position=(0., 0., 0.), kind_name='Ba')
        a.append_kind(k)
        a.append_site(s)

        a.append_atom(symbols='Ti', position=[0., 0., 0.])

        a.store()

        k2 = Kind(symbols='Ba', name='Ba')
        # Nothing should be changed after store()
        with self.assertRaises(ModificationNotAllowed):
            a.append_kind(k2)
        with self.assertRaises(ModificationNotAllowed):
            a.append_site(s)
        with self.assertRaises(ModificationNotAllowed):
            a.clear_sites()
        with self.assertRaises(ModificationNotAllowed):
            a.clear_kinds()
        with self.assertRaises(ModificationNotAllowed):
            a.cell = cell
        with self.assertRaises(ModificationNotAllowed):
            a.pbc = [True, True, True]

        _ = a.get_cell_volume()
        _ = a.is_alloy()
        _ = a.has_vacancies()

        b = a.copy()
        # I check that I can edit after copy
        b.append_site(s)
        b.clear_sites()
        # I check that the original did not change
        self.assertNotEquals(len(a.sites), 0)
        b.cell = cell
        b.pbc = [True, True, True]


class TestStructureDataReload(AiidaTestCase):
    """
    Tests the creation of StructureData, converting it to a raw format and
    converting it back.
    """

    def test_reload(self):
        """
        Start from a StructureData object, convert to raw and then back
        """
        from aiida.orm.data.structure import StructureData

        cell = ((1., 0., 0.), (0., 2., 0.), (0., 0., 3.))
        a = StructureData(cell=cell)

        a.pbc = [False, True, True]

        a.append_atom(position=(0., 0., 0.), symbols=['Ba'])
        a.append_atom(position=(1., 1., 1.), symbols=['Ti'])

        a.store()

        b = StructureData(dbnode=a.dbnode)

        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(cell[i][j], b.cell[i][j])

        self.assertEqual(b.pbc, (False, True, True))
        self.assertEqual(len(b.sites), 2)
        self.assertEqual(b.kinds[0].symbols[0], 'Ba')
        self.assertEqual(b.kinds[1].symbols[0], 'Ti')
        for i in range(3):
            self.assertAlmostEqual(b.sites[0].position[i], 0.)
        for i in range(3):
            self.assertAlmostEqual(b.sites[1].position[i], 1.)

        # Fully reload from UUID
        b = load_node(a.uuid, parent_class=StructureData)

        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(cell[i][j], b.cell[i][j])

        self.assertEqual(b.pbc, (False, True, True))
        self.assertEqual(len(b.sites), 2)
        self.assertEqual(b.kinds[0].symbols[0], 'Ba')
        self.assertEqual(b.kinds[1].symbols[0], 'Ti')
        for i in range(3):
            self.assertAlmostEqual(b.sites[0].position[i], 0.)
        for i in range(3):
            self.assertAlmostEqual(b.sites[1].position[i], 1.)


    def test_copy(self):
        """
        Start from a StructureData object, copy it and see if it is preserved
        """
        from aiida.orm.data.structure import StructureData

        cell = ((1., 0., 0.), (0., 2., 0.), (0., 0., 3.))
        a = StructureData(cell=cell)

        a.pbc = [False, True, True]

        a.append_atom(position=(0., 0., 0.), symbols=['Ba'])
        a.append_atom(position=(1., 1., 1.), symbols=['Ti'])

        b = a.copy()

        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(cell[i][j], b.cell[i][j])

        self.assertEqual(b.pbc, (False, True, True))
        self.assertEqual(len(b.kinds), 2)
        self.assertEqual(len(b.sites), 2)
        self.assertEqual(b.kinds[0].symbols[0], 'Ba')
        self.assertEqual(b.kinds[1].symbols[0], 'Ti')
        for i in range(3):
            self.assertAlmostEqual(b.sites[0].position[i], 0.)
        for i in range(3):
            self.assertAlmostEqual(b.sites[1].position[i], 1.)

        a.store()

        # Copy after store()
        c = a.copy()
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(cell[i][j], c.cell[i][j])

        self.assertEqual(c.pbc, (False, True, True))
        self.assertEqual(len(c.kinds), 2)
        self.assertEqual(len(c.sites), 2)
        self.assertEqual(c.kinds[0].symbols[0], 'Ba')
        self.assertEqual(c.kinds[1].symbols[0], 'Ti')
        for i in range(3):
            self.assertAlmostEqual(c.sites[0].position[i], 0.)
        for i in range(3):
            self.assertAlmostEqual(c.sites[1].position[i], 1.)


class TestStructureDataFromAse(AiidaTestCase):
    """
    Tests the creation of Sites from/to a ASE object.
    """
    from aiida.orm.data.structure import has_ase

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    def test_ase(self):
        from aiida.orm.data.structure import StructureData
        import ase

        a = ase.Atoms('SiGe', cell=(1., 2., 3.), pbc=(True, False, False))
        a.set_positions(
            ((0., 0., 0.),
             (0.5, 0.7, 0.9),)
        )
        a[1].mass = 110.2

        b = StructureData(ase=a)
        c = b.get_ase()

        self.assertEqual(a[0].symbol, c[0].symbol)
        self.assertEqual(a[1].symbol, c[1].symbol)
        for i in range(3):
            self.assertAlmostEqual(a[0].position[i], c[0].position[i])
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(a.cell[i][j], c.cell[i][j])

        self.assertAlmostEqual(c[1].mass, 110.2)

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    def test_conversion_of_types_1(self):
        from aiida.orm.data.structure import StructureData
        import ase

        a = ase.Atoms('Si4Ge4', cell=(1., 2., 3.), pbc=(True, False, False))
        a.set_positions(
            ((0.0, 0.0, 0.0),
             (0.1, 0.1, 0.1),
             (0.2, 0.2, 0.2),
             (0.3, 0.3, 0.3),
             (0.4, 0.4, 0.4),
             (0.5, 0.5, 0.5),
             (0.6, 0.6, 0.6),
             (0.7, 0.7, 0.7),
             )
        )

        a.set_tags((0, 1, 2, 3, 4, 5, 6, 7))

        b = StructureData(ase=a)
        self.assertEquals([k.name for k in b.kinds],
                          ["Si", "Si1", "Si2", "Si3",
                           "Ge4", "Ge5", "Ge6", "Ge7"])
        c = b.get_ase()

        a_tags = list(a.get_tags())
        c_tags = list(c.get_tags())
        self.assertEqual(a_tags, c_tags)

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    def test_conversion_of_types_2(self):
        from aiida.orm.data.structure import StructureData
        import ase

        a = ase.Atoms('Si4', cell=(1., 2., 3.), pbc=(True, False, False))
        a.set_positions(
            ((0.0, 0.0, 0.0),
             (0.1, 0.1, 0.1),
             (0.2, 0.2, 0.2),
             (0.3, 0.3, 0.3),
             )
        )

        a.set_tags((0, 1, 0, 1))
        a[2].mass = 100.
        a[3].mass = 300.

        b = StructureData(ase=a)
        # This will give funny names to the kinds, because I am using
        # both tags and different properties (mass). I just check to have
        # 4 kinds
        self.assertEquals(len(b.kinds), 4)

        # Do I get the same tags after one full iteration back and forth?
        c = b.get_ase()
        d = StructureData(ase=c)
        e = d.get_ase()
        c_tags = list(c.get_tags())
        e_tags = list(e.get_tags())
        self.assertEqual(c_tags, e_tags)

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    def test_conversion_of_types_3(self):
        from aiida.orm.data.structure import StructureData

        a = StructureData()
        a.append_atom(position=(0., 0., 0.), symbols='Ba', name='Ba')
        a.append_atom(position=(0., 0., 0.), symbols='Ba', name='Ba1')
        a.append_atom(position=(0., 0., 0.), symbols='Cu', name='Cu')
        # continues with a number
        a.append_atom(position=(0., 0., 0.), symbols='Cu', name='Cu2')
        # does not continue with a number
        a.append_atom(position=(0., 0., 0.), symbols='Cu', name='Cu_my')
        # random string
        a.append_atom(position=(0., 0., 0.), symbols='Cu', name='a_name')
        # a name of another chemical symbol
        a.append_atom(position=(0., 0., 0.), symbols='Cu', name='Fe')
        # lowercase! as if it were a random string
        a.append_atom(position=(0., 0., 0.), symbols='Cu', name='cu1')

        # Just to be sure that the species were saved with the correct name
        # in the first place
        self.assertEquals([k.name for k in a.kinds],
                          ['Ba', 'Ba1', 'Cu', 'Cu2', 'Cu_my',
                           'a_name', 'Fe', 'cu1'])

        b = a.get_ase()
        self.assertEquals(b.get_chemical_symbols(), ['Ba', 'Ba', 'Cu',
                                                     'Cu', 'Cu', 'Cu',
                                                     'Cu', 'Cu'])
        self.assertEquals(list(b.get_tags()), [0, 1, 0, 2, 3, 4, 5, 6])

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    def test_conversion_of_types_4(self):
        from aiida.orm.data.structure import StructureData
        import ase

        atoms = ase.Atoms('Fe5')
        atoms[2].tag = 1
        atoms[3].tag = 1
        atoms[4].tag = 4
        s = StructureData(ase=atoms)
        kindnames = set([k.name for k in s.kinds])
        self.assertEquals(kindnames, set(['Fe', 'Fe1', 'Fe4']))

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    def test_conversion_of_types_5(self):
        from aiida.orm.data.structure import StructureData
        import ase

        atoms = ase.Atoms('Fe5')
        atoms[0].tag = 1
        atoms[2].tag = 1
        atoms[3].tag = 4
        s = StructureData(ase=atoms)
        kindnames = set([k.name for k in s.kinds])
        self.assertEquals(kindnames, set(['Fe', 'Fe1', 'Fe4']))


class TestStructureDataFromPymatgen(AiidaTestCase):
    """
    Tests the creation of StructureData from a pymatgen Structure and
    Molecule objects.
    """
    from distutils.version import StrictVersion
    from aiida.orm.data.structure import has_pymatgen, get_pymatgen_version

    @unittest.skipIf(not has_pymatgen(), "Unable to import pymatgen")
    @unittest.skipIf(has_pymatgen() and
                     StrictVersion(get_pymatgen_version()) !=
                     StrictVersion('4.5.3'),
                    "Mismatch in the version of pymatgen (expected 4.5.3)")
    def test_1(self):
        """
        Test's imput is derived from COD entry 9011963, processed with
        cif_mark_disorder (from cod-tools) and abbreviated.
        """
        from aiida.orm.data.structure import StructureData
        from pymatgen.io.cif import CifParser

        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".cif") as f:
            f.write("""data_9011963
                _space_group_IT_number           166
                _symmetry_space_group_name_Hall  '-R 3 2"'
                _symmetry_space_group_name_H-M   'R -3 m :H'
                _cell_angle_alpha                90
                _cell_angle_beta                 90
                _cell_angle_gamma                120
                _cell_length_a                   4.298
                _cell_length_b                   4.298
                _cell_length_c                   29.774
                loop_
                _atom_site_label
                _atom_site_fract_x
                _atom_site_fract_y
                _atom_site_fract_z
                _atom_site_occupancy
                _atom_site_U_iso_or_equiv
                _atom_site_disorder_assembly
                _atom_site_disorder_group
                Bi 0.00000 0.00000 0.39580 1.00000 0.02343 . .
                Te1 0.00000 0.00000 0.00000 0.66667 0.02343 A 1
                Se1 0.00000 0.00000 0.00000 0.33333 0.02343 A 2
                Te2 0.00000 0.00000 0.21180 0.66667 0.02343 B 1
                Se2 0.00000 0.00000 0.21180 0.33333 0.02343 B 2
                """)
            f.flush()
            pymatgen_parser = CifParser(f.name)
            pymatgen_struct = pymatgen_parser.get_structures()[0]

        structs_to_test = [StructureData(pymatgen=pymatgen_struct),
                           StructureData(pymatgen_structure=pymatgen_struct)]

        for struct in structs_to_test:
            self.assertEquals(struct.get_site_kindnames(),
                              ['Bi', 'Bi', 'SeTe', 'SeTe', 'SeTe'])
            self.assertEquals([x.symbols for x in struct.kinds],
                              [('Bi',), ('Se', 'Te')])
            self.assertEquals([x.weights for x in struct.kinds],
                              [(1.0,), (0.33333, 0.66667)])

        struct = StructureData(pymatgen_structure=pymatgen_struct)

        # Testing pymatgen Structure -> StructureData -> pymatgen Structure
        # roundtrip.

        pymatgen_struct_roundtrip = struct.get_pymatgen_structure()
        dict1 = pymatgen_struct.as_dict()
        dict2 = pymatgen_struct_roundtrip.as_dict()

        for i in dict1['sites']:
            i['abc'] = [round(j, 2) for j in i['abc']]
        for i in dict2['sites']:
            i['abc'] = [round(j, 2) for j in i['abc']]

        self.assertEquals(dict1, dict2)

    @unittest.skipIf(not has_pymatgen(), "Unable to import pymatgen")
    @unittest.skipIf(has_pymatgen() and
                     StrictVersion(get_pymatgen_version()) !=
                     StrictVersion('4.5.3'),
                     "Mismatch in the version of pymatgen (expected 4.5.3)")
    def test_2(self):
        """
        Input source: http://pymatgen.org/_static/Molecule.html
        """
        from aiida.orm.data.structure import StructureData
        from pymatgen.io.xyz import XYZ

        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".xyz") as f:
            f.write("""5
                H4 C1
                C 0.000000 0.000000 0.000000
                H 0.000000 0.000000 1.089000
                H 1.026719 0.000000 -0.363000
                H -0.513360 -0.889165 -0.363000
                H -0.513360 0.889165 -0.363000""")
            f.flush()
            pymatgen_xyz = XYZ.from_file(f.name)
            pymatgen_mol = pymatgen_xyz.molecule

        for struct in [StructureData(pymatgen=pymatgen_mol),
                       StructureData(pymatgen_molecule=pymatgen_mol)]:
            self.assertEquals(struct.get_site_kindnames(),
                              ['H', 'H', 'H', 'H', 'C'])
            self.assertEquals(struct.pbc, (False, False, False))
            self.assertEquals(
                [round(x, 2) for x in list(struct.sites[0].position)],
                [5.77, 5.89, 6.81])
            self.assertEquals(
                [round(x, 2) for x in list(struct.sites[1].position)],
                [6.8, 5.89, 5.36])
            self.assertEquals(
                [round(x, 2) for x in list(struct.sites[2].position)],
                [5.26, 5.0, 5.36])
            self.assertEquals(
                [round(x, 2) for x in list(struct.sites[3].position)],
                [5.26, 6.78, 5.36])
            self.assertEquals(
                [round(x, 2) for x in list(struct.sites[4].position)],
                [5.77, 5.89, 5.73])


class TestPymatgenFromStructureData(AiidaTestCase):
    """
    Tests the creation of pymatgen Structure and Molecule objects from
    StructureData.
    """
    from distutils.version import StrictVersion
    from aiida.orm.data.structure import has_ase, has_pymatgen, \
        get_pymatgen_version

    @unittest.skipIf(not has_pymatgen(), "Unable to import pymatgen")
    @unittest.skipIf(has_pymatgen() and
                     StrictVersion(get_pymatgen_version()) !=
                     StrictVersion('4.5.3'),
                     "Mismatch in the version of pymatgen (expected 4.5.3)")
    def test_1(self):
        """
        Test the check of periodic boundary conditions.
        """
        from aiida.orm.data.structure import StructureData

        struct = StructureData()

        struct.pbc = [True, True, True]
        pmg_struct = struct.get_pymatgen_structure()

        struct.pbc = [True, True, False]
        with self.assertRaises(ValueError):
            pmg_struct = struct.get_pymatgen_structure()

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    @unittest.skipIf(not has_pymatgen(), "Unable to import pymatgen")
    @unittest.skipIf(has_pymatgen() and
                     StrictVersion(get_pymatgen_version()) !=
                     StrictVersion('4.5.3'),
                     "Mismatch in the version of pymatgen (expected 4.5.3)")
    def test_2(self):
        from aiida.orm.data.structure import StructureData
        import ase

        aseatoms = ase.Atoms('Si4', cell=(1., 2., 3.),
                             pbc=(True, True, True))
        aseatoms.set_scaled_positions(
            ((0.0, 0.0, 0.0),
             (0.1, 0.1, 0.1),
             (0.2, 0.2, 0.2),
             (0.3, 0.3, 0.3),
             )
        )

        a_struct = StructureData(ase=aseatoms)
        p_struct = a_struct.get_pymatgen_structure()

        p_struct_dict = p_struct.as_dict()
        coord_array = [x['abc'] for x in p_struct_dict['sites']]
        for i in range(len(coord_array)):
            coord_array[i] = [round(x, 2) for x in coord_array[i]]

        self.assertEquals(coord_array,
                          [[0.0, 0.0, 0.0],
                           [0.1, 0.1, 0.1],
                           [0.2, 0.2, 0.2],
                           [0.3, 0.3, 0.3]])

    @unittest.skipIf(not has_ase(), "Unable to import ase")
    @unittest.skipIf(not has_pymatgen(), "Unable to import pymatgen")
    @unittest.skipIf(has_pymatgen() and
                     StrictVersion(get_pymatgen_version()) !=
                     StrictVersion('4.5.3'),
                     "Mismatch in the version of pymatgen (expected 4.5.3)")
    def test_3(self):
        """
        Test the conversion of StructureData to pymatgen's Molecule.
        """
        from aiida.orm.data.structure import StructureData
        import ase

        aseatoms = ase.Atoms('Si4', cell=(10, 10, 10),
                             pbc=(True, True, True))
        aseatoms.set_scaled_positions(
            ((0.0, 0.0, 0.0),
             (0.1, 0.1, 0.1),
             (0.2, 0.2, 0.2),
             (0.3, 0.3, 0.3),
             )
        )

        a_struct = StructureData(ase=aseatoms)
        p_mol = a_struct.get_pymatgen_molecule()

        p_mol_dict = p_mol.as_dict()
        self.assertEquals([x['xyz'] for x in p_mol_dict['sites']],
                          [[0.0, 0.0, 0.0],
                           [1.0, 1.0, 1.0],
                           [2.0, 2.0, 2.0],
                           [3.0, 3.0, 3.0]])


class TestArrayData(AiidaTestCase):
    """
    Tests the ArrayData objects.
    """

    def test_creation(self):
        """
        Check the methods to add, remove, modify, and get arrays and
        array shapes.
        """
        from aiida.orm.data.array import ArrayData
        import numpy

        # Create a node with two arrays
        n = ArrayData()
        first = numpy.random.rand(2, 3, 4)
        n.set_array('first', first)

        second = numpy.arange(10)
        n.set_array('second', second)

        third = numpy.random.rand(6, 6)
        n.set_array('third', third)

        # Check if the arrays are there
        self.assertEquals(set(['first', 'second', 'third']),
                          set(n.arraynames()))
        self.assertAlmostEquals(abs(first - n.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second - n.get_array('second')).max(), 0.)
        self.assertAlmostEquals(abs(third - n.get_array('third')).max(), 0.)
        self.assertEquals(first.shape, n.get_shape('first'))
        self.assertEquals(second.shape, n.get_shape('second'))
        self.assertEquals(third.shape, n.get_shape('third'))

        with self.assertRaises(KeyError):
            n.get_array('nonexistent_array')

        # Delete an array, and try to delete a non-existing one
        n.delete_array('third')
        with self.assertRaises(KeyError):
            n.delete_array('nonexistent_array')

        # Overwrite an array
        first = numpy.random.rand(4, 5, 6)
        n.set_array('first', first)

        # Check if the arrays are there, and if I am getting the new one
        self.assertEquals(set(['first', 'second']), set(n.arraynames()))
        self.assertAlmostEquals(abs(first - n.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second - n.get_array('second')).max(), 0.)
        self.assertEquals(first.shape, n.get_shape('first'))
        self.assertEquals(second.shape, n.get_shape('second'))

        n.store()

        # Same checks, after storing
        self.assertEquals(set(['first', 'second']), set(n.arraynames()))
        self.assertAlmostEquals(abs(first - n.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second - n.get_array('second')).max(), 0.)
        self.assertEquals(first.shape, n.get_shape('first'))
        self.assertEquals(second.shape, n.get_shape('second'))

        # Same checks, again (this is checking the caching features)
        self.assertEquals(set(['first', 'second']), set(n.arraynames()))
        self.assertAlmostEquals(abs(first - n.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second - n.get_array('second')).max(), 0.)
        self.assertEquals(first.shape, n.get_shape('first'))
        self.assertEquals(second.shape, n.get_shape('second'))

        # Same checks, after reloading
        n2 = ArrayData(dbnode=n.dbnode)
        self.assertEquals(set(['first', 'second']), set(n2.arraynames()))
        self.assertAlmostEquals(abs(first - n2.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second - n2.get_array('second')).max(), 0.)
        self.assertEquals(first.shape, n2.get_shape('first'))
        self.assertEquals(second.shape, n2.get_shape('second'))

        # Same checks, after reloading with UUID
        n2 = load_node(n.uuid, parent_class=ArrayData)
        self.assertEquals(set(['first', 'second']), set(n2.arraynames()))
        self.assertAlmostEquals(abs(first - n2.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second - n2.get_array('second')).max(), 0.)
        self.assertEquals(first.shape, n2.get_shape('first'))
        self.assertEquals(second.shape, n2.get_shape('second'))

        # Check that I cannot modify the node after storing
        with self.assertRaises(ModificationNotAllowed):
            n.delete_array('first')
        with self.assertRaises(ModificationNotAllowed):
            n.set_array('second', first)

        # Again same checks, to verify that the attempts to delete/overwrite
        # arrays did not damage the node content
        self.assertEquals(set(['first', 'second']), set(n.arraynames()))
        self.assertAlmostEquals(abs(first - n.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second - n.get_array('second')).max(), 0.)
        self.assertEquals(first.shape, n.get_shape('first'))
        self.assertEquals(second.shape, n.get_shape('second'))

    def test_iteration(self):
        """
        Check the functionality of the iterarrays() iterator
        """
        from aiida.orm.data.array import ArrayData
        import numpy

        # Create a node with two arrays
        n = ArrayData()
        first = numpy.random.rand(2, 3, 4)
        n.set_array('first', first)

        second = numpy.arange(10)
        n.set_array('second', second)

        third = numpy.random.rand(6, 6)
        n.set_array('third', third)

        for name, array in n.iterarrays():
            if name == 'first':
                self.assertAlmostEquals(abs(first - array).max(), 0.)
            if name == 'second':
                self.assertAlmostEquals(abs(second - array).max(), 0.)
            if name == 'third':
                self.assertAlmostEquals(abs(third - array).max(), 0.)


class TestTrajectoryData(AiidaTestCase):
    """
    Tests the TrajectoryData objects.
    """

    def test_creation(self):
        """
        Check the methods to set and retrieve a trajectory.
        """
        from aiida.orm.data.array.trajectory import TrajectoryData
        import numpy

        # Create a node with two arrays
        n = TrajectoryData()

        # I create sample data
        stepids = numpy.array([60, 70])
        times = stepids * 0.01
        cells = numpy.array([
            [[2., 0., 0., ],
             [0., 2., 0., ],
             [0., 0., 2., ]],
            [[3., 0., 0., ],
             [0., 3., 0., ],
             [0., 0., 3., ]]])
        symbols = numpy.array(['H', 'O', 'C'])
        positions = numpy.array([
            [[0., 0., 0.],
             [0.5, 0.5, 0.5],
             [1.5, 1.5, 1.5]],
            [[0., 0., 0.],
             [0.5, 0.5, 0.5],
             [1.5, 1.5, 1.5]]])
        velocities = numpy.array([
            [[0., 0., 0.],
             [0., 0., 0.],
             [0., 0., 0.]],
            [[0.5, 0.5, 0.5],
             [0.5, 0.5, 0.5],
             [-0.5, -0.5, -0.5]]])

        # I set the node
        n.set_trajectory(stepids=stepids, cells=cells, symbols=symbols,
                         positions=positions, times=times,
                         velocities=velocities)

        # Generic checks
        self.assertEqual(n.numsites, 3)
        self.assertEqual(n.numsteps, 2)
        self.assertAlmostEqual(abs(stepids - n.get_stepids()).sum(), 0.)
        self.assertAlmostEqual(abs(times - n.get_times()).sum(), 0.)
        self.assertAlmostEqual(abs(cells - n.get_cells()).sum(), 0.)
        self.assertEqual(symbols.tolist(), n.get_symbols().tolist())
        self.assertAlmostEqual(abs(positions - n.get_positions()).sum(), 0.)
        self.assertAlmostEqual(abs(velocities - n.get_velocities()).sum(), 0.)

        # get_step_data function check
        data = n.get_step_data(1)
        self.assertEqual(data[0], stepids[1])
        self.assertAlmostEqual(data[1], times[1])
        self.assertAlmostEqual(abs(cells[1] - data[2]).sum(), 0.)
        self.assertEqual(symbols.tolist(), data[3].tolist())
        self.assertAlmostEqual(abs(data[4] - positions[1]).sum(), 0.)
        self.assertAlmostEqual(abs(data[5] - velocities[1]).sum(), 0.)

        # Step 70 has index 1
        self.assertEqual(1, n.get_index_from_stepid(70))
        with self.assertRaises(ValueError):
            # Step 66 does not exist
            n.get_index_from_stepid(66)

        ########################################################
        # I set the node, this time without times or velocities (the same node)
        n.set_trajectory(stepids=stepids, cells=cells, symbols=symbols,
                         positions=positions)
        # Generic checks
        self.assertEqual(n.numsites, 3)
        self.assertEqual(n.numsteps, 2)
        self.assertAlmostEqual(abs(stepids - n.get_stepids()).sum(), 0.)
        self.assertIsNone(n.get_times())
        self.assertAlmostEqual(abs(cells - n.get_cells()).sum(), 0.)
        self.assertEqual(symbols.tolist(), n.get_symbols().tolist())
        self.assertAlmostEqual(abs(positions - n.get_positions()).sum(), 0.)
        self.assertIsNone(n.get_velocities())

        # Same thing, but for a new node
        n = TrajectoryData()
        n.set_trajectory(stepids=stepids, cells=cells, symbols=symbols,
                         positions=positions)
        # Generic checks
        self.assertEqual(n.numsites, 3)
        self.assertEqual(n.numsteps, 2)
        self.assertAlmostEqual(abs(stepids - n.get_stepids()).sum(), 0.)
        self.assertIsNone(n.get_times())
        self.assertAlmostEqual(abs(cells - n.get_cells()).sum(), 0.)
        self.assertEqual(symbols.tolist(), n.get_symbols().tolist())
        self.assertAlmostEqual(abs(positions - n.get_positions()).sum(), 0.)
        self.assertIsNone(n.get_velocities())

        ########################################################
        # I set the node, this time without velocities (the same node)
        n.set_trajectory(stepids=stepids, cells=cells, symbols=symbols,
                         positions=positions, times=times)
        # Generic checks
        self.assertEqual(n.numsites, 3)
        self.assertEqual(n.numsteps, 2)
        self.assertAlmostEqual(abs(stepids - n.get_stepids()).sum(), 0.)
        self.assertAlmostEqual(abs(times - n.get_times()).sum(), 0.)
        self.assertAlmostEqual(abs(cells - n.get_cells()).sum(), 0.)
        self.assertEqual(symbols.tolist(), n.get_symbols().tolist())
        self.assertAlmostEqual(abs(positions - n.get_positions()).sum(), 0.)
        self.assertIsNone(n.get_velocities())

        # Same thing, but for a new node
        n = TrajectoryData()
        n.set_trajectory(stepids=stepids, cells=cells, symbols=symbols,
                         positions=positions, times=times)
        # Generic checks
        self.assertEqual(n.numsites, 3)
        self.assertEqual(n.numsteps, 2)
        self.assertAlmostEqual(abs(stepids - n.get_stepids()).sum(), 0.)
        self.assertAlmostEqual(abs(times - n.get_times()).sum(), 0.)
        self.assertAlmostEqual(abs(cells - n.get_cells()).sum(), 0.)
        self.assertEqual(symbols.tolist(), n.get_symbols().tolist())
        self.assertAlmostEqual(abs(positions - n.get_positions()).sum(), 0.)
        self.assertIsNone(n.get_velocities())

        n.store()

        # Again same checks, but after storing
        # Generic checks
        self.assertEqual(n.numsites, 3)
        self.assertEqual(n.numsteps, 2)
        self.assertAlmostEqual(abs(stepids - n.get_stepids()).sum(), 0.)
        self.assertAlmostEqual(abs(times - n.get_times()).sum(), 0.)
        self.assertAlmostEqual(abs(cells - n.get_cells()).sum(), 0.)
        self.assertEqual(symbols.tolist(), n.get_symbols().tolist())
        self.assertAlmostEqual(abs(positions - n.get_positions()).sum(), 0.)
        self.assertIsNone(n.get_velocities())

        # get_step_data function check
        data = n.get_step_data(1)
        self.assertEqual(data[0], stepids[1])
        self.assertAlmostEqual(data[1], times[1])
        self.assertAlmostEqual(abs(cells[1] - data[2]).sum(), 0.)
        self.assertEqual(symbols.tolist(), data[3].tolist())
        self.assertAlmostEqual(abs(data[4] - positions[1]).sum(), 0.)
        self.assertIsNone(data[5])

        # Step 70 has index 1
        self.assertEqual(1, n.get_index_from_stepid(70))
        with self.assertRaises(ValueError):
            # Step 66 does not exist
            n.get_index_from_stepid(66)

        ##############################################################
        # Again, but after reloading from uuid
        n = load_node(n.uuid, parent_class=TrajectoryData)
        # Generic checks
        self.assertEqual(n.numsites, 3)
        self.assertEqual(n.numsteps, 2)
        self.assertAlmostEqual(abs(stepids - n.get_stepids()).sum(), 0.)
        self.assertAlmostEqual(abs(times - n.get_times()).sum(), 0.)
        self.assertAlmostEqual(abs(cells - n.get_cells()).sum(), 0.)
        self.assertEqual(symbols.tolist(), n.get_symbols().tolist())
        self.assertAlmostEqual(abs(positions - n.get_positions()).sum(), 0.)
        self.assertIsNone(n.get_velocities())

        # get_step_data function check
        data = n.get_step_data(1)
        self.assertEqual(data[0], stepids[1])
        self.assertAlmostEqual(data[1], times[1])
        self.assertAlmostEqual(abs(cells[1] - data[2]).sum(), 0.)
        self.assertEqual(symbols.tolist(), data[3].tolist())
        self.assertAlmostEqual(abs(data[4] - positions[1]).sum(), 0.)
        self.assertIsNone(data[5])

        # Step 70 has index 1
        self.assertEqual(1, n.get_index_from_stepid(70))
        with self.assertRaises(ValueError):
            # Step 66 does not exist
            n.get_index_from_stepid(66)

    def test_conversion_to_structure(self):
        """
        Check the methods to export a given time step to a StructureData node.
        """
        from aiida.orm.data.array.trajectory import TrajectoryData
        from aiida.orm.data.structure import Kind
        import numpy

        # Create a node with two arrays
        n = TrajectoryData()

        # I create sample data
        stepids = numpy.array([60, 70])
        times = stepids * 0.01
        cells = numpy.array([
            [[2., 0., 0., ],
             [0., 2., 0., ],
             [0., 0., 2., ]],
            [[3., 0., 0., ],
             [0., 3., 0., ],
             [0., 0., 3., ]]])
        symbols = numpy.array(['H', 'O', 'C'])
        positions = numpy.array([
            [[0., 0., 0.],
             [0.5, 0.5, 0.5],
             [1.5, 1.5, 1.5]],
            [[0., 0., 0.],
             [0.5, 0.5, 0.5],
             [1.5, 1.5, 1.5]]])
        velocities = numpy.array([
            [[0., 0., 0.],
             [0., 0., 0.],
             [0., 0., 0.]],
            [[0.5, 0.5, 0.5],
             [0.5, 0.5, 0.5],
             [-0.5, -0.5, -0.5]]])

        # I set the node
        n.set_trajectory(stepids=stepids, cells=cells, symbols=symbols,
                         positions=positions, times=times,
                         velocities=velocities)

        from_step = n.get_step_structure(1)
        from_get_aiida_structure = n._get_aiida_structure(index=1)

        for struc in [from_step, from_get_aiida_structure]:
            self.assertEqual(len(struc.sites), 3)  # 3 sites
            self.assertAlmostEqual(
                abs(numpy.array(struc.cell) - cells[1]).sum(), 0)
            newpos = numpy.array([s.position for s in struc.sites])
            self.assertAlmostEqual(abs(newpos - positions[1]).sum(), 0)
            newkinds = [s.kind_name for s in struc.sites]
            self.assertEqual(newkinds, symbols.tolist())

            # Weird assignments (nobody should ever do this, but it is possible in
            # principle and we want to check
            k1 = Kind(name='C', symbols='Cu')
            k2 = Kind(name='H', symbols='He')
            k3 = Kind(name='O', symbols='Os', mass=100.)
            k4 = Kind(name='Ge', symbols='Ge')

            with self.assertRaises(ValueError):
                # Not enough kinds
                struc = n.get_step_structure(1, custom_kinds=[k1, k2])

            with self.assertRaises(ValueError):
                # Too many kinds
                struc = n.get_step_structure(1, custom_kinds=[k1, k2, k3, k4])

            with self.assertRaises(ValueError):
                # Wrong kinds
                struc = n.get_step_structure(1, custom_kinds=[k1, k2, k4])

            with self.assertRaises(ValueError):
                # Two kinds with the same name
                struc = n.get_step_structure(1, custom_kinds=[k1, k2, k3, k3])

            # Correct kinds
            struc = n.get_step_structure(1, custom_kinds=[k1, k2, k3])

            # Checks
            self.assertEqual(len(struc.sites), 3)  # 3 sites
            self.assertAlmostEqual(
                abs(numpy.array(struc.cell) - cells[1]).sum(), 0)
            newpos = numpy.array([s.position for s in struc.sites])
            self.assertAlmostEqual(abs(newpos - positions[1]).sum(), 0)
            newkinds = [s.kind_name for s in struc.sites]
            # Kinds are in the same order as given in the custm_kinds list
            self.assertEqual(newkinds, symbols.tolist())
            newatomtypes = [struc.get_kind(s.kind_name).symbols[0] for s in
                            struc.sites]
            # Atoms remain in the same order as given in the positions list
            self.assertEqual(newatomtypes, ['He', 'Os', 'Cu'])
            # Check the mass of the kind of the second atom ('O' _> symbol Os, mass 100)
            self.assertAlmostEqual(
                struc.get_kind(struc.sites[1].kind_name).mass, 100.)

    def test_conversion_from_structurelist(self):
        """
        Check the method to create a TrajectoryData from list of AiiDA
        structures.
        """
        from aiida.orm.data.structure import StructureData
        from aiida.orm.data.array.trajectory import TrajectoryData

        cells = [
            [[2., 0., 0., ],
             [0., 2., 0., ],
             [0., 0., 2., ]],
            [[3., 0., 0., ],
             [0., 3., 0., ],
             [0., 0., 3., ]]
        ]
        symbols = [['H', 'O', 'C'], ['H', 'O', 'C']]
        positions = [
            [[0., 0., 0.],
             [0.5, 0.5, 0.5],
             [1.5, 1.5, 1.5]],
            [[0., 0., 0.],
             [0.75, 0.75, 0.75],
             [1.25, 1.25, 1.25]]
        ]
        structurelist = []
        for i in range(0, 2):
            struct = StructureData(cell=cells[i])
            for j, symbol in enumerate(symbols[i]):
                struct.append_atom(symbols=symbol, position=positions[i][j])
            structurelist.append(struct)

        td = TrajectoryData(structurelist=structurelist)
        self.assertEqual(td.get_cells().tolist(), cells)
        self.assertEqual(td.get_symbols().tolist(), symbols[0])
        self.assertEqual(td.get_positions().tolist(), positions)

        symbols = [['H', 'O', 'C'], ['H', 'O', 'P']]
        structurelist = []
        for i in range(0, 2):
            struct = StructureData(cell=cells[i])
            for j, symbol in enumerate(symbols[i]):
                struct.append_atom(symbols=symbol, position=positions[i][j])
            structurelist.append(struct)

        with self.assertRaises(ValueError):
            td = TrajectoryData(structurelist=structurelist)

    def test_export_to_file(self):
        """
        Export the band structure on a file, check if it is working
        """
        import numpy
        import os
        import tempfile
        from aiida.orm.data.array.trajectory import TrajectoryData

        n = TrajectoryData()

        # I create sample data
        stepids = numpy.array([60, 70])
        times = stepids * 0.01
        cells = numpy.array([
            [[2., 0., 0., ],
             [0., 2., 0., ],
             [0., 0., 2., ]],
            [[3., 0., 0., ],
             [0., 3., 0., ],
             [0., 0., 3., ]]])
        symbols = numpy.array(['H', 'O', 'C'])
        positions = numpy.array([
            [[0., 0., 0.],
             [0.5, 0.5, 0.5],
             [1.5, 1.5, 1.5]],
            [[0., 0., 0.],
             [0.5, 0.5, 0.5],
             [1.5, 1.5, 1.5]]])
        velocities = numpy.array([
            [[0., 0., 0.],
             [0., 0., 0.],
             [0., 0., 0.]],
            [[0.5, 0.5, 0.5],
             [0.5, 0.5, 0.5],
             [-0.5, -0.5, -0.5]]])

        # I set the node
        n.set_trajectory(stepids=stepids, cells=cells, symbols=symbols,
                         positions=positions, times=times,
                         velocities=velocities)


        # define a cell
        alat = 4.
        cell = numpy.array([[alat, 0., 0.],
                            [0., alat, 0.],
                            [0., 0., alat],
                            ])


        # It is not obvious how to check that the bands are correct.
        # I just check, for a few formats, that the file is correctly
        # created, at this stage
        ## I use this to get a file. I then close it and ask the .export() function
        ## to create it again. I have to remember to delete everything at the end.
        handle, filename = tempfile.mkstemp()
        os.close(handle)
        os.remove(filename)

        for format in ['cif', 'xsf']:
            files_created = [] # In case there is an exception
            try:
                files_created = n.export(filename, fileformat=format)
                with open(filename) as f:
                    filedata = f.read()
            finally:
                for file in files_created:
                    if os.path.exists(file):
                        os.remove(file)


class TestKpointsData(AiidaTestCase):
    """
    Tests the TrajectoryData objects.
    """

    # TODO: I should find a way to check the special points, case by case

    def test_mesh(self):
        """
        Check the methods to set and retrieve a mesh.
        """
        from aiida.orm.data.array.kpoints import KpointsData

        # Create a node with two arrays
        k = KpointsData()

        # check whether the mesh can be set properly
        input_mesh = [4, 4, 4]
        k.set_kpoints_mesh(input_mesh)
        mesh, offset = k.get_kpoints_mesh()
        self.assertEqual(mesh, list(input_mesh))
        self.assertEqual(offset,
                         [0., 0., 0.])  # must be a tuple of three 0 by default

        # a too long list should fail
        with self.assertRaises(ValueError):
            k.set_kpoints_mesh([4, 4, 4, 4])

        # now try to put explicitely an offset
        input_offset = [0.5, 0.5, 0.5]
        k.set_kpoints_mesh(input_mesh, input_offset)
        mesh, offset = k.get_kpoints_mesh()
        self.assertEqual(mesh, list(input_mesh))
        self.assertEqual(offset, list(input_offset))

        # verify the same but after storing
        k.store()
        self.assertEqual(mesh, list(input_mesh))
        self.assertEqual(offset, list(input_offset))

        # cannot modify it after storage
        with self.assertRaises(ModificationNotAllowed):
            k.set_kpoints_mesh(input_mesh)

    def test_list(self):
        """
        Test the method to set and retrieve a kpoint list.
        """
        from aiida.orm.data.array.kpoints import KpointsData
        import numpy

        k = KpointsData()

        input_klist = numpy.array([(0.0, 0.0, 0.0),
                                   (0.2, 0.0, 0.0),
                                   (0.0, 0.2, 0.0),
                                   (0.0, 0.0, 0.2),
                                   ])

        # set kpoints list
        k.set_kpoints(input_klist)
        klist = k.get_kpoints()

        # try to get the same
        self.assertTrue(numpy.array_equal(input_klist, klist))

        # if no cell is set, cannot convert into cartesian
        with self.assertRaises(AttributeError):
            _ = k.get_kpoints(cartesian=True)

        # try to set also weights
        # should fail if the weights length do not match kpoints
        input_weights = numpy.ones(6)
        with self.assertRaises(ValueError):
            k.set_kpoints(input_klist, weights=input_weights)

        # try a right one
        input_weights = numpy.ones(4)
        k.set_kpoints(input_klist, weights=input_weights)
        klist, weights = k.get_kpoints(also_weights=True)
        self.assertTrue(numpy.array_equal(weights, input_weights))
        self.assertTrue(numpy.array_equal(klist, input_klist))

        # verify the same, but after storing
        k.store()
        klist, weights = k.get_kpoints(also_weights=True)
        self.assertTrue(numpy.array_equal(weights, input_weights))
        self.assertTrue(numpy.array_equal(klist, input_klist))

        # cannot modify it after storage
        with self.assertRaises(ModificationNotAllowed):
            k.set_kpoints(input_klist)

    def test_kpoints_to_cartesian(self):
        """
        Test how the list of kpoints is converted to cartesian coordinates
        """
        from aiida.orm.data.array.kpoints import KpointsData
        import numpy

        k = KpointsData()

        input_klist = numpy.array([(0.0, 0.0, 0.0),
                                   (0.2, 0.0, 0.0),
                                   (0.0, 0.2, 0.0),
                                   (0.0, 0.0, 0.2),
                                   ])

        # define a cell
        alat = 4.
        cell = numpy.array([[alat, 0., 0.],
                            [0., alat, 0.],
                            [0., 0., alat],
                            ])

        k.set_cell(cell)

        # set kpoints list
        k.set_kpoints(input_klist)

        # verify that it is not the same of the input
        # (at least I check that there something has been done)
        klist = k.get_kpoints(cartesian=True)
        self.assertFalse(numpy.array_equal(klist, input_klist))

        # put the kpoints in cartesian and get them back, they should be equal
        # internally it is doing two matrix transforms
        k.set_kpoints(input_klist, cartesian=True)
        klist = k.get_kpoints(cartesian=True)
        self.assertTrue(numpy.allclose(klist, input_klist, atol=1e-16))

    def test_path(self):
        """
        Test the methods to generate automatically a list of kpoints
        """
        from aiida.orm.data.array.kpoints import KpointsData
        import numpy
        
        k = KpointsData()
        
        # shouldn't get anything wiothout having set the cell
        with self.assertRaises(ValueError):
            k.set_kpoints_path()
        
        # define a cell
        alat = 4.
        cell = numpy.array([[alat, 0., 0.],
                            [0., alat, 0.],
                            [0., 0., alat],
                            ])
        
        k.set_cell(cell)
        k.set_kpoints_path()
        # something should be retrieved
        klist = k.get_kpoints()
        
        # test the various formats for specifying the path
        k.set_kpoints_path([('G','M'),
                            ])
        k.set_kpoints_path([('G','M',30),
                            ])
        k.set_kpoints_path([('G',(0.,0.,0.),'M',(1.,1.,1.)),
                            ])
        k.set_kpoints_path([('G',(0.,0.,0.),'M',(1.,1.,1.),30),
                            ])

        # at least 2 points per segment
        with self.assertRaises(ValueError):
            k.set_kpoints_path([('G','M',1),
                                ])
        with self.assertRaises(ValueError):
            k.set_kpoints_path([('G',(0.,0.,0.),'M',(1.,1.,1.),1),
                                ])
        
        # try to set points with a spacing
        k.set_kpoints_path(kpoint_distance=0.1)
        
        # try to modify after storage
        k.store()
        with self.assertRaises(ModificationNotAllowed):
            k.set_kpoints_path()

    def test_tetra_x(self):
      """
      testing tetragonal cells with axis along X
      """
      import numpy
      from aiida.orm import DataFactory
      alat = 1.5
      cell_x = [[alat,0,0],[0,1,0],[0,0,1]]
      K = DataFactory('array.kpoints')
      k = K()
      k.set_cell(cell_x)
      points = k.get_special_points(cartesian=True)

      self.assertAlmostEqual(points[0]['Z'][0], numpy.pi/alat )
      self.assertAlmostEqual(points[0]['Z'][1], 0.)

    def test_tetra_z(self):
      """
      testing tetragonal cells with axis along X
      """
      import numpy
      from aiida.orm import DataFactory
      alat = 1.5
      cell_x = [[1,0,0],[0,1,0],[0,0,alat]]
      K = DataFactory('array.kpoints')
      k = K()
      k.set_cell(cell_x)
      points = k.get_special_points(cartesian=True)

      self.assertAlmostEqual(points[0]['Z'][2], numpy.pi/alat )
      self.assertAlmostEqual(points[0]['Z'][0], 0.)

            
class TestBandsData(AiidaTestCase):
    """
    Tests the BandsData objects.
    """
    
    def test_band(self):
        """
        Check the methods to set and retrieve a mesh.
        """
        from aiida.orm.data.array.bands import BandsData
        from aiida.orm.data.array.kpoints import KpointsData
        import numpy
        
        # define a cell
        alat = 4.
        cell = numpy.array([[alat, 0., 0.],
                            [0., alat, 0.],
                            [0., 0., alat],
                            ])
        
        k = KpointsData()
        k.set_cell(cell)
        k.set_kpoints_path()
        
        b = BandsData()
        b.set_kpointsdata(k)
        self.assertTrue( numpy.array_equal(b.cell,k.cell) )
        
        input_bands = numpy.array([numpy.ones(4) for i in range(k.get_kpoints().shape[0]) ]) 
        input_occupations = input_bands
        
        b.set_bands(input_bands, occupations=input_occupations, units='ev')
        b.set_bands(input_bands, units='ev')
        b.set_bands(input_bands, occupations=input_occupations)
        with self.assertRaises(TypeError):
            b.set_bands(occupations=input_occupations, units='ev')
        
        b.set_bands(input_bands, occupations=input_occupations, units='ev')
        bands,occupations = b.get_bands(also_occupations=True)
        
        self.assertTrue( numpy.array_equal(bands,input_bands) )
        self.assertTrue( numpy.array_equal(occupations,input_occupations) )
        self.assertTrue( b.units=='ev' )
        
        b.store()
        with self.assertRaises(ModificationNotAllowed):
            b.set_bands(bands)

    def test_export_to_file(self):
        """
        Export the band structure on a file, check if it is working
        """
        import numpy
        import os
        import tempfile
        from aiida.orm.data.array.bands import BandsData
        from aiida.orm.data.array.kpoints import KpointsData

        # define a cell
        alat = 4.
        cell = numpy.array([[alat, 0., 0.],
                            [0., alat, 0.],
                            [0., 0., alat],
                            ])

        k = KpointsData()
        k.set_cell(cell)
        k.set_kpoints_path()

        b = BandsData()
        b.set_kpointsdata(k)

        # 4 bands with linearly increasing energies, it does not make sense
        # but is good for testing
        input_bands = numpy.array([numpy.ones(4)*i for i in range(k.get_kpoints().shape[0]) ])

        b.set_bands(input_bands, units='eV')

        # It is not obvious how to check that the bands are correct.
        # I just check, for a few formats, that the file is correctly
        # created, at this stage
        ## I use this to get a file. I then close it and ask the .export() function
        ## to create it again. I have to remember to delete everything at the end.
        handle, filename = tempfile.mkstemp()
        os.close(handle)
        os.remove(filename)

        for format in ['agr', 'agr_batch', 'json', 'mpl_singlefile',
                       'dat_blocks', 'dat_multicolumn']:
            files_created = [] # In case there is an exception
            try:
                files_created = b.export(filename, fileformat=format)
                with open(filename) as f:
                    filedata = f.read()
            finally:
                for file in files_created:
                    if os.path.exists(file):
                        os.remove(file)


# class TestData(AiidaTestCase):
#     """
#     Tests generic Data class.
#     """
# 
#     "Validation for source is disabled due to Issue #9 on https://bitbucket.org/epfl_theos/aiida_epfl/issues/9"
#     def test_license_validation(self):
#         """
#         Test the validation of source licenses.
#         """
#         from aiida.orm.data import Data
# 
#         data = Data(source={'license': 'CC0'})
#         data.store()
# 
#         data = Data(source={'license': 'CC-BY-SA'})
#         # CC-BY* type licenses must be accompanied by attribution, given
#         # in 'description' key of source dictionary. This is enforced in
#         # Data._validate(), thus the ValidationError.
#         with self.assertRaises(ValidationError):
#             data.store()
#
