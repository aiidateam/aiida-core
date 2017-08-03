# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.tools.dbimporters.baseclasses import (DbImporter, DbSearchResults,
                                                 CifEntry)



class MpodDbImporter(DbImporter):
    """
    Database importer for Material Properties Open Database.
    """

    def _str_clause(self, key, alias, values):
        """
        Returns part of HTTP GET query for querying string fields.
        """
        if not isinstance(values, basestring) and not isinstance(values, int):
            raise ValueError("incorrect value for keyword '" + alias + \
                             "' -- only strings and integers are accepted")
        return "{}={}".format(key, values)

    _keywords = {'phase_name': ['phase_name', _str_clause],
                 'formula': ['formula', _str_clause],
                 'element': ['element', None],
                 'cod_id': ['cod_code', _str_clause],
                 'authors': ['publ_author', _str_clause]}

    def __init__(self, **kwargs):
        self._query_url = "http://mpod.cimav.edu.mx/data/search/"
        self.setup_db(**kwargs)

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
        if not isinstance(elements, list):
            elements = [elements]

        get_parts = []
        for key in self._keywords.keys():
            if key in kwargs.keys():
                values = kwargs.pop(key)
                get_parts.append(
                    self._keywords[key][1](self,
                                           self._keywords[key][0],
                                           key,
                                           values))

        if kwargs.keys():
            raise NotImplementedError("search keyword(s) '"
                                      "', '".join(kwargs.keys()) + "' "
                                                                   "is(are) not implemented for MPOD")

        queries = []
        for e in elements:
            queries.append(self._query_url + '?' +
                           "&".join(get_parts +
                                    [self._str_clause('formula', 'element', e)]))
        if not queries:
            queries.append(self._query_url + '?' + "&".join(get_parts))

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

        query_statements = self.query_get(**kwargs)
        results = None
        for query in query_statements:
            response = urllib2.urlopen(query).read()
            this_results = re.findall("/datafiles/(\d+)\.mpod", response)
            if results is None:
                results = this_results
            else:
                results = filter(set(results).__contains__, this_results)

        return MpodSearchResults([{"id": x} for x in results])

    def setup_db(self, query_url=None, **kwargs):
        """
        Changes the database connection details.
        """
        if query_url:
            self._query_url = query_url

        if kwargs.keys():
            raise NotImplementedError( \
                "unknown database connection parameter(s): '" + \
                "', '".join(kwargs.keys()) + \
                "', available parameters: 'query_url'")

    def get_supported_keywords(self):
        """
        Returns the list of all supported query keywords.

        :return: list of strings
        """
        return self._keywords.keys()


class MpodSearchResults(DbSearchResults):
    """
    Results of the search, performed on MPOD.
    """
    _base_url = "http://mpod.cimav.edu.mx/datafiles/"

    def __init__(self, results):
        super(MpodSearchResults, self).__init__(results)
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
        return self._base_url + result_dict['id'] + ".mpod"


class MpodEntry(CifEntry):
    """
    Represents an entry from MPOD.
    """

    def __init__(self, uri, **kwargs):
        """
        Creates an instance of
        :py:class:`aiida.tools.dbimporters.plugins.mpod.MpodEntry`, related
        to the supplied URI.
        """
        super(MpodEntry, self).__init__(db_name='Material Properties Open Database',
                                        db_uri='http://mpod.cimav.edu.mx',
                                        uri=uri,
                                        **kwargs)
