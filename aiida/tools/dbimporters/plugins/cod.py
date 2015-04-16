# -*- coding: utf-8 -*-

from aiida.tools.dbimporters.baseclasses \
    import DbImporter, DbSearchResults, DbEntry

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Andrius Merkys, Giovanni Pizzi"

class CodDbImporter(DbImporter):
    """
    Database importer for Crystallography Open Database.
    """

    def _int_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying integer fields.
        """
        for e in values:
            if not isinstance( e, int ) and not isinstance( e, basestring ):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only integers and strings are accepted")
        return key + " IN (" + ", ".join( map( lambda i: str( int( i ) ),
                                               values ) ) + ")"

    def _str_exact_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying string fields.
        """
        clause_parts = []
        for e in values:
            if not isinstance( e, int ) and not isinstance( e, basestring ):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only integers and strings are accepted")
            if isinstance( e, int ):
                e = str(e)
            clause_parts.append("'" + e + "'")
        return key + " IN (" + ", ".join(clause_parts) + ")"

    def _formula_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying formula fields.
        """
        for e in values:
            if not isinstance( e, str ):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only strings are accepted")
        return self._str_exact_clause( key, \
                                       alias, \
                                       map( lambda f: "- " + str(f) + " -", \
                                            values ) )

    def _str_fuzzy_clause(self, key, alias, values):
        """
        Returns SQL query predicate for fuzzy querying of string fields.
        """
        clause_parts = []
        for e in values:
            if not isinstance( e, int ) and not isinstance( e, basestring ):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only integers and strings are accepted")
            if isinstance( e, int ):
                e = str(e)
            clause_parts.append(key + " LIKE '%" + e + "%'")
        return " OR ".join(clause_parts)

    def _composition_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying elements in formula fields.
        """
        clause_parts = []
        for e in values:
            if not isinstance( e, basestring ):
                raise ValueError("incorrect value for keyword '" + alias + \
                                 "' -- only strings are accepted")
            clause_parts.append("formula REGEXP ' " + e + "[0-9 ]'")
        return " AND ".join(clause_parts)

    def _double_clause(self, key, alias, values, precision):
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
    pressure_precision    = 1

    def _length_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying lattice vector lengths.
        """
        return self._double_clause(key, alias, values, self.length_precision)

    def _angle_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying lattice angles.
        """
        return self._double_clause(key, alias, values, self.angle_precision)

    def _volume_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying unit cell volume.
        """
        return self._double_clause(key, alias, values, self.volume_precision)

    def _temperature_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying temperature.
        """
        return self._double_clause(key, alias, values, self.temperature_precision)

    def _pressure_clause(self, key, alias, values):
        """
        Returns SQL query predicate for querying pressure.
        """
        return self._double_clause(key, alias, values, self.pressure_precision)

    _keywords = { 'id'                : [ 'file',          _int_clause ],
                  'element'           : [ 'element',       _composition_clause ],
                  'number_of_elements': [ 'nel',           _int_clause ],
                  'mineral_name'      : [ 'mineral',       _str_fuzzy_clause ],
                  'chemical_name'     : [ 'chemname',      _str_fuzzy_clause ],
                  'formula'           : [ 'formula',       _formula_clause ],
                  'volume'            : [ 'vol',           _volume_clause ],
                  'spacegroup'        : [ 'sg',            _str_exact_clause ],
                  'spacegroup_hall'   : [ 'sgHall',        _str_exact_clause ],
                  'a'                 : [ 'a',             _length_clause ],
                  'b'                 : [ 'b',             _length_clause ],
                  'c'                 : [ 'c',             _length_clause ],
                  'alpha'             : [ 'alpha',         _angle_clause ],
                  'beta'              : [ 'beta',          _angle_clause ],
                  'gamma'             : [ 'gamma',         _angle_clause ],
                  'z'                 : [ 'Z',             _int_clause ],
                  'measurement_temp'  : [ 'celltemp',      _temperature_clause ],
                  'diffraction_temp'  : [ 'diffrtemp',     _temperature_clause ],
                  'measurement_pressure':
                                        [ 'cellpressure',  _pressure_clause ],
                  'diffraction_pressure':
                                        [ 'diffrpressure', _pressure_clause ],
                  'authors'           : [ 'authors',       _str_fuzzy_clause ],
                  'journal'           : [ 'journal',       _str_fuzzy_clause ],
                  'title'             : [ 'title',         _str_fuzzy_clause ],
                  'year'              : [ 'year',          _int_clause ],
                  'journal_volume'    : [ 'volume',        _int_clause ],
                  'journal_issue'     : [ 'issue',         _str_exact_clause ],
                  'first_page'        : [ 'firstpage',     _str_exact_clause ],
                  'last_page'         : [ 'lastpage',      _str_exact_clause ],
                  'doi'               : [ 'doi',           _str_exact_clause ] }

    def __init__(self, **kwargs):
        self._db     = None
        self._cursor = None
        self._db_parameters = { 'host':   'www.crystallography.net',
                                'user':   'cod_reader',
                                'passwd': '',
                                'db':     'cod' }
        self.setup_db( **kwargs )

    def query_sql(self, **kwargs):
        """
        Forms a SQL query for querying the COD database using
        ``keyword = value`` pairs, specified in ``kwargs``.

        :return: string containing a SQL statement.
        """
        sql_parts = [ "(status IS NULL OR status != 'retracted')" ]
        for key in self._keywords.keys():
            if key in kwargs.keys():
                values = kwargs.pop(key)
                if not isinstance( values, list ):
                    values = [ values ]
                sql_parts.append( \
                    "(" + self._keywords[key][1]( self, \
                                                  self._keywords[key][0], \
                                                  key, \
                                                  values ) + \
                    ")" )
        if len( kwargs.keys() ) > 0:
            raise NotImplementedError( \
                "search keyword(s) '" + \
                "', '".join( kwargs.keys() ) + "' " + \
                "is(are) not implemented for COD" )
        return "SELECT file, svnrevision FROM data WHERE " + \
               " AND ".join( sql_parts )

    def query(self, **kwargs):
        """
        Performs a query on the COD database using ``keyword = value`` pairs,
        specified in ``kwargs``.

        :return: an instance of
            :py:class:`aiida.tools.dbimporters.plugins.cod.CodSearchResults`.
        """
        query_statement = self.query_sql( **kwargs )
        self._connect_db()
        results = []
        try:
            self._cursor.execute( query_statement )
            self._db.commit()
            for row in self._cursor.fetchall():
                results.append({ 'id'         : str(row[0]),
                                 'svnrevision': str(row[1]) })
        finally:
            self._disconnect_db()

        return CodSearchResults( results )

    def setup_db(self, **kwargs):
        """
        Changes the database connection details.
        """
        for key in self._db_parameters.keys():
            if key in kwargs.keys():
                self._db_parameters[key] = kwargs.pop(key)
        if len( kwargs.keys() ) > 0:
            raise NotImplementedError( \
                "unknown database connection parameter(s): '" + \
                "', '".join( kwargs.keys() ) + \
                "', available parameters: '" + \
                "', '".join( self._db_parameters.keys() ) + "'" )

    def get_supported_keywords(self):
        """
        Returns the list of all supported query keywords.

        :return: list of strings
        """
        return self._keywords.keys()

    def _connect_db(self):
        """
        Connects to the MySQL database for performing searches.
        """
        import MySQLdb

        self._db = MySQLdb.connect( host =   self._db_parameters['host'],
                                    user =   self._db_parameters['user'],
                                    passwd = self._db_parameters['passwd'],
                                    db =     self._db_parameters['db'] )
        self._cursor = self._db.cursor()

    def _disconnect_db(self):
        """
        Closes connection to the MySQL database.
        """
        self._db.close()

