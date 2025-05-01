###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for subclasses of DbImporter, DbSearchResults and DbEntry"""

import pytest

from tests.static import STATIC_DIR


class TestCodDbImporter:
    """Test the CodDbImporter class."""

    from aiida.orm.nodes.data.cif import has_pycifrw  # type: ignore[misc]

    def test_query_construction_1(self):
        """Test query construction."""
        import re

        from aiida.tools.dbimporters.plugins.cod import CodDbImporter

        codi = CodDbImporter()
        q_sql = codi.query_sql(
            id=['1000000', 3000000],
            element=['C', 'H', 'Cl'],
            number_of_elements=5,
            chemical_name=['caffeine', 'serotonine'],
            formula=['C6 H6'],
            volume=[100, 120.005],
            spacegroup='P -1',
            a=[10.0 / 3, 1],
            alpha=[10.0 / 6, 0],
            measurement_temp=[0, 10.5],
            measurement_pressure=[1000, 1001],
            determination_method=['single crystal', None],
        )

        # Rounding errors occur in Python 3 thus they are averted using
        # the following precision stripping regular expressions.
        q_sql = re.sub(r'(\d\.\d{6})\d+', r'\1', q_sql)
        q_sql = re.sub(r'(120.00)39+', r'\g<1>4', q_sql)

        assert (
            q_sql == 'SELECT file, svnrevision FROM data WHERE '
            "(status IS NULL OR status != 'retracted') AND "
            '(a BETWEEN 3.332333 AND 3.334333 OR '
            'a BETWEEN 0.999 AND 1.001) AND '
            '(alpha BETWEEN 1.665666 AND 1.667666 OR '
            'alpha BETWEEN -0.001 AND 0.001) AND '
            "(chemname LIKE '%caffeine%' OR "
            "chemname LIKE '%serotonine%') AND "
            "(method IN ('single crystal') OR method IS NULL) AND "
            "(formula REGEXP ' C[0-9 ]' AND "
            "formula REGEXP ' H[0-9 ]' AND "
            "formula REGEXP ' Cl[0-9 ]') AND "
            "(formula IN ('- C6 H6 -')) AND "
            '(file IN (1000000, 3000000)) AND '
            '(cellpressure BETWEEN 999 AND 1001 OR '
            'cellpressure BETWEEN 1000 AND 1002) AND '
            '(celltemp BETWEEN -0.001 AND 0.001 OR '
            'celltemp BETWEEN 10.499 AND 10.501) AND '
            "(nel IN (5)) AND (sg IN ('P -1')) AND "
            '(vol BETWEEN 99.999 AND 100.001 OR '
            'vol BETWEEN 120.004 AND 120.006)'
        )

    def test_datatype_checks(self):
        """Rather complicated, but wide-coverage test for data types, accepted
        and rejected by CodDbImporter._*_clause methods.
        """
        from aiida.tools.dbimporters.plugins.cod import CodDbImporter

        codi = CodDbImporter()
        messages = [
            '',
            "incorrect value for keyword 'test' only integers and strings are accepted",
            "incorrect value for keyword 'test' only strings are accepted",
            "incorrect value for keyword 'test' only integers and floats are accepted",
            "invalid literal for int() with base 10: 'text'",
        ]
        values = [10, 'text', 'text', '10', 1.0 / 3, [1, 2, 3]]
        methods = [
            codi._int_clause,
            codi._str_exact_clause,
            codi._formula_clause,
            codi._str_fuzzy_clause,
            codi._composition_clause,
            codi._volume_clause,
        ]
        results = [
            [0, 4, 4, 0, 1, 1],
            [0, 0, 0, 0, 1, 1],
            [2, 0, 0, 0, 2, 2],
            [0, 0, 0, 0, 1, 1],
            [2, 0, 0, 0, 2, 2],
            [0, 3, 3, 3, 0, 3],
        ]

        for i, method in enumerate(methods):
            for j, value in enumerate(values):
                message = messages[0]
                try:
                    method('test', 'test', [value])
                except ValueError as exc:
                    message = str(exc)
                assert message == messages[results[i][j]]

    def test_dbentry_creation(self):
        """Tests the creation of CodEntry from CodSearchResults."""
        from aiida.tools.dbimporters.plugins.cod import CodSearchResults

        results = CodSearchResults(
            [
                {'id': '1000000', 'svnrevision': None},
                {'id': '1000001', 'svnrevision': '1234'},
                {'id': '2000000', 'svnrevision': '1234'},
            ]
        )
        assert [res for res in iter(results)] == [results.at(0), results.at(1), results.at(2)]
        assert len(results) == 3
        assert results.at(1).source == {
            'db_name': 'Crystallography Open Database',
            'db_uri': 'http://www.crystallography.net/cod',
            'extras': {},
            'id': '1000001',
            'license': 'CC0',
            'source_md5': None,
            'uri': 'http://www.crystallography.net/cod/1000001.cif@1234',
            'version': '1234',
        }
        assert [x.source['uri'] for x in results] == [
            'http://www.crystallography.net/cod/1000000.cif',
            'http://www.crystallography.net/cod/1000001.cif@1234',
            'http://www.crystallography.net/cod/2000000.cif@1234',
        ]

    @pytest.mark.skipif(not has_pycifrw(), reason='Unable to import PyCifRW')
    def test_dbentry_to_cif_node(self):
        """Tests the creation of CifData node from CodEntry."""
        from aiida.orm import CifData
        from aiida.tools.dbimporters.plugins.cod import CodEntry

        entry = CodEntry('http://www.crystallography.net/cod/1000000.cif')
        entry.cif = "data_test _publ_section_title 'Test structure'"

        cif = entry.get_cif_node()
        assert isinstance(cif, CifData) is True
        assert cif.base.attributes.get('md5') == '070711e8e99108aade31d20cd5c94c48'
        assert cif.source == {
            'db_name': 'Crystallography Open Database',
            'db_uri': 'http://www.crystallography.net/cod',
            'id': None,
            'version': None,
            'extras': {},
            'source_md5': '070711e8e99108aade31d20cd5c94c48',
            'uri': 'http://www.crystallography.net/cod/1000000.cif',
            'license': 'CC0',
        }


