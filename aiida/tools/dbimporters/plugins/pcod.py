# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""""Implementation of `DbImporter` for the PCOD database."""
from aiida.tools.dbimporters.plugins.cod import CodDbImporter, CodEntry, CodSearchResults


class PcodDbImporter(CodDbImporter):
    """
    Database importer for Predicted Crystallography Open Database.
    """

    _keywords = {
        'id': ['file', CodDbImporter._int_clause],
        'element': ['element', CodDbImporter._composition_clause],
        'number_of_elements': ['nel', CodDbImporter._int_clause],
        'formula': ['formula', CodDbImporter._formula_clause],
        'volume': ['vol', CodDbImporter._volume_clause],
        'spacegroup': ['sg', CodDbImporter._str_exact_clause],
        'a': ['a', CodDbImporter._length_clause],
        'b': ['b', CodDbImporter._length_clause],
        'c': ['c', CodDbImporter._length_clause],
        'alpha': ['alpha', CodDbImporter._angle_clause],
        'beta': ['beta', CodDbImporter._angle_clause],
        'gamma': ['gamma', CodDbImporter._angle_clause],
        'text': ['text', CodDbImporter._str_fuzzy_clause]
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._db_parameters = {'host': 'www.crystallography.net', 'user': 'pcod_reader', 'passwd': '', 'db': 'pcod'}
        self.setup_db(**kwargs)

    def query_sql(self, **kwargs):
        """
        Forms a SQL query for querying the PCOD database using
        ``keyword = value`` pairs, specified in ``kwargs``.

        :return: string containing a SQL statement.
        """
        sql_parts = []
        for key, value in self._keywords.items():
            if key in kwargs:
                values = kwargs.pop(key)
                if not isinstance(values, list):
                    values = [values]
                sql_parts.append(f'({value[1](self, value[0], key, values)})')
        if kwargs:
            raise NotImplementedError(f"following keyword(s) are not implemented: {', '.join(kwargs.keys())}")

        return f"SELECT file FROM data WHERE {' AND '.join(sql_parts)}"

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


class PcodSearchResults(CodSearchResults):  # pylint: disable=abstract-method
    """
    Results of the search, performed on PCOD.
    """
    _base_url = 'http://www.crystallography.net/pcod/cif/'

    def __init__(self, results):
        super().__init__(results)
        self._return_class = PcodEntry

    def _get_url(self, result_dict):
        """
        Returns an URL of an entry CIF file.

        :param result_dict: dictionary, describing an entry in the results.
        """
        return f"{self._base_url + result_dict['id'][0]}/{result_dict['id'][0:3]}/{result_dict['id']}.cif"


class PcodEntry(CodEntry):  # pylint: disable=abstract-method
    """
    Represents an entry from PCOD.
    """
    _license = 'CC0'

    def __init__(
        self,
        uri,
        db_name='Predicted Crystallography Open Database',
        db_uri='http://www.crystallography.net/pcod',
        **kwargs
    ):
        """
        Creates an instance of
        :py:class:`aiida.tools.dbimporters.plugins.pcod.PcodEntry`, related
        to the supplied URI.
        """
        super().__init__(db_name=db_name, db_uri=db_uri, uri=uri, **kwargs)
