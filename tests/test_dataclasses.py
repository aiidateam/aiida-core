###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# ruff: noqa: N806
"""Tests for specific subclasses of Data."""

import os
import tempfile

import numpy as np
import pytest

from aiida.common.exceptions import ModificationNotAllowed
from aiida.common.utils import Capturing
from aiida.orm import ArrayData, BandsData, CifData, Dict, KpointsData, StructureData, TrajectoryData, load_node
from aiida.orm.nodes.data.cif import has_pycifrw
from aiida.orm.nodes.data.structure import (
    Kind,
    Site,
    _atomic_masses,
    ase_refine_cell,
    get_formula,
    has_ase,
    has_atomistic,
    has_pymatgen,
    has_spglib,
)


def has_seekpath():
    """Check if there is the seekpath dependency

    :return: True if seekpath is installed, False otherwise
    """
    try:
        import seekpath  # noqa: F401

        return True
    except ImportError:
        return False


def to_list_of_lists(lofl):
    """Converts an iterable of iterables to a list of lists, needed
    for some tests (e.g. when one has a tuple of lists, a list of tuples, ...)

    :param lofl: an iterable of iterables

    :return: a list of lists
    """
    return [[el for el in lst] for lst in lofl]


def simplify(string):
    """Takes a string, strips spaces in each line and returns it
    Useful to compare strings when different versions of a code give
    different spaces.
    """
    return '\n'.join(s.strip() for s in string.split())


skip_ase = pytest.mark.skipif(not has_ase(), reason='Unable to import ase')
skip_spglib = pytest.mark.skipif(not has_spglib(), reason='Unable to import spglib')
skip_pycifrw = pytest.mark.skipif(not has_pycifrw(), reason='Unable to import PyCifRW')
skip_pymatgen = pytest.mark.skipif(not has_pymatgen(), reason='Unable to import pymatgen')
skip_atomistic = pytest.mark.skipif(not has_atomistic(), reason='Unable to import aiida-atomistic')


class TestCifData:
    """Tests for CifData class."""

    valid_sample_cif_str = """
        data_test
        _cell_length_a    10
        _cell_length_b    10
        _cell_length_c    10
        _cell_angle_alpha 90
        _cell_angle_beta  90
        _cell_angle_gamma 90
        _chemical_formula_sum 'C O2'
        loop_
        _atom_site_label
        _atom_site_fract_x
        _atom_site_fract_y
        _atom_site_fract_z
        _atom_site_attached_hydrogens
        C 0 0 0 0
        O 0.5 0.5 0.5 .
        H 0.75 0.75 0.75 0
    """

    valid_sample_cif_str_2 = """
        data_test
        _cell_length_a    10
        _cell_length_b    10
        _cell_length_c    10
        _cell_angle_alpha 90
        _cell_angle_beta  90
        _cell_angle_gamma 90
        _chemical_formula_sum 'C O'
        loop_
        _atom_site_label
        _atom_site_fract_x
        _atom_site_fract_y
        _atom_site_fract_z
        _atom_site_attached_hydrogens
        C 0 0 0 0
        O 0.5 0.5 0.5 .
    """

    @skip_pycifrw
    def test_reload_cifdata(self):
        """Test `CifData` cycle."""
        file_content = 'data_test _cell_length_a 10(1)'
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            filename = tmpf.name
            basename = os.path.split(filename)[1]
            tmpf.write(file_content)
            tmpf.flush()
            a = CifData(file=filename, source={'version': '1234', 'db_name': 'COD', 'id': '0000001'})

        # Key 'db_kind' is not allowed in source description:
        with pytest.raises(KeyError):
            a.source = {'db_kind': 'small molecule'}

        the_uuid = a.uuid

        assert a.base.repository.list_object_names() == [basename]

        with a.open() as fhandle:
            assert fhandle.read() == file_content

        a.store()

        assert a.source == {
            'db_name': 'COD',
            'id': '0000001',
            'version': '1234',
        }

        with a.open() as fhandle:
            assert fhandle.read() == file_content
        assert a.base.repository.list_object_names() == [basename]

        b = load_node(the_uuid)

        # I check the retrieved object
        assert isinstance(b, CifData)
        assert b.base.repository.list_object_names() == [basename]
        with b.open() as fhandle:
            assert fhandle.read() == file_content

        # Checking the get_or_create() method:
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(file_content)
            tmpf.flush()
            c, created = CifData.get_or_create(tmpf.name, store_cif=False)

        assert isinstance(c, CifData)
        assert not created
        assert c.get_content() == file_content

        other_content = 'data_test _cell_length_b 10(1)'
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(other_content)
            tmpf.flush()
            c, created = CifData.get_or_create(tmpf.name, store_cif=False)

        assert isinstance(c, CifData)
        assert created
        assert c.get_content() == other_content

    @skip_pycifrw
    def test_parse_cifdata(self):
        """Test parsing a CIF file."""
        file_content = 'data_test _cell_length_a 10(1)'
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(file_content)
            tmpf.flush()
            a = CifData(file=tmpf.name)

        assert list(a.values.keys()) == ['test']

    @skip_pycifrw
    def test_change_cifdata_file(self):
        """Test changing file for `CifData` before storing."""
        file_content_1 = 'data_test _cell_length_a 10(1)'
        file_content_2 = 'data_test _cell_length_a 11(1)'
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(file_content_1)
            tmpf.flush()
            a = CifData(file=tmpf.name)

        assert a.values['test']['_cell_length_a'] == '10(1)'

        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(file_content_2)
            tmpf.flush()
            a.set_file(tmpf.name)

        assert a.values['test']['_cell_length_a'] == '11(1)'

    @skip_ase
    @skip_pycifrw
    @pytest.mark.requires_rmq
    @pytest.mark.filterwarnings('ignore:Cannot determine chemical composition from CIF:UserWarning:pymatgen.io')
    def test_get_structure(self):
        """Test `CifData.get_structure`."""
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(
                """
data_test
_cell_length_a    10
_cell_length_b    10
_cell_length_c    10
_cell_angle_alpha 90
_cell_angle_beta  90
_cell_angle_gamma 90
loop_
_symmetry_equiv_pos_site_id
_symmetry_equiv_pos_as_xyz
1 +x,+y,+z
loop_
_atom_site_label
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
C 0 0 0
O 0.5 0.5 0.5
            """
            )
            tmpf.flush()
            a = CifData(file=tmpf.name)

        with pytest.raises(ValueError):
            a.get_structure(converter='none')

        c = a.get_structure()

        assert c.get_kind_names() == ['C', 'O']

    @skip_ase
    @skip_pycifrw
    @pytest.mark.requires_rmq
    def test_ase_primitive_and_conventional_cells_ase(self):
        """Checking the number of atoms per primitive/conventional cell
        returned by ASE ase.io.read() method. Test input is
        adapted from http://www.crystallography.net/cod/9012064.cif@120115
        """

        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(
                """
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
            """
            )
            tmpf.flush()
            c = CifData(file=tmpf.name)

        assert c.get_structure(converter='ase', primitive_cell=False).get_ase().get_global_number_of_atoms() == 15
        assert c.get_structure(converter='ase').get_ase().get_global_number_of_atoms() == 15

        structure = c.get_structure(converter='ase', primitive_cell=True, subtrans_included=False)
        assert structure.get_ase().get_global_number_of_atoms() == 5

    @skip_ase
    @skip_pycifrw
    @skip_pymatgen
    @pytest.mark.requires_rmq
    @pytest.mark.filterwarnings('ignore:Cannot determine chemical composition from CIF:UserWarning:pymatgen.io')
    def test_ase_primitive_and_conventional_cells_pymatgen(self):
        """Checking the number of atoms per primitive/conventional cell
        returned by ASE ase.io.read() method. Test input is
        adapted from http://www.crystallography.net/cod/9012064.cif@120115
        """
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(
                """
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
_symmetry_equiv_pos_as_xyz
x,y,z
2/3+x,1/3+y,1/3+z
1/3+x,2/3+y,2/3+z
x,x-y,z
2/3+x,1/3+x-y,1/3+z
1/3+x,2/3+x-y,2/3+z
y,x,-z
2/3+y,1/3+x,1/3-z
1/3+y,2/3+x,2/3-z
-x+y,y,z
loop_
_atom_site_label
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_site_U_iso_or_equiv
Bi 0.00000 0.00000 0.40046 0.02330
Te1 0.00000 0.00000 0.00000 0.01748
Te2 0.00000 0.00000 0.79030 0.01912
            """
            )
            tmpf.flush()
            c = CifData(file=tmpf.name)

        ase = c.get_structure(converter='pymatgen', primitive_cell=False).get_ase()
        assert ase.get_global_number_of_atoms() == 15

        ase = c.get_structure(converter='pymatgen').get_ase()
        assert ase.get_global_number_of_atoms() == 15

        ase = c.get_structure(converter='pymatgen', primitive_cell=True).get_ase()
        assert ase.get_global_number_of_atoms() == 5

    @skip_pycifrw
    def test_pycifrw_from_datablocks(self):
        """Tests CifData.pycifrw_from_cif()"""
        import re

        from aiida.orm.nodes.data.cif import pycifrw_from_cif

        datablocks = [
            {
                '_atom_site_label': ['A', 'B', 'C'],
                '_atom_site_occupancy': [1.0, 0.5, 0.5],
                '_publ_section_title': 'Test CIF',
            }
        ]
        with Capturing():
            lines = pycifrw_from_cif(datablocks).WriteOut().split('\n')
        non_comments = []
        for line in lines:
            if not re.search('^#', line):
                non_comments.append(line)
        assert simplify('\n'.join(non_comments)) == simplify(
            """
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
"""
        )

        loops = {'_atom_site': ['_atom_site_label', '_atom_site_occupancy']}
        with Capturing():
            lines = pycifrw_from_cif(datablocks, loops).WriteOut().split('\n')
        non_comments = []
        for line in lines:
            if not re.search('^#', line):
                non_comments.append(line)
        assert simplify('\n'.join(non_comments)) == simplify(
            """
data_0
loop_
  _atom_site_label
  _atom_site_occupancy
   A  1.0
   B  0.5
   C  0.5

_publ_section_title                     'Test CIF'
"""
        )

    @skip_pycifrw
    def test_pycifrw_syntax(self):
        """Tests CifData.pycifrw_from_cif() - check syntax pb in PyCifRW 3.6."""
        import re

        from aiida.orm.nodes.data.cif import pycifrw_from_cif

        datablocks = [
            {
                '_tag': '[value]',
            }
        ]
        with Capturing():
            lines = pycifrw_from_cif(datablocks).WriteOut().split('\n')
        non_comments = []
        for line in lines:
            if not re.search('^#', line):
                non_comments.append(line)
        assert simplify('\n'.join(non_comments)) == simplify(
            """
data_0
_tag                                    '[value]'
"""
        )

    @skip_pycifrw
    @staticmethod
    def test_cif_with_long_line():
        """Tests CifData - check that long lines (longer than 2048 characters) are supported.
        Should not raise any error.
        """
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(
                f"""
data_0
_tag   {'a' * 5000}
 """
            )
            tmpf.flush()
            _ = CifData(file=tmpf.name)

    @skip_ase
    @skip_pycifrw
    def test_cif_roundtrip(self):
        """Test the `CifData` roundtrip."""
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(
                """
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
            """
            )
            tmpf.flush()
            a = CifData(file=tmpf.name)

        b = CifData(values=a.values)
        c = CifData(values=b.values)
        assert b._prepare_cif() == c._prepare_cif()

        b = CifData(ase=a.ase)
        c = CifData(ase=b.ase)
        assert b._prepare_cif() == c._prepare_cif()

    def test_symop_string_from_symop_matrix_tr(self):
        """Test symmetry operations."""
        from aiida.tools.data.cif import symop_string_from_symop_matrix_tr

        assert symop_string_from_symop_matrix_tr([[1, 0, 0], [0, 1, 0], [0, 0, 1]]) == 'x,y,z'

        assert symop_string_from_symop_matrix_tr([[1, 0, 0], [0, -1, 0], [0, 1, 1]]) == 'x,-y,y+z'

        assert symop_string_from_symop_matrix_tr([[-1, 0, 0], [0, 1, 0], [0, 0, 1]], [1, -1, 0]) == '-x+1,y-1,z'

    @skip_ase
    @skip_pycifrw
    def test_attached_hydrogens(self):
        """Test parsing of file with attached hydrogens."""
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(
                """
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
            """
            )
            tmpf.flush()
            a = CifData(file=tmpf.name)

        assert a.has_attached_hydrogens is False

        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(
                """
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
            """
            )
            tmpf.flush()
            a = CifData(file=tmpf.name)

        assert a.has_attached_hydrogens is True

    @skip_ase
    @skip_pycifrw
    @skip_spglib
    @pytest.mark.requires_rmq
    def test_refine(self):
        """Test case for refinement (space group determination) for a
        CifData object.
        """
        from aiida.tools.data.cif import refine_inline

        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(
                """
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
            """
            )
            tmpf.flush()
            a = CifData(file=tmpf.name)

        ret_dict = refine_inline(a)
        b = ret_dict['cif']
        assert list(b.values.keys()) == ['test']
        assert b.values['test']['_chemical_formula_sum'] == 'C O2'
        assert b.values['test']['_symmetry_equiv_pos_as_xyz'] == [
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
            '-y,-x,z',
        ]

        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(
                """
                data_a
                data_b
            """
            )
            tmpf.flush()
            c = CifData(file=tmpf.name)

        with pytest.raises(ValueError):
            ret_dict = refine_inline(c)

    @skip_pycifrw
    def test_scan_type(self):
        """Check that different scan_types of PyCifRW produce the same result."""
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(self.valid_sample_cif_str)
            tmpf.flush()

            default = CifData(file=tmpf.name)
            default2 = CifData(file=tmpf.name, scan_type='standard')
            assert default._prepare_cif() == default2._prepare_cif()

            flex = CifData(file=tmpf.name, scan_type='flex')
            assert default._prepare_cif() == flex._prepare_cif()

    @skip_pycifrw
    def test_empty_cif(self):
        """Test empty CifData

        Note: This test does not need PyCifRW.
        """
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(self.valid_sample_cif_str)
            tmpf.flush()

            # empty cifdata should be possible
            a = CifData()

            # but it does not have a file
            with pytest.raises(AttributeError):
                _ = a.filename

            # now it has
            a.set_file(tmpf.name)
            _ = a.filename

            a.store()

    @skip_pycifrw
    def test_parse_policy(self):
        """Test that loading of CIF file occurs as defined by parse_policy."""
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(self.valid_sample_cif_str)
            tmpf.flush()

            # this will parse the cif
            eager = CifData(file=tmpf.name, parse_policy='eager')
            assert eager._values is not None

            # this should not parse the cif
            lazy = CifData(file=tmpf.name, parse_policy='lazy')
            assert lazy._values is None

            # also lazy-loaded nodes should be storable
            lazy.store()

            # this should parse the cif
            _ = lazy.values
            assert lazy._values is not None

    @skip_pycifrw
    def test_set_file(self):
        """Test that setting a new file clears formulae and spacegroups."""
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(self.valid_sample_cif_str)
            tmpf.flush()

            a = CifData(file=tmpf.name)
            f1 = a.get_formulae()
            assert f1 is not None

        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(self.valid_sample_cif_str_2)
            tmpf.flush()

            # this should reset formulae and spacegroup_numbers
            a.set_file(tmpf.name)
            assert a.base.attributes.get('formulae') is None
            assert a.base.attributes.get('spacegroup_numbers') is None

            # this should populate formulae
            a.parse()
            f2 = a.get_formulae()
            assert f2 is not None

            # empty cifdata should be possible
            a = CifData()
            # but it does not have a file
            with pytest.raises(AttributeError):
                _ = a.filename
            # now it has
            a.set_file(tmpf.name)
            a.parse()
            _ = a.filename

        assert f1 != f2

    @skip_pycifrw
    def test_has_partial_occupancies(self):
        """Test structure with partial occupancies."""
        tests = [
            # Unreadable occupations should not count as a partial occupancy
            ('O 0.5 0.5(1) 0.5 ?', False),
            # The default epsilon for deviation of unity for an occupation to be considered partial is 1E-6
            ('O 0.5 0.5(1) 0.5 1.0(000000001)', False),
            # Partial occupancies should be able to deal with parentheses in the value
            ('O 0.5 0.5(1) 0.5 1.0(000132)', True),
            # Partial occupancies should be able to deal with parentheses in the value
            ('O 0.5 0.5(1) 0.5 0.9(0000132)', True),
        ]

        for test_string, result in tests:
            with tempfile.NamedTemporaryFile(mode='w+') as handle:
                handle.write(
                    f"""
                    data_test
                    loop_
                    _atom_site_label
                    _atom_site_fract_x
                    _atom_site_fract_y
                    _atom_site_fract_z
                    _atom_site_occupancy
                    {test_string}
                """
                )
                handle.flush()
                cif = CifData(file=handle.name)
                assert cif.has_partial_occupancies == result

    @skip_pycifrw
    def test_has_unknown_species(self):
        """Test structure with unknown species."""
        tests = [
            ('H2 O', False),  # No unknown species
            ('OsAx', True),  # Ax is an unknown specie
            ('UX', True),  # X counts as unknown specie despite being defined in aiida.common.constants.elements
            ('', None),  # If no chemical formula is defined, None should be returned
        ]

        for formula, result in tests:
            with tempfile.NamedTemporaryFile(mode='w+') as handle:
                formula_string = f"_chemical_formula_sum '{formula}'" if formula else '\n'
                handle.write(f"""data_test\n{formula_string}\n""")
                handle.flush()
                cif = CifData(file=handle.name)
                assert cif.has_unknown_species == result, formula_string

    @skip_pycifrw
    def test_has_undefined_atomic_sites(self):
        """Test structure with undefined atomic sites."""
        tests = [
            ('C 0.0 0.0 0.0', False),  # Should return False because all sites have valid coordinates
            ('C 0.0 0.0 ?', True),  # Should return True because one site has an undefined coordinate
            ('', True),  # Should return True if no sites defined at all
        ]

        for test_string, result in tests:
            with tempfile.NamedTemporaryFile(mode='w+') as handle:
                base = 'loop_\n_atom_site_label\n_atom_site_fract_x\n_atom_site_fract_y\n_atom_site_fract_z'
                atomic_site_string = f'{base}\n{test_string}' if test_string else ''
                handle.write(f"""data_test\n{atomic_site_string}\n""")
                handle.flush()
                cif = CifData(file=handle.name)
                assert cif.has_undefined_atomic_sites == result