class TestTcodDbImporter:
    """Test the TcodDbImporter class."""

    def test_dbentry_creation(self):
        """Tests the creation of TcodEntry from TcodSearchResults."""
        from aiida.tools.dbimporters.plugins.tcod import TcodSearchResults

        results = TcodSearchResults(
            [
                {'id': '10000000', 'svnrevision': None},
                {'id': '10000001', 'svnrevision': '1234'},
                {'id': '20000000', 'svnrevision': '1234'},
            ]
        )
        assert len(results) == 3
        assert results.at(1).source == {
            'db_name': 'Theoretical Crystallography Open Database',
            'db_uri': 'http://www.crystallography.net/tcod',
            'extras': {},
            'id': '10000001',
            'license': 'CC0',
            'source_md5': None,
            'uri': 'http://www.crystallography.net/tcod/10000001.cif@1234',
            'version': '1234',
        }
        assert [x.source['uri'] for x in results] == [
            'http://www.crystallography.net/tcod/10000000.cif',
            'http://www.crystallography.net/tcod/10000001.cif@1234',
            'http://www.crystallography.net/tcod/20000000.cif@1234',
        ]


class TestPcodDbImporter:
    """Test the PcodDbImporter class."""

    def test_dbentry_creation(self):
        """Tests the creation of PcodEntry from PcodSearchResults."""
        from aiida.tools.dbimporters.plugins.pcod import PcodSearchResults

        results = PcodSearchResults([{'id': '12345678'}])
        assert len(results) == 1
        assert results.at(0).source == {
            'db_name': 'Predicted Crystallography Open Database',
            'db_uri': 'http://www.crystallography.net/pcod',
            'extras': {},
            'id': '12345678',
            'license': 'CC0',
            'source_md5': None,
            'uri': 'http://www.crystallography.net/pcod/cif/1/123/12345678.cif',
            'version': None,
        }


class TestMpodDbImporter:
    """Test the MpodDbImporter class."""

    def test_dbentry_creation(self):
        """Tests the creation of MpodEntry from MpodSearchResults."""
        from aiida.tools.dbimporters.plugins.mpod import MpodSearchResults

        results = MpodSearchResults([{'id': '1234567'}])
        assert len(results) == 1
        assert results.at(0).source == {
            'db_name': 'Material Properties Open Database',
            'db_uri': 'http://mpod.cimav.edu.mx',
            'extras': {},
            'id': '1234567',
            'license': None,
            'source_md5': None,
            'uri': 'http://mpod.cimav.edu.mx/datafiles/1234567.mpod',
            'version': None,
        }


class TestNnincDbImporter:
    """Test the UpfEntry class."""

    def test_upfentry_creation(self):
        """Tests the creation of NnincEntry from NnincSearchResults."""
        import os

        from aiida.common.exceptions import ParsingError
        from aiida.tools.dbimporters.plugins.nninc import NnincSearchResults

        upf = 'Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030'

        results = NnincSearchResults([{'id': upf}])
        entry = results.at(0)

        path_pseudos = os.path.join(STATIC_DIR, 'pseudos')
        with open(os.path.join(path_pseudos, f'{upf}.UPF'), 'r', encoding='utf8') as fpntr:
            entry._contents = fpntr.read()

        upfnode = entry.get_upf_node()
        assert upfnode.element == 'Ba'

        entry.source = {'id': 'O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF'}

        # get_upf_node() will name pseudopotential file after source['id'],
        # thus UpfData parser will complain about the mismatch of chemical
        # element, mentioned in file name, and the one described in the
        # pseudopotential file.
        with pytest.raises(ParsingError):
            upfnode = entry.get_upf_node()
