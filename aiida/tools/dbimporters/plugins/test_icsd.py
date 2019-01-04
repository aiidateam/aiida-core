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

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import unittest

from aiida.backends.testbase import AiidaTestCase

from . import icsd


def has_mysqldb():
    """
    :return: True if the ase module can be imported, False otherwise.
    """
    # pylint: disable=unused-import,unused-variable
    try:
        import MySQLdb
    except ImportError:
        try:
            import pymysql as MySQLdb
        except ImportError:
            return False
    return True


def has_icsd_config():
    """
    :return: True if the currently loaded profile has a ICSD configuration
    """

    from aiida.settings import PROFILE_CONF

    required_keywords = {
        'ICSD_SERVER_URL', 'ICSD_MYSQL_HOST', 'ICSD_MYSQL_USER', 'ICSD_MYSQL_PASSWORD', 'ICSD_MYSQL_DB'
    }

    return required_keywords <= set(PROFILE_CONF.keys())


@unittest.skipUnless(has_mysqldb() and has_icsd_config(), "ICSD configuration in profile required")
class TestIcsd(AiidaTestCase):
    """
    Tests for the ICSD importer
    """

    def setUp(self):
        """
        Set up IcsdDbImporter for web and mysql db query.
        """
        from aiida.settings import PROFILE_CONF

        self.server = PROFILE_CONF['ICSD_SERVER_URL']
        self.host = PROFILE_CONF['ICSD_MYSQL_HOST']
        self.user = PROFILE_CONF['ICSD_MYSQL_USER']
        self.password = PROFILE_CONF['ICSD_MYSQL_PASSWORD']
        self.dbname = PROFILE_CONF['ICSD_MYSQL_DB']
        self.dbport = PROFILE_CONF.get('ICSD_MYSQL_PORT', 3306)

        self.importerdb = icsd.IcsdDbImporter(server=self.server, host=self.host)
        self.importerweb = icsd.IcsdDbImporter(server=self.server, host=self.host, querydb=False)

    def test_server(self):
        """
        Test Icsd intranet webinterface
        """
        from six.moves import urllib
        urllib.request.urlopen(self.server + "icsd/").read()

    def test_mysqldb(self):
        """
        Test connection to Icsd mysql database.
        """
        try:
            import MySQLdb
        except ImportError:
            import pymysql as MySQLdb

        mydb = MySQLdb.connect(host=self.host, user=self.user, passwd=self.password, db=self.dbname, port=self.dbport)
        mydb.cursor()

    def test_web_zero_results(self):
        """
        No results should be obtained from year 3000.
        """
        with self.assertRaises(icsd.NoResultsWebExp):
            self.importerweb.query(year="3000")

    def test_web_collcode_155006(self):
        """
        Query for the CIF code 155006, should return 1 result.
        """

        queryresults = self.importerweb.query(id="155006")
        self.assertEqual(queryresults.number_of_results, 1)

        with self.assertRaises(StopIteration):
            next(queryresults)
            next(queryresults)

        with self.assertRaises(IndexError):
            queryresults.at(10)

    def test_dbquery_zero_results(self):
        """
        check handling a zero result case
        """

        importer = icsd.IcsdDbImporter(server=self.server, host=self.host)
        noresults = importer.query(year="3000")  # which should work at least for the next 85 years..
        self.assertEqual(noresults.number_of_results, 0)

        with self.assertRaises(StopIteration):
            next(noresults)

        with self.assertRaises(IndexError):
            noresults.at(0)
