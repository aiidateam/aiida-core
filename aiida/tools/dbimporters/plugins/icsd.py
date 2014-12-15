# -*- coding: utf-8 -*-

import aiida.tools.dbimporters.baseclasses
import MySQLdb

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.3.0"

class IcsdImporterExp(Exception):
    pass

class CifFileErrorExp(IcsdImporterExp):
    pass

class IcsdDbImporter(aiida.tools.dbimporters.baseclasses.DbImporter):
    """
    Importer for the Inorganic Crystal Structure Database, short ICSD, provided by
    FIZ Karlsruhe. It allows to run queries and analyse all the results.
    """

    # for mysql db query
    def int_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying integer fields
        :param key: Database keyword
        :param alias: Query parameter name
        :param values: Corresponding values from query
        :return: SQL query predicate
        """
        for e in values:
            if not isinstance( e, int ) and not isinstance( e, str ):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only integers and strings are accepted")
        return key + " IN (" + ", ".join( map( lambda i: str( int( i ) ),
                                               values ) ) + ")"

    def str_exact_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying string fields.
        """
        for e in values:
            if not isinstance( e, int ) and not isinstance( e, str ):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only integers and strings are accepted")
        return key + \
               " IN (" + ", ".join( map( lambda f: "'" + str(f) + "'", \
                                         values ) ) + ")"
    def formula_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying formula fields.
        """
        for e in values:
            if not isinstance( e, str ):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only strings are accepted")
        return self.str_exact_clause( key, \
                                      alias, \
                                      map( lambda f: "- " + str(f) + " -", \
                                           values ) )

    def str_fuzzy_clause(self, key, alias, values):
        """
        Returns SQL query predicate for fuzzy querying of string fields.
        """
        for e in values:
            if not isinstance( e, int ) and not isinstance( e, str ):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only integers and strings are accepted")
        return " OR ".join( map( lambda s: key + \
                                           " LIKE '%" + str(s) + "%'", values ) )

    def composition_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying elements in formula fields.
        """
        for e in values:
            if not isinstance( e, str ):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only strings are accepted")
        return " AND ".join( map( lambda e: "STRUCT_FORM REGEXP ' " + \
                                            e + "[0-9 ]'", \
                                  values ) )

    def double_clause(self, key, alias, values, precision):
        """
        Returns SQL query predicate for querying double-valued fields.
        """
        for e in values:
            if not isinstance( e, int ) and not isinstance( e, float ):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only integers and floats are accepted")
        return " OR ".join( map( lambda d: key + \
                                           " BETWEEN " + \
                                           str( d - precision ) + " AND " + \
                                           str( d + precision ), \
                                 values ) )




    def crystal_system_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying crystal_system.
        """
        valid_systems = {
        "cubic": "CU",
        "hexagonal": "HE",
        "monoclinic": "MO",
        "orthorhombic": "OR",
        "tetragonal": "TE",
        "trigonal": "TG",
        "triclinic": "TC"
        } #from icsd accepted crystal systems

        for e in values:
            if not isinstance( e, int ) and not isinstance( e, str ):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only strings are accepted")
        return key + \
               " IN (" + ", ".join( map( lambda f: "'" + valid_systems[f.lower()] + "'", \
                                         values ) ) + ")"


    length_precision      = 0.001
    angle_precision       = 0.001
    volume_precision      = 0.001
    temperature_precision = 0.001
    density_precision     = 0.001
    pressure_precision    = 1

    def length_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying lattice vector lengths.
        """
        return self.double_clause(key, alias, values, self.length_precision)

    def density_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying density.
        """
        return self.double_clause(key, alias, values, self.density_precision)

    def angle_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying lattice angles.
        """
        return self.double_clause(key, alias, values, self.angle_precision)

    def volume_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying unit cell volume.
        """
        return self.double_clause(key, alias, values, self.volume_precision)

    def temperature_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying temperature.
        """
        return self.double_clause(key, alias, values, self.temperature_precision)

    def pressure_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying pressure.
        """
        return self.double_clause(key, alias, values, self.pressure_precision)


    # mysql database - query parameter (alias) : [mysql keyword (key), function to call]
    keywords_db = {'id'             : [ 'COLL_CODE',          int_clause ],
                 'element'           : [ 'STRUCT_FORM;',       composition_clause ],
                 'number_of_elements': [ 'EL_COUNT',           int_clause ],
                 'chemical_name'     : [ 'CHEM_NAME',      str_fuzzy_clause ],
                 'formula'           : [ 'SUM_FORM',       formula_clause ],
                 'volume'            : [ 'C_VOL',           volume_clause ],
                 'spacegroup'        : [ 'SGR',            str_exact_clause ],
                 'a'                 : [ 'A_LEN',             length_clause ],
                 'b'                 : [ 'B_LEN',             length_clause ],
                 'c'                 : [ 'C_LEN',             length_clause ],
                 'alpha'             : [ 'ALPHA',         angle_clause ],
                 'beta'              : [ 'BETA',          angle_clause ],
                 'gamma'             : [ 'GAMMA',         angle_clause ],
                 'density'           : [ 'DENSITY_CALC',  density_clause],
                 'wyckoff'           : ['WYCK', str_exact_clause],
                 'molar_mass'        : ['MOL_MASS', density_clause],
                 'pdf_num'           : ['PDF_NUM', str_exact_clause],
                 'z'                 : [ 'Z',             int_clause ],
                 'measurement_temp'  : [ 'TEMPERATURE',      temperature_clause ],
                 'authors'           : [ 'AUTHORS_TEXT',       str_fuzzy_clause ],
                 'journal'           : [ 'journal',       str_fuzzy_clause ],
                 'title'             : [ 'AU_TITLE',         str_fuzzy_clause ],
                 'year'              : [ 'MPY',          int_clause ],
                 'crystal_system'    : ['CRYST_SYS_CODE', crystal_system_clause],
                 }

    # for the web query
    def parse_all(k,v):
        """
        Converts numbers, strings, lists into strings.
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

    def parse_number(k,v):
        """
        Converts int into string.
        :param k: query parameter
        :param v: corresponding values
        :return retval: string
        """
        if type(v) is int:
            retval = str(v)
        elif type (v) is str:
            retval = v
        return retval

    def parse_mineral(k,v):
        """
        Converts mineral_name and chemical_name into right format.
        :param k: query parameter
        :param v: corresponding values
        :return retval: string
        """
        if k == "mineral_name":
            retval = "M="+ v
        elif k == "chemical_name":
            retval = "C=" + v
        return retval

    def parse_volume(k,v):
        """
        Converts volume, cell parameter and angle queries into right format.
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

    def parse_system(k,v):
        """
        Returns crystal system in the right format.
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

    # keywords accepted for the web page query
    keywords = { "id"                : ("authors", parse_all),
                 "authors"           : ("authors", parse_all),
                 "element"           : ("elements", parse_all),
                 "number_of_elements": ("elementc", parse_all),
                 "mineral_name"      : ("mineral", parse_mineral),
                 "chemical_name"     : ("mineral", parse_mineral),
                 "formula"           : ("formula", parse_all),
                 "volume"            : ("volume", parse_volume),
                 "a"                 : ("volume", parse_volume),
                 "b"                 : ("volume", parse_volume),
                 "c"                 : ("volume", parse_volume),
                 "alpha"             : ("volume", parse_volume),
                 "beta"              : ("volume", parse_volume),
                 "gamma"             : ("volume", parse_volume),
                 "spacegroup"        : ("spaceg", parse_all),
                 "journal"           : ("journal", parse_all),
                 "title"             : ("title", parse_all),
                 "year"              : ("year", parse_all),
                 "crystal_system"    : ("system", parse_system),
                 }



    def __init__(self, **kwargs):
        """
        Sets up the database importer.
        :param server: Server URL, the web page of the database. It is
            important to have access to the full data base.
        :param urladd: part of URL which is added between query and and the server URL
            (default: index.php?) only needed for web page query

        :param querydb: True (default) means the mysql database is queried.
            If False, the query results are provide by the web page query, which is
            restricted to a maximum of 1000 results at once.

        :param host: mysql database host, one way is to setup an ssh tunnel to the host
            using:
            ssh -L 3306:localhost:3306 username@hostname.com
            and put "127.0.0.1" as host. Google for ssh -L for more information.
        :param user: mysql database username (default: dba)
        :param passwd: mysql database password (default: sql)
        :param db: name of the database (default: icsd)
        :param dl_db: icsd comes with a full (default: icsd) and a demo database (icsdd).
            This parameter allows to switch to the demo database for testing purpose,
            if the access rights to the full database are not granted.
        :param port: Port to access the mysql database (default: 3306)
        """

        self.db_parameters = { "server":   "",
                               "urladd": "index.php?",
                               "querydb": True,
                               "dl_db": "icsd",

                               "host":   "",
                               "user":   "dba",
                               "passwd": "sql",
                               "db":     "icsd",
                               "port": "3306",
                            }
        self.setup_db( **kwargs )

    def query(self, **kwargs):
        """
        Depending on the db_parameters, the mysql database or the web page are queried.
        Valid parameters are found using IcsdDbImporter.get_supported_keywords().
        :param **kwargs: A list of ``keyword = [values]`` pairs.
        """

        if self.db_parameters["querydb"]:
            return self._query_sql_db(**kwargs)
        else:
            return self._queryweb( **kwargs)

    def _query_sql_db(self, **kwargs):
        """
        Performs a query on Icsd mysql database using ``keyword = value`` pairs,
        specified in ``kwargs``. Returns an instance of IcsdSearchResults.
        :param **kwargs: A list of ``keyword = [values]`` pairs
        :return: IcsdSearchResults
        """

        sql_where_query = [] #second part of sql query

        for k, v in kwargs.iteritems():
                if not isinstance( v, list ):
                    v = [ v ]
                sql_where_query.append( \
                    "(" + self.keywords_db[k][1]( self, \
                                                 self.keywords_db[k][0], \
                                                 k, \
                                                 v ) + \
                    ")" )
        if "crystal_system" in kwargs.keys(): # to query another table than the main one, add LEFT JOIN in front of WHERE
            sql_query = "LEFT JOIN space_group ON space_group.sgr=icsd.sgr LEFT JOIN space_group_number ON space_group_number.sgr_num=space_group.sgr_num " +  "WHERE" + " AND ".join(sql_where_query)
        else:
            sql_query =  "WHERE" + " AND ".join(sql_where_query)

        return IcsdSearchResults(query = sql_query, db_parameters= self.db_parameters)


    def _queryweb(self, **kwargs):
        """
        Performs a query on the Icsd web database using ``keyword = value`` pairs,
        specified in ``kwargs``. Returns an instance of IcsdSearchResults.
        :note: Web search has a maximum result number fixed at 1000.
        :param **kwargs: A list of ``keyword = [values]`` pairs
        :return: IcsdSearchResults
        """
        import urllib

        self.actual_args = {
            "action": "Search",
            "nb_rows" : "100", #max is 100
            "order_by" : "yearDesc",
            "authors" : "",
            "volume" : "",
            "mineral" : ""
        }

        for k, v in kwargs.iteritems():
            try:
                realname = self.keywords[k][0]
                newv = self.keywords[k][1](k,v)
                # Because different keys correspond to the same search field.
                if realname in  ["authors","volume","mineral"]:
                    self.actual_args[realname] = self.actual_args[realname] + newv + " "
                else:
                    self.actual_args[realname] = newv
            except KeyError as e:
                raise TypeError("ICSDImporter got an unexpected keyword argument '{}'".format(e.message))

        url_values = urllib.urlencode(self.actual_args)
        query_url = self.db_parameters["urladd"] + url_values

        return IcsdSearchResults(query = query_url, db_parameters= self.db_parameters)

    def setup_db(self, **kwargs):
        """
        Changes the database connection details. At least the host server has to be defined.
        :param **kwargs: db_parameters for the mysql database connection
            (host, user, passwd, db, port)
        """
        for key in self.db_parameters.keys():
            if key in kwargs.keys():
                self.db_parameters[key] = kwargs[key]

    def get_supported_keywords(self):
        """
        :return: List of all supported query keywords.
        """
        if db_parameters["querydb"]:
            return self.keywords_db.keys()
        else:
            return self.keywords.keys()