class CodSearchResults(DbSearchResults):
    """
    Results of the search, performed on COD.
    """
    _base_url = "http://www.crystallography.net/cod/"

    def __init__(self, results):
        self._results = results
        self._entries = {}
        self._return_class = CodEntry

    def __len__(self):
        return len(self._results)

    def at(self, position):
        """
        Returns ``position``-th result as
        :py:class:`aiida.tools.dbimporters.plugins.cod.CodEntry`.

        :param position: zero-based index of a result.

        :raise IndexError: if ``position`` is out of bounds.
        """
        if position < 0 | position >= len( self._results ):
            raise IndexError( "index out of bounds" )
        if position not in self._entries:
            db_id       = self._results[position]['id']
            svnrevision = self._results[position]['svnrevision']
            url = self._base_url + db_id + ".cif"
            source_dict = {'db_id': db_id}
            if svnrevision is not None:
                source_dict['db_version'] = svnrevision
                url = "{}@{}".format(url,svnrevision)
            self._entries[position] = self._return_class( url, **source_dict )
        return self._entries[position]

class CodEntry(DbEntry):
    """
    Represents an entry from COD.
    """

    def __init__(self,url,db_source='Crystallography Open Database',
                 db_url='http://www.crystallography.net',**kwargs):
        """
        Creates an instance of
        :py:class:`aiida.tools.dbimporters.plugins.cod.CodEntry`, related
        to the supplied URL.
        """
        super(CodEntry, self).__init__(db_source=db_source,db_url=db_url,
                                       url=url,**kwargs)
