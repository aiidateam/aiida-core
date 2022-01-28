# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=no-self-use
""""Implementation of `DbImporter` for the MPOD database."""
from aiida.tools.dbimporters.baseclasses import CifEntry, DbImporter, DbSearchResults


class MpodDbImporter(DbImporter):
    """
    Database importer for Material Properties Open Database.
    """

    def _str_clause(self, key, alias, values):
        """
        Returns part of HTTP GET query for querying string fields.
        """
        if not isinstance(values, str) and not isinstance(values, int):
            raise ValueError(f"incorrect value for keyword '{alias}' -- only strings and integers are accepted")
        return f'{key}={values}'

    _keywords = {
        'phase_name': ['phase_name', _str_clause],
        'formula': ['formula', _str_clause],
        'element': ['element', None],
        'cod_id': ['cod_code', _str_clause],
        'authors': ['publ_author', _str_clause]
    }

    def __init__(self, **kwargs):
        self._query_url = 'http://mpod.cimav.edu.mx/data/search/'
        self.setup_db(**kwargs)

    def query_get(self, **kwargs):
        """
        Forms a HTTP GET query for querying the MPOD database.
        May return more than one query in case an intersection is needed.

        :return: a list containing strings for HTTP GET statement.
        """
        if 'formula' in kwargs and 'element' in kwargs:
            raise ValueError('can not query both formula and elements in MPOD')

        elements = []
        if 'element' in kwargs:
            elements = kwargs.pop('element')
        if not isinstance(elements, list):
            elements = [elements]

        get_parts = []
        for key, value in self._keywords.items():
            if key in kwargs:
                values = kwargs.pop(key)
                get_parts.append(value[1](self, value[0], key, values))

        if kwargs:
            raise NotImplementedError(f"following keyword(s) are not implemented: {', '.join(kwargs.keys())}")

        queries = []
        for element in elements:
            clauses = [self._str_clause('formula', 'element', element)]
            queries.append(f"{self._query_url}?{'&'.join(get_parts + clauses)}")
        if not queries:
            queries.append(f"{self._query_url}?{'&'.join(get_parts)}")

        return queries

    def query(self, **kwargs):
        """
        Performs a query on the MPOD database using ``keyword = value`` pairs,
        specified in ``kwargs``.

        :return: an instance of
            :py:class:`aiida.tools.dbimporters.plugins.mpod.MpodSearchResults`.
        """
        import re
        from urllib.request import urlopen

        query_statements = self.query_get(**kwargs)
        results = None
        for query in query_statements:
            with urlopen(query) as handle:
                response = handle.read()
            this_results = re.findall(r'/datafiles/(\d+)\.mpod', response)
            if results is None:
                results = this_results
            else:
                results = list(filter(set(results).__contains__, this_results))

        return MpodSearchResults([{'id': x} for x in results])

    def setup_db(self, query_url=None, **kwargs):  # pylint: disable=arguments-differ
        """
        Changes the database connection details.
        """
        if query_url:
            self._query_url = query_url

        if kwargs:
            raise NotImplementedError(f"following keyword(s) are not implemented: {', '.join(kwargs.keys())}")

    def get_supported_keywords(self):
        """
        Returns the list of all supported query keywords.

        :return: list of strings
        """
        return self._keywords.keys()


class MpodSearchResults(DbSearchResults):  # pylint: disable=abstract-method
    """
    Results of the search, performed on MPOD.
    """
    _base_url = 'http://mpod.cimav.edu.mx/datafiles/'

    def __init__(self, results):
        super().__init__(results)
        self._return_class = MpodEntry

    def __len__(self):
        return len(self._results)

    def _get_source_dict(self, result_dict):
        """
        Returns a dictionary, which is passed as kwargs to the created
        DbEntry instance, describing the source of the entry.

        :param result_dict: dictionary, describing an entry in the results.
        """
        return {'id': result_dict['id']}

    def _get_url(self, result_dict):
        """
        Returns an URL of an entry CIF file.

        :param result_dict: dictionary, describing an entry in the results.
        """
        return f"{self._base_url + result_dict['id']}.mpod"


class MpodEntry(CifEntry):  # pylint: disable=abstract-method
    """
    Represents an entry from MPOD.
    """

    def __init__(self, uri, **kwargs):
        """
        Creates an instance of
        :py:class:`aiida.tools.dbimporters.plugins.mpod.MpodEntry`, related
        to the supplied URI.
        """
        super().__init__(
            db_name='Material Properties Open Database', db_uri='http://mpod.cimav.edu.mx', uri=uri, **kwargs
        )
