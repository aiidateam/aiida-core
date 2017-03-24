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
Tests for IcsdDbImporter
"""
from django.utils import unittest
from aiida.djsite.db.testbase import AiidaTestCase

import aiida.tools.dbimporters.plugins.icsd



def has_mysqldb():
    """
    :return: True if the ase module can be imported, False otherwise.
    """
    try:
        import MySQLdb
    except ImportError:
        try:
            import pymysql as MySQLdb
        except ImportError:
            return False
    return True

server = None
host = None

#define appropriate server and host to make the tests run.
#server = "http://localhost:8001/"
#host = "127.0.0.1"


@unittest.skipIf(server is None, "Server name required")
class TestIcsd(AiidaTestCase):




    def setUp(self):
        """
        Set up IcsdDbImporter for web and mysql db query.
        """

        self.server = server
        self.host = host


        self.importerdb = aiida.tools.dbimporters.plugins.icsd.IcsdDbImporter(server=self.server, host= self.host)
        self.importerweb = aiida.tools.dbimporters.plugins.icsd.IcsdDbImporter(server=self.server, host= self.host, querydb = False)


    def test_server(self):
        """
        Test Icsd intranet webinterface
        """
        import urllib2
        html = urllib2.urlopen(self.server + "icsd/").read()

    @unittest.skipIf(host is None or not has_mysqldb(), "host required to query mysql db or unable to import MySQLdb")
    def test_mysqldb(self):
        """
        Test connection to Icsd mysql database.
        """
        import MySQLdb
        db = MySQLdb.connect(host = self.host, user ="dba", passwd = "sql", db = "icsd", port=3306)

        cursor = db.cursor()

    def test_web_zero_results(self):
        """
        No results should be obtained from year 3000.
        """
        with self.assertRaises(aiida.tools.dbimporters.plugins.icsd.NoResultsWebExp):
            self.noresults = self.importerweb.query(year="3000")


    def test_web_COLLCODE_155006(self):
        """
        Query for the CIF code 155006, should return 1 result.
        """

        queryresults =  self.importerweb.query(id="155006")
        self.assertEqual(queryresults.number_of_results,1)

        with self.assertRaises(StopIteration):
            queryresults.next()
            queryresults.next()

        with self.assertRaises(IndexError):
            queryresults.at(10)


    @unittest.skipIf(host is None or not has_mysqldb(), "host required to query mysql db or unable to import MySQLdb")
    def test_dbquery_zero_results(self):
        import aiida.tools.dbimporters.plugins.icsd
        self.importer = aiida.tools.dbimporters.plugins.icsd.IcsdDbImporter(server=self.server, host= self.host)
        self.noresults = self.importer.query(year="3000") # which should work at least for the next 85 years..
        self.assertEqual(self.noresults.number_of_results, 0)

        with self.assertRaises(StopIteration):
            self.noresults.next()

        with self.assertRaises(IndexError):
            self.noresults.at(0)


if __name__ == '__main__':
    from aiida import load_dbenv
    load_dbenv()
    unittest.main()





