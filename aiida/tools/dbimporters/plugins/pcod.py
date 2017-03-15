# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.tools.dbimporters.plugins.cod import (CodDbImporter,
                                                 CodSearchResults, CodEntry)



class PcodDbImporter(CodDbImporter):
    """
    Database importer for Predicted Crystallography Open Database.
    """

    def _int_clause(self, *args, **kwargs):
        return super(PcodDbImporter, self)._int_clause(*args, **kwargs)

    def _composition_clause(self, *args, **kwargs):
        return super(PcodDbImporter, self)._composition_clause(*args, **kwargs)

    def _formula_clause(self, *args, **kwargs):
        return super(PcodDbImporter, self)._formula_clause(*args, **kwargs)

    def _volume_clause(self, *args, **kwargs):
        return super(PcodDbImporter, self)._volume_clause(*args, **kwargs)

    def _str_exact_clause(self, *args, **kwargs):
        return super(PcodDbImporter, self)._str_exact_clause(*args, **kwargs)

    def _length_clause(self, *args, **kwargs):
        return super(PcodDbImporter, self)._length_clause(*args, **kwargs)

    def _angle_clause(self, *args, **kwargs):
        return super(PcodDbImporter, self)._angle_clause(*args, **kwargs)

    def _str_fuzzy_clause(self, *args, **kwargs):
        return super(PcodDbImporter, self)._str_fuzzy_clause(*args, **kwargs)

    _keywords = {'id': ['file', _int_clause],
                 'element': ['element', _composition_clause],
                 'number_of_elements': ['nel', _int_clause],
                 'formula': ['formula', _formula_clause],
                 'volume': ['vol', _volume_clause],
                 'spacegroup': ['sg', _str_exact_clause],
                 'a': ['a', _length_clause],
                 'b': ['b', _length_clause],
                 'c': ['c', _length_clause],
                 'alpha': ['alpha', _angle_clause],
                 'beta': ['beta', _angle_clause],
                 'gamma': ['gamma', _angle_clause],
                 'text': ['text', _str_fuzzy_clause]}

    def __init__(self, **kwargs):
        super(PcodDbImporter, self).__init__(**kwargs)
        self._db_parameters = {'host': 'www.crystallography.net',
                               'user': 'pcod_reader',
                               'passwd': '',
                               'db': 'pcod'}
        self.setup_db(**kwargs)

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
                if not isinstance(values, list):
                    values = [values]
                sql_parts.append( \
                    "(" + self._keywords[key][1](self, \
                                                 self._keywords[key][0], \
                                                 key, \
                                                 values) + \
                    ")")
        if len(kwargs.keys()) > 0:
            raise NotImplementedError( \
                "search keyword(s) '" + \
                "', '".join(kwargs.keys()) + "' " + \
                "is(are) not implemented for PCOD")
        return "SELECT file FROM data WHERE " + \
               " AND ".join(sql_parts)

    def query(self, **kwargs):
        """
        Performs a query on the PCOD database using ``keyword = value`` pairs,
        specified in ``kwargs``.

        :return: an instance of
            :py:class:`aiida.tools.dbimporters.plugins.pcod.PcodSearchResults`.
        """
        query_statement = self.query_sql(**kwargs)
        self._connect_db()
        results = []
        try:
            self._cursor.execute(query_statement)
            self._db.commit()
            for row in self._cursor.fetchall():
                results.append({'id': str(row[0])})
        finally:
            self._disconnect_db()

        return PcodSearchResults(results)


class PcodSearchResults(CodSearchResults):
    """
    Results of the search, performed on PCOD.
    """
    _base_url = "http://www.crystallography.net/pcod/cif/"

    def __init__(self, results):
        super(PcodSearchResults, self).__init__(results)
        self._return_class = PcodEntry

    def _get_url(self, result_dict):
        """
        Returns an URL of an entry CIF file.

        :param result_dict: dictionary, describing an entry in the results.
        """
        return self._base_url + \
               result_dict['id'][0] + "/" + \
               result_dict['id'][0:3] + "/" + \
               result_dict['id'] + ".cif"


class PcodEntry(CodEntry):
    """
    Represents an entry from PCOD.
    """
    _license = 'CC0'

    def __init__(self, uri,
                 db_name='Predicted Crystallography Open Database',
                 db_uri='http://www.crystallography.net/pcod', **kwargs):
        """
        Creates an instance of
        :py:class:`aiida.tools.dbimporters.plugins.pcod.PcodEntry`, related
        to the supplied URI.
        """
        super(PcodEntry, self).__init__(db_name=db_name,
                                        db_uri=db_uri,
                                        uri=uri,
                                        **kwargs)