class IcsdSearchResults(aiida.tools.dbimporters.baseclasses.DbSearchResults):
    """
    Results of the search, performed on Icsd.
    :param query: mysql query or webpage query
    :param db_parameters: database parameter setup during the initialisation of the
        IcsdDbImporter.
    """

    # url add to download cif files, make to db_parameter (question)
    cif_url = "index.php?format=cif&action=Export&id%5B%5D={}"
    db_name = "Icsd"

    def __init__(self, query, db_parameters):

        self.db         = None
        self.cursor     = None
        self.db_parameters= db_parameters
        self.query = query
        self.number_of_results = None
        self.results = []
        self.icsd_numbers = []
        self.entries = {}
        self.page = 1
        self.position = 0
        self.sql_select_query = "SELECT SQL_CALC_FOUND_ROWS icsd.IDNUM, icsd.COLL_CODE, icsd.STRUCT_FORM "
        self.sql_from_query = "FROM icsd "

        self.query_page()

    def next(self):
        """
        Returns next result as IcsdEntry.
        """
        if len( self.results ) > self.position and self.number_of_results > self.position:
            self.position = self.position + 1
            return self.at( self.position - 1 )
        else:
            raise StopIteration()

    def at(self, position):
        """
        Returns ``position``-th result as IcsdEntry.
        """

        if position < 0 or position >= self.number_of_results:
            raise IndexError( "index out of bounds" )
        while position >= len(self.results):
            self.page = self.page + 1
            self.query_page()
        if position not in self.entries:
            self.entries[position] = IcsdEntry( self.db_parameters["server"]+ self.db_parameters["dl_db"] + self.cif_url.format(self.results[position]), \
                          source_db = self.db_name, db_id = self.results[position], extras = {'icsd_nr' : self.icsd_numbers[position]} )
        return self.entries[position]



    def query_page(self):
        """
        Queries the mysql or web page database, depending on the db_parameters.
        Stores the number_of_results, cif file number and the corresponding icsd number.
        :note: Icsd uses its own number system, not the cif file numbers.
        """
        if self.db_parameters["querydb"]:

            self._connect_db()
            query_statement = self.sql_select_query+ self.sql_from_query + self.query + " LIMIT " + str((self.page-1)*100) + ", " + str(self.page*100)
        #try:
            print query_statement

            self.cursor.execute( query_statement )
            self.db.commit()

            for row in self.cursor.fetchall():
                self.results.append( str( row[0] ) )
                self.icsd_numbers.append( str(row[1]))


            if self.number_of_results is None:
                self.cursor.execute( "SELECT FOUND_ROWS()")
                self.number_of_results =  int(self.cursor.fetchone()[0])

        #finally:
            self._disconnect_db()


        else:
            import urllib2
            from bs4 import BeautifulSoup
            import re

            self.html = urllib2.urlopen(self.db_parameters["server"] + self.query.format(str(self.page))).read()

            self.soup = BeautifulSoup(self.html)

            if self.number_of_results is None:
                #is there a better way to get this number?
                number_of_results = int(re.findall(r'\d+', str(self.soup.find_all("i")[-1]))[0])

            for i in self.soup.find_all('input', type="checkbox"):
                #x = SearchResult(server, cif_url, i['id'])
                self.results.append(i['id'])

    def _connect_db(self):
        """
        Connects to the MySQL database for performing searches.
        """
        self.db = MySQLdb.connect( host =   self.db_parameters['host'],
                                   user =   self.db_parameters['user'],
                                   passwd = self.db_parameters['passwd'],
                                   db =     self.db_parameters['db'],
                                   port = int(self.db_parameters['port'])
                                   )
        self.cursor = self.db.cursor()

    def _disconnect_db(self):
        """
        Closes connection to the MySQL database.
        """
        self.db.close()