class TestKindValidSymbols:
    """Tests the symbol validation of the aiida.orm.nodes.data.structure.Kind class."""

    def test_bad_symbol(self):
        """Should not accept a non-existing symbol."""
        with pytest.raises(ValueError):
            Kind(symbols='Hxx')

    def test_empty_list_symbols(self):
        """Should not accept an empty list."""
        with pytest.raises(ValueError):
            Kind(symbols=[])

    @staticmethod
    def test_valid_list():
        """Should not raise any error."""
        Kind(symbols=['H', 'He'], weights=[0.5, 0.5])

    @staticmethod
    def test_unknown_symbol():
        """Should test if symbol X is valid and defined in the elements dictionary."""
        Kind(symbols=['X'])


class TestSiteValidWeights:
    """Tests valid weight lists."""

    def test_isnot_list(self):
        """Should not accept a non-list, non-number weight."""
        with pytest.raises(ValueError):
            Kind(symbols='Ba', weights='aaa')

    def test_empty_list_weights(self):
        """Should not accept an empty list."""
        with pytest.raises(ValueError):
            Kind(symbols='Ba', weights=[])

    def test_symbol_weight_mismatch(self):
        """Should not accept a size mismatch of the symbols and weights list."""
        with pytest.raises(ValueError):
            Kind(symbols=['Ba', 'C'], weights=[1.0])

        with pytest.raises(ValueError):
            Kind(symbols=['Ba'], weights=[0.1, 0.2])

    def test_negative_value(self):
        """Should not accept a negative weight."""
        with pytest.raises(ValueError):
            Kind(symbols=['Ba', 'C'], weights=[-0.1, 0.3])

    def test_sum_greater_one(self):
        """Should not accept a sum of weights larger than one."""
        with pytest.raises(ValueError):
            Kind(symbols=['Ba', 'C'], weights=[0.5, 0.6])

    @staticmethod
    def test_sum_one_weights():
        """Should accept a sum equal to one."""
        Kind(symbols=['Ba', 'C'], weights=[1.0 / 3.0, 2.0 / 3.0])

    @staticmethod
    def test_sum_less_one_weights():
        """Should accept a sum equal less than one."""
        Kind(symbols=['Ba', 'C'], weights=[1.0 / 3.0, 1.0 / 3.0])

    @staticmethod
    def test_none():
        """Should accept None."""
        Kind(symbols='Ba', weights=None)


class TestKindTestGeneral:
    """Tests the creation of Kind objects and their methods."""

    def test_sum_one_general(self):
        """Should accept a sum equal to one."""
        a = Kind(symbols=['Ba', 'C'], weights=[1.0 / 3.0, 2.0 / 3.0])
        assert a.is_alloy
        assert not a.has_vacancies

    def test_sum_less_one_general(self):
        """Should accept a sum equal less than one."""
        a = Kind(symbols=['Ba', 'C'], weights=[1.0 / 3.0, 1.0 / 3.0])
        assert a.is_alloy
        assert a.has_vacancies

    def test_no_position(self):
        """Should not accept a 'positions' parameter."""
        with pytest.raises(ValueError):
            Kind(position=[0.0, 0.0, 0.0], symbols=['Ba'], weights=[1.0])

    def test_simple(self):
        """Should recognize a simple element."""
        a = Kind(symbols='Ba')
        assert not a.is_alloy
        assert not a.has_vacancies

        b = Kind(symbols='Ba', weights=1.0)
        assert not b.is_alloy
        assert not b.has_vacancies

        c = Kind(symbols='Ba', weights=None)
        assert not c.is_alloy
        assert not c.has_vacancies

    def test_automatic_name(self):
        """Check the automatic name generator."""
        a = Kind(symbols='Ba')
        assert a.name == 'Ba'

        a = Kind(symbols='X')
        assert a.name == 'X'

        a = Kind(symbols=('Si', 'Ge'), weights=(1.0 / 3.0, 2.0 / 3.0))
        assert a.name == 'GeSi'

        a = Kind(symbols=('Si', 'X'), weights=(1.0 / 3.0, 2.0 / 3.0))
        assert a.name == 'SiX'

        a = Kind(symbols=('Si', 'Ge'), weights=(0.4, 0.5))
        assert a.name == 'GeSiX'

        a = Kind(symbols=('Si', 'X'), weights=(0.4, 0.5))
        assert a.name == 'SiXX'

        # Manually setting the name of the species
        a.name = 'newstring'
        assert a.name == 'newstring'


class TestKindTestMasses:
    """Tests the management of masses during the creation of Kind objects."""

    def test_auto_mass_one(self):
        """Mass for elements with sum one"""
        a = Kind(symbols=['Ba', 'C'], weights=[1.0 / 3.0, 2.0 / 3.0])
        assert round(abs(a.mass - (_atomic_masses['Ba'] + 2.0 * _atomic_masses['C']) / 3.0), 7) == 0

    def test_sum_less_one_masses(self):
        """Mass for elements with sum less than one"""
        a = Kind(symbols=['Ba', 'C'], weights=[1.0 / 3.0, 1.0 / 3.0])
        assert round(abs(a.mass - (_atomic_masses['Ba'] + _atomic_masses['C']) / 2.0), 7) == 0

    def test_sum_less_one_singleelem(self):
        """Mass for a single element"""
        a = Kind(symbols=['Ba'])
        assert round(abs(a.mass - _atomic_masses['Ba']), 7) == 0

    def test_manual_mass(self):
        """Mass set manually"""
        a = Kind(symbols=['Ba', 'C'], weights=[1.0 / 3.0, 1.0 / 3.0], mass=1000.0)
        assert round(abs(a.mass - 1000.0), 7) == 0


class TestStructureDataInit:
    """Tests the creation of StructureData objects (cell and pbc)."""

    def test_cell_wrong_size_1(self):
        """Wrong cell size (not 3x3)"""
        with pytest.raises(ValueError):
            StructureData(cell=((1.0, 2.0, 3.0),))

    def test_cell_wrong_size_2(self):
        """Wrong cell size (not 3x3)"""
        with pytest.raises(ValueError):
            StructureData(cell=((1.0, 0.0, 0.0), (0.0, 0.0, 3.0), (0.0, 3.0)))

    def test_cell_zero_vector(self):
        """Wrong cell (one vector has zero length)"""
        with pytest.raises(ValueError):
            StructureData(cell=((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))).store()

    def test_cell_zero_volume(self):
        """Wrong cell (volume is zero)"""
        with pytest.raises(ValueError):
            StructureData(cell=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0))).store()

    def test_cell_ok_init(self):
        """Correct cell"""
        cell = ((1.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 3.0))
        a = StructureData(cell=cell)
        out_cell = a.cell

        for i in range(3):
            for j in range(3):
                assert round(abs(cell[i][j] - out_cell[i][j]), 7) == 0

    def test_volume(self):
        """Check the volume calculation"""
        a = StructureData(cell=((1.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 3.0)))
        assert round(abs(a.get_cell_volume() - 6.0), 7) == 0

    def test_wrong_pbc_1(self):
        """Wrong pbc parameter (not bool or iterable)"""
        with pytest.raises(ValueError):
            cell = ((1.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 3.0))
            StructureData(cell=cell, pbc=1)

    def test_wrong_pbc_2(self):
        """Wrong pbc parameter (iterable but with wrong len)"""
        with pytest.raises(ValueError):
            cell = ((1.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 3.0))
            StructureData(cell=cell, pbc=[True, True])

    def test_wrong_pbc_3(self):
        """Wrong pbc parameter (iterable but with wrong len)"""
        with pytest.raises(ValueError):
            cell = ((1.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 3.0))
            StructureData(cell=cell, pbc=[])

    def test_ok_pbc_1(self):
        """Single pbc value"""
        cell = ((1.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 3.0))
        a = StructureData(cell=cell, pbc=True)
        assert a.pbc == tuple([True, True, True])

        a = StructureData(cell=cell, pbc=False)
        assert a.pbc == tuple([False, False, False])

    def test_ok_pbc_2(self):
        """One-element list"""
        cell = ((1.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 3.0))
        a = StructureData(cell=cell, pbc=[True])
        assert a.pbc == tuple([True, True, True])

        a = StructureData(cell=cell, pbc=[False])
        assert a.pbc == tuple([False, False, False])

    def test_ok_pbc_3(self):
        """Three-element list"""
        cell = ((1.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 3.0))
        a = StructureData(cell=cell, pbc=[True, False, True])
        assert a.pbc == tuple([True, False, True])


