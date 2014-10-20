# -*- coding: utf-8 -*-

import basedbimporter
import dbentry
import MySQLdb

class CODImporter(basedbimporter.BaseDBImporter):
    db_parameters = { 'host':   'www.crystallography.net',
                      'user':   'cod_reader',
                      'passwd': '',
                      'db':     'cod' }

    keyword_aliases = { 'id':                 'file',
                        'number_of_elements': 'nel',
                        'mineral_name':       'mineral',
                        'chemical_name':      'chemname',
                        'volume':             'vol',
                        'spacegroup':         'sg',
                      }

    def __init__(self):
        self.connect_db()

    def query(self, **kwargs):
        sql_parts = [ "(status IS NULL OR status != 'retracted')",
                      "(duplicateof IS NULL)" ]
        for key in kwargs.keys():
            keyname = key
            operand = ""
            if isinstance( kwargs[key], list ):
                operand = "IN ('" + "', '".join( kwargs[key] ) + "')"
            else:
                operand = "= '" + kwargs[key] + "'"
            if key in self.keyword_aliases.keys():
                keyname = self.keyword_aliases[key]
            sql_parts.append( "(" + keyname + " " + operand + ")" )
        self.cursor.execute( "SELECT file FROM data WHERE " +
                             " AND ".join( sql_parts ) + " LIMIT 5" )
        self.db.commit()
        results = []
        for row in self.cursor.fetchall():
            results.append( str( row[0] ) )
        return CODSearchResults( results )

    def setup_db(self, **kwargs):
        for p in self.db.keys():
            if p in kwargs.keys():
                self.db_parameters[p] = kwargs[p]
        self.db = self.connect()

    def connect_db(self):
        self.db = MySQLdb.connect( host =   self.db_parameters['host'],
                                   user =   self.db_parameters['user'],
                                   passwd = self.db_parameters['passwd'],
                                   db =     self.db_parameters['db'] )
        self.cursor = self.db.cursor()

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
