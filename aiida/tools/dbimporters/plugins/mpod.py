# -*- coding: utf-8 -*-

from aiida.tools.dbimporters.baseclasses \
    import DbImporter, DbSearchResults, DbEntry
import MySQLdb

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.3.0"

class MpodDbImporter(DbImporter):
    """
    Database importer for Material Properties Open Database.
    """

    def _str_clause(self, key, alias, values):
        """
        Returns part of HTTP GET query for querying string fields.
        """
        if not isinstance( values, str ) and not isinstance( values, int ):
            raise ValueError("incorrect value for keyword '" + alias + \
                             "' -- only strings and integers are accepted")
        return "{}={}".format(key, values)

    keywords = { 'phase_name': [ 'phase_name',  _str_clause ],
                 'formula'   : [ 'formula',     _str_clause ],
                 'element'   : [ 'element',     None ],
                 'cod_id'    : [ 'cod_code',    _str_clause ],
                 'authors'   : [ 'publ_author', _str_clause ] }

    def __init__(self, **kwargs):
        self.query_url = "http://mpod.cimav.edu.mx/data/search/"
        self.setup_db( **kwargs )

    def query_get(self, **kwargs):
        """
        Forms a HTTP GET query for querying the MPOD database.
        May return more than one query in case an intersection is needed.

        :return: a list containing strings for HTTP GET statement.
        """
        if 'formula' in kwargs.keys() and 'element' in kwargs.keys():
            raise ValueError("can not query both formula and elements "
                             "in MPOD")

        elements = []
        if 'element' in kwargs.keys():
            elements = kwargs.pop('element')
        if not isinstance(elements,list):
            elements = [elements]

        get_parts = []
        for key in self.keywords.keys():
            if key in kwargs.keys():
                values = kwargs.pop(key)
                get_parts.append(
                    self.keywords[key][1](self,
                                          self.keywords[key][0],
                                          key,
                                          values))

        if kwargs.keys():
            raise NotImplementedError("search keyword(s) '"
                                      "', '".join( kwargs.keys() ) + "' "
                                      "is(are) not implemented for MPOD")

        queries = []
        for e in elements:
            queries.append(self.query_url + '?' +
                           "&".join(get_parts +
                                    [self._str_clause('formula','element',e)]))
        if not queries:
            queries.append(self.query_url + '?' + "&".join(get_parts))

        return queries

    def query(self, **kwargs):
        """
        Performs a query on the MPOD database using ``keyword = value`` pairs,
        specified in ``kwargs``.

        :return: an instance of
            :py:class:`aiida.tools.dbimporters.plugins.mpod.MpodSearchResults`.
        """
        import urllib2
        import re
        query_statements = self.query_get( **kwargs )
        results = None
        for query in query_statements:
            response = urllib2.urlopen(query).read()
            this_results = re.findall("/datafiles/(\d+)\.mpod",response)
            if results is None:
                results = this_results
            else:
                results = filter(set(results).__contains__,this_results)

        return MpodSearchResults( results )

    def setup_db(self,query_url=None,**kwargs):
        """
        Changes the database connection details.
        """
        if query_url:
            self.query_url = query_url

        if kwargs.keys():
            raise NotImplementedError( \
                "unknown database connection parameter(s): '" + \
                "', '".join( kwargs.keys() ) + \
                "', available parameters: 'query_url'" )

    def get_supported_keywords(self):
        """
        Returns the list of all supported query keywords.

        :return: list of strings
        """
        return self.keywords.keys()

class MpodSearchResults(DbSearchResults):
    """
    Results of the search, performed on MPOD.
    """
    base_url = "http://mpod.cimav.edu.mx/datafiles/"
    db_name = "MPOD"

    def __init__(self, results):
        self.results = results
        self.entries = {}
        self.position = 0

    def at(self, position):
        """
        Returns ``position``-th result as
        :py:class:`aiida.tools.dbimporters.plugins.mpod.MpodEntry`.

        :param position: zero-based index of a result.

        :raise IndexError: if ``position`` is out of bounds.
        """
        if position < 0 | position >= len( self.results ):
            raise IndexError( "index out of bounds" )
        if position not in self.entries:
            db_id       = self.results[position]
            url = self.base_url + db_id + ".mpod"
            self.entries[position] = MpodEntry( url, db_id = db_id )
        return self.entries[position]

class MpodEntry(DbEntry):
    """
    Represents an entry from MPOD.
    """

    def __init__(self, url, **kwargs):
        """
        Creates an instance of
        :py:class:`aiida.tools.dbimporters.plugins.mpod.MpodEntry`, related
        to the supplied URL.
        """
        super(MpodEntry, self).__init__(db_source='Material Properties Open Database',
                                        db_url='http://mpod.cimav.edu.mx',
                                        url=url,
                                        **kwargs)
