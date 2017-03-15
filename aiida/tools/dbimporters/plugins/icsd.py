# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.tools.dbimporters.baseclasses import (DbImporter, DbSearchResults,
                                                 CifEntry)



class IcsdImporterExp(Exception):
    pass


class CifFileErrorExp(IcsdImporterExp):
    """
    Raised when the author loop is missing in a CIF file.
    """
    pass


class NoResultsWebExp(IcsdImporterExp):
    """
    Raised when a webpage query returns no results.
    """
    pass


class IcsdDbImporter(DbImporter):
    """
    Importer for the Inorganic Crystal Structure Database, short ICSD, provided by
    FIZ Karlsruhe. It allows to run queries and analyse all the results.
    See the :ref:`DbImporter documentation and
    tutorial page <ICSD_importer_guide>` for more information.

    :param server: Server URL, the web page of the database. It is
        required in order to have access to the full database.
        I t should contain both the protocol and the domain name
        and end with a slash, as in::

          server = "http://ICSDSERVER.com/"

    :param urladd: part of URL which is added between query and and the server URL
        (default: ``index.php?``). only needed for web page query
    :param querydb: boolean, decides whether the mysql database is queried
        (default: True).
        If False, the query results are obtained through the web page
        query, which is
        restricted to a maximum of 1000 results per query.
    :param dl_db: icsd comes with a full (default: ``icsd``) and a demo
        database (``icsdd``).
        This parameter allows the user to switch to the demo database
        for testing purposes, if the access rights to the full database
        are not granted.
    :param host: MySQL database host. If the MySQL database is hosted on
        a different machine, use  "127.0.0.1" as host, and open
        a SSH tunnel to the host using::

            ssh -L 3306:localhost:3306 username@hostname.com

        or (if e.g. you get an URLError with Errno 111 (Connection refused)
        upon querying)::
        
            ssh -L 3306:localhost:3306 -L 8010:localhost:80 username@hostname.com

    :param user: mysql database username (default: dba)
    :param passwd: mysql database password (default: sql)
    :param db: name of the database (default: icsd)
    :param port: Port to access the mysql database (default: 3306)
    """

    length_precision = 0.001
    angle_precision = 0.001
    volume_precision = 0.001
    temperature_precision = 0.001
    density_precision = 0.001
    pressure_precision = 1

    def __init__(self, **kwargs):

        self.db_parameters = {"server": "",
                              "urladd": "index.php?",
                              "querydb": True,
                              "dl_db": "icsd",
                              "host": "",
                              "user": "dba",
                              "passwd": "sql",
                              "db": "icsd",
                              "port": "3306",
        }
        self.setup_db(**kwargs)

    # for mysql db query
    def _int_clause(self, key, alias, values):
        """
        Return SQL query predicate for querying integer fields
        :param key: Database keyword
        :param alias: Query parameter name
        :param values: Corresponding values from query
        :return: SQL query predicate
        """
        for e in values:
            if not isinstance(e, (int, long)) and not isinstance(e, basestring):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only integers and strings are accepted")
        return key + " IN (" + ", ".join(map(lambda i: str(int(i)),
                                             values)) + ")"

    def _str_exact_clause(self, key, alias, values):
        """
        Return SQL query predicate for querying string fields.
        """
        for e in values:
            if not isinstance(e, (int, long)) and not isinstance(e, basestring):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only integers and strings are accepted")
        return key + \
               " IN (" + ", ".join(map(lambda f: "'" + str(f) + "'", \
                                       values)) + ")"

    def _formula_clause(self, key, alias, values):
        """
        Return SQL query predicate for querying formula fields.
        """
        for e in values:
            if not isinstance(e, basestring):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only strings are accepted")
        return self._str_exact_clause(key, \
                                     alias, \
                                     map(lambda f: str(f), \
                                         values))

    def _str_fuzzy_clause(self, key, alias, values):
        """
        Return SQL query predicate for fuzzy querying of string fields.
        """
        for e in values:
            if not isinstance(e, (int, long)) and not isinstance(e, basestring):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only integers and strings are accepted")
        return " OR ".join(map(lambda s: key + \
                                         " LIKE '%" + str(s) + "%'", values))

    def _composition_clause(self, key, alias, values):
        """
        Return SQL query predicate for querying elements in formula fields.
        """
        for e in values:
            if not isinstance(e, basestring):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only strings are accepted")
        return " AND ".join(map(lambda e: "STRUCT_FORM REGEXP ' " + \
                                          e + "[0-9 ]'", \
                                values))

    def _double_clause(self, key, alias, values, precision):
        """
        Return SQL query predicate for querying double-valued fields.
        """
        for e in values:
            if not isinstance(e, (int, long)) and not isinstance(e, float):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only integers and floats are accepted")
        return " OR ".join(map(lambda d: key + \
                                         " BETWEEN " + \
                                         str(d - precision) + " AND " + \
                                         str(d + precision), \
                               values))


    def _crystal_system_clause(self, key, alias, values):
        """
        Return SQL query predicate for querying crystal_system.
        """
        valid_systems = {
            "cubic": "CU",
            "hexagonal": "HE",
            "monoclinic": "MO",
            "orthorhombic": "OR",
            "tetragonal": "TE",
            "trigonal": "TG",
            "triclinic": "TC"
        }  # from icsd accepted crystal systems

        for e in values:
            if not isinstance(e, (int, long)) and not isinstance(e, basestring):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only strings are accepted")
        return key + \
               " IN (" + ", ".join(map(lambda f: "'" + valid_systems[f.lower()] + "'", \
                                       values)) + ")"

    def _length_clause(self, key, alias, values):
        """
        Return SQL query predicate for querying lattice vector lengths.
        """
        return self.double_clause(key, alias, values, self.length_precision)

    def _density_clause(self, key, alias, values):
        """
        Return SQL query predicate for querying density.
        """
        return self.double_clause(key, alias, values, self.density_precision)

    def _angle_clause(self, key, alias, values):
        """
        Return SQL query predicate for querying lattice angles.
        """
        return self.double_clause(key, alias, values, self.angle_precision)

    def _volume_clause(self, key, alias, values):
        """
        Return SQL query predicate for querying unit cell volume.
        """
        return self.double_clause(key, alias, values, self.volume_precision)

    def _temperature_clause(self, key, alias, values):
        """
        Return SQL query predicate for querying temperature.
        """
        return self.double_clause(key, alias, values, self.temperature_precision)

    def _pressure_clause(self, key, alias, values):
        """
        Return SQL query predicate for querying pressure.
        """
        return self.double_clause(key, alias, values, self.pressure_precision)

    # for the web query
    def _parse_all(k, v):
        """
        Convert numbers, strings, lists into strings.
        :param k: query parameter
        :param v: corresponding values
        :return retval: string
        """
        if type(v) is list:
            retval = ' '.join(v)
        elif type(v) is int:
            retval = str(v)
        elif type(v) is str:
            retval = v
        return retval

    def _parse_number(k, v):
        """
        Convert int into string.
        :param k: query parameter
        :param v: corresponding values
        :return retval: string
        """
        if type(v) is int:
            retval = str(v)
        elif type(v) is str:
            retval = v
        return retval

    def _parse_mineral(k, v):
        """
        Convert mineral_name and chemical_name into right format.
        :param k: query parameter
        :param v: corresponding values
        :return retval: string
        """
        if k == "mineral_name":
            retval = "M=" + v
        elif k == "chemical_name":
            retval = "C=" + v
        return retval

    def _parse_volume(k, v):
        """
        Convert volume, cell parameter and angle queries into right format.
        :param k: query parameter
        :param v: corresponding values
        :return retval: string
        """
        if k == "volume":
            return "v=" + v
        elif k == "a":
            return "a=" + v
        elif k == "b":
            return "b=" + v
        elif k == "c":
            return "c=" + v
        elif k == "alpha":
            return "al=" + v
        elif k == "beta":
            return "be=" + v
        elif k == "gamma":
            return "ga=" + v

    def _parse_system(k, v):
        """
        Return crystal system in the right format.
        :param k: query parameter
        :param v: corresponding values
        :return retval: string
        """
        valid_systems = {
            "cubic": "CU",
            "hexagonal": "HE",
            "monoclinic": "MO",
            "orthorhombic": "OR",
            "tetragonal": "TE",
            "trigonal": "TG",
            "triclinic": "TC"
        }

        return valid_systems[v.lower()]

    # mysql database - query parameter (alias) : [mysql keyword (key), function to call]
    keywords_db = {'id': ['COLL_CODE', _int_clause],
                   'element': ['STRUCT_FORM;', _composition_clause],
                   'number_of_elements': ['EL_COUNT', _int_clause],
                   'chemical_name': ['CHEM_NAME', _str_fuzzy_clause],
                   'formula': ['SUM_FORM', _formula_clause],
                   'volume': ['C_VOL', _volume_clause],
                   'spacegroup': ['SGR', _str_exact_clause],
                   'a': ['A_LEN', _length_clause],
                   'b': ['B_LEN', _length_clause],
                   'c': ['C_LEN', _length_clause],
                   'alpha': ['ALPHA', _angle_clause],
                   'beta': ['BETA', _angle_clause],
                   'gamma': ['GAMMA', _angle_clause],
                   'density': ['DENSITY_CALC', _density_clause],
                   'wyckoff': ['WYCK', _str_exact_clause],
                   'molar_mass': ['MOL_MASS', _density_clause],
                   'pdf_num': ['PDF_NUM', _str_exact_clause],
                   'z': ['Z', _int_clause],
                   'measurement_temp': ['TEMPERATURE', _temperature_clause],
                   'authors': ['AUTHORS_TEXT', _str_fuzzy_clause],
                   'journal': ['journal', _str_fuzzy_clause],
                   'title': ['AU_TITLE', _str_fuzzy_clause],
                   'year': ['MPY', _int_clause],
                   'crystal_system': ['CRYST_SYS_CODE', _crystal_system_clause],
    }
    # keywords accepted for the web page query
    keywords = {"id": ("authors", _parse_all),
                "authors": ("authors", _parse_all),
                "element": ("elements", _parse_all),
                "number_of_elements": ("elementc", _parse_all),
                "mineral_name": ("mineral", _parse_mineral),
                "chemical_name": ("mineral", _parse_mineral),
                "formula": ("formula", _parse_all),
                "volume": ("volume", _parse_volume),
                "a": ("volume", _parse_volume),
                "b": ("volume", _parse_volume),
                "c": ("volume", _parse_volume),
                "alpha": ("volume", _parse_volume),
                "beta": ("volume", _parse_volume),
                "gamma": ("volume", _parse_volume),
                "spacegroup": ("spaceg", _parse_all),
                "journal": ("journal", _parse_all),
                "title": ("title", _parse_all),
                "year": ("year", _parse_all),
                "crystal_system": ("system", _parse_system),
    }
    
    def query(self, **kwargs):
        """
        Depending on the db_parameters, the mysql database or the web page are queried.
        Valid parameters are found using IcsdDbImporter.get_supported_keywords().

        :param kwargs: A list of ''keyword = [values]'' pairs.
        """

        if self.db_parameters["querydb"]:
            return self._query_sql_db(**kwargs)
        else:
            return self._queryweb(**kwargs)

    def _query_sql_db(self, **kwargs):
        """
        Perform a query on Icsd mysql database using ``keyword = value`` pairs,
        specified in ``kwargs``. Returns an instance of IcsdSearchResults.
        :param kwargs: A list of ``keyword = [values]`` pairs
        :return: IcsdSearchResults
        """

        sql_where_query = []  # second part of sql query

        for k, v in kwargs.iteritems():
            if not isinstance(v, list):
                v = [v]
            sql_where_query.append("({})".format(self.keywords_db[k][1](self, 
                                                        self.keywords_db[k][0], 
                                                        k, v)))
        if "crystal_system" in kwargs.keys():  # to query another table than the main one, add LEFT JOIN in front of WHERE
            sql_query = "LEFT JOIN space_group ON space_group.sgr=icsd.sgr LEFT "\
                        "JOIN space_group_number ON "\
                        "space_group_number.sgr_num=space_group.sgr_num "\
                        + "WHERE" + " AND ".join(sql_where_query)
        elif sql_where_query:
            sql_query = "WHERE" + " AND ".join(sql_where_query)
        else:
            sql_query = ""

        return IcsdSearchResults(query=sql_query, db_parameters=self.db_parameters)


    def _queryweb(self, **kwargs):
        """
        Perform a query on the Icsd web database using ``keyword = value`` pairs,
        specified in ``kwargs``. Returns an instance of IcsdSearchResults.
        :note: Web search has a maximum result number fixed at 1000.
        :param kwargs: A list of ``keyword = [values]`` pairs
        :return: IcsdSearchResults
        """
        import urllib

        self.actual_args = {
            "action": "Search",
            "nb_rows": "100",  # max is 100
            "order_by": "yearDesc",
            "authors": "",
            "volume": "",
            "mineral": ""
        }

        for k, v in kwargs.iteritems():
            try:
                realname = self.keywords[k][0]
                newv = self.keywords[k][1](k, v)
                # Because different keys correspond to the same search field.
                if realname in ["authors", "volume", "mineral"]:
                    self.actual_args[realname] = self.actual_args[realname] + newv + " "
                else:
                    self.actual_args[realname] = newv
            except KeyError as e:
                raise TypeError("ICSDImporter got an unexpected keyword argument '{}'".format(e.message))

        url_values = urllib.urlencode(self.actual_args)
        query_url = self.db_parameters["urladd"] + url_values

        return IcsdSearchResults(query=query_url, db_parameters=self.db_parameters)

    def setup_db(self, **kwargs):
        """
        Change the database connection details.
        At least the host server has to be defined.

        :param kwargs: db_parameters for the mysql database connection
          (host, user, passwd, db, port)
        """
        for key in self.db_parameters.keys():
            if key in kwargs.keys():
                self.db_parameters[key] = kwargs[key]

    def get_supported_keywords(self):
        """
        :return: List of all supported query keywords.
        """
        if self.db_parameters["querydb"]:
            return self.keywords_db.keys()
        else:
            return self.keywords.keys()


