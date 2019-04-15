# -*- coding: utf-8 -*-

from aiida.tools.dbimporters.plugins.cod import (CodDbImporter,
                                                 CodSearchResults, CodEntry)

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0.1"
__authors__ = "The AiiDA team."


class TcodDbImporter(CodDbImporter):
    """
    Database importer for Theoretical Crystallography Open Database.
    """

    def __init__(self, **kwargs):
        super(TcodDbImporter, self).__init__(**kwargs)
        self._db_parameters = {'host': 'www.crystallography.net',
                               'user': 'cod_reader',
                               'passwd': '',
                               'db': 'tcod'}
        self.setup_db(**kwargs)

    def query(self, **kwargs):
        """
        Performs a query on the TCOD database using ``keyword = value`` pairs,
        specified in ``kwargs``.

        :return: an instance of
            :py:class:`aiida.tools.dbimporters.plugins.tcod.TcodSearchResults`.
        """
        query_statement = self.query_sql(**kwargs)
        self._connect_db()
        results = []
        try:
            self._cursor.execute(query_statement)
            self._db.commit()
            for row in self._cursor.fetchall():
                results.append({'id': str(row[0]),
                                'svnrevision': str(row[1])})
        finally:
            self._disconnect_db()

        return TcodSearchResults(results)


class TcodSearchResults(CodSearchResults):
    """
    Results of the search, performed on TCOD.
    """
    _base_url = "http://www.crystallography.net/tcod/"

    def __init__(self, results):
        super(TcodSearchResults, self).__init__(results)
        self._return_class = TcodEntry


class TcodEntry(CodEntry):
    """
    Represents an entry from TCOD.
    """
    _license = 'CC0'

    def __init__(self, uri,
                 db_name='Theoretical Crystallography Open Database',
                 db_uri='http://www.crystallography.net/tcod', **kwargs):
        """
        Creates an instance of
        :py:class:`aiida.tools.dbimporters.plugins.tcod.TcodEntry`, related
        to the supplied URI.
        """
        super(TcodEntry, self).__init__(db_name=db_name,
                                        db_uri=db_uri,
                                        uri=uri,
                                        **kwargs)
