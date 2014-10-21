# -*- coding: utf-8 -*-

import aiida.tools.basedbimporter
import MySQLdb

class CODImporter(aiida.tools.basedbimporter.BaseDBImporter):
    """
    Database importer for Crystallography Open Database.
    """

    def int_clause(self, key, values):
        """
        Returns SQL query predicate for querying integer fields.
        """
        return key + " IN (" + ", ".join( map( lambda i: str( int( i ) ),
                                               values ) ) + ")"

    def str_exact_clause(self, key, values):
        """
        Returns SQL query predicate for querying string fields.
        """
        return key + \
               " IN (" + ", ".join( map( lambda f: "'" + f + "'", \
                                         values ) ) + ")"
    def formula_clause(self, key, values):
        """
        Returns SQL query predicate for querying formula fields.
        """
        return self.str_exact_clause( key, \
                                      map( lambda f: "- " + f + " -", \
                                           values ) )

    def str_fuzzy_clause(self, key, values):
        """
        Returns SQL query predicate for fuzzy querying of string fields.
        """
        return " OR ".join( map( lambda s: key + \
                                           " LIKE '%" + s + "%'", values ) )

    def composition_clause(self, key, values):
        """
        Returns SQL query predicate for querying elements in formula fields.
        """
        return " AND ".join( map( lambda e: "formula REGEXP ' " + \
                                            e + "[0-9 ]'", \
                                  values ) )

    def double_clause(self, key, values, precision):
        """
        Returns SQL query predicate for querying double-valued fields.
        """
        return " OR ".join( map( lambda d: key + \
                                           " BETWEEN " + \
                                           str( d - precision ) + " AND " + \
                                           str( d + precision ), \
                                 values ) )

    length_precision = 0.001
    angle_precision  = 0.001
    volume_precision = 0.001

    def length_clause(self, key, values):
        """
        Returns SQL query predicate for querying lattice vector lengths.
        """
        return self.double_clause(key, values, self.length_precision)

    def angle_clause(self, key, values):
        """
        Returns SQL query predicate for querying lattice angles.
        """
        return self.double_clause(key, values, self.angle_precision)

    def volume_clause(self, key, values):
        """
        Returns SQL query predicate for querying unit cell volume.
        """
        return self.double_clause(key, values, self.volume_precision)

    keywords = { 'id'                : [ 'file',     int_clause ],
                 'element'           : [ 'element',  composition_clause ],
                 'number_of_elements': [ 'nel',      int_clause ],
                 'mineral_name'      : [ 'mineral',  str_fuzzy_clause ],
                 'chemical_name'     : [ 'chemname', str_fuzzy_clause ],
                 'formula'           : [ 'formula',  formula_clause ],
                 'volume'            : [ 'vol',      volume_clause ],
                 'spacegroup'        : [ 'sg',       str_exact_clause ],
                 'a'                 : [ 'a',        length_clause ],
                 'b'                 : [ 'b',        length_clause ],
                 'c'                 : [ 'c',        length_clause ],
                 'alpha'             : [ 'alpha',    angle_clause ],
                 'beta'              : [ 'beta',     angle_clause ],
                 'gamma'             : [ 'gamma',    angle_clause ],
                 'authors'           : [ 'authors',  str_fuzzy_clause ],
                 'journal'           : [ 'journal',  str_fuzzy_clause ],
                 'title'             : [ 'title',    str_fuzzy_clause ],
                 'year'              : [ 'year',     int_clause ] }

    def __init__(self, **kwargs):
        self.db        = None
        self.cursor    = None
        self.query_sql = None
        self.db_parameters = { 'host':   'www.crystallography.net',
                               'user':   'cod_reader',
                               'passwd': '',
                               'db':     'cod' }
        self.setup_db( **kwargs )

    def query(self, **kwargs):
        """
        Performs a query on the COD database using ``keyword = value`` pairs,
        specified in ``kwargs``. Returns an instance of CODSearchResults.
        """
        sql_parts = [ "(status IS NULL OR status != 'retracted')" ]
        for key in kwargs.keys():
            if key not in self.keywords.keys():
                raise NotImplementedError( 'search keyword ' + key + \
                                           ' is not implemented for COD' )
            if not isinstance( kwargs[key], list ):
                kwargs[key] = [ kwargs[key] ]
            sql_parts.append( "(" + self.keywords[key][1]( self, \
                                                           self.keywords[key][0], \
                                                           kwargs[key] ) + \
                              ")" )
        self.query_sql = "SELECT file FROM data WHERE " + \
                         " AND ".join( sql_parts )

        self._connect_db()
        self.cursor.execute( self.query_sql )
        self.db.commit()
        results = []
        for row in self.cursor.fetchall():
            results.append( str( row[0] ) )
        self._disconnect_db()

        return CODSearchResults( results )

    def setup_db(self, **kwargs):
        """
        Changes the database connection details.
        """
        for key in self.db_parameters.keys():
            if key in kwargs.keys():
                self.db_parameters[key] = kwargs[key]

    def _connect_db(self):
        """
        Connects to the MySQL database for performing searches.
        """
        self.db = MySQLdb.connect( host =   self.db_parameters['host'],
                                   user =   self.db_parameters['user'],
                                   passwd = self.db_parameters['passwd'],
                                   db =     self.db_parameters['db'] )
        self.cursor = self.db.cursor()

    def _disconnect_db(self):
        """
        Closes connection to the MySQL database.
        """
        self.db.close()


class CODSearchResults(aiida.tools.basedbimporter.BaseDBSearchResults):
    """
    Results of the search, performed on COD.
    """
    base_url = "http://www.crystallography.net/cod/"
    db_name = "COD"

    def __init__(self, results):
        self.results = results
        self.entries = {}
        self.position = 0

    def next(self):
        """
        Returns next result as CODEntry.
        """
        if len( self.results ) > self.position:
            self.position = self.position + 1
            return self.at( self.position - 1 )
        else:
            raise StopIteration()

    def at(self, position):
        """
        Returns ``position``-th result as CODEntry.
        """
        if position < 0 | position >= len( self.results ):
            raise IndexError( "index out of bounds" )
        if position not in self.entries:
            self.entries[position] = \
                aiida.tools.codimporter.CODEntry( self.base_url + \
                                                  self.results[position] + ".cif", \
                                                  source_db = self.db_name, \
                                                  db_id = self.results[position] )
        return self.entries[position]

class CODEntry(aiida.tools.basedbimporter.BaseDBEntry):
    """
    Represents an entry from COD.
    """

    def __init__(self, url, **kwargs):
        """
        Creates an instance of CODEntry, related to the supplied URL.
        """
        self.url       = url
        self.source_db = None
        self.db_id     = None
        self._cif      = None
        if 'source_db' in kwargs.keys():
            self.source_db = kwargs['source_db']
        if 'db_id' in kwargs.keys():
            self.db_id = kwargs['db_id']

    @property
    def cif(self):
        if self._cif is None:
            import urllib2
            self._cif = urllib2.urlopen( self.url ).read()
        return self._cif

    def get_ase_structure(self):
        """
        Returns ASE representation of the CIF.
        """
        import ase.io.cif
        import StringIO
        return ase.io.cif.read_cif( StringIO.StringIO( self.cif ) )
