# -*- coding: utf-8 -*-

from aiida.tools.dbimporters.plugins.cod \
    import CodDbImporter, CodSearchResults, CodEntry

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.0"
__contributors__ = "Andrea Cepellotti, Andrius Merkys, Giovanni Pizzi"

class TcodDbImporter(CodDbImporter):
    """
    Database importer for Theoretical Crystallography Open Database.
    """

    def __init__(self, **kwargs):
        super(TcodDbImporter,self).__init__(**kwargs)
        self.db_parameters = { 'host':   'www.crystallography.net',
                               'user':   'cod_reader',
                               'passwd': '',
                               'db':     'tcod' }
        self.setup_db( **kwargs )

    def query(self, **kwargs):
        """
        Performs a query on the TCOD database using ``keyword = value`` pairs,
        specified in ``kwargs``.

        :return: an instance of
            :py:class:`aiida.tools.dbimporters.plugins.tcod.TcodSearchResults`.
        """
        query_statement = self.query_sql( **kwargs )
        self._connect_db()
        results = []
        try:
            self.cursor.execute( query_statement )
            self.db.commit()
            for row in self.cursor.fetchall():
                results.append({ 'id'         : str(row[0]),
                                 'svnrevision': str(row[1]) })
        finally:
            self._disconnect_db()

        return TcodSearchResults( results )


class TcodSearchResults(CodSearchResults):
    """
    Results of the search, performed on TCOD.
    """
    base_url = "http://www.crystallography.net/tcod/"

    def __init__(self, results):
        super(TcodSearchResults, self).__init__(results)
        self.return_class = TcodEntry

class TcodEntry(CodEntry):
    """
    Represents an entry from TCOD.
    """

    def __init__(self, url, **kwargs):
        """
        Creates an instance of
        :py:class:`aiida.tools.dbimporters.plugins.tcod.TcodEntry`, related
        to the supplied URL.
        """
        super(TcodEntry, self).__init__(db_source='Theoretical Crystallography Open Database',
                                        db_url='http://tcod.crystallography.net',
                                        url=url,
                                        **kwargs)