class TestStructureData:
    """Tests the creation of StructureData objects (cell and pbc)."""

    def test_cell_ok_and_atoms(self):
        """Test the creation of a cell and the appending of atoms"""
        cell = [[2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0]]

        a = StructureData(cell=cell)
        out_cell = a.cell
        np.testing.assert_allclose(out_cell, cell)

        a.append_atom(position=(0.0, 0.0, 0.0), symbols=['Ba'])
        a.append_atom(position=(1.0, 1.0, 1.0), symbols=['Ti'])
        a.append_atom(position=(1.2, 1.4, 1.6), symbols=['Ti'])
        assert not a.is_alloy
        assert not a.has_vacancies
        # There should be only two kinds! (two atoms of kind Ti should
        # belong to the same kind)
        assert len(a.kinds) == 2

        a.append_atom(position=(0.5, 1.0, 1.5), symbols=['O', 'C'], weights=[0.5, 0.5])
        assert a.is_alloy
        assert not a.has_vacancies

        a.append_atom(position=(0.5, 1.0, 1.5), symbols=['O'], weights=[0.5])
        assert a.is_alloy
        assert a.has_vacancies

        a.clear_kinds()
        a.append_atom(position=(0.5, 1.0, 1.5), symbols=['O'], weights=[0.5])
        assert not a.is_alloy
        assert a.has_vacancies

    def test_cell_ok_and_unknown_atoms(self):
        """Test the creation of a cell and the appending of atoms, including
        the unknown entry.
        """
        cell = [[2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0]]

        a = StructureData(cell=cell)
        out_cell = a.cell
        np.testing.assert_allclose(out_cell, cell)

        a.append_atom(position=(0.0, 0.0, 0.0), symbols=['Ba'])
        a.append_atom(position=(1.0, 1.0, 1.0), symbols=['X'])
        a.append_atom(position=(1.2, 1.4, 1.6), symbols=['X'])
        assert not a.is_alloy
        assert not a.has_vacancies
        # There should be only two kinds! (two atoms of kind X should
        # belong to the same kind)
        assert len(a.kinds) == 2

        a.append_atom(position=(0.5, 1.0, 1.5), symbols=['O', 'C'], weights=[0.5, 0.5])
        assert a.is_alloy
        assert not a.has_vacancies

        a.append_atom(position=(0.5, 1.0, 1.5), symbols=['O'], weights=[0.5])
        assert a.is_alloy
        assert a.has_vacancies

        a.clear_kinds()
        a.append_atom(position=(0.5, 1.0, 1.5), symbols=['X'], weights=[0.5])
        assert not a.is_alloy
        assert a.has_vacancies

    def test_kind_1(self):
        """Test the management of kinds (automatic detection of kind of
        simple atoms).
        """
        a = StructureData(cell=((2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)))

        a.append_atom(position=(0.0, 0.0, 0.0), symbols=['Ba'])
        a.append_atom(position=(0.5, 0.5, 0.5), symbols=['Ba'])
        a.append_atom(position=(1.0, 1.0, 1.0), symbols=['Ti'])

        assert len(a.kinds) == 2  # I should only have two types
        # I check for the default names of kinds
        assert set(k.name for k in a.kinds) == set(('Ba', 'Ti'))

    def test_kind_1_unknown(self):
        """Test the management of kinds (automatic detection of kind of
        simple atoms), inluding the unknown entry.
        """
        a = StructureData(cell=((2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)))

        a.append_atom(position=(0.0, 0.0, 0.0), symbols=['X'])
        a.append_atom(position=(0.5, 0.5, 0.5), symbols=['X'])
        a.append_atom(position=(1.0, 1.0, 1.0), symbols=['Ti'])

        assert len(a.kinds) == 2  # I should only have two types
        # I check for the default names of kinds
        assert set(k.name for k in a.kinds) == set(('X', 'Ti'))

    def test_kind_2(self):
        """Test the management of kinds (manual specification of kind name)."""
        a = StructureData(cell=((2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)))

        a.append_atom(position=(0.0, 0.0, 0.0), symbols=['Ba'], name='Ba1')
        a.append_atom(position=(0.5, 0.5, 0.5), symbols=['Ba'], name='Ba2')
        a.append_atom(position=(1.0, 1.0, 1.0), symbols=['Ti'])

        kind_list = a.kinds
        assert len(kind_list) == 3  # I should have now three kinds
        assert set(k.name for k in kind_list) == set(('Ba1', 'Ba2', 'Ti'))

    def test_kind_2_unknown(self):
        """Test the management of kinds (manual specification of kind name),
        including the unknown entry.
        """
        a = StructureData(cell=((2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)))

        a.append_atom(position=(0.0, 0.0, 0.0), symbols=['X'], name='X1')
        a.append_atom(position=(0.5, 0.5, 0.5), symbols=['X'], name='X2')
        a.append_atom(position=(1.0, 1.0, 1.0), symbols=['Ti'])

        kind_list = a.kinds
        assert len(kind_list) == 3  # I should have now three kinds
        assert set(k.name for k in kind_list) == set(('X1', 'X2', 'Ti'))

    def test_kind_3(self):
        """Test the management of kinds (adding an atom with different mass)."""
        a = StructureData(cell=((2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)))

        a.append_atom(position=(0.0, 0.0, 0.0), symbols=['Ba'], mass=100.0)
        with pytest.raises(ValueError):
            # Shouldn't allow, I am adding two sites with the same name 'Ba'
            a.append_atom(position=(0.5, 0.5, 0.5), symbols=['Ba'], mass=101.0, name='Ba')

            # now it should work because I am using a different kind name
        a.append_atom(position=(0.5, 0.5, 0.5), symbols=['Ba'], mass=101.0, name='Ba2')

        a.append_atom(position=(1.0, 1.0, 1.0), symbols=['Ti'])

        assert len(a.kinds) == 3  # I should have now three types
        assert len(a.sites) == 3  # and 3 sites
        assert set(k.name for k in a.kinds) == set(('Ba', 'Ba2', 'Ti'))

    def test_kind_3_unknown(self):
        """Test the management of kinds (adding an atom with different mass),
        including the unknown entry.
        """
        a = StructureData(cell=((2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)))

        a.append_atom(position=(0.0, 0.0, 0.0), symbols=['X'], mass=100.0)
        with pytest.raises(ValueError):
            # Shouldn't allow, I am adding two sites with the same name 'Ba'
            a.append_atom(position=(0.5, 0.5, 0.5), symbols=['X'], mass=101.0, name='X')

            # now it should work because I am using a different kind name
        a.append_atom(position=(0.5, 0.5, 0.5), symbols=['X'], mass=101.0, name='X2')

        a.append_atom(position=(1.0, 1.0, 1.0), symbols=['Ti'])

        assert len(a.kinds) == 3  # I should have now three types
        assert len(a.sites) == 3  # and 3 sites
        assert set(k.name for k in a.kinds) == set(('X', 'X2', 'Ti'))

    def test_kind_4(self):
        """Test the management of kind (adding an atom with different symbols
        or weights).
        """
        a = StructureData(cell=((2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)))

        a.append_atom(position=(0.0, 0.0, 0.0), symbols=['Ba', 'Ti'], weights=(1.0, 0.0), name='mytype')

        with pytest.raises(ValueError):
            # Shouldn't allow, different weights
            a.append_atom(position=(0.5, 0.5, 0.5), symbols=['Ba', 'Ti'], weights=(0.9, 0.1), name='mytype')

        with pytest.raises(ValueError):
            # Shouldn't allow, different weights (with vacancy)
            a.append_atom(position=(0.5, 0.5, 0.5), symbols=['Ba', 'Ti'], weights=(0.8, 0.1), name='mytype')

        with pytest.raises(ValueError):
            # Shouldn't allow, different symbols list
            a.append_atom(position=(0.5, 0.5, 0.5), symbols=['Ba'], name='mytype')

        with pytest.raises(ValueError):
            # Shouldn't allow, different symbols list
            a.append_atom(position=(0.5, 0.5, 0.5), symbols=['Si', 'Ti'], weights=(1.0, 0.0), name='mytype')

            # should allow because every property is identical
        a.append_atom(position=(0.0, 0.0, 0.0), symbols=['Ba', 'Ti'], weights=(1.0, 0.0), name='mytype')

        assert len(a.kinds) == 1

    def test_kind_4_unknown(self):
        """Test the management of kind (adding an atom with different symbols
        or weights), including the unknown entry.
        """
        a = StructureData(cell=((2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)))

        a.append_atom(position=(0.0, 0.0, 0.0), symbols=['X', 'Ti'], weights=(1.0, 0.0), name='mytype')

        with pytest.raises(ValueError):
            # Shouldn't allow, different weights
            a.append_atom(position=(0.5, 0.5, 0.5), symbols=['X', 'Ti'], weights=(0.9, 0.1), name='mytype')

        with pytest.raises(ValueError):
            # Shouldn't allow, different weights (with vacancy)
            a.append_atom(position=(0.5, 0.5, 0.5), symbols=['X', 'Ti'], weights=(0.8, 0.1), name='mytype')

        with pytest.raises(ValueError):
            # Shouldn't allow, different symbols list
            a.append_atom(position=(0.5, 0.5, 0.5), symbols=['X'], name='mytype')

        with pytest.raises(ValueError):
            # Shouldn't allow, different symbols list
            a.append_atom(position=(0.5, 0.5, 0.5), symbols=['Si', 'Ti'], weights=(1.0, 0.0), name='mytype')

            # should allow because every property is identical
        a.append_atom(position=(0.0, 0.0, 0.0), symbols=['X', 'Ti'], weights=(1.0, 0.0), name='mytype')

        assert len(a.kinds) == 1

    def test_kind_5(self):
        """Test the management of kinds (automatic creation of new kind
        if name is not specified and properties are different).
        """
        a = StructureData(cell=((2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)))

        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Ba', mass=100.0)
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Ti')
        # The name does not exist
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Ti', name='Ti2')
        # The name already exists, but the properties are identical => OK
        a.append_atom(position=(1.0, 1.0, 1.0), symbols='Ti', name='Ti2')
        # The name already exists, but the properties are different!
        with pytest.raises(ValueError):
            a.append_atom(position=(1.0, 1.0, 1.0), symbols='Ti', mass=100.0, name='Ti2')
        # Should not complain, should create a new type
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Ba', mass=150.0)

        # There should be 4 kinds, the automatic name for the last one
        # should be Ba1
        assert [k.name for k in a.kinds] == ['Ba', 'Ti', 'Ti2', 'Ba1']
        assert len(a.sites) == 5

    def test_kind_5_unknown(self):
        """Test the management of kinds (automatic creation of new kind
        if name is not specified and properties are different), including
        the unknown entry.
        """
        a = StructureData(cell=((2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)))

        a.append_atom(position=(0.0, 0.0, 0.0), symbols='X', mass=100.0)
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Ti')
        # The name does not exist
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Ti', name='Ti2')
        # The name already exists, but the properties are identical => OK
        a.append_atom(position=(1.0, 1.0, 1.0), symbols='Ti', name='Ti2')
        # The name already exists, but the properties are different!
        with pytest.raises(ValueError):
            a.append_atom(position=(1.0, 1.0, 1.0), symbols='Ti', mass=100.0, name='Ti2')
        # Should not complain, should create a new type
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='X', mass=150.0)

        # There should be 4 kinds, the automatic name for the last one
        # should be Ba1
        assert [k.name for k in a.kinds] == ['X', 'Ti', 'Ti2', 'X1']
        assert len(a.sites) == 5

    def test_kind_5_bis(self):
        """Test the management of kinds (automatic creation of new kind
        if name is not specified and properties are different).
        This test was failing in, e.g., commit f6a8f4b.
        """
        from aiida.common.constants import elements

        s = StructureData(cell=((6.0, 0.0, 0.0), (0.0, 6.0, 0.0), (0.0, 0.0, 6.0)))

        s.append_atom(symbols='Fe', position=[0, 0, 0], mass=12)
        s.append_atom(symbols='Fe', position=[1, 0, 0], mass=12)
        s.append_atom(symbols='Fe', position=[2, 0, 0], mass=12)
        s.append_atom(symbols='Fe', position=[2, 0, 0])
        s.append_atom(symbols='Fe', position=[4, 0, 0])

        # I expect only two species, the first one with name 'Fe', mass 12,
        # and referencing the first three atoms; the second with name
        # 'Fe1', mass = elements[26]['mass'], and referencing the last two atoms
        assert {(k.name, k.mass) for k in s.kinds} == {('Fe', 12.0), ('Fe1', elements[26]['mass'])}

        kind_of_each_site = [site.kind_name for site in s.sites]
        assert kind_of_each_site == ['Fe', 'Fe', 'Fe', 'Fe1', 'Fe1']

    def test_kind_5_bis_unknown(self):
        """Test the management of kinds (automatic creation of new kind
        if name is not specified and properties are different).
        This test was failing in, e.g., commit f6a8f4b. This also includes
        the unknown entry.
        """
        from aiida.common.constants import elements

        s = StructureData(cell=((6.0, 0.0, 0.0), (0.0, 6.0, 0.0), (0.0, 0.0, 6.0)))

        s.append_atom(symbols='X', position=[0, 0, 0], mass=12)
        s.append_atom(symbols='X', position=[1, 0, 0], mass=12)
        s.append_atom(symbols='X', position=[2, 0, 0], mass=12)
        s.append_atom(symbols='X', position=[2, 0, 0])
        s.append_atom(symbols='X', position=[4, 0, 0])

        # I expect only two species, the first one with name 'X', mass 12,
        # and referencing the first three atoms; the second with name
        # 'X', mass = elements[0]['mass'], and referencing the last two atoms
        assert {(k.name, k.mass) for k in s.kinds} == {('X', 12.0), ('X1', elements[0]['mass'])}

        kind_of_each_site = [site.kind_name for site in s.sites]
        assert kind_of_each_site == ['X', 'X', 'X', 'X1', 'X1']

    @skip_ase
    def test_kind_5_bis_ase(self):
        """Same test as test_kind_5_bis, but using ase"""
        import ase

        asecell = ase.Atoms('Fe5', cell=((6.0, 0.0, 0.0), (0.0, 6.0, 0.0), (0.0, 0.0, 6.0)))
        asecell.set_positions(
            [
                [0, 0, 0],
                [1, 0, 0],
                [2, 0, 0],
                [3, 0, 0],
                [4, 0, 0],
            ]
        )

        asecell[0].mass = 12.0
        asecell[1].mass = 12.0
        asecell[2].mass = 12.0

        s = StructureData(ase=asecell)

        # I expect only two species, the first one with name 'Fe', mass 12,
        # and referencing the first three atoms; the second with name
        # 'Fe1', mass = elements[26]['mass'], and referencing the last two atoms
        assert {(k.name, k.mass) for k in s.kinds} == {('Fe', 12.0), ('Fe1', asecell[3].mass)}

        kind_of_each_site = [site.kind_name for site in s.sites]
        assert kind_of_each_site == ['Fe', 'Fe', 'Fe', 'Fe1', 'Fe1']

    @skip_ase
    def test_kind_5_bis_ase_unknown(self):
        """Same test as test_kind_5_bis_unknown, but using ase"""
        import ase

        asecell = ase.Atoms('X5', cell=((6.0, 0.0, 0.0), (0.0, 6.0, 0.0), (0.0, 0.0, 6.0)))
        asecell.set_positions(
            [
                [0, 0, 0],
                [1, 0, 0],
                [2, 0, 0],
                [3, 0, 0],
                [4, 0, 0],
            ]
        )

        asecell[0].mass = 12.0
        asecell[1].mass = 12.0
        asecell[2].mass = 12.0

        s = StructureData(ase=asecell)

        # I expect only two species, the first one with name 'X', mass 12,
        # and referencing the first three atoms; the second with name
        # 'X1', mass = elements[26]['mass'], and referencing the last two atoms
        assert {(k.name, k.mass) for k in s.kinds} == {('X', 12.0), ('X1', asecell[3].mass)}

        kind_of_each_site = [site.kind_name for site in s.sites]
        assert kind_of_each_site == ['X', 'X', 'X', 'X1', 'X1']

    def test_kind_6(self):
        """Test the returning of kinds from the string name (most of the code
        copied from :py:meth:`.test_kind_5`).
        """
        a = StructureData(cell=((2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)))

        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Ba', mass=100.0)
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Ti')
        # The name does not exist
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Ti', name='Ti2')
        # The name already exists, but the properties are identical => OK
        a.append_atom(position=(1.0, 1.0, 1.0), symbols='Ti', name='Ti2')
        # Should not complain, should create a new type
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Ba', mass=150.0)
        # There should be 4 kinds, the automatic name for the last one
        # should be Ba1 (same check of test_kind_5
        assert [k.name for k in a.kinds] == ['Ba', 'Ti', 'Ti2', 'Ba1']
        #############################
        # Here I start the real tests
        # No such kind
        with pytest.raises(ValueError):
            a.get_kind('Ti3')
        k = a.get_kind('Ba1')
        assert k.symbols == ('Ba',)
        assert round(abs(k.mass - 150.0), 7) == 0

    def test_kind_6_unknown(self):
        """Test the returning of kinds from the string name (most of the code
        copied from :py:meth:`.test_kind_5`), including the unknown entry.
        """
        a = StructureData(cell=((2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)))

        a.append_atom(position=(0.0, 0.0, 0.0), symbols='X', mass=100.0)
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Ti')
        # The name does not exist
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Ti', name='Ti2')
        # The name already exists, but the properties are identical => OK
        a.append_atom(position=(1.0, 1.0, 1.0), symbols='Ti', name='Ti2')
        # Should not complain, should create a new type
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='X', mass=150.0)
        # There should be 4 kinds, the automatic name for the last one
        # should be Ba1 (same check of test_kind_5
        assert [k.name for k in a.kinds] == ['X', 'Ti', 'Ti2', 'X1']
        #############################
        # Here I start the real tests
        # No such kind
        with pytest.raises(ValueError):
            a.get_kind('Ti3')
        k = a.get_kind('X1')
        assert k.symbols == ('X',)
        assert round(abs(k.mass - 150.0), 7) == 0

    def test_kind_7(self):
        """Test the functions returning the list of kinds, symbols, ..."""
        a = StructureData(cell=((2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)))

        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Ba', mass=100.0)
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Ti')
        # The name does not exist
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Ti', name='Ti2')
        # The name already exists, but the properties are identical => OK
        a.append_atom(position=(0.0, 0.0, 0.0), symbols=['O', 'H'], weights=[0.9, 0.1], mass=15.0)

        assert a.get_symbols_set() == set(['Ba', 'Ti', 'O', 'H'])

    def test_kind_7_unknown(self):
        """Test the functions returning the list of kinds, symbols, ...
        including the unknown entry.
        """
        a = StructureData(cell=((2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)))

        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Ba', mass=100.0)
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='X')
        # The name does not exist
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='X', name='X2')
        # The name already exists, but the properties are identical => OK
        a.append_atom(position=(0.0, 0.0, 0.0), symbols=['O', 'H'], weights=[0.9, 0.1], mass=15.0)

        assert a.get_symbols_set() == set(['Ba', 'X', 'O', 'H'])

    @skip_ase
    @skip_spglib
    def test_kind_8(self):
        """Test the ase_refine_cell() function"""
        import math

        import ase

        a = ase.Atoms(cell=[10, 10, 10])
        a.append(ase.Atom('C', [0, 0, 0]))
        a.append(ase.Atom('C', [5, 0, 0]))
        b, sym = ase_refine_cell(a)
        sym.pop('rotations')
        sym.pop('translations')
        assert b.get_chemical_symbols() == ['C']
        assert b.cell.tolist() == [[10, 0, 0], [0, 10, 0], [0, 0, 5]]
        assert sym == {'hall': '-P 4 2', 'hm': 'P4/mmm', 'tables': 123}

        a = ase.Atoms(cell=[10, 2 * math.sqrt(75), 10])
        a.append(ase.Atom('C', [0, 0, 0]))
        a.append(ase.Atom('C', [5, math.sqrt(75), 0]))
        b, sym = ase_refine_cell(a)
        sym.pop('rotations')
        sym.pop('translations')
        assert b.get_chemical_symbols() == ['C']
        assert np.round(b.cell, 2).tolist() == [[10, 0, 0], [-5, 8.66, 0], [0, 0, 10]]
        assert sym == {'hall': '-P 6 2', 'hm': 'P6/mmm', 'tables': 191}

        a = ase.Atoms(cell=[[10, 0, 0], [-10, 10, 0], [0, 0, 10]])
        a.append(ase.Atom('C', [5, 5, 5]))
        a.append(ase.Atom('F', [0, 0, 0]))
        b, sym = ase_refine_cell(a)
        sym.pop('rotations')
        sym.pop('translations')
        assert b.get_chemical_symbols() == ['C', 'F']
        assert b.cell.tolist() == [[10, 0, 0], [0, 10, 0], [0, 0, 10]]
        assert b.get_scaled_positions().tolist() == [[0.5, 0.5, 0.5], [0, 0, 0]]
        assert sym == {'hall': '-P 4 2 3', 'hm': 'Pm-3m', 'tables': 221}

        a = ase.Atoms(cell=[[10, 0, 0], [-10, 10, 0], [0, 0, 10]])
        a.append(ase.Atom('C', [0, 0, 0]))
        a.append(ase.Atom('F', [5, 5, 5]))
        b, sym = ase_refine_cell(a)
        sym.pop('rotations')
        sym.pop('translations')
        assert b.get_chemical_symbols() == ['C', 'F']
        assert b.cell.tolist() == [[10, 0, 0], [0, 10, 0], [0, 0, 10]]
        assert b.get_scaled_positions().tolist() == [[0, 0, 0], [0.5, 0.5, 0.5]]
        assert sym == {'hall': '-P 4 2 3', 'hm': 'Pm-3m', 'tables': 221}

        a = ase.Atoms(cell=[[12.132, 0, 0], [0, 6.0606, 0], [0, 0, 8.0956]])
        a.append(ase.Atom('Ba', [1.5334848, 1.3999986, 2.00042276]))
        b, sym = ase_refine_cell(a)
        sym.pop('rotations')
        sym.pop('translations')
        assert b.cell.tolist() == [[6.0606, 0, 0], [0, 8.0956, 0], [0, 0, 12.132]]
        assert b.get_scaled_positions().tolist() == [[0, 0, 0]]

        a = ase.Atoms(cell=[10, 10, 10])
        a.append(ase.Atom('C', [5, 5, 5]))
        a.append(ase.Atom('O', [2.5, 5, 5]))
        a.append(ase.Atom('O', [7.5, 5, 5]))
        b, sym = ase_refine_cell(a)
        sym.pop('rotations')
        sym.pop('translations')
        assert b.get_chemical_symbols() == ['C', 'O']
        assert sym == {'hall': '-P 4 2', 'hm': 'P4/mmm', 'tables': 123}

        # Generated from COD entry 1507756
        # (http://www.crystallography.net/cod/1507756.cif@87343)
        from ase.spacegroup import crystal

        a = crystal(
            ['Ba', 'Ti', 'O', 'O'],
            [[0, 0, 0], [0.5, 0.5, 0.482], [0.5, 0.5, 0.016], [0.5, 0, 0.515]],
            cell=[3.9999, 3.9999, 4.0170],
            spacegroup=99,
        )
        b, sym = ase_refine_cell(a)
        sym.pop('rotations')
        sym.pop('translations')
        assert b.get_chemical_symbols() == ['Ba', 'Ti', 'O', 'O']
        assert sym == {'hall': 'P 4 -2', 'hm': 'P4mm', 'tables': 99}

    def test_get_formula(self):
        """Tests the generation of formula"""
        assert get_formula(['Ba', 'Ti'] + ['O'] * 3) == 'BaO3Ti'
        assert get_formula(['Ba', 'Ti', 'C'] + ['O'] * 3, separator=' ') == 'C Ba O3 Ti'
        assert get_formula(['H'] * 6 + ['C'] * 6) == 'C6H6'
        assert get_formula(['H'] * 6 + ['C'] * 6, mode='hill_compact') == 'CH'
        assert (
            get_formula((['Ba', 'Ti'] + ['O'] * 3) * 2 + ['Ba'] + ['Ti'] * 2 + ['O'] * 3, mode='group')
            == '(BaTiO3)2BaTi2O3'
        )
        assert (
            get_formula((['Ba', 'Ti'] + ['O'] * 3) * 2 + ['Ba'] + ['Ti'] * 2 + ['O'] * 3, mode='group', separator=' ')
            == '(Ba Ti O3)2 Ba Ti2 O3'
        )
        assert (
            get_formula((['Ba', 'Ti'] + ['O'] * 3) * 2 + ['Ba'] + ['Ti'] * 2 + ['O'] * 3, mode='reduce')
            == 'BaTiO3BaTiO3BaTi2O3'
        )
        assert (
            get_formula((['Ba', 'Ti'] + ['O'] * 3) * 2 + ['Ba'] + ['Ti'] * 2 + ['O'] * 3, mode='reduce', separator=', ')
            == 'Ba, Ti, O3, Ba, Ti, O3, Ba, Ti2, O3'
        )
        assert get_formula((['Ba', 'Ti'] + ['O'] * 3) * 2, mode='count') == 'Ba2Ti2O6'
        assert get_formula((['Ba', 'Ti'] + ['O'] * 3) * 2, mode='count_compact') == 'BaTiO3'

    def test_get_formula_unknown(self):
        """Tests the generation of formula, including unknown entry."""
        assert get_formula(['Ba', 'Ti'] + ['X'] * 3) == 'BaTiX3'
        assert get_formula(['Ba', 'Ti', 'C'] + ['X'] * 3, separator=' ') == 'C Ba Ti X3'
        assert get_formula(['X'] * 6 + ['C'] * 6) == 'C6X6'
        assert get_formula(['X'] * 6 + ['C'] * 6, mode='hill_compact') == 'CX'
        assert (
            get_formula((['Ba', 'Ti'] + ['X'] * 3) * 2 + ['Ba'] + ['X'] * 2 + ['O'] * 3, mode='group')
            == '(BaTiX3)2BaX2O3'
        )
        assert (
            get_formula((['Ba', 'Ti'] + ['X'] * 3) * 2 + ['Ba'] + ['X'] * 2 + ['O'] * 3, mode='group', separator=' ')
            == '(Ba Ti X3)2 Ba X2 O3'
        )
        assert (
            get_formula((['Ba', 'Ti'] + ['X'] * 3) * 2 + ['Ba'] + ['Ti'] * 2 + ['X'] * 3, mode='reduce')
            == 'BaTiX3BaTiX3BaTi2X3'
        )
        assert (
            get_formula((['Ba', 'Ti'] + ['X'] * 3) * 2 + ['Ba'] + ['Ti'] * 2 + ['X'] * 3, mode='reduce', separator=', ')
            == 'Ba, Ti, X3, Ba, Ti, X3, Ba, Ti2, X3'
        )
        assert get_formula((['Ba', 'Ti'] + ['O'] * 3) * 2, mode='count') == 'Ba2Ti2O6'
        assert get_formula((['Ba', 'Ti'] + ['X'] * 3) * 2, mode='count_compact') == 'BaTiX3'

    @skip_ase
    @skip_pycifrw
    @pytest.mark.requires_rmq
    def test_get_cif(self):
        """Tests the conversion to CifData"""
        import re

        a = StructureData(cell=((2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)))

        a.append_atom(position=(0.0, 0.0, 0.0), symbols=['Ba'])
        a.append_atom(position=(0.5, 0.5, 0.5), symbols=['Ba'])
        a.append_atom(position=(1.0, 1.0, 1.0), symbols=['Ti'])

        c = a.get_cif()
        lines = c._prepare_cif()[0].decode('utf-8').split('\n')
        non_comments = []
        for line in lines:
            if not re.search('^#', line):
                non_comments.append(line)
        assert simplify('\n'.join(non_comments)) == simplify(
            """
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

_symmetry_int_tables_number             1
_symmetry_space_group_name_H-M          'P 1'
"""
        )

    def test_xyz_parser(self):
        """Test XYZ parser."""
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
            assert not any(s.pbc)
            # Making sure that the structure has sites, kinds and a cell
            assert s.sites
            assert s.kinds
            assert s.cell

            # The default cell is given in these cases:
            assert s.cell == np.diag([0, 0, 0]).tolist()

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
            with pytest.raises(TypeError):
                StructureData()._parse_xyz(xyz_string)