class IcsdSearchResults(DbSearchResults):
    """
    Result manager for the query performed on ICSD.

    :param query: mysql query or webpage query
    :param db_parameters: database parameter setup during the
      initialisation of the IcsdDbImporter.
    """
    cif_url = "/index.php?format=cif&action=Export&id%5B%5D={}"
    db_name = "Icsd"

    def __init__(self, query, db_parameters):

        self.db = None
        self.cursor = None
        self.db_parameters = db_parameters
        self.query = query
        self.number_of_results = None
        self.results = []
        self.cif_numbers = []
        self.entries = {}
        self.page = 1
        self.position = 0
        self.db_version = None
        self.sql_select_query = "SELECT SQL_CALC_FOUND_ROWS icsd.IDNUM, icsd.COLL_CODE, icsd.STRUCT_FORM "
        self.sql_from_query = "FROM icsd "
        
        if self.db_parameters["querydb"]:
            self.query_db_version()
        self.query_page()

    def next(self):
        """
        Return next result as IcsdEntry.
        """
        if self.number_of_results > self.position:
            self.position = self.position + 1
            return self.at(self.position - 1)
        else:
            self.position = 0
            raise StopIteration()

    def at(self, position):
        """
        Return ``position``-th result as IcsdEntry.
        """

        if position < 0 or position >= self.number_of_results:
            raise IndexError("index out of bounds")
        while position + 1 >= len(self.results) and len(self.results) < self.number_of_results:
            self.page = self.page + 1
            self.query_page()

        if position not in self.entries:
            if self.db_parameters["querydb"]:
                self.entries[position] = IcsdEntry(self.db_parameters["server"] + 
                        self.db_parameters["dl_db"] + self.cif_url.format(
                        self.results[position]),
                    db_name=self.db_name, id=self.cif_numbers[position], 
                    version = self.db_version, 
                    extras={'idnum': self.results[position]})
            else:
                self.entries[position] = IcsdEntry(self.db_parameters["server"] + 
                        self.db_parameters["dl_db"] + self.cif_url.format(
                        self.results[position]),
                    db_name=self.db_name, extras={'idnum': self.results[position]})
        return self.entries[position]


    def query_db_version(self):
        """
        Query the version of the icsd database (last row of RELEASE_TAGS).
        """
        results = []
        if self.db_parameters["querydb"]:

            sql_select_query = "SELECT RELEASE_TAG "
            sql_from_query = "FROM icsd.icsd_database_information "

            self._connect_db()
            query_statement = "{}{}".format(sql_select_query, sql_from_query)
            self.cursor.execute(query_statement)
            self.db.commit()

            for row in self.cursor.fetchall():
                results.append(str(row[0]))

            self._disconnect_db()
            try:
                self.db_version = results[-1]
            except IndexError:
                raise IcsdImporterExp("Database version not found")

        else:
            raise NotImplementedError("Cannot query the database version with "
                                      "a web query.")
        
    def query_page(self):
        """
        Query the mysql or web page database, depending on the db_parameters.
        Store the number_of_results, cif file number and the corresponding icsd number.

        :note: Icsd uses its own number system, different from the CIF
                file numbers.
        """
        if self.db_parameters["querydb"]:

            self._connect_db()
            query_statement = "{}{}{} LIMIT {}, 100".format(self.sql_select_query,
                                                            self.sql_from_query,
                                                            self.query,
                                                            (self.page-1)*100)
            self.cursor.execute(query_statement)
            self.db.commit()

            for row in self.cursor.fetchall():
                self.results.append(str(row[0]))
                self.cif_numbers.append(str(row[1]))

            if self.number_of_results is None:
                self.cursor.execute("SELECT FOUND_ROWS()")
                self.number_of_results = int(self.cursor.fetchone()[0])

            self._disconnect_db()


        else:
            import urllib2
            from bs4 import BeautifulSoup
            import re

            self.html = urllib2.urlopen(self.db_parameters["server"] + 
                                        self.db_parameters["db"] + "/" + 
                                        self.query.format(str(self.page))).read()

            self.soup = BeautifulSoup(self.html)

            try:

                if self.number_of_results is None:
                    self.number_of_results = int(re.findall(r'\d+',
                                                    str(self.soup.find_all("i")[-1]))[0])
            except IndexError:
                raise NoResultsWebExp

            for i in self.soup.find_all('input', type="checkbox"):
                self.results.append(i['id'])

    def _connect_db(self):
        """
        Connect to the MySQL database for performing searches.
        """
        try:
            import MySQLdb
        except ImportError:
            import pymysql as MySQLdb

        self.db = MySQLdb.connect(host=self.db_parameters['host'],
                                  user=self.db_parameters['user'],
                                  passwd=self.db_parameters['passwd'],
                                  db=self.db_parameters['db'],
                                  port=int(self.db_parameters['port'])
        )
        self.cursor = self.db.cursor()

    def _disconnect_db(self):
        """
        Close connection to the MySQL database.
        """
        self.db.close()


