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
Tests for subclasses of DbImporter, DbSearchResults and DbEntry
"""
from aiida.backends.testbase import AiidaTestCase
import unittest



class TestCodDbImporter(AiidaTestCase):
    """
    Test the CodDbImporter class.
    """
    from aiida.orm.data.cif import has_pycifrw

    def test_query_construction_1(self):
        from aiida.tools.dbimporters.plugins.cod import CodDbImporter

        codi = CodDbImporter()
        q = codi.query_sql(id=["1000000", 3000000],
                           element=["C", "H", "Cl"],
                           number_of_elements=5,
                           chemical_name=["caffeine", "serotonine"],
                           formula=["C6 H6"],
                           volume=[100, 120.005],
                           spacegroup="P -1",
                           a=[10.0 / 3, 1],
                           alpha=[10.0 / 6, 0],
                           measurement_temp=[0, 10.5],
                           measurement_pressure=[1000, 1001],
                           determination_method=["single crystal", None])
        self.assertEquals(q, \
                          "SELECT file, svnrevision FROM data WHERE "
                          "(status IS NULL OR status != 'retracted') AND "
                          "(method IN ('single crystal') OR method IS NULL) AND "
                          "(file IN (1000000, 3000000)) AND "
                          "(chemname LIKE '%caffeine%' OR "
                          "chemname LIKE '%serotonine%') AND "
                          "(formula IN ('- C6 H6 -')) AND "
                          "(a BETWEEN 3.33233333333 AND 3.33433333333 OR "
                          "a BETWEEN 0.999 AND 1.001) AND "
                          "(celltemp BETWEEN -0.001 AND 0.001 OR "
                          "celltemp BETWEEN 10.499 AND 10.501) AND "
                          "(vol BETWEEN 99.999 AND 100.001 OR "
                          "vol BETWEEN 120.004 AND 120.006) AND "
                          "(alpha BETWEEN 1.66566666667 AND 1.66766666667 OR "
                          "alpha BETWEEN -0.001 AND 0.001) AND "
                          "(cellpressure BETWEEN 999 AND 1001 OR "
                          "cellpressure BETWEEN 1000 AND 1002) AND "
                          "(formula REGEXP ' C[0-9 ]' AND "
                          "formula REGEXP ' H[0-9 ]' AND "
                          "formula REGEXP ' Cl[0-9 ]') AND "
                          "(nel IN (5)) AND (sg IN ('P -1'))")

    def test_datatype_checks(self):
        """
        Rather complicated, but wide-coverage test for data types, accepted
        and rejected by CodDbImporter._*_clause methods.
        """
        from aiida.tools.dbimporters.plugins.cod import CodDbImporter

        codi = CodDbImporter()
        messages = ["",
                    "incorrect value for keyword 'test' -- " + \
                    "only integers and strings are accepted",
                    "incorrect value for keyword 'test' -- " + \
                    "only strings are accepted",
                    "incorrect value for keyword 'test' -- " + \
                    "only integers and floats are accepted",
                    "invalid literal for int() with base 10: 'text'"]
        values = [10, 'text', u'text', '10', 1.0 / 3, [1, 2, 3]]
        methods = [codi._int_clause,
                   codi._str_exact_clause,
                   codi._formula_clause,
                   codi._str_fuzzy_clause,
                   codi._composition_clause,
                   codi._volume_clause]
        results = [[0, 4, 4, 0, 1, 1],
                   [0, 0, 0, 0, 1, 1],
                   [2, 0, 2, 0, 2, 2],
                   [0, 0, 0, 0, 1, 1],
                   [2, 0, 0, 0, 2, 2],
                   [0, 3, 3, 3, 0, 3]]

        for i in range(0, len(methods)):
            for j in range(0, len(values)):
                message = messages[0]
                try:
                    methods[i]("test", "test", [values[j]])
                except ValueError as e:
                    message = e.message
                self.assertEquals(message, messages[results[i][j]])

    def test_dbentry_creation(self):
        """
        Tests the creation of CodEntry from CodSearchResults.
        """
        from aiida.tools.dbimporters.plugins.cod \
            import CodSearchResults

        results = CodSearchResults([{'id': '1000000', 'svnrevision': None},
                                    {'id': '1000001', 'svnrevision': '1234'},
                                    {'id': '2000000', 'svnrevision': '1234'}])
        self.assertEquals(len(results), 3)
        self.assertEquals(str(results.at(1)),
                          'CodEntry(license="CC0",'
                          'db_name="Crystallography Open Database",version="1234",'
                          'uri="http://www.crystallography.net/cod/1000001.cif@1234",'
                          'source_md5=None,db_uri="http://www.crystallography.net",'
                          'id="1000001",extras={})')
        self.assertEquals(results.at(1).source['uri'], \
                          "http://www.crystallography.net/cod/1000001.cif@1234")
        self.assertEquals([x.source['uri'] for x in results],
                          ["http://www.crystallography.net/cod/1000000.cif",
                           "http://www.crystallography.net/cod/1000001.cif@1234",
                           "http://www.crystallography.net/cod/2000000.cif@1234"])

    @unittest.skipIf(not has_pycifrw(), "Unable to import PyCifRW")
    def test_dbentry_to_cif_node(self):
        """
        Tests the creation of CifData node from CodEntry.
        """
        from aiida.tools.dbimporters.plugins.cod import CodEntry
        from aiida.orm.data.cif import CifData

        entry = CodEntry("http://www.crystallography.net/cod/1000000.cif")
        entry.cif = "data_test _publ_section_title 'Test structure'"

        cif = entry.get_cif_node()
        self.assertEquals(isinstance(cif, CifData), True)
        self.assertEquals(cif.get_attr('md5'),
                          '070711e8e99108aade31d20cd5c94c48')
        self.assertEquals(cif.source, {
            'db_name': 'Crystallography Open Database',
            'db_uri': 'http://www.crystallography.net',
            'id': None,
            'version': None,
            'extras': {},
            'source_md5': '070711e8e99108aade31d20cd5c94c48',
            'uri': 'http://www.crystallography.net/cod/1000000.cif',
            'license': 'CC0',
        })


class TestTcodDbImporter(AiidaTestCase):
    """
    Test the TcodDbImporter class.
    """

    def test_dbentry_creation(self):
        """
        Tests the creation of TcodEntry from TcodSearchResults.
        """
        from aiida.tools.dbimporters.plugins.tcod import TcodSearchResults

        results = TcodSearchResults([{'id': '10000000', 'svnrevision': None},
                                     {'id': '10000001', 'svnrevision': '1234'},
                                     {'id': '20000000', 'svnrevision': '1234'}])
        self.assertEquals(len(results), 3)
        self.assertEquals(str(results.at(1)),
                          'TcodEntry(license="CC0",'
                          'db_name="Theoretical Crystallography Open Database",'
                          'version="1234",'
                          'uri="http://www.crystallography.net/tcod/10000001.cif@1234",'
                          'source_md5=None,db_uri="http://www.crystallography.net/tcod",'
                          'id="10000001",extras={})')
        self.assertEquals(results.at(1).source['uri'], \
                          "http://www.crystallography.net/tcod/10000001.cif@1234")
        self.assertEquals([x.source['uri'] for x in results],
                          ["http://www.crystallography.net/tcod/10000000.cif",
                           "http://www.crystallography.net/tcod/10000001.cif@1234",
                           "http://www.crystallography.net/tcod/20000000.cif@1234"])


class TestPcodDbImporter(AiidaTestCase):
    """
    Test the PcodDbImporter class.
    """

    def test_dbentry_creation(self):
        """
        Tests the creation of PcodEntry from PcodSearchResults.
        """
        from aiida.tools.dbimporters.plugins.pcod import PcodSearchResults

        results = PcodSearchResults([{'id': '12345678'}])
        self.assertEquals(len(results), 1)
        self.assertEquals(str(results.at(0)),
                          'PcodEntry(license="CC0",'
                          'db_name="Predicted Crystallography Open Database",'
                          'version=None,'
                          'uri="http://www.crystallography.net/pcod/cif/1/123/12345678.cif",'
                          'source_md5=None,db_uri="http://www.crystallography.net/pcod",'
                          'id="12345678",extras={})')
        self.assertEquals([x.source['uri'] for x in results],
                          ["http://www.crystallography.net/pcod/cif/1/123/12345678.cif"])


class TestMpodDbImporter(AiidaTestCase):
    """
    Test the MpodDbImporter class.
    """

    def test_dbentry_creation(self):
        """
        Tests the creation of MpodEntry from MpodSearchResults.
        """
        from aiida.tools.dbimporters.plugins.mpod import MpodSearchResults

        results = MpodSearchResults([{'id': '1234567'}])
        self.assertEquals(len(results), 1)
        self.assertEquals(str(results.at(0)),
                          'MpodEntry(license=None,'
                          'db_name="Material Properties Open Database",'
                          'version=None,'
                          'uri="http://mpod.cimav.edu.mx/datafiles/1234567.mpod",'
                          'source_md5=None,db_uri="http://mpod.cimav.edu.mx",'
                          'id="1234567",extras={})')
        self.assertEquals([x.source['uri'] for x in results],
                          ["http://mpod.cimav.edu.mx/datafiles/1234567.mpod"])


class TestNnincDbImporter(AiidaTestCase):
    """
    Test the UpfEntry class.
    """

    def test_upfentry_creation(self):
        """
        Tests the creation of NnincEntry from NnincSearchResults.
        """
        import os

        from aiida.tools.dbimporters.plugins.nninc import NnincSearchResults
        from aiida.common.exceptions import ParsingError
        import aiida

        upf = 'Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030'

        results = NnincSearchResults([{'id': upf}])
        entry = results.at(0)

        with open(os.path.join(
                os.path.split(aiida.__file__)[0], os.pardir,
                "examples", "testdata", "qepseudos", "{}.UPF".format(upf))
                , 'r') as f:
            entry._contents = f.read()

        upfnode = entry.get_upf_node()
        self.assertEquals(upfnode.element, 'Ba')

        entry.source = {'id': 'O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF'}

        # get_upf_node() will name pseudopotential file after source['id'],
        # thus UpfData parser will complain about the mismatch of chemical
        # element, mentioned in file name, and the one described in the
        # pseudopotential file.
        with self.assertRaises(ParsingError):
            upfnode = entry.get_upf_node()