def test_lock():
    """Test that the structure is locked after storage."""
    cell = ((1.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 3.0))
    a = StructureData(cell=cell)

    a.pbc = [False, True, True]

    k = Kind(symbols='Ba', name='Ba')
    s = Site(position=(0.0, 0.0, 0.0), kind_name='Ba')
    a.append_kind(k)
    a.append_site(s)

    a.append_atom(symbols='Ti', position=[0.0, 0.0, 0.0])

    a.store()

    k2 = Kind(symbols='Ba', name='Ba')
    # Nothing should be changed after store()
    with pytest.raises(ModificationNotAllowed):
        a.append_kind(k2)
    with pytest.raises(ModificationNotAllowed):
        a.append_site(s)
    with pytest.raises(ModificationNotAllowed):
        a.clear_sites()
    with pytest.raises(ModificationNotAllowed):
        a.clear_kinds()
    with pytest.raises(ModificationNotAllowed):
        a.cell = cell
    with pytest.raises(ModificationNotAllowed):
        a.pbc = [True, True, True]

    _ = a.get_cell_volume()
    _ = a.is_alloy
    _ = a.has_vacancies

    b = a.clone()
    # I check that clone returned an unstored copy and so can be altered
    b.append_site(s)
    b.clear_sites()
    # I check that the original did not change
    assert len(a.sites) != 0
    b.cell = cell
    b.pbc = [True, True, True]


class TestStructureDataReload:
    """Tests the creation of StructureData, converting it to a raw format and
    converting it back.
    """

    def test_reload(self):
        """Start from a StructureData object, convert to raw and then back"""
        cell = ((1.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 3.0))
        a = StructureData(cell=cell)

        a.pbc = [False, True, True]

        a.append_atom(position=(0.0, 0.0, 0.0), symbols=['Ba'])
        a.append_atom(position=(1.0, 1.0, 1.0), symbols=['Ti'])

        a.store()

        b = load_node(uuid=a.uuid)

        for i in range(3):
            for j in range(3):
                assert round(abs(cell[i][j] - b.cell[i][j]), 7) == 0

        assert b.pbc == (False, True, True)
        assert len(b.sites) == 2
        assert b.kinds[0].symbols[0] == 'Ba'
        assert b.kinds[1].symbols[0] == 'Ti'
        for i in range(3):
            assert round(abs(b.sites[0].position[i] - 0.0), 7) == 0
        for i in range(3):
            assert round(abs(b.sites[1].position[i] - 1.0), 7) == 0

        # Fully reload from UUID
        b = load_node(a.uuid, sub_classes=(StructureData,))

        for i in range(3):
            for j in range(3):
                assert round(abs(cell[i][j] - b.cell[i][j]), 7) == 0

        assert b.pbc == (False, True, True)
        assert len(b.sites) == 2
        assert b.kinds[0].symbols[0] == 'Ba'
        assert b.kinds[1].symbols[0] == 'Ti'
        for i in range(3):
            assert round(abs(b.sites[0].position[i] - 0.0), 7) == 0
        for i in range(3):
            assert round(abs(b.sites[1].position[i] - 1.0), 7) == 0

    def test_clone(self):
        """Start from a StructureData object, clone it and see if it is preserved"""
        cell = ((1.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 3.0))
        a = StructureData(cell=cell)

        a.pbc = [False, True, True]

        a.append_atom(position=(0.0, 0.0, 0.0), symbols=['Ba'])
        a.append_atom(position=(1.0, 1.0, 1.0), symbols=['Ti'])

        b = a.clone()

        for i in range(3):
            for j in range(3):
                assert round(abs(cell[i][j] - b.cell[i][j]), 7) == 0

        assert b.pbc == (False, True, True)
        assert len(b.kinds) == 2
        assert len(b.sites) == 2
        assert b.kinds[0].symbols[0] == 'Ba'
        assert b.kinds[1].symbols[0] == 'Ti'
        for i in range(3):
            assert round(abs(b.sites[0].position[i] - 0.0), 7) == 0
        for i in range(3):
            assert round(abs(b.sites[1].position[i] - 1.0), 7) == 0

        a.store()

        # Clone after store()
        c = a.clone()
        for i in range(3):
            for j in range(3):
                assert round(abs(cell[i][j] - c.cell[i][j]), 7) == 0

        assert c.pbc == (False, True, True)
        assert len(c.kinds) == 2
        assert len(c.sites) == 2
        assert c.kinds[0].symbols[0] == 'Ba'
        assert c.kinds[1].symbols[0] == 'Ti'
        for i in range(3):
            assert round(abs(c.sites[0].position[i] - 0.0), 7) == 0
        for i in range(3):
            assert round(abs(c.sites[1].position[i] - 1.0), 7) == 0


@skip_atomistic
def test_to_atomistic(self):
    """Test the conversion from orm.StructureData to the atomistic structure."""

    # Create a structure with a single atom
    from aiida_atomistic import StructureData as AtomisticStructureData

    legacy = StructureData(cell=((1.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 3.0)))
    legacy.append_atom(position=(0.0, 0.0, 0.0), symbols=['Ba'], name='Ba1')

    # Convert to atomistic structure
    structure = legacy.to_atomistic()

    # Check that the structure is as expected
    assert isinstance(structure, AtomisticStructureData)
    assert structure.properties.sites[0].kinds == legacy.sites[0].kind_name
    assert structure.properties.sites[0].positions == list(legacy.sites[0].position)
    assert structure.properties.cell == legacy.cell


