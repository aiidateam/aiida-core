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
""""Implementation of `DbImporter` for the NNIN/C database."""
from aiida.tools.dbimporters.baseclasses import DbImporter, DbSearchResults, UpfEntry


class NnincDbImporter(DbImporter):
    """
    Database importer for NNIN/C Pseudopotential Virtual Vault.
    """

    def _str_clause(self, key, alias, values):
        """
        Returns part of HTTP GET query for querying string fields.
        """
        if not isinstance(values, str):
            raise ValueError(f"incorrect value for keyword '{alias}' -- only strings and integers are accepted")
        return f'{key}={values}'

    _keywords = {
        'xc_approximation': ['frmxcprox', _str_clause],
        'xc_type': ['frmxctype', _str_clause],
        'pseudopotential_class': ['frmspclass', _str_clause],
        'element': ['element', None]
    }

    def __init__(self, **kwargs):
        self._query_url = 'http://nninc.cnf.cornell.edu/dd_search.php'
        self.setup_db(**kwargs)

    def query_get(self, **kwargs):
        """
        Forms a HTTP GET query for querying the NNIN/C Pseudopotential
        Virtual Vault.

        :return: a string with HTTP GET statement.
        """
        get_parts = []
        for key, value in self._keywords.items():
            if key in kwargs:
                values = kwargs.pop(key)
                if value[1] is not None:
                    get_parts.append(value[1](self, value[0], key, values))

        if kwargs:
            raise NotImplementedError(f"following keyword(s) are not implemented: {', '.join(kwargs.keys())}")

        return f"{self._query_url}?{'&'.join(get_parts)}"

    def query(self, **kwargs):
        """
        Performs a query on the NNIN/C Pseudopotential Virtual Vault using
        ``keyword = value`` pairs, specified in ``kwargs``.

        :return: an instance of
            :py:class:`aiida.tools.dbimporters.plugins.nninc.NnincSearchResults`.
        """
        import re
        from urllib.request import urlopen

        query = self.query_get(**kwargs)
        with urlopen(query) as handle:
            response = handle.read()
        results = re.findall(r'psp_files/([^\']+)\.UPF', response)

        elements = kwargs.get('element', None)
        if elements and not isinstance(elements, list):
            elements = [elements]

        if elements:
            results_now = set()
            for psp in results:
                for element in elements:
                    if psp.startswith(f'{element}.'):
                        results_now = results_now | set([psp])
            results = list(results_now)

        return NnincSearchResults([{'id': x} for x in results])

    def setup_db(self, query_url=None, **kwargs):  # pylint: disable=arguments-differ
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


class NnincSearchResults(DbSearchResults):  # pylint: disable=abstract-method
    """
    Results of the search, performed on NNIN/C Pseudopotential Virtual
    Vault.
    """
    _base_url = 'http://nninc.cnf.cornell.edu/psp_files/'

    def __init__(self, results):
        super().__init__(results)
        self._return_class = NnincEntry

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
        return f"{self._base_url + result_dict['id']}.UPF"


class NnincEntry(UpfEntry):
    """
    Represents an entry from NNIN/C Pseudopotential Virtual Vault.
    """

    def __init__(self, uri, **kwargs):
        """
        Creates an instance of
        :py:class:`aiida.tools.dbimporters.plugins.nninc.NnincEntry`, related
        to the supplied URI.
        """
        super().__init__(
            db_name='NNIN/C Pseudopotential Virtual Vault', db_uri='http://nninc.cnf.cornell.edu', uri=uri, **kwargs
        )