class IcsdEntry(aiida.tools.dbimporters.baseclasses.DbEntry):
    """
    Represents an entry from Icsd.
    """

    def __init__(self, url, **kwargs):
        """
        Creates an instance of IcsdEntry, related to the supplied URL.
        """
        super(IcsdEntry, self).__init__(**kwargs)
        self.source = {
            'db_source' : 'Icsd',
            'db_url'    : None, # Server ?
            'db_id'     : None,
            'db_version': None,
            'url'       : url,
            'extras'     : {'icsd_nr'   : None},
        }
        self.icsd_nr = None
        if 'db_source' in kwargs.keys():
            self.source["db_source"] = kwargs['db_source']
        if 'db_id' in kwargs.keys():
            self.source["db_id"] = kwargs['db_id']
        if 'extras' in kwargs.keys() and 'icsd_nr' in kwargs['extras']:
            self.source['extras']["icsd_nr"] = kwargs['extras']['icsd_nr']

        self._cif = None

    @property
    def cif(self):
        """
        :return: cif file of Icsd entry.
        """
        if self._cif is None:
            import urllib2
            self._cif = urllib2.urlopen( self.source["url"] ).read()
        return self._cif

    def get_cif_node(self):
        """
        Creates a CIF node, that can be used in AiiDA workflow.

        :return: :py:class:`aiida.orm.data.cif.CifData` object
        """
        from aiida.orm.data.cif import CifData
        import tempfile
        with tempfile.NamedTemporaryFile() as f:
            f.write(self.get_corrected_cif())
            f.flush()
            return CifData(file=f.name, source=self.source)

    def get_corrected_cif(self):
        """
        Adds quotes to the lines in the author loop if missing.
        :note: ase raises an AssertionError if the quotes in the author loop are missing.
        """
        return correct_cif(self.cif)

    def get_ase_structure(self):
        """
        :return: ASE structure corresponding to the cif file.
        """
        import ase.io.cif
        import StringIO
        return ase.io.cif.read_cif( StringIO.StringIO( self.get_corrected_cif() ) )



    def get_aiida_structure(self):
        """
        :return: Aiida structure corresponding to the cif file.
        """
        from aiida.orm import DataFactory
        S = DataFactory("structure")
        aiida_structure = S(ase=self.get_ase_structure())
        return aiida_structure



def correct_cif(cif):
    """
    This function corrects the format of the cif files

    :note: the ase.read.io only works if the author names are quoted, if not an AssertionError is raised.
    :param cif: A string containing the content of the CIF file.
    """
    #Do more checks to be sure it's working in everycase -> no _publ_author_name, several lines, correct input
    lines = cif.split('\n')

    try:
        author_index = lines.index('_publ_author_name')
    except ValueError:
        raise CifFileErrorExp('_publ_author_name line missing in cif file')
    else:
        inc = 1
        while True:
            words = lines[author_index+inc].split()
            #in case loop is finished -> return cif lines.
            #use regular expressions ?
            if len(words) == 0 or words[0] == "loop_" or words[0][0] == '_':
                return '\n'.join(lines)
            elif (words[0][0] == "'" and words[-1][-1] == "'") or (words[0][0] == '"' and words[-1][-1] == '"'):
                # if quotes are already there, check next line
                inc = inc + 1
            else:
                lines[author_index+inc] = "'" + lines[author_index+inc] + "'"
                inc = inc + 1