class IcsdEntry(CifEntry):
    """
    Represent an entry from Icsd.
    
    :note:
      - Before July 2nd 2015, source['id'] contained icsd.IDNUM (internal
        icsd id number) and source['extras']['cif_nr'] the cif number 
        (icsd.COLL_CODE).
      - After July 2nd 2015, source['id'] has been replaced by the cif 
        number and source['extras']['idnum'] is icsd.IDNUM .
    """
    _license = 'ICSD'

    def __init__(self, uri, **kwargs):
        """
        Create an instance of IcsdEntry, related to the supplied URI.
        """
        super(IcsdEntry, self).__init__(**kwargs)
        self.source = {
            'db_name': kwargs.get('db_name','Icsd'),
            'db_uri': None,  # Server ?
            'id': kwargs.get('id',None),
            'version': kwargs.get('version',None),
            'uri': uri,
            'extras': {'idnum': kwargs.get('extras',{}).get('idnum',None)},
            'license': self._license,
        }
        self._cif = None

    @property
    def cif(self):
        """
        :return: cif file of Icsd entry.
        """
        if self._cif is None:
            import urllib2

            self._cif = urllib2.urlopen(self.source["uri"]).read()
        return self._cif

    def get_cif_node(self):
        """
        Create a CIF node, that can be used in AiiDA workflow.

        :return: :py:class:`aiida.orm.data.cif.CifData` object
        """
        from aiida.orm.data.cif import CifData
        import tempfile

        with tempfile.NamedTemporaryFile() as f:
            f.write(self.cif)
            f.flush()
            return CifData(file=f.name, source=self.source)

    def get_corrected_cif(self):
        """
        Add quotes to the lines in the author loop if missing.

        :note: ase raises an AssertionError if the quotes in the
          author loop are missing.
        """
        return correct_cif(self.cif)

    def get_ase_structure(self):
        """
        :return: ASE structure corresponding to the cif file.
        """
        from aiida.orm.data.cif import CifData
        import StringIO

        return CifData.read_cif(StringIO.StringIO(self.get_corrected_cif()))


    def get_aiida_structure(self):
        """
        :return: AiiDA structure corresponding to the CIF file.
        """
        from aiida.orm import DataFactory

        S = DataFactory("structure")
        aiida_structure = S(ase=self.get_ase_structure())
        return aiida_structure


def correct_cif(cif):
    """
    Correct the format of the CIF files.
    At the moment, it only fixes missing quotes in the authors field
    (``ase.read.io`` only works if the author names are quoted,
    if not an AssertionError is raised).

    :param cif: A string containing the content of the CIF file.
    :return: a string containing the corrected CIF file.
    """
    # Do more checks to be sure it's working in everycase 
    # -> no _publ_author_name, several lines, correct input
    lines = cif.split('\n')

    try:
        author_index = lines.index('_publ_author_name')
    except ValueError:
        raise CifFileErrorExp('_publ_author_name line missing in cif file')
    else:
        inc = 1
        while True:
            words = lines[author_index + inc].split()
            #in case loop is finished -> return cif lines.
            #use regular expressions ?
            if len(words) == 0 or words[0] == "loop_" or words[0][0] == '_':
                return '\n'.join(lines)
            elif ((words[0][0] == "'" and words[-1][-1] == "'")
                  or (words[0][0] == '"' and words[-1][-1] == '"')):
                # if quotes are already there, check next line
                inc = inc + 1
            else:
                lines[author_index + inc] = "'" + lines[author_index + inc] + "'"
                inc = inc + 1