class TestStructureDataFromAse:
    """Tests the creation of Sites from/to a ASE object."""

    @skip_ase
    def test_ase(self):
        """Tests roundtrip ASE -> StructureData -> ASE."""
        import ase

        a = ase.Atoms('SiGe', cell=(1.0, 2.0, 3.0), pbc=(True, False, False))
        a.set_positions(
            (
                (0.0, 0.0, 0.0),
                (0.5, 0.7, 0.9),
            )
        )
        a[1].mass = 110.2

        b = StructureData(ase=a)
        c = b.get_ase()

        assert a[0].symbol == c[0].symbol
        assert a[1].symbol == c[1].symbol
        for i in range(3):
            assert round(abs(a[0].position[i] - c[0].position[i]), 7) == 0
        for i in range(3):
            for j in range(3):
                assert round(abs(a.cell[i][j] - c.cell[i][j]), 7) == 0

        assert round(abs(c[1].mass - 110.2), 7) == 0

    @skip_ase
    def test_ase_molecule(self):
        """Tests that importing a molecule from ASE works."""
        from ase.build import molecule

        s = StructureData(ase=molecule('H2O'))

        assert s.pbc == (False, False, False)
        retdict = s.get_dimensionality()
        assert retdict['value'] == 0
        assert retdict['dim'] == 0

        with pytest.raises(ValueError):
            # A periodic cell requires a nonzero volume in periodic directions
            s.set_pbc(True)
            s.store()

        # after setting a cell, we should be able to store
        s.set_cell([[5, 0, 0], [0, 5, 0], [0, 0, 5]])
        s.store()

    @skip_ase
    def test_conversion_of_types_1(self):
        """Tests roundtrip ASE -> StructureData -> ASE, with tags"""
        import ase

        a = ase.Atoms('Si4Ge4', cell=(1.0, 2.0, 3.0), pbc=(True, False, False))
        a.set_positions(
            (
                (0.0, 0.0, 0.0),
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
        assert [k.name for k in b.kinds] == ['Si', 'Si1', 'Si2', 'Si3', 'Ge4', 'Ge5', 'Ge6', 'Ge7']
        c = b.get_ase()

        a_tags = list(a.get_tags())
        c_tags = list(c.get_tags())
        assert a_tags == c_tags

    @skip_ase
    def test_conversion_of_types_2(self):
        """Tests roundtrip ASE -> StructureData -> ASE, with tags, and
        changing the atomic masses
        """
        import ase

        a = ase.Atoms('Si4', cell=(1.0, 2.0, 3.0), pbc=(True, False, False))
        a.set_positions(
            (
                (0.0, 0.0, 0.0),
                (0.1, 0.1, 0.1),
                (0.2, 0.2, 0.2),
                (0.3, 0.3, 0.3),
            )
        )

        a.set_tags((0, 1, 0, 1))
        a[2].mass = 100.0
        a[3].mass = 300.0

        b = StructureData(ase=a)
        # This will give funny names to the kinds, because I am using
        # both tags and different properties (mass). I just check to have
        # 4 kinds
        assert len(b.kinds) == 4

        # Do I get the same tags after one full iteration back and forth?
        c = b.get_ase()
        d = StructureData(ase=c)
        e = d.get_ase()
        c_tags = list(c.get_tags())
        e_tags = list(e.get_tags())
        assert c_tags == e_tags

    @skip_ase
    def test_conversion_of_types_3(self):
        """Tests StructureData -> ASE, with all sorts of kind names"""
        a = StructureData(cell=[[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Ba', name='Ba')
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Ba', name='Ba1')
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Cu', name='Cu')
        # continues with a number
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Cu', name='Cu2')
        # does not continue with a number
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Cu', name='Cu_my')
        # random string
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Cu', name='a_name')
        # a name of another chemical symbol
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Cu', name='Fe')
        # lowercase! as if it were a random string
        a.append_atom(position=(0.0, 0.0, 0.0), symbols='Cu', name='cu1')

        # Just to be sure that the species were saved with the correct name
        # in the first place
        assert [k.name for k in a.kinds] == ['Ba', 'Ba1', 'Cu', 'Cu2', 'Cu_my', 'a_name', 'Fe', 'cu1']

        b = a.get_ase()
        assert b.get_chemical_symbols() == ['Ba', 'Ba', 'Cu', 'Cu', 'Cu', 'Cu', 'Cu', 'Cu']
        assert list(b.get_tags()) == [0, 1, 0, 2, 3, 4, 5, 6]

    @skip_ase
    def test_conversion_of_types_4(self):
        """Tests ASE -> StructureData -> ASE, in particular conversion tags / kind names"""
        import ase

        atoms = ase.Atoms('Fe5')
        atoms[2].tag = 1
        atoms[3].tag = 1
        atoms[4].tag = 4
        atoms.set_cell([1, 1, 1])
        s = StructureData(ase=atoms)
        kindnames = {k.name for k in s.kinds}
        assert kindnames == set(['Fe', 'Fe1', 'Fe4'])
        # check roundtrip ASE -> StructureData -> ASE
        atoms2 = s.get_ase()
        assert list(atoms2.get_tags()) == list(atoms.get_tags())
        assert list(atoms2.get_chemical_symbols()) == list(atoms.get_chemical_symbols())
        assert atoms2.get_chemical_formula() == 'Fe5'

    @skip_ase
    def test_conversion_of_types_5(self):
        """Tests ASE -> StructureData -> ASE, in particular conversion tags / kind names
        (subtle variation of test_conversion_of_types_4)
        """
        import ase

        atoms = ase.Atoms('Fe5')
        atoms[0].tag = 1
        atoms[2].tag = 1
        atoms[3].tag = 4
        atoms.set_cell([1, 1, 1])
        s = StructureData(ase=atoms)
        kindnames = {k.name for k in s.kinds}
        assert kindnames == set(['Fe', 'Fe1', 'Fe4'])
        # check roundtrip ASE -> StructureData -> ASE
        atoms2 = s.get_ase()
        assert list(atoms2.get_tags()) == list(atoms.get_tags())
        assert list(atoms2.get_chemical_symbols()) == list(atoms.get_chemical_symbols())
        assert atoms2.get_chemical_formula() == 'Fe5'

    @skip_ase
    def test_conversion_of_types_6(self):
        """Tests roundtrip StructureData -> ASE -> StructureData, with tags/kind names"""
        a = StructureData(cell=[[4, 0, 0], [0, 4, 0], [0, 0, 4]])
        a.append_atom(position=(0, 0, 0), symbols='Ni', name='Ni1')
        a.append_atom(position=(2, 2, 2), symbols='Ni', name='Ni2')
        a.append_atom(position=(1, 0, 1), symbols='Cl', name='Cl')
        a.append_atom(position=(1, 3, 1), symbols='Cl', name='Cl')

        b = a.get_ase()
        assert b.get_chemical_symbols() == ['Ni', 'Ni', 'Cl', 'Cl']
        assert list(b.get_tags()) == [1, 2, 0, 0]

        c = StructureData(ase=b)
        assert c.get_site_kindnames() == ['Ni1', 'Ni2', 'Cl', 'Cl']
        assert [k.symbol for k in c.kinds] == ['Ni', 'Ni', 'Cl']
        assert [s.position for s in c.sites] == [(0.0, 0.0, 0.0), (2.0, 2.0, 2.0), (1.0, 0.0, 1.0), (1.0, 3.0, 1.0)]


class TestStructureDataFromPymatgen:
    """Tests the creation of StructureData from a pymatgen Structure and
    Molecule objects.
    """

    @skip_pymatgen
    @pytest.mark.filterwarnings('ignore:Cannot determine chemical composition from CIF:UserWarning:pymatgen.io')
    def test_1(self):
        """Tests roundtrip pymatgen -> StructureData -> pymatgen
        Test's input is derived from COD entry 9011963, processed with
        cif_mark_disorder (from cod-tools) and abbreviated.
        """
        from pymatgen.io.cif import CifParser

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.cif') as tmpf:
            tmpf.write(
                """data_9011963
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
                """
            )
            tmpf.flush()
            pymatgen_parser = CifParser(tmpf.name)
            pymatgen_struct = pymatgen_parser.parse_structures(primitive=True)[0]

        structs_to_test = [StructureData(pymatgen=pymatgen_struct), StructureData(pymatgen_structure=pymatgen_struct)]

        for struct in structs_to_test:
            assert struct.get_site_kindnames() == ['Bi', 'Bi', 'SeTe', 'SeTe', 'SeTe']

            # Pymatgen's Composition does not guarantee any particular ordering of the kinds,
            # see the definition of its internal datatype at
            #   pymatgen/core/composition.py#L135 (d4fe64c18a52949a4e22bfcf7b45de5b87242c51)
            assert [sorted(x.symbols) for x in struct.kinds] == [
                [
                    'Bi',
                ],
                ['Se', 'Te'],
            ]
            assert [sorted(x.weights) for x in struct.kinds] == [
                [
                    1.0,
                ],
                [0.33333, 0.66667],
            ]

        struct = StructureData(pymatgen_structure=pymatgen_struct)

        # Testing pymatgen Structure -> StructureData -> pymatgen Structure roundtrip.
        pymatgen_struct_roundtrip = struct.get_pymatgen_structure()
        dict1 = pymatgen_struct.as_dict()
        dict2 = pymatgen_struct_roundtrip.as_dict()

        # In pymatgen v2023.7.14 the CIF parsing was updated to include the parsing to atomic site labels. However, this
        # information is not stored in the ``StructureData`` and so the structure after the roundtrip uses the default
        # which is the specie name. The latter is correct in that it reflects the partial occupancies, but it differs
        # from the labels parsed from the CIF which is simply parsed as ``Se1`` causing the test to fail. Since the
        # site label information is not stored in the ``StructureData`` it is not possible to preserve it in the
        # roundtrip and so it is excluded from the check.
        for dictionary in [dict1, dict2]:
            for site in dictionary['sites']:
                site.pop('label', None)

        for i in dict1['sites']:
            i['abc'] = [round(j, 2) for j in i['abc']]
        for i in dict2['sites']:
            i['abc'] = [round(j, 2) for j in i['abc']]

        def recursively_compare_values(left, right):
            from collections.abc import Mapping

            from numpy import testing

            if isinstance(left, Mapping):
                for key, value in left.items():
                    recursively_compare_values(value, right[key])
            elif isinstance(left, (list, tuple)):
                for val1, val2 in zip(left, right):
                    recursively_compare_values(val1, val2)
            elif isinstance(left, float):
                testing.assert_almost_equal(left, right)
            else:
                assert left == right, f'{left} is not {right}'

        recursively_compare_values(dict1, dict2)

    @skip_pymatgen
    def test_2(self):
        """Tests xyz -> pymatgen -> StructureData
        Input source: http://pymatgen.org/_static/Molecule.html
        """
        from pymatgen.io.xyz import XYZ

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.xyz') as tmpf:
            tmpf.write(
                """5
                H4 C1
                C 0.000000 0.000000 0.000000
                H 0.000000 0.000000 1.089000
                H 1.026719 0.000000 -0.363000
                H -0.513360 -0.889165 -0.363000
                H -0.513360 0.889165 -0.363000"""
            )
            tmpf.flush()
            pymatgen_xyz = XYZ.from_file(tmpf.name)
            pymatgen_mol = pymatgen_xyz.molecule

        for struct in [StructureData(pymatgen=pymatgen_mol), StructureData(pymatgen_molecule=pymatgen_mol)]:
            assert struct.get_site_kindnames() == ['H', 'H', 'H', 'H', 'C']
            assert struct.pbc == (False, False, False)
            assert [round(x, 2) for x in list(struct.sites[0].position)] == [5.77, 5.89, 6.81]
            assert [round(x, 2) for x in list(struct.sites[1].position)] == [6.8, 5.89, 5.36]
            assert [round(x, 2) for x in list(struct.sites[2].position)] == [5.26, 5.0, 5.36]
            assert [round(x, 2) for x in list(struct.sites[3].position)] == [5.26, 6.78, 5.36]
            assert [round(x, 2) for x in list(struct.sites[4].position)] == [5.77, 5.89, 5.73]

    @skip_pymatgen
    def test_partial_occ_and_spin(self):
        """Tests pymatgen -> StructureData, with partial occupancies and spins.
        This should raise a ValueError.
        """
        from pymatgen.core.composition import Composition
        from pymatgen.core.periodic_table import Specie
        from pymatgen.core.structure import Structure

        try:
            Fe_spin_up = Specie('Fe', 0, spin=1)
            Mn_spin_up = Specie('Mn', 0, spin=1)
            Fe_spin_down = Specie('Fe', 0, spin=-1)
            Mn_spin_down = Specie('Mn', 0, spin=-1)
        except TypeError:
            Fe_spin_up = Specie('Fe', 0, properties={'spin': 1})
            Mn_spin_up = Specie('Mn', 0, properties={'spin': 1})
            Fe_spin_down = Specie('Fe', 0, properties={'spin': -1})
            Mn_spin_down = Specie('Mn', 0, properties={'spin': -1})
        FeMn1 = Composition({Fe_spin_up: 0.5, Mn_spin_up: 0.5})
        FeMn2 = Composition({Fe_spin_down: 0.5, Mn_spin_down: 0.5})
        a = Structure(
            lattice=[[4, 0, 0], [0, 4, 0], [0, 0, 4]], species=[FeMn1, FeMn2], coords=[[0, 0, 0], [0.5, 0.5, 0.5]]
        )

        with pytest.raises(ValueError):
            StructureData(pymatgen=a)

        # same, with vacancies
        Fe1 = Composition({Fe_spin_up: 0.5})
        Fe2 = Composition({Fe_spin_down: 0.5})
        a = Structure(
            lattice=[[4, 0, 0], [0, 4, 0], [0, 0, 4]], species=[Fe1, Fe2], coords=[[0, 0, 0], [0.5, 0.5, 0.5]]
        )

        with pytest.raises(ValueError):
            StructureData(pymatgen=a)

    @skip_pymatgen
    @staticmethod
    def test_multiple_kinds_partial_occupancies():
        """Tests that a structure with multiple sites with the same element but different
        partial occupancies, get their own unique kind name.
        """
        from pymatgen.core.composition import Composition
        from pymatgen.core.structure import Structure

        Mg1 = Composition({'Mg': 0.50})
        Mg2 = Composition({'Mg': 0.25})

        a = Structure(
            lattice=[[4, 0, 0], [0, 4, 0], [0, 0, 4]], species=[Mg1, Mg2], coords=[[0, 0, 0], [0.5, 0.5, 0.5]]
        )

        StructureData(pymatgen=a)

    @skip_pymatgen
    @staticmethod
    def test_multiple_kinds_alloy():
        """Tests that a structure with multiple sites with the same alloy symbols but different
        weights, get their own unique kind name
        """
        from pymatgen.core.composition import Composition
        from pymatgen.core.structure import Structure

        alloy_one = Composition({'Mg': 0.25, 'Al': 0.75})
        alloy_two = Composition({'Mg': 0.45, 'Al': 0.55})

        a = Structure(
            lattice=[[4, 0, 0], [0, 4, 0], [0, 0, 4]],
            species=[alloy_one, alloy_two],
            coords=[[0, 0, 0], [0.5, 0.5, 0.5]],
        )

        StructureData(pymatgen=a)


class TestPymatgenFromStructureData:
    """Tests the creation of pymatgen Structure and Molecule objects from
    StructureData.
    """

    @skip_pymatgen
    @pytest.mark.parametrize(
        'pbc', ((True, True, True), (True, True, False), (True, False, False), (False, False, False))
    )
    def test_get_pymatgen_structure_pbc(self, pbc):
        """Tests the check of periodic boundary conditions when using the `get_pymatgen_structure` method."""
        import numpy as np

        cell = np.diag((1, 1, 1)).tolist()
        symbols = ['Ba', 'Ba', 'Zr', 'Zr', 'O', 'O', 'O', 'O', 'O', 'O']
        structure = StructureData(cell=cell, pbc=pbc)

        for symbol in symbols:
            structure.append_atom(name=symbol, symbols=[symbol], position=[0, 0, 0])

        pymatgen = structure.get_pymatgen_structure()
        assert pymatgen.lattice.pbc == pbc
        assert pymatgen.lattice.matrix.tolist() == cell

    @skip_pymatgen
    def test_no_pbc(self):
        """Tests the `get_pymatgen*` methods for a 0D system, i.e. no periodic boundary conditions.

        We expect `get_pymatgen` to return a `pymatgen.core.structure.Molecule` instance, and
        `get_pymatgen_structure` to except since we did not set a cell, i.e. singular matrix is given.
        """
        from pymatgen.core.structure import Molecule

        symbol, pbc = 'Si', (False, False, False)
        structure = StructureData(pbc=pbc)
        structure.append_atom(name=symbol, symbols=[symbol], position=[0, 0, 0])

        pymatgen = structure.get_pymatgen()
        assert isinstance(pymatgen, Molecule)

        match = 'Singular cell detected. Probably the cell was not set?'
        with pytest.raises(ValueError, match=match):
            structure.get_pymatgen_structure()

    @skip_ase
    @skip_pymatgen
    def test_roundtrip_ase_aiida_pymatgen_structure(self):
        """Tests ASE -> StructureData -> pymatgen."""
        import ase

        aseatoms = ase.Atoms('Si4', cell=(1.0, 2.0, 3.0), pbc=(True, True, True))
        aseatoms.set_scaled_positions(
            (
                (0.0, 0.0, 0.0),
                (0.1, 0.1, 0.1),
                (0.2, 0.2, 0.2),
                (0.3, 0.3, 0.3),
            )
        )

        a_struct = StructureData(ase=aseatoms)
        p_struct = a_struct.get_pymatgen_structure()

        p_struct_dict = p_struct.as_dict()
        coord_array = [x['abc'] for x in p_struct_dict['sites']]
        for i, _ in enumerate(coord_array):
            coord_array[i] = [round(x, 2) for x in coord_array[i]]

        assert coord_array == [[0.0, 0.0, 0.0], [0.1, 0.1, 0.1], [0.2, 0.2, 0.2], [0.3, 0.3, 0.3]]

    @skip_ase
    @skip_pymatgen
    def test_roundtrip_ase_aiida_pymatgen_molecule(self):
        """Tests the conversion of StructureData to pymatgen's Molecule
        (ASE -> StructureData -> pymatgen)
        """
        import ase

        aseatoms = ase.Atoms('Si4', cell=(10, 10, 10), pbc=(True, True, True))
        aseatoms.set_scaled_positions(
            (
                (0.0, 0.0, 0.0),
                (0.1, 0.1, 0.1),
                (0.2, 0.2, 0.2),
                (0.3, 0.3, 0.3),
            )
        )

        a_struct = StructureData(ase=aseatoms)
        p_mol = a_struct.get_pymatgen_molecule()

        p_mol_dict = p_mol.as_dict()
        assert [x['xyz'] for x in p_mol_dict['sites']] == [
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0],
            [3.0, 3.0, 3.0],
        ]

    @skip_pymatgen
    def test_roundtrip_aiida_pymatgen_aiida(self):
        """Tests roundtrip StructureData -> pymatgen -> StructureData
        (no spins)
        """
        a = StructureData(cell=[[5.6, 0, 0], [0, 5.6, 0], [0, 0, 5.6]])
        a.append_atom(position=(0, 0, 0), symbols='Cl')
        a.append_atom(position=(2.8, 0, 2.8), symbols='Cl')
        a.append_atom(position=(0, 2.8, 2.8), symbols='Cl')
        a.append_atom(position=(2.8, 2.8, 0), symbols='Cl')
        a.append_atom(position=(2.8, 2.8, 2.8), symbols='Na')
        a.append_atom(position=(2.8, 0, 0), symbols='Na')
        a.append_atom(position=(0, 2.8, 0), symbols='Na')
        a.append_atom(position=(0, 0, 2.8), symbols='Na')

        b = a.get_pymatgen()
        c = StructureData(pymatgen=b)
        assert c.get_site_kindnames() == ['Cl', 'Cl', 'Cl', 'Cl', 'Na', 'Na', 'Na', 'Na']
        assert [k.symbol for k in c.kinds] == ['Cl', 'Na']
        assert [s.position for s in c.sites] == [
            (0.0, 0.0, 0.0),
            (2.8, 0, 2.8),
            (0, 2.8, 2.8),
            (2.8, 2.8, 0),
            (2.8, 2.8, 2.8),
            (2.8, 0, 0),
            (0, 2.8, 0),
            (0, 0, 2.8),
        ]

    @skip_pymatgen
    def test_roundtrip_kindnames(self):
        """Tests roundtrip StructureData -> pymatgen -> StructureData
        (no spins, but with all kind of kind names)
        """
        a = StructureData(cell=[[5.6, 0, 0], [0, 5.6, 0], [0, 0, 5.6]])
        a.append_atom(position=(0, 0, 0), symbols='Cl', name='Cl')
        a.append_atom(position=(2.8, 0, 2.8), symbols='Cl', name='Cl10')
        a.append_atom(position=(0, 2.8, 2.8), symbols='Cl', name='Cla')
        a.append_atom(position=(2.8, 2.8, 0), symbols='Cl', name='cl_x')
        a.append_atom(position=(2.8, 2.8, 2.8), symbols='Na', name='Na1')
        a.append_atom(position=(2.8, 0, 0), symbols='Na', name='Na2')
        a.append_atom(position=(0, 2.8, 0), symbols='Na', name='Na_Na')
        a.append_atom(position=(0, 0, 2.8), symbols='Na', name='Na4')

        b = a.get_pymatgen()
        assert [site.properties['kind_name'] for site in b.sites] == [
            'Cl',
            'Cl10',
            'Cla',
            'cl_x',
            'Na1',
            'Na2',
            'Na_Na',
            'Na4',
        ]

        c = StructureData(pymatgen=b)
        assert c.get_site_kindnames() == ['Cl', 'Cl10', 'Cla', 'cl_x', 'Na1', 'Na2', 'Na_Na', 'Na4']
        assert c.get_symbols_set() == set(['Cl', 'Na'])
        assert [s.position for s in c.sites] == [
            (0.0, 0.0, 0.0),
            (2.8, 0, 2.8),
            (0, 2.8, 2.8),
            (2.8, 2.8, 0),
            (2.8, 2.8, 2.8),
            (2.8, 0, 0),
            (0, 2.8, 0),
            (0, 0, 2.8),
        ]

    @skip_pymatgen
    def test_roundtrip_spins(self):
        """Tests roundtrip StructureData -> pymatgen -> StructureData
        (with spins)
        """
        a = StructureData(cell=[[5.6, 0, 0], [0, 5.6, 0], [0, 0, 5.6]])
        a.append_atom(position=(0, 0, 0), symbols='Mn', name='Mn1')
        a.append_atom(position=(2.8, 0, 2.8), symbols='Mn', name='Mn1')
        a.append_atom(position=(0, 2.8, 2.8), symbols='Mn', name='Mn1')
        a.append_atom(position=(2.8, 2.8, 0), symbols='Mn', name='Mn1')
        a.append_atom(position=(2.8, 2.8, 2.8), symbols='Mn', name='Mn2')
        a.append_atom(position=(2.8, 0, 0), symbols='Mn', name='Mn2')
        a.append_atom(position=(0, 2.8, 0), symbols='Mn', name='Mn2')
        a.append_atom(position=(0, 0, 2.8), symbols='Mn', name='Mn2')

        b = a.get_pymatgen(add_spin=True)
        # check the spins
        try:
            assert [s.as_dict()['spin'] for s in b.species] == [-1, -1, -1, -1, 1, 1, 1, 1]
        except KeyError:
            assert [s.as_dict()['properties']['spin'] for s in b.species] == [-1, -1, -1, -1, 1, 1, 1, 1]
        # back to StructureData
        c = StructureData(pymatgen=b)
        assert c.get_site_kindnames() == ['Mn1', 'Mn1', 'Mn1', 'Mn1', 'Mn2', 'Mn2', 'Mn2', 'Mn2']
        assert [k.symbol for k in c.kinds] == ['Mn', 'Mn']
        assert [s.position for s in c.sites] == [
            (0.0, 0.0, 0.0),
            (2.8, 0, 2.8),
            (0, 2.8, 2.8),
            (2.8, 2.8, 0),
            (2.8, 2.8, 2.8),
            (2.8, 0, 0),
            (0, 2.8, 0),
            (0, 0, 2.8),
        ]

    @skip_pymatgen
    def test_roundtrip_partial_occ(self):
        """Tests roundtrip StructureData -> pymatgen -> StructureData
        (with partial occupancies).
        """
        from numpy import testing

        a = StructureData(cell=[[4.0, 0.0, 0.0], [-2.0, 3.5, 0.0], [0.0, 0.0, 16.0]])
        a.append_atom(position=(0.0, 0.0, 13.5), symbols='Mn')
        a.append_atom(position=(0.0, 0.0, 2.6), symbols='Mn')
        a.append_atom(position=(0.0, 0.0, 5.5), symbols='Mn')
        a.append_atom(position=(0.0, 0.0, 11.0), symbols='Mn')
        a.append_atom(position=(2.0, 1.0, 12.0), symbols='Mn', weights=0.8)
        a.append_atom(position=(0.0, 2.2, 4.0), symbols='Mn', weights=0.8)
        a.append_atom(position=(0.0, 2.2, 12.0), symbols='Si')
        a.append_atom(position=(2.0, 1.0, 4.0), symbols='Si')
        a.append_atom(position=(2.0, 1.0, 15.0), symbols='N')
        a.append_atom(position=(0.0, 2.2, 1.5), symbols='N')
        a.append_atom(position=(0.0, 2.2, 7.0), symbols='N')
        a.append_atom(position=(2.0, 1.0, 9.5), symbols='N')

        # a few checks on the structure kinds and symbols
        assert a.get_symbols_set() == set(['Mn', 'Si', 'N'])
        assert a.get_site_kindnames() == ['Mn', 'Mn', 'Mn', 'Mn', 'MnX', 'MnX', 'Si', 'Si', 'N', 'N', 'N', 'N']
        assert a.get_formula() == 'Mn4N4Si2{Mn0.80X0.20}2'

        b = a.get_pymatgen()
        # check the partial occupancies
        assert [s.as_dict() for s in b.species_and_occu] == [
            {'Mn': 1.0},
            {'Mn': 1.0},
            {'Mn': 1.0},
            {'Mn': 1.0},
            {'Mn': 0.8},
            {'Mn': 0.8},
            {'Si': 1.0},
            {'Si': 1.0},
            {'N': 1.0},
            {'N': 1.0},
            {'N': 1.0},
            {'N': 1.0},
        ]

        # back to StructureData
        c = StructureData(pymatgen=b)
        assert c.cell == [[4.0, 0.0, 0.0], [-2.0, 3.5, 0.0], [0.0, 0.0, 16.0]]
        assert c.get_symbols_set() == set(['Mn', 'Si', 'N'])
        assert c.get_site_kindnames() == ['Mn', 'Mn', 'Mn', 'Mn', 'MnX', 'MnX', 'Si', 'Si', 'N', 'N', 'N', 'N']
        assert c.get_formula() == 'Mn4N4Si2{Mn0.80X0.20}2'
        testing.assert_allclose(
            [s.position for s in c.sites],
            [
                (0.0, 0.0, 13.5),
                (0.0, 0.0, 2.6),
                (0.0, 0.0, 5.5),
                (0.0, 0.0, 11.0),
                (2.0, 1.0, 12.0),
                (0.0, 2.2, 4.0),
                (0.0, 2.2, 12.0),
                (2.0, 1.0, 4.0),
                (2.0, 1.0, 15.0),
                (0.0, 2.2, 1.5),
                (0.0, 2.2, 7.0),
                (2.0, 1.0, 9.5),
            ],
        )

    @skip_pymatgen
    def test_partial_occ_and_spin(self):
        """Tests StructureData -> pymatgen, with partial occupancies and spins.
        This should raise a ValueError.
        """
        a = StructureData(cell=[[4, 0, 0], [0, 4, 0], [0, 0, 4]])
        a.append_atom(position=(0, 0, 0), symbols=('Fe', 'Al'), weights=(0.8, 0.2), name='FeAl1')
        a.append_atom(position=(2, 2, 2), symbols=('Fe', 'Al'), weights=(0.8, 0.2), name='FeAl2')

        # a few checks on the structure kinds and symbols
        assert a.get_symbols_set() == set(['Fe', 'Al'])
        assert a.get_site_kindnames() == ['FeAl1', 'FeAl2']
        assert a.get_formula() == '{Al0.20Fe0.80}2'

        with pytest.raises(ValueError):
            a.get_pymatgen(add_spin=True)

        # same, with vacancies
        a = StructureData(cell=[[4, 0, 0], [0, 4, 0], [0, 0, 4]])
        a.append_atom(position=(0, 0, 0), symbols='Fe', weights=0.8, name='FeX1')
        a.append_atom(position=(2, 2, 2), symbols='Fe', weights=0.8, name='FeX2')

        # a few checks on the structure kinds and symbols
        assert a.get_symbols_set() == set(['Fe'])
        assert a.get_site_kindnames() == ['FeX1', 'FeX2']
        assert a.get_formula() == '{Fe0.80X0.20}2'

        with pytest.raises(ValueError):
            a.get_pymatgen(add_spin=True)


class TestArrayData:
    """Tests the ArrayData objects."""

    def test_creation(self):
        """Check the methods to add, remove, modify, and get arrays and
        array shapes.
        """
        # Create a node with two arrays
        n = ArrayData()
        first = np.random.rand(2, 3, 4)
        n.set_array('first', first)

        second = np.arange(10)
        n.set_array('second', second)

        third = np.random.rand(6, 6)
        n.set_array('third', third)

        # Check if the arrays are there
        assert set(['first', 'second', 'third']) == set(n.get_arraynames())
        assert round(abs(abs(first - n.get_array('first')).max() - 0.0), 7) == 0
        assert round(abs(abs(second - n.get_array('second')).max() - 0.0), 7) == 0
        assert round(abs(abs(third - n.get_array('third')).max() - 0.0), 7) == 0
        assert first.shape == n.get_shape('first')
        assert second.shape == n.get_shape('second')
        assert third.shape == n.get_shape('third')

        with pytest.raises(KeyError):
            n.get_array('nonexistent_array')

        # Delete an array, and try to delete a non-existing one
        n.delete_array('third')
        with pytest.raises(KeyError):
            n.delete_array('nonexistent_array')

        # Overwrite an array
        first = np.random.rand(4, 5, 6)
        n.set_array('first', first)

        # Check if the arrays are there, and if I am getting the new one
        assert set(['first', 'second']) == set(n.get_arraynames())
        assert round(abs(abs(first - n.get_array('first')).max() - 0.0), 7) == 0
        assert round(abs(abs(second - n.get_array('second')).max() - 0.0), 7) == 0
        assert first.shape == n.get_shape('first')
        assert second.shape == n.get_shape('second')

        n.store()

        # Same checks, after storing
        assert set(['first', 'second']) == set(n.get_arraynames())
        assert round(abs(abs(first - n.get_array('first')).max() - 0.0), 7) == 0
        assert round(abs(abs(second - n.get_array('second')).max() - 0.0), 7) == 0
        assert first.shape == n.get_shape('first')
        assert second.shape == n.get_shape('second')

        # Same checks, again (this is checking the caching features)
        assert set(['first', 'second']) == set(n.get_arraynames())
        assert round(abs(abs(first - n.get_array('first')).max() - 0.0), 7) == 0
        assert round(abs(abs(second - n.get_array('second')).max() - 0.0), 7) == 0
        assert first.shape == n.get_shape('first')
        assert second.shape == n.get_shape('second')

        # Same checks, after reloading
        n2 = load_node(uuid=n.uuid)
        assert set(['first', 'second']) == set(n2.get_arraynames())
        assert round(abs(abs(first - n2.get_array('first')).max() - 0.0), 7) == 0
        assert round(abs(abs(second - n2.get_array('second')).max() - 0.0), 7) == 0
        assert first.shape == n2.get_shape('first')
        assert second.shape == n2.get_shape('second')

        # Same checks, after reloading with UUID
        n2 = load_node(n.uuid, sub_classes=(ArrayData,))
        assert set(['first', 'second']) == set(n2.get_arraynames())
        assert round(abs(abs(first - n2.get_array('first')).max() - 0.0), 7) == 0
        assert round(abs(abs(second - n2.get_array('second')).max() - 0.0), 7) == 0
        assert first.shape == n2.get_shape('first')
        assert second.shape == n2.get_shape('second')

        # Check that I cannot modify the node after storing
        with pytest.raises(ModificationNotAllowed):
            n.delete_array('first')
        with pytest.raises(ModificationNotAllowed):
            n.set_array('second', first)

        # Again same checks, to verify that the attempts to delete/overwrite
        # arrays did not damage the node content
        assert set(['first', 'second']) == set(n.get_arraynames())
        assert round(abs(abs(first - n.get_array('first')).max() - 0.0), 7) == 0
        assert round(abs(abs(second - n.get_array('second')).max() - 0.0), 7) == 0
        assert first.shape == n.get_shape('first')
        assert second.shape == n.get_shape('second')

    def test_iteration(self):
        """Check the functionality of the get_iterarrays() iterator"""
        # Create a node with two arrays
        n = ArrayData()
        first = np.random.rand(2, 3, 4)
        n.set_array('first', first)

        second = np.arange(10)
        n.set_array('second', second)

        third = np.random.rand(6, 6)
        n.set_array('third', third)

        for name, array in n.get_iterarrays():
            if name == 'first':
                assert round(abs(abs(first - array).max() - 0.0), 7) == 0
            if name == 'second':
                assert round(abs(abs(second - array).max() - 0.0), 7) == 0
            if name == 'third':
                assert round(abs(abs(third - array).max() - 0.0), 7) == 0


class TestTrajectoryData:
    """Tests the TrajectoryData objects."""

    def test_creation(self):
        """Check the methods to set and retrieve a trajectory."""
        # Create a node with two arrays
        n = TrajectoryData()

        # I create sample data
        stepids = np.array([60, 70])
        times = stepids * 0.01
        cells = np.array(
            [
                [
                    [
                        2.0,
                        0.0,
                        0.0,
                    ],
                    [
                        0.0,
                        2.0,
                        0.0,
                    ],
                    [
                        0.0,
                        0.0,
                        2.0,
                    ],
                ],
                [
                    [
                        3.0,
                        0.0,
                        0.0,
                    ],
                    [
                        0.0,
                        3.0,
                        0.0,
                    ],
                    [
                        0.0,
                        0.0,
                        3.0,
                    ],
                ],
            ]
        )
        symbols = ['H', 'O', 'C']
        positions = np.array(
            [[[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]], [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]]]
        )
        velocities = np.array(
            [
                [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
                [[0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, -0.5, -0.5]],
            ]
        )

        # I set the node
        n.set_trajectory(
            stepids=stepids, cells=cells, symbols=symbols, positions=positions, times=times, velocities=velocities
        )

        # Generic checks
        assert n.numsites == 3
        assert n.numsteps == 2
        assert round(abs(abs(stepids - n.get_stepids()).sum() - 0.0), 7) == 0
        assert round(abs(abs(times - n.get_times()).sum() - 0.0), 7) == 0
        assert round(abs(abs(cells - n.get_cells()).sum() - 0.0), 7) == 0
        assert symbols == n.symbols
        assert round(abs(abs(positions - n.get_positions()).sum() - 0.0), 7) == 0
        assert round(abs(abs(velocities - n.get_velocities()).sum() - 0.0), 7) == 0

        # get_step_data function check
        data = n.get_step_data(1)
        assert data[0] == stepids[1]
        assert round(abs(data[1] - times[1]), 7) == 0
        assert round(abs(abs(cells[1] - data[2]).sum() - 0.0), 7) == 0
        assert symbols == data[3]
        assert round(abs(abs(data[4] - positions[1]).sum() - 0.0), 7) == 0
        assert round(abs(abs(data[5] - velocities[1]).sum() - 0.0), 7) == 0

        # Step 70 has index 1
        assert n.get_index_from_stepid(70) == 1
        with pytest.raises(ValueError):
            # Step 66 does not exist
            n.get_index_from_stepid(66)

        ########################################################
        # I set the node, this time without times or velocities (the same node)
        n.set_trajectory(stepids=stepids, cells=cells, symbols=symbols, positions=positions)
        # Generic checks
        assert n.numsites == 3
        assert n.numsteps == 2
        assert round(abs(abs(stepids - n.get_stepids()).sum() - 0.0), 7) == 0
        assert n.get_times() is None
        assert round(abs(abs(cells - n.get_cells()).sum() - 0.0), 7) == 0
        assert symbols == n.symbols
        assert round(abs(abs(positions - n.get_positions()).sum() - 0.0), 7) == 0
        assert n.get_velocities() is None

        # Same thing, but for a new node
        n = TrajectoryData()
        n.set_trajectory(stepids=stepids, cells=cells, symbols=symbols, positions=positions)
        # Generic checks
        assert n.numsites == 3
        assert n.numsteps == 2
        assert round(abs(abs(stepids - n.get_stepids()).sum() - 0.0), 7) == 0
        assert n.get_times() is None
        assert round(abs(abs(cells - n.get_cells()).sum() - 0.0), 7) == 0
        assert symbols == n.symbols
        assert round(abs(abs(positions - n.get_positions()).sum() - 0.0), 7) == 0
        assert n.get_velocities() is None

        ########################################################
        # I set the node, this time without velocities (the same node)
        n.set_trajectory(stepids=stepids, cells=cells, symbols=symbols, positions=positions, times=times)
        # Generic checks
        assert n.numsites == 3
        assert n.numsteps == 2
        assert round(abs(abs(stepids - n.get_stepids()).sum() - 0.0), 7) == 0
        assert round(abs(abs(times - n.get_times()).sum() - 0.0), 7) == 0
        assert round(abs(abs(cells - n.get_cells()).sum() - 0.0), 7) == 0
        assert symbols == n.symbols
        assert round(abs(abs(positions - n.get_positions()).sum() - 0.0), 7) == 0
        assert n.get_velocities() is None

        # Same thing, but for a new node
        n = TrajectoryData()
        n.set_trajectory(stepids=stepids, cells=cells, symbols=symbols, positions=positions, times=times)
        # Generic checks
        assert n.numsites == 3
        assert n.numsteps == 2
        assert round(abs(abs(stepids - n.get_stepids()).sum() - 0.0), 7) == 0
        assert round(abs(abs(times - n.get_times()).sum() - 0.0), 7) == 0
        assert round(abs(abs(cells - n.get_cells()).sum() - 0.0), 7) == 0
        assert symbols == n.symbols
        assert round(abs(abs(positions - n.get_positions()).sum() - 0.0), 7) == 0
        assert n.get_velocities() is None

        n.store()

        # Again same checks, but after storing
        # Generic checks
        assert n.numsites == 3
        assert n.numsteps == 2
        assert round(abs(abs(stepids - n.get_stepids()).sum() - 0.0), 7) == 0
        assert round(abs(abs(times - n.get_times()).sum() - 0.0), 7) == 0
        assert round(abs(abs(cells - n.get_cells()).sum() - 0.0), 7) == 0
        assert symbols == n.symbols
        assert round(abs(abs(positions - n.get_positions()).sum() - 0.0), 7) == 0
        assert n.get_velocities() is None

        # get_step_data function check
        data = n.get_step_data(1)
        assert data[0] == stepids[1]
        assert round(abs(data[1] - times[1]), 7) == 0
        assert round(abs(abs(cells[1] - data[2]).sum() - 0.0), 7) == 0
        assert symbols == data[3]
        assert round(abs(abs(data[4] - positions[1]).sum() - 0.0), 7) == 0
        assert data[5] is None

        # Step 70 has index 1
        assert n.get_index_from_stepid(70) == 1
        with pytest.raises(ValueError):
            # Step 66 does not exist
            n.get_index_from_stepid(66)

        ##############################################################
        # Again, but after reloading from uuid
        n = load_node(n.uuid, sub_classes=(TrajectoryData,))
        # Generic checks
        assert n.numsites == 3
        assert n.numsteps == 2
        assert round(abs(abs(stepids - n.get_stepids()).sum() - 0.0), 7) == 0
        assert round(abs(abs(times - n.get_times()).sum() - 0.0), 7) == 0
        assert round(abs(abs(cells - n.get_cells()).sum() - 0.0), 7) == 0
        assert symbols == n.symbols
        assert round(abs(abs(positions - n.get_positions()).sum() - 0.0), 7) == 0
        assert n.get_velocities() is None

        # get_step_data function check
        data = n.get_step_data(1)
        assert data[0] == stepids[1]
        assert round(abs(data[1] - times[1]), 7) == 0
        assert round(abs(abs(cells[1] - data[2]).sum() - 0.0), 7) == 0
        assert symbols == data[3]
        assert round(abs(abs(data[4] - positions[1]).sum() - 0.0), 7) == 0
        assert data[5] is None

        # Step 70 has index 1
        assert n.get_index_from_stepid(70) == 1
        with pytest.raises(ValueError):
            # Step 66 does not exist
            n.get_index_from_stepid(66)

    @pytest.mark.requires_rmq
    def test_conversion_to_structure(self):
        """Check the methods to export a given time step to a StructureData node."""
        # Create a node with two arrays
        n = TrajectoryData()

        # I create sample data
        stepids = np.array([60, 70])
        times = stepids * 0.01
        cells = np.array(
            [
                [
                    [
                        2.0,
                        0.0,
                        0.0,
                    ],
                    [
                        0.0,
                        2.0,
                        0.0,
                    ],
                    [
                        0.0,
                        0.0,
                        2.0,
                    ],
                ],
                [
                    [
                        3.0,
                        0.0,
                        0.0,
                    ],
                    [
                        0.0,
                        3.0,
                        0.0,
                    ],
                    [
                        0.0,
                        0.0,
                        3.0,
                    ],
                ],
            ]
        )
        symbols = ['H', 'O', 'C']
        positions = np.array(
            [[[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]], [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]]]
        )
        velocities = np.array(
            [
                [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
                [[0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, -0.5, -0.5]],
            ]
        )

        # I set the node
        n.set_trajectory(
            stepids=stepids, cells=cells, symbols=symbols, positions=positions, times=times, velocities=velocities
        )

        from_step = n.get_step_structure(1)
        from_get_structure = n.get_structure(index=1)

        for struc in [from_step, from_get_structure]:
            assert len(struc.sites) == 3  # 3 sites
            assert round(abs(abs(np.array(struc.cell) - cells[1]).sum() - 0), 7) == 0
            newpos = np.array([s.position for s in struc.sites])
            assert round(abs(abs(newpos - positions[1]).sum() - 0), 7) == 0
            newkinds = [s.kind_name for s in struc.sites]
            assert newkinds == symbols

            # Weird assignments (nobody should ever do this, but it is possible in
            # principle and we want to check
            k1 = Kind(name='C', symbols='Cu')
            k2 = Kind(name='H', symbols='He')
            k3 = Kind(name='O', symbols='Os', mass=100.0)
            k4 = Kind(name='Ge', symbols='Ge')

            with pytest.raises(ValueError):
                # Not enough kinds
                n.get_step_structure(1, custom_kinds=[k1, k2])

            with pytest.raises(ValueError):
                # Too many kinds
                n.get_step_structure(1, custom_kinds=[k1, k2, k3, k4])

            with pytest.raises(ValueError):
                # Wrong kinds
                n.get_step_structure(1, custom_kinds=[k1, k2, k4])

            with pytest.raises(ValueError):
                # Two kinds with the same name
                n.get_step_structure(1, custom_kinds=[k1, k2, k3, k3])

            # Correct kinds
            structure = n.get_step_structure(1, custom_kinds=[k1, k2, k3])

            # Checks
            assert len(structure.sites) == 3  # 3 sites
            assert round(abs(abs(np.array(structure.cell) - cells[1]).sum() - 0), 7) == 0
            newpos = np.array([s.position for s in structure.sites])
            assert round(abs(abs(newpos - positions[1]).sum() - 0), 7) == 0
            newkinds = [s.kind_name for s in structure.sites]
            # Kinds are in the same order as given in the custm_kinds list
            assert newkinds == symbols
            newatomtypes = [structure.get_kind(s.kind_name).symbols[0] for s in structure.sites]
            # Atoms remain in the same order as given in the positions list
            assert newatomtypes == ['He', 'Os', 'Cu']
            # Check the mass of the kind of the second atom ('O' _> symbol Os, mass 100)
            assert round(abs(structure.get_kind(structure.sites[1].kind_name).mass - 100.0), 7) == 0

    def test_conversion_from_structurelist(self):
        """Check the method to create a TrajectoryData from list of AiiDA
        structures.
        """
        cells = [
            [
                [
                    2.0,
                    0.0,
                    0.0,
                ],
                [
                    0.0,
                    2.0,
                    0.0,
                ],
                [
                    0.0,
                    0.0,
                    2.0,
                ],
            ],
            [
                [
                    3.0,
                    0.0,
                    0.0,
                ],
                [
                    0.0,
                    3.0,
                    0.0,
                ],
                [
                    0.0,
                    0.0,
                    3.0,
                ],
            ],
        ]
        symbols = [['H', 'O', 'C'], ['H', 'O', 'C']]
        positions = [
            [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]],
            [[0.0, 0.0, 0.0], [0.75, 0.75, 0.75], [1.25, 1.25, 1.25]],
        ]
        structurelist = []
        for i in range(0, 2):
            struct = StructureData(cell=cells[i])
            for j, symbol in enumerate(symbols[i]):
                struct.append_atom(symbols=symbol, position=positions[i][j])
            structurelist.append(struct)

        td = TrajectoryData(structurelist=structurelist)
        assert td.get_cells().tolist() == cells
        assert td.symbols == symbols[0]
        assert td.get_positions().tolist() == positions

        symbols = [['H', 'O', 'C'], ['H', 'O', 'P']]
        structurelist = []
        for i in range(0, 2):
            struct = StructureData(cell=cells[i])
            for j, symbol in enumerate(symbols[i]):
                struct.append_atom(symbols=symbol, position=positions[i][j])
            structurelist.append(struct)

        with pytest.raises(ValueError):
            td = TrajectoryData(structurelist=structurelist)

    @staticmethod
    def test_export_to_file():
        """Export the band structure on a file, check if it is working."""
        n = TrajectoryData()

        # I create sample data
        stepids = np.array([60, 70])
        times = stepids * 0.01
        cells = np.array(
            [
                [
                    [
                        2.0,
                        0.0,
                        0.0,
                    ],
                    [
                        0.0,
                        2.0,
                        0.0,
                    ],
                    [
                        0.0,
                        0.0,
                        2.0,
                    ],
                ],
                [
                    [
                        3.0,
                        0.0,
                        0.0,
                    ],
                    [
                        0.0,
                        3.0,
                        0.0,
                    ],
                    [
                        0.0,
                        0.0,
                        3.0,
                    ],
                ],
            ]
        )
        symbols = ['H', 'O', 'C']
        positions = np.array(
            [[[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]], [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [1.5, 1.5, 1.5]]]
        )
        velocities = np.array(
            [
                [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
                [[0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, -0.5, -0.5]],
            ]
        )

        # I set the node
        n.set_trajectory(
            stepids=stepids, cells=cells, symbols=symbols, positions=positions, times=times, velocities=velocities
        )

        # It is not obvious how to check that the bands are correct.
        # I just check, for a few formats, that the file is correctly
        # created, at this stage
        ## I use this to get a file. I then close it and ask the .export() function
        ## to create it again. I have to remember to delete everything at the end.
        handle, filename = tempfile.mkstemp()
        os.close(handle)
        os.remove(filename)

        if has_pycifrw():
            formats_to_test = ['cif', 'xsf']
        else:
            formats_to_test = ['xsf']
        for frmt in formats_to_test:
            files_created = []  # In case there is an exception
            try:
                files_created = n.export(filename, fileformat=frmt)
                with open(filename, encoding='utf8') as fhandle:
                    fhandle.read()
            finally:
                for file in files_created:
                    if os.path.exists(file):
                        os.remove(file)


class TestKpointsData:
    """Tests the KpointsData objects."""

    def test_mesh(self):
        """Check the methods to set and retrieve a mesh."""
        # Create a node with two arrays
        k = KpointsData()

        # check whether the mesh can be set properly
        input_mesh = [4, 4, 4]
        k.set_kpoints_mesh(input_mesh)
        mesh, offset = k.get_kpoints_mesh()
        assert mesh == input_mesh
        assert offset == [0.0, 0.0, 0.0]  # must be a tuple of three 0 by default

        # a too long list should fail
        with pytest.raises(ValueError):
            k.set_kpoints_mesh([4, 4, 4, 4])

        # now try to put explicitely an offset
        input_offset = [0.5, 0.5, 0.5]
        k.set_kpoints_mesh(input_mesh, input_offset)
        mesh, offset = k.get_kpoints_mesh()
        assert mesh == input_mesh
        assert offset == input_offset

        # verify the same but after storing
        k.store()
        assert mesh == input_mesh
        assert offset == input_offset

        # cannot modify it after storage
        with pytest.raises(ModificationNotAllowed):
            k.set_kpoints_mesh(input_mesh)

    def test_list(self):
        """Test the method to set and retrieve a kpoint list."""
        k = KpointsData()

        input_klist = np.array(
            [
                (0.0, 0.0, 0.0),
                (0.2, 0.0, 0.0),
                (0.0, 0.2, 0.0),
                (0.0, 0.0, 0.2),
            ]
        )

        # set kpoints list
        k.set_kpoints(input_klist)
        klist = k.get_kpoints()

        # try to get the same
        assert np.array_equal(input_klist, klist)

        # if no cell is set, cannot convert into cartesian
        with pytest.raises(AttributeError):
            _ = k.get_kpoints(cartesian=True)

        # try to set also weights
        # should fail if the weights length do not match kpoints
        input_weights = np.ones(6)
        with pytest.raises(ValueError):
            k.set_kpoints(input_klist, weights=input_weights)

        # try a right one
        input_weights = np.ones(4)
        k.set_kpoints(input_klist, weights=input_weights)
        klist, weights = k.get_kpoints(also_weights=True)
        assert np.array_equal(weights, input_weights)
        assert np.array_equal(klist, input_klist)

        # verify the same, but after storing
        k.store()
        klist, weights = k.get_kpoints(also_weights=True)
        assert np.array_equal(weights, input_weights)
        assert np.array_equal(klist, input_klist)

        # cannot modify it after storage
        with pytest.raises(ModificationNotAllowed):
            k.set_kpoints(input_klist)

    def test_kpoints_to_cartesian(self):
        """Test how the list of kpoints is converted to cartesian coordinates"""
        k = KpointsData()

        input_klist = np.array(
            [
                (0.0, 0.0, 0.0),
                (0.2, 0.0, 0.0),
                (0.0, 0.2, 0.0),
                (0.0, 0.0, 0.2),
            ]
        )

        # define a cell
        alat = 4.0
        cell = np.array(
            [
                [alat, 0.0, 0.0],
                [0.0, alat, 0.0],
                [0.0, 0.0, alat],
            ]
        )

        k.set_cell(cell)

        # set kpoints list
        k.set_kpoints(input_klist)

        # verify that it is not the same of the input
        # (at least I check that there something has been done)
        klist = k.get_kpoints(cartesian=True)
        assert not np.array_equal(klist, input_klist)

        # put the kpoints in cartesian and get them back, they should be equal
        # internally it is doing two matrix transforms
        k.set_kpoints(input_klist, cartesian=True)
        klist = k.get_kpoints(cartesian=True)
        assert np.allclose(klist, input_klist, atol=1e-16)

    def test_path_wrapper_legacy(self):
        """This is a clone of the test_path test but instead it goes through the new wrapper
        calling the deprecated legacy implementation. This tests that the wrapper maintains
        the same behavior of the old implementation
        """
        from aiida.tools.data.array.kpoints import get_explicit_kpoints_path

        # Shouldn't get anything without having set the cell
        with pytest.raises(AttributeError):
            get_explicit_kpoints_path(None)

        # Define a cell
        alat = 4.0
        cell = np.array(
            [
                [alat, 0.0, 0.0],
                [0.0, alat, 0.0],
                [0.0, 0.0, alat],
            ]
        )

        structure = StructureData(cell=cell)

        # test the various formats for specifying the path
        get_explicit_kpoints_path(
            structure,
            method='legacy',
            value=[
                ('G', 'M'),
            ],
        )
        get_explicit_kpoints_path(
            structure,
            method='legacy',
            value=[
                ('G', 'M', 30),
            ],
        )
        get_explicit_kpoints_path(
            structure,
            method='legacy',
            value=[
                ('G', (0.0, 0.0, 0.0), 'M', (1.0, 1.0, 1.0)),
            ],
        )
        get_explicit_kpoints_path(
            structure,
            method='legacy',
            value=[
                ('G', (0.0, 0.0, 0.0), 'M', (1.0, 1.0, 1.0), 30),
            ],
        )

        # at least 2 points per segment
        with pytest.raises(ValueError):
            get_explicit_kpoints_path(
                structure,
                method='legacy',
                value=[
                    ('G', 'M', 1),
                ],
            )

        with pytest.raises(ValueError):
            get_explicit_kpoints_path(
                structure,
                method='legacy',
                value=[
                    ('G', (0.0, 0.0, 0.0), 'M', (1.0, 1.0, 1.0), 1),
                ],
            )

        # try to set points with a spacing
        get_explicit_kpoints_path(structure, method='legacy', kpoint_distance=0.1)

    def test_tetra_z_wrapper_legacy(self):
        """This is a clone of the test_tetra_z test but instead it goes through the new wrapper
        calling the deprecated legacy implementation. This tests that the wrapper maintains
        the same behavior of the old implementation
        """
        from aiida.tools.data.array.kpoints import get_kpoints_path

        alat = 1.5
        cell_x = [[1, 0, 0], [0, 1, 0], [0, 0, alat]]
        s = StructureData(cell=cell_x)
        result = get_kpoints_path(s, method='legacy', cartesian=True)

        assert isinstance(result['parameters'], Dict)

        point_coords = result['parameters'].dict.point_coords

        assert round(abs(point_coords['Z'][2] - np.pi / alat), 7) == 0
        assert round(abs(point_coords['Z'][0] - 0.0), 7) == 0


class TestSpglibTupleConversion:
    """Tests for conversion of Spglib tuples."""

    def test_simple_to_aiida(self):
        """Test conversion of a simple tuple to an AiiDA structure"""
        from aiida.tools import spglib_tuple_to_structure

        cell = np.array([[4.0, 1.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 4.0]])

        relcoords = np.array(
            [
                [0.09493671, 0.0, 0.0],
                [0.59493671, 0.5, 0.5],
                [0.59493671, 0.5, 0.0],
                [0.59493671, 0.0, 0.5],
                [0.09493671, 0.5, 0.5],
            ]
        )

        abscoords = np.dot(cell.T, relcoords.T).T

        numbers = [56, 22, 8, 8, 8]

        struc = spglib_tuple_to_structure((cell, relcoords, numbers))

        assert round(abs(np.sum(np.abs(np.array(struc.cell) - np.array(cell))) - 0.0), 7) == 0
        assert (
            round(abs(np.sum(np.abs(np.array([site.position for site in struc.sites]) - np.array(abscoords))) - 0.0), 7)
            == 0
        )
        assert [site.kind_name for site in struc.sites] == ['Ba', 'Ti', 'O', 'O', 'O']

    def test_complex1_to_aiida(self):
        """Test conversion of a  tuple to an AiiDA structure when passing also information on the kinds."""
        from aiida.tools import spglib_tuple_to_structure

        cell = np.array([[4.0, 1.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 4.0]])

        relcoords = np.array(
            [
                [0.09493671, 0.0, 0.0],
                [0.59493671, 0.5, 0.5],
                [0.59493671, 0.5, 0.0],
                [0.59493671, 0.0, 0.5],
                [0.09493671, 0.5, 0.5],
                [0.09493671, 0.5, 0.5],
                [0.09493671, 0.5, 0.5],
                [0.09493671, 0.5, 0.5],
                [0.09493671, 0.5, 0.5],
            ]
        )

        abscoords = np.dot(cell.T, relcoords.T).T

        numbers = [56, 22, 8, 8, 8, 56000, 200000, 200001, 56001]

        kind_info = {'Ba': 56, 'Ba2': 56000, 'Ba3': 56001, 'BaTi': 200000, 'BaTi2': 200001, 'O': 8, 'Ti': 22}

        kind_info_wrong = {'Ba': 56, 'Ba2': 56000, 'Ba3': 56002, 'BaTi': 200000, 'BaTi2': 200001, 'O': 8, 'Ti': 22}

        kinds = [
            Kind(name='Ba', symbols='Ba'),
            Kind(name='Ti', symbols='Ti'),
            Kind(name='O', symbols='O'),
            Kind(name='Ba2', symbols='Ba', mass=100.0),
            Kind(name='BaTi', symbols=('Ba', 'Ti'), weights=(0.5, 0.5), mass=100.0),
            Kind(name='BaTi2', symbols=('Ba', 'Ti'), weights=(0.4, 0.6), mass=100.0),
            Kind(name='Ba3', symbols='Ba', mass=100.0),
        ]

        kinds_wrong = [
            Kind(name='Ba', symbols='Ba'),
            Kind(name='Ti', symbols='Ti'),
            Kind(name='O', symbols='O'),
            Kind(name='Ba2', symbols='Ba', mass=100.0),
            Kind(name='BaTi', symbols=('Ba', 'Ti'), weights=(0.5, 0.5), mass=100.0),
            Kind(name='BaTi2', symbols=('Ba', 'Ti'), weights=(0.4, 0.6), mass=100.0),
            Kind(name='Ba4', symbols='Ba', mass=100.0),
        ]

        # Must specify also kind_info and kinds
        with pytest.raises(ValueError):
            struc = spglib_tuple_to_structure(
                (cell, relcoords, numbers),
            )

        # There is no kind_info for one of the numbers
        with pytest.raises(ValueError):
            struc = spglib_tuple_to_structure((cell, relcoords, numbers), kind_info=kind_info_wrong, kinds=kinds)

        # There is no kind in the kinds for one of the labels
        # specified in kind_info
        with pytest.raises(ValueError):
            struc = spglib_tuple_to_structure((cell, relcoords, numbers), kind_info=kind_info, kinds=kinds_wrong)

        struc = spglib_tuple_to_structure((cell, relcoords, numbers), kind_info=kind_info, kinds=kinds)

        assert round(abs(np.sum(np.abs(np.array(struc.cell) - np.array(cell))) - 0.0), 7) == 0
        assert (
            round(abs(np.sum(np.abs(np.array([site.position for site in struc.sites]) - np.array(abscoords))) - 0.0), 7)
            == 0
        )
        assert [site.kind_name for site in struc.sites] == ['Ba', 'Ti', 'O', 'O', 'O', 'Ba2', 'BaTi', 'BaTi2', 'Ba3']

    def test_from_aiida(self):
        """Test conversion of an AiiDA structure to a spglib tuple."""
        from aiida.tools import structure_to_spglib_tuple

        cell = np.array([[4.0, 1.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 4.0]])

        struc = StructureData(cell=cell)
        struc.append_atom(symbols='Ba', position=(0, 0, 0))
        struc.append_atom(symbols='Ti', position=(1, 2, 3))
        struc.append_atom(symbols='O', position=(-1, -2, -4))
        struc.append_kind(Kind(name='Ba2', symbols='Ba', mass=100.0))
        struc.append_site(Site(kind_name='Ba2', position=[3, 2, 1]))
        struc.append_kind(Kind(name='Test', symbols=['Ba', 'Ti'], weights=[0.2, 0.4], mass=120.0))
        struc.append_site(Site(kind_name='Test', position=[3, 5, 1]))

        struc_tuple, kind_info, _ = structure_to_spglib_tuple(struc)

        abscoords = np.array([_.position for _ in struc.sites])
        struc_relpos = np.dot(np.linalg.inv(cell.T), abscoords.T).T

        assert round(abs(np.sum(np.abs(np.array(struc.cell) - np.array(struc_tuple[0]))) - 0.0), 7) == 0
        assert round(abs(np.sum(np.abs(np.array(struc_tuple[1]) - struc_relpos)) - 0.0), 7) == 0

        expected_kind_info = [kind_info[site.kind_name] for site in struc.sites]
        assert struc_tuple[2] == expected_kind_info

    def test_aiida_roundtrip(self):
        """Convert an AiiDA structure to a tuple and go back to see if we get the same results"""
        from aiida.tools import spglib_tuple_to_structure, structure_to_spglib_tuple

        cell = np.array([[4.0, 1.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 4.0]])

        struc = StructureData(cell=cell)
        struc.append_atom(symbols='Ba', position=(0, 0, 0))
        struc.append_atom(symbols='Ti', position=(1, 2, 3))
        struc.append_atom(symbols='O', position=(-1, -2, -4))
        struc.append_kind(Kind(name='Ba2', symbols='Ba', mass=100.0))
        struc.append_site(Site(kind_name='Ba2', position=[3, 2, 1]))
        struc.append_kind(Kind(name='Test', symbols=['Ba', 'Ti'], weights=[0.2, 0.4], mass=120.0))
        struc.append_site(Site(kind_name='Test', position=[3, 5, 1]))

        struc_tuple, kind_info, kinds = structure_to_spglib_tuple(struc)
        roundtrip_struc = spglib_tuple_to_structure(struc_tuple, kind_info, kinds)

        assert round(abs(np.sum(np.abs(np.array(struc.cell) - np.array(roundtrip_struc.cell))) - 0.0), 7) == 0
        assert struc.base.attributes.get('kinds') == roundtrip_struc.base.attributes.get('kinds')
        assert [_.kind_name for _ in struc.sites] == [_.kind_name for _ in roundtrip_struc.sites]
        assert (
            np.sum(
                np.abs(
                    np.array([_.position for _ in struc.sites]) - np.array([_.position for _ in roundtrip_struc.sites])
                )
            )
            == 0.0
        )


@pytest.mark.skipif(not has_seekpath(), reason='No seekpath available')
def test_seekpath_explicit_path():
    """ "Tests the `get_explicit_kpoints_path` from SeeK-path."""
    from aiida.plugins import DataFactory
    from aiida.tools import get_explicit_kpoints_path

    structure = DataFactory('core.structure')(cell=[[4, 0, 0], [0, 4, 0], [0, 0, 6]])
    structure.append_atom(symbols='Ba', position=[0, 0, 0])
    structure.append_atom(symbols='Ti', position=[2, 2, 3])
    structure.append_atom(symbols='O', position=[2, 2, 0])
    structure.append_atom(symbols='O', position=[2, 0, 3])
    structure.append_atom(symbols='O', position=[0, 2, 3])

    params = {'with_time_reversal': True, 'reference_distance': 0.025, 'recipe': 'hpkot', 'threshold': 1.0e-7}

    return_value = get_explicit_kpoints_path(structure, method='seekpath', **params)
    retdict = return_value['parameters'].get_dict()

    assert retdict['has_inversion_symmetry']
    assert not retdict['augmented_path']
    assert round(abs(retdict['volume_original_wrt_prim'] - 1.0), 7) == 0
    assert to_list_of_lists(retdict['explicit_segments']) == [
        [0, 31],
        [30, 61],
        [60, 104],
        [103, 123],
        [122, 153],
        [152, 183],
        [182, 226],
        [226, 246],
        [246, 266],
    ]

    ret_k = return_value['explicit_kpoints']
    assert to_list_of_lists(ret_k.labels) == [
        [0, 'GAMMA'],
        [30, 'X'],
        [60, 'M'],
        [103, 'GAMMA'],
        [122, 'Z'],
        [152, 'R'],
        [182, 'A'],
        [225, 'Z'],
        [226, 'X'],
        [245, 'R'],
        [246, 'M'],
        [265, 'A'],
    ]
    kpts = ret_k.get_kpoints(cartesian=False)
    highsympoints_relcoords = [kpts[idx] for idx, label in ret_k.labels]
    assert (
        round(
            abs(
                np.sum(
                    np.abs(
                        np.array(
                            [
                                [0.0, 0.0, 0.0],  # Gamma
                                [0.0, 0.5, 0.0],  # X
                                [0.5, 0.5, 0.0],  # M
                                [0.0, 0.0, 0.0],  # Gamma
                                [0.0, 0.0, 0.5],  # Z
                                [0.0, 0.5, 0.5],  # R
                                [0.5, 0.5, 0.5],  # A
                                [0.0, 0.0, 0.5],  # Z
                                [0.0, 0.5, 0.0],  # X
                                [0.0, 0.5, 0.5],  # R
                                [0.5, 0.5, 0.0],  # M
                                [0.5, 0.5, 0.5],  # A
                            ]
                        )
                        - np.array(highsympoints_relcoords)
                    )
                )
                - 0.0
            ),
            7,
        )
        == 0
    )

    ret_prims = return_value['primitive_structure']
    ret_convs = return_value['conv_structure']
    # The primitive structure should be the same as the one I input
    assert round(abs(np.sum(np.abs(np.array(structure.cell) - np.array(ret_prims.cell))) - 0.0), 7) == 0
    assert [_.kind_name for _ in structure.sites] == [_.kind_name for _ in ret_prims.sites]
    assert (
        np.sum(
            np.abs(np.array([_.position for _ in structure.sites]) - np.array([_.position for _ in ret_prims.sites]))
        )
        == 0.0
    )

    # Also the conventional structure should be the same as the one I input
    assert round(abs(np.sum(np.abs(np.array(structure.cell) - np.array(ret_convs.cell))) - 0.0), 7) == 0
    assert [_.kind_name for _ in structure.sites] == [_.kind_name for _ in ret_convs.sites]
    assert (
        np.sum(
            np.abs(np.array([_.position for _ in structure.sites]) - np.array([_.position for _ in ret_convs.sites]))
        )
        == 0.0
    )


@pytest.mark.skipif(not has_seekpath(), reason='No seekpath available')
def test_seekpath():
    """Test SeekPath for BaTiO3 structure."""
    from aiida.plugins import DataFactory
    from aiida.tools import get_kpoints_path

    structure = DataFactory('core.structure')(cell=[[4, 0, 0], [0, 4, 0], [0, 0, 6]])
    structure.append_atom(symbols='Ba', position=[0, 0, 0])
    structure.append_atom(symbols='Ti', position=[2, 2, 3])
    structure.append_atom(symbols='O', position=[2, 2, 0])
    structure.append_atom(symbols='O', position=[2, 0, 3])
    structure.append_atom(symbols='O', position=[0, 2, 3])

    params = {'with_time_reversal': True, 'recipe': 'hpkot', 'threshold': 1.0e-7}

    return_value = get_kpoints_path(structure, method='seekpath', **params)
    retdict = return_value['parameters'].get_dict()

    assert retdict['has_inversion_symmetry']
    assert not retdict['augmented_path']
    assert round(abs(retdict['volume_original_wrt_prim'] - 1.0), 7) == 0
    assert round(abs(retdict['volume_original_wrt_conv'] - 1.0), 7) == 0
    assert retdict['bravais_lattice'] == 'tP'
    assert retdict['bravais_lattice_extended'] == 'tP1'
    assert to_list_of_lists(retdict['path']) == [
        ['GAMMA', 'X'],
        ['X', 'M'],
        ['M', 'GAMMA'],
        ['GAMMA', 'Z'],
        ['Z', 'R'],
        ['R', 'A'],
        ['A', 'Z'],
        ['X', 'R'],
        ['M', 'A'],
    ]

    assert retdict['point_coords'] == {
        'A': [0.5, 0.5, 0.5],
        'M': [0.5, 0.5, 0.0],
        'R': [0.0, 0.5, 0.5],
        'X': [0.0, 0.5, 0.0],
        'Z': [0.0, 0.0, 0.5],
        'GAMMA': [0.0, 0.0, 0.0],
    }

    assert (
        round(
            abs(
                np.sum(
                    np.abs(
                        np.array(retdict['inverse_primitive_transformation_matrix'])
                        - np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
                    )
                )
                - 0.0
            ),
            7,
        )
        == 0
    )

    ret_prims = return_value['primitive_structure']
    ret_convs = return_value['conv_structure']
    # The primitive structure should be the same as the one I input
    assert round(abs(np.sum(np.abs(np.array(structure.cell) - np.array(ret_prims.cell))) - 0.0), 7) == 0
    assert [_.kind_name for _ in structure.sites] == [_.kind_name for _ in ret_prims.sites]
    assert (
        np.sum(
            np.abs(np.array([_.position for _ in structure.sites]) - np.array([_.position for _ in ret_prims.sites]))
        )
        == 0.0
    )

    # Also the conventional structure should be the same as the one I input
    assert round(abs(np.sum(np.abs(np.array(structure.cell) - np.array(ret_convs.cell))) - 0.0), 7) == 0
    assert [_.kind_name for _ in structure.sites] == [_.kind_name for _ in ret_convs.sites]
    assert (
        np.sum(
            np.abs(np.array([_.position for _ in structure.sites]) - np.array([_.position for _ in ret_convs.sites]))
        )
        == 0.0
    )


class TestBandsData:
    """Tests the BandsData objects."""

    def test_band(self):
        """Check the methods to set and retrieve a mesh."""
        # define a cell
        alat = 4.0
        cell = np.array(
            [
                [alat, 0.0, 0.0],
                [0.0, alat, 0.0],
                [0.0, 0.0, alat],
            ]
        )

        k = KpointsData()
        k.set_cell(cell)
        k.set_kpoints([[0.0, 0.0, 0.0], [0.1, 0.1, 0.1]])

        b = BandsData()
        b.set_kpointsdata(k)
        assert np.array_equal(b.cell, k.cell)

        input_bands = np.array([np.ones(4) for i in range(k.get_kpoints().shape[0])])
        input_occupations = input_bands

        b.set_bands(input_bands, occupations=input_occupations, units='ev')
        b.set_bands(input_bands, units='ev')
        b.set_bands(input_bands, occupations=input_occupations)
        with pytest.raises(TypeError):
            b.set_bands(occupations=input_occupations, units='ev')

        b.set_bands(input_bands, occupations=input_occupations, units='ev')
        bands, occupations = b.get_bands(also_occupations=True)

        assert np.array_equal(bands, input_bands)
        assert np.array_equal(occupations, input_occupations)
        assert b.units == 'ev'

        b.store()
        with pytest.raises(ModificationNotAllowed):
            b.set_bands(bands)

    @staticmethod
    def test_export_to_file():
        """Export the band structure on a file, check if it is working."""
        # define a cell
        alat = 4.0
        cell = np.array(
            [
                [alat, 0.0, 0.0],
                [0.0, alat, 0.0],
                [0.0, 0.0, alat],
            ]
        )

        k = KpointsData()
        k.set_cell(cell)
        k.set_kpoints([[0.0, 0.0, 0.0], [0.1, 0.1, 0.1]])

        b = BandsData()
        b.set_kpointsdata(k)

        # 4 bands with linearly increasing energies, it does not make sense
        # but is good for testing
        input_bands = np.array([np.ones(4) * i for i in range(k.get_kpoints().shape[0])])

        b.set_bands(input_bands, units='eV')

        # It is not obvious how to check that the bands are correct.
        # I just check, for a few formats, that the file is correctly
        # created, at this stage
        # I use this to get a file. I then close it and ask the .export() function
        # to create it again. I have to remember to delete everything at the end.
        handle, filename = tempfile.mkstemp()
        os.close(handle)
        os.remove(filename)

        for frmt in ['agr', 'agr_batch', 'json', 'mpl_singlefile', 'dat_blocks', 'dat_multicolumn']:
            files_created = []  # In case there is an exception
            try:
                files_created = b.export(filename, fileformat=frmt)
                with open(filename, encoding='utf8') as fhandle:
                    _ = fhandle.read()
            finally:
                for file in files_created:
                    if os.path.exists(file):
                        os.remove(file)
