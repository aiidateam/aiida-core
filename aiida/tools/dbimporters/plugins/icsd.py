# -*- coding: utf-8 -*-

import aiida.tools.dbimporters.baseclasses
import MySQLdb

class IcsdDbImporter(aiida.tools.dbimporters.baseclasses.DbImporter):
    """
    Database importer for ICSD.
    """
    # for mysql db
    def int_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying integer fields.
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

    # for the web query

    def parse_all(k,v):
        """
        Takes numbers, strings, list and returns a string.
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
        int to string
        """
        if type(v) is int:
            retval = str(v)
        elif type (v) is str:
            retval = v
        return retval

    def parse_mineral(k,v):
        if k == "mineral_name":
            retval = "M="+ v
        elif k == "chemical_name":
            retval = "C=" + v
        return retval

    def parse_volume(k,v):
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
        valid_systems = {
        "cubic": "CU",
        "hexagonal": "HE",
        "monoclinic": "MO",
        "orthorhombic": "OR",
        "tetragonal": "TE",
        "trigonal": "TG",
        "triclinic": "TC"
        }
        return valid_systems[v]

    def parse_db_id(k,v):

        query_string = "(COLL_CODE in ("
        if type(v) is list:
            query_string = query_string + ','.join(v)
        elif type(v) is int:
            query_string = query_string + str(v)
        elif type(v) is str:
            query_string = query_string + v
        query_string = query_string + ")"

        return query_string


    def parse_db_element(k,v):
        query_string = "(COLL_CODE in ("
        if type(v) is list:
            query_string = query_string + ','.join(v)
        elif type(v) is int:
            query_string = query_string + str(v)
        elif type(v) is str:
            query_string = query_string + v
        query_string = query_string + ")"

        return query_string

    def parse_db_num_of_el(k,v):

        return query_string



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
                 #"crystal_system"    : ("system", parse_system),
                 }

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
                 'year'              : [ 'MPY',          int_clause ] }


    def __init__(self, **kwargs):
        #import logging
        #aiidalogger  =  logging.getLogger("aiida")
        #self.logger  =  aiidalogger.getChild("ICSDImporter")
        self.db_parameters = { "server":   "",
                               #"db":     "icsd",
                               "urladd": "index.php?",
                               "querydb": True,
                               "host":   "",
                               "user":   "dba",
                               "passwd": "",
                               "db":     "icsd",
                               "port": "3306",
                               "full_access": True
                            }
        self.setup_db( **kwargs )

    def query(self, **kwargs):
        #query web or mysql db
        if self.db_parameters["querydb"]:
            return self._query_sql_db(**kwargs)
        else:
            return self._queryweb( **kwargs)

    def _query_sql_db(self, **kwargs):
        """
        Performs a query on Icsd database.
        """

        sql_where_query = []

        for k, v in kwargs.iteritems():
                if not isinstance( v, list ):
                    v = [ v ]
                sql_where_query.append( \
                    "(" + self.keywords_db[k][1]( self, \
                                                 self.keywords_db[k][0], \
                                                 k, \
                                                 v ) + \
                    ")" )


        sql_query = "WHERE" + " AND ".join(sql_where_query)
        return IcsdSearchResults(query = sql_query, db_parameters= self.db_parameters)


    def _queryweb(self, **kwargs):
        """
        Performs a query on the Icsd web database using ``keyword = value`` pairs,
        specified in ``kwargs``. Returns an instance of IcsdSearchResults.
        Web search has a maximum result number fixed at 1000.
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
        Changes the database connection details. At least the server has to be defined.
        """
        for key in self.db_parameters.keys():
            if key in kwargs.keys():
                self.db_parameters[key] = kwargs[key]

    def get_supported_keywords(self):
        """
        Returns the list of all supported query keywords.
        """
        if db_parameters["querydb"]:
            return self.keywords_db.keys()
        else:
            return self.keywords.keys()


class IcsdSearchResults(aiida.tools.dbimporters.baseclasses.DbSearchResults):
    """
    Results of the search, performed on Icsd.
    """

    cif_url = "/index.php?format=cif&action=Export&id%5B%5D={}"
    db_name = "Icsd"

    def __init__(self, query, db_parameters):

        self.db         = None
        self.cursor     = None
        self.db_parameters= db_parameters
        self.query = query
        self.number_of_results = None
        self.results = []
        self.entries = {}
        self.page = 1
        self.position = 0
        self.sql_select_query = "SELECT SQL_CALC_FOUND_ROWS icsd.IDNUM, icsd.COLL_CODE, icsd.STRUCT_FORM "
        if db_parameters["full_access"]:
            self.sql_from_query = "FROM icsd.icsd "
        else:
            self.sql_from_query = "FROM icsdd.icsd "

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
        if self.position < 0 or self.position >= self.number_of_results:
            raise IndexError( "index out of bounds" )
        while self.position >= len(self.results):
            self.page = self.page + 1
            self.query_page()
        if position not in self.entries:
            self.entries[self.position] = IcsdEntry( self.db_parameters["server"]+ self.db_parameters["db"] + self.cif_url.format(self.results[position]), \
                          source_db = self.db_name, \
                          db_id = self.results[self.position] )
        return self.entries[self.position]



    def query_page(self):
        if self.db_parameters["querydb"]:

            self._connect_db()
            query_statement = self.sql_select_query+ self.sql_from_query + self.query + " LIMIT " + str((self.page-1)*100) + ", " + str(self.page*100)
        #try:
            print query_statement

            self.cursor.execute( query_statement )
            self.db.commit()

            for row in self.cursor.fetchall():
                self.results.append( str( row[0] ) )


            if self.number_of_results is None:
                self.cursor.execute( "SELECT FOUND_ROWS()")
                #self.number_of_results = self.cursor.fetch()[0]
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
                                   #db =     self.db_parameters['db']
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
            'url'       : url
        }
        if 'db_source' in kwargs.keys():
            self.source["db_source"] = kwargs['db_source']
        if 'db_id' in kwargs.keys():
            self.source["db_id"] = kwargs['db_id']

    @property
    def cif(self):
        if self._cif is None:
            import urllib2
            self._cif = urllib2.urlopen( self.source["url"] ).read()
        return self._cif

    def get_corrected_cif(self):
        """
        Adds quotes to the lines in the author loop if missing.
        :note: ase raises an AssertionError if the quotes in the author loop are missing.
        """
        return correct_cif(self.cif())

    def get_ase_structure(self):
        """
        Returns ASE representation of the CIF.
        """
        import ase.io.cif
        import StringIO
        return ase.io.cif.read_cif( StringIO.StringIO( self.get_corrected_cif() ) )



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
        pass
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

