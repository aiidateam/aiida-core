# -*- coding: utf-8 -*-

import basedbimporter
import dbentry
import MySQLdb

class CODImporter(basedbimporter.BaseDBImporter):
    """
    Database importer for Crystallography Open Database.
    """

    db_parameters = { 'host':   'www.crystallography.net',
                      'user':   'cod_reader',
                      'passwd': '',
                      'db':     'cod' }

    def int_clause(self, key, values):
        return key + " IN (" + ", ".join( map( lambda i: str( i ),
                                               values ) ) + ")"

    def str_exact_clause(self, key, values):
        return key + \
               " IN (" + ", ".join( map( lambda f: "'" + f + "'", \
                                         values ) ) + ")"
    def formula_clause(self, key, values):
        return self.str_exact_clause( key, \
                                      map( lambda f: "- " + f + " -", values ) )

    def str_fuzzy_clause(self, key, values):
        return " OR ".join( map( lambda s: key + \
                                           " LIKE '%" + s + "%'", values ) )

    def composition_clause(self, key, values):
        return " AND ".join( map( lambda e: "formula REGEXP ' " + e + "[0-9 ]'",
                                  values ) )

    def double_clause(self, key, values, precision):
        return " OR ".join( map( lambda d: key + \
                                           " BETWEEN " + \
                                           str( d - precision ) + " AND " + \
                                           str( d + precision ),
                                 values ) )

    length_precision = 0.001
    angle_precision  = 0.001
    volume_precision = 0.001

    def length_clause(self, key, values):
        return self.double_clause(key, values, self.length_precision)

    def angle_clause(self, key, values):
        return self.double_clause(key, values, self.angle_precision)

    def volume_clause(self, key, values):
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
                 'gamma'             : [ 'gamma',    angle_clause ] }

    def __init__(self):
        pass

    def query(self, **kwargs):
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

        self.connect_db()
        self.cursor.execute( self.query_sql )
        self.db.commit()
        results = []
        for row in self.cursor.fetchall():
            results.append( str( row[0] ) )
        self.disconnect_db()

        return CODSearchResults( results )

    def setup_db(self, **kwargs):
        for p in self.db.keys():
            if p in kwargs.keys():
                self.db_parameters[p] = kwargs[p]

    def connect_db(self):
        """
        Connects to the MySQL database for performing searches.
        """
        self.db = MySQLdb.connect( host =   self.db_parameters['host'],
                                   user =   self.db_parameters['user'],
                                   passwd = self.db_parameters['passwd'],
                                   db =     self.db_parameters['db'] )
        self.cursor = self.db.cursor()

    def disconnect_db(self):
        """
        Closes connection to the MySQL database.
        """
        self.db.close()

class CODSearchResults(basedbimporter.BaseDBSearchResults):

    base_url = "http://www.crystallography.net/cod/"
    db_name = "COD"
    results  = []
    entries  = {}
    position = 0

    def __init__(self, results):
        self.results = results

    def fetch_all(self):
        for i in range( 0, len( self.results )-1 ):
            if i not in self.entries:
                self.entries[i] = \
                    dbentry.DBEntry( self.base_url + \
                                     self.results[i] + ".cif", \
                                     source_db = self.db_name, \
                                     db_id = self.results[i] )
        return self.entries.values()

    def next(self):
        if len( self.results ) > self.position:
            self.position = self.position + 1
            if self.position not in self.entries:
                self.entries[self.position-1] = \
                    dbentry.DBEntry( self.base_url + \
                                     self.results[self.position-1] + ".cif", \
                                     source_db = self.db_name, \
                                     db_id = self.results[self.position-1] )
            return self.entries[self.position-1]
        else:
            raise StopIteration()

    def at(self, position):
        if position < 0 | position >= len( self.results ):
            raise IndexError( "index out of bounds" )
        if position not in self.entries:
            self.entries[position] = \
                dbentry.DBEntry( self.base_url + \
                                 self.results[position-1] + ".cif", \
                                 source_db = self.db_name, \
                                 db_id = self.results[self.position-1] )
        return self.entries[position]
