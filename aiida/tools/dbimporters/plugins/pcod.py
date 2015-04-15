# -*- coding: utf-8 -*-

from aiida.tools.dbimporters.plugins.cod \
    import CodDbImporter, CodSearchResults, CodEntry

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Andrius Merkys, Giovanni Pizzi"

class PcodDbImporter(CodDbImporter):
    """
    Database importer for Predicted Crystallography Open Database.
    """

    def _int_clause(self,*args,**kwargs):
        return super(PcodDbImporter,self)._int_clause(*args,**kwargs)

    def _composition_clause(self,*args,**kwargs):
        return super(PcodDbImporter,self)._composition_clause(*args,**kwargs)

    def _formula_clause(self,*args,**kwargs):
        return super(PcodDbImporter,self)._formula_clause(*args,**kwargs)

    def _volume_clause(self,*args,**kwargs):
        return super(PcodDbImporter,self)._volume_clause(*args,**kwargs)

    def _str_exact_clause(self,*args,**kwargs):
        return super(PcodDbImporter,self)._str_exact_clause(*args,**kwargs)

    def _length_clause(self,*args,**kwargs):
        return super(PcodDbImporter,self)._length_clause(*args,**kwargs)

    def _angle_clause(self,*args,**kwargs):
        return super(PcodDbImporter,self)._angle_clause(*args,**kwargs)

    def _str_fuzzy_clause(self,*args,**kwargs):
        return super(PcodDbImporter,self)._str_fuzzy_clause(*args,**kwargs)

    _keywords = { 'id'                : [ 'file',          _int_clause ],
                  'element'           : [ 'element',       _composition_clause ],
                  'number_of_elements': [ 'nel',           _int_clause ],
                  'formula'           : [ 'formula',       _formula_clause ],
                  'volume'            : [ 'vol',           _volume_clause ],
                  'spacegroup'        : [ 'sg',            _str_exact_clause ],
                  'a'                 : [ 'a',             _length_clause ],
                  'b'                 : [ 'b',             _length_clause ],
                  'c'                 : [ 'c',             _length_clause ],
                  'alpha'             : [ 'alpha',         _angle_clause ],
                  'beta'              : [ 'beta',          _angle_clause ],
                  'gamma'             : [ 'gamma',         _angle_clause ],
                  'text'              : [ 'text',          _str_fuzzy_clause ] }

    def __init__(self, **kwargs):
        super(PcodDbImporter,self).__init__(**kwargs)
        self._db_parameters = { 'host':   'www.crystallography.net',
                                'user':   'pcod_reader',
                                'passwd': '',
                                'db':     'pcod' }
        self.setup_db( **kwargs )

    def query_sql(self, **kwargs):
        """
        Forms a SQL query for querying the PCOD database using
        ``keyword = value`` pairs, specified in ``kwargs``.

        :return: string containing a SQL statement.
        """
        sql_parts = []
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
                "is(are) not implemented for PCOD" )
        return "SELECT file FROM data WHERE " + \
               " AND ".join( sql_parts )

    def query(self, **kwargs):
        """
        Performs a query on the PCOD database using ``keyword = value`` pairs,
        specified in ``kwargs``.

        :return: an instance of
            :py:class:`aiida.tools.dbimporters.plugins.pcod.PcodSearchResults`.
        """
        query_statement = self.query_sql( **kwargs )
        self._connect_db()
        results = []
        try:
            self._cursor.execute( query_statement )
            self._db.commit()
            for row in self._cursor.fetchall():
                results.append({ 'id': str(row[0]) })
        finally:
            self._disconnect_db()

        return PcodSearchResults( results )

class PcodSearchResults(CodSearchResults):
    """
    Results of the search, performed on PCOD.
    """
    _base_url = "http://www.crystallography.net/pcod/cif/"

    def __init__(self, results):
        super(PcodSearchResults, self).__init__(results)
        self._return_class = PcodEntry

    def at(self, position):
        """
        Returns ``position``-th result as
        :py:class:`aiida.tools.dbimporters.plugins.pcod.PcodEntry`.

        :param position: zero-based index of a result.

        :raise IndexError: if ``position`` is out of bounds.
        """
        if position < 0 | position >= len( self._results ):
            raise IndexError( "index out of bounds" )
        if position not in self._entries:
            db_id       = self._results[position]['id']
            url = self._base_url + db_id[0] + "/" + db_id[0:3] + "/" + \
                  db_id + ".cif"
            source_dict = {'db_id': db_id}
            self._entries[position] = self._return_class( url, **source_dict )
        return self._entries[position]

class PcodEntry(CodEntry):
    """
    Represents an entry from PCOD.
    """

    def __init__(self,url,
                 db_source='Predicted Crystallography Open Database',
                 db_url='http://www.crystallography.net/pcod',**kwargs):
        """
        Creates an instance of
        :py:class:`aiida.tools.dbimporters.plugins.pcod.PcodEntry`, related
        to the supplied URL.
        """
        super(PcodEntry, self).__init__(db_source=db_source,
                                        db_url=db_url,
                                        url=url,
                                        **kwargs)
