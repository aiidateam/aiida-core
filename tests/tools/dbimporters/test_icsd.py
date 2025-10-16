###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for IcsdDbImporter"""

import urllib.request

import pytest

from aiida import get_profile
from aiida.tools.dbimporters.plugins import icsd


def has_mysqldb():
    """:return: True if the ase module can be imported, False otherwise."""
    try:
        import MySQLdb
    except ImportError:
        try:
            import pymysql as MySQLdb  # noqa: N812, F401
        except ImportError:
            return False
    return True


def has_icsd_config():
    """:return: True if the currently loaded profile has a ICSD configuration"""
    profile = get_profile()

    required_keywords = {
        'ICSD_SERVER_URL',
        'ICSD_MYSQL_HOST',
        'ICSD_MYSQL_USER',
        'ICSD_MYSQL_PASSWORD',
        'ICSD_MYSQL_DB',
    }

    return required_keywords <= set(profile.dictionary.keys())


class TestIcsd:
    """Tests for the ICSD importer"""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile and set up IcsdDbImporter for web and mysql db query."""
        if not (has_mysqldb() and has_icsd_config()):
            pytest.skip('ICSD configuration in profile required')
        profile = get_profile()

        self.server = profile.dictionary['ICSD_SERVER_URL']
        self.host = profile.dictionary['ICSD_MYSQL_HOST']
        self.user = profile.dictionary['ICSD_MYSQL_USER']
        self.password = profile.dictionary['ICSD_MYSQL_PASSWORD']
        self.dbname = profile.dictionary['ICSD_MYSQL_DB']
        self.dbport = profile.dictionary.get('ICSD_MYSQL_PORT', 3306)

        self.importerdb = icsd.IcsdDbImporter(server=self.server, host=self.host)
        self.importerweb = icsd.IcsdDbImporter(server=self.server, host=self.host, querydb=False)

    def test_server(self):
        """Test Icsd intranet webinterface"""
        with urllib.request.urlopen(f'{self.server}icsd/') as handle:
            handle.read()

    def test_mysqldb(self):
        """Test connection to Icsd mysql database."""
        try:
            import MySQLdb
        except ImportError:
            import pymysql as MySQLdb  # noqa: N812

        mydb = MySQLdb.connect(host=self.host, user=self.user, passwd=self.password, db=self.dbname, port=self.dbport)
        mydb.cursor()

    def test_web_zero_results(self):
        """No results should be obtained from year 3000."""
        with pytest.raises(icsd.NoResultsWebExp):
            self.importerweb.query(year='3000')

    def test_web_collcode_155006(self):
        """Query for the CIF code 155006, should return 1 result."""
        queryresults = self.importerweb.query(id='155006')
        assert queryresults.number_of_results == 1

        with pytest.raises(StopIteration):
            next(queryresults)
            next(queryresults)

        with pytest.raises(IndexError):
            queryresults.at(10)

    def test_dbquery_zero_results(self):
        """Check handling a zero result case"""
        importer = icsd.IcsdDbImporter(server=self.server, host=self.host)
        noresults = importer.query(year='3000')  # which should work at least for the next 85 years..
        assert noresults.number_of_results == 0

        with pytest.raises(StopIteration):
            next(noresults)

        with pytest.raises(IndexError):
            noresults.at(0)
