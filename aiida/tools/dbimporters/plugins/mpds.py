# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""""Implementation of `DbImporter` for the MPDS database."""
import copy
import enum
import json
import os

import requests

from aiida.tools.dbimporters.baseclasses import CifEntry, DbEntry, DbImporter, DbSearchResults


class ApiFormat(enum.Enum):
    JSON = 'json'
    CIF = 'cif'


DEFAULT_API_FORMAT = ApiFormat.JSON
CIF_ENTRY_ID_TAG = '_pauling_file_entry'


class MpdsDbImporter(DbImporter):
    """
    Database importer for the Materials Platform for Data Science (MPDS)
    """

    _url = 'https://api.mpds.io/v0/download/facet'
    _api_key = None
    _collection = 'structures'
    _pagesize = 1000

    _supported_keywords = [
        'props',
        'elements',
        'classes',
        'lattices',
        'formulae',
        'sgs',
        'protos',
        'aeatoms',
        'aetype',
        'authors',
        'codens',
        'years',
    ]

    def __init__(self, url=None, api_key=None):
        """
        Instantiate the MpdsDbImporter by setting up the API connection details

        :param url: the full base url of the REST API endpoint
        :param api_key: the API key to be used for HTTP requests
        """
        self.setup_db(url=url, api_key=api_key)
        self._structures = StructuresCollection(self)

    def setup_db(self, url=None, api_key=None, collection=None):  # pylint: disable=arguments-differ
        """
        Setup the required parameters for HTTP requests to the REST API

        :param url: the full base url of the REST API endpoint
        :param api_key: the API key to be used for HTTP requests
        """
        if url is not None:
            self._url = url

        if collection is not None:
            self._collection = collection

        if api_key is not None:
            self._api_key = api_key
        else:
            try:
                self._api_key = os.environ['MPDS_KEY']
            except KeyError:
                raise ValueError('API key not supplied and MPDS_KEY environment variable not set')

    @property
    def api_key(self):
        """
        Return the API key configured for the importer
        """
        return self._api_key

    @property
    def collection(self):
        """
        Return the collection that will be queried
        """
        return self._collection

    @property
    def pagesize(self):
        """
        Return the pagesize set for the importer
        """
        return self._pagesize

    @property
    def structures(self):
        """
        Access the structures collection in the MPDS
        """
        return self._structures

    @property
    def get_supported_keywords(self):  # pylint: disable=invalid-overridden-method
        """
        Returns the list of all supported query keywords

        :return: list of strings
        """
        return self._supported_keywords

    @property
    def url(self):
        """
        Return the base url configured for the importer
        """
        return self._url

    def query(self, query, collection=None):  # pylint: disable=arguments-differ
        """
        Query the database with a given dictionary of query parameters for a given collection

        :param query: a dictionary with the query parameters
        :param collection: the collection to query
        """
        if collection is None:
            collection = self.collection

        if collection == 'structures':

            results = []
            results_cif = {}
            results_json = []

            for entry in self.structures.find(query, fmt=ApiFormat.JSON):
                results_json.append(entry)

            for entry in self.structures.find(query, fmt=ApiFormat.CIF):
                entry_id = self.get_id_from_cif(entry)
                results_cif[entry_id] = entry

            for entry in results_json:

                entry_id = entry['entry']

                try:
                    cif = results_cif[entry_id]
                except KeyError:
                    # Corresponding cif file was not retrieved, skipping
                    continue

                result_entry = copy.deepcopy(entry)
                result_entry['cif'] = cif
                results.append(result_entry)

            search_results = MpdsSearchResults(results, return_class=MpdsCifEntry)
        else:
            raise ValueError(f'Unsupported collection: {collection}')

        return search_results

    def find(self, query, fmt=DEFAULT_API_FORMAT):
        """
        Query the database with a given dictionary of query parameters

        :param query: a dictionary with the query parameters
        """
        # pylint: disable=too-many-branches

        if not isinstance(query, dict):
            raise TypeError('The query argument should be a dictionary')

        pagesize = self.pagesize

        response = self.get(q=json.dumps(query), fmt=ApiFormat.JSON, pagesize=pagesize)
        content = self.get_response_content(response, fmt=ApiFormat.JSON)

        count = content['count']

        for page in range(content['npages']):

            response = self.get(q=json.dumps(query), fmt=fmt, pagesize=pagesize, page=page)
            content = self.get_response_content(response, fmt=fmt)

            if fmt == ApiFormat.JSON:

                if (page + 1) * pagesize > count:
                    last = count - (page * pagesize)
                else:
                    last = pagesize

                for i in range(last):
                    result = content['out'][i]
                    result['license'] = content['disclaimer']

                    yield result

            elif fmt == ApiFormat.CIF:

                cif = []
                for line in content.splitlines():
                    if cif:
                        if line.startswith('data_'):
                            text = '\n'.join(cif)
                            cif = [line]
                            yield text
                        else:
                            cif.append(line)
                    elif line.startswith('data_'):
                        cif.append(line)
                if cif:
                    yield '\n'.join(cif)

    def get(self, fmt=DEFAULT_API_FORMAT, **kwargs):
        """
        Perform a GET request to the REST API using the kwargs as request parameters
        The url and API key will be used that were set upon construction

        :param fmt: the format of the response, 'cif' or json' (default)
        :param kwargs: parameters for the GET request
        """
        kwargs['fmt'] = fmt.value
        return requests.get(url=self.url, params=kwargs, headers={'Key': self.api_key})

    @staticmethod
    def get_response_content(response, fmt=DEFAULT_API_FORMAT):
        """
        Analyze the response of an HTTP GET request, verify that the response code is OK
        and return the json loaded response text

        :param response: HTTP response
        :raises RuntimeError: HTTP response is not 200
        :raises ValueError: HTTP response 200 contained non zero error message
        """
        if not response.ok:
            raise RuntimeError(f'HTTP[{response.status_code}] request failed: {response.text}')

        if fmt == ApiFormat.JSON:
            content = response.json()
            error = content.get('error', None)

            if error is not None:
                raise ValueError(f'Got error response: {error}')

            return content

        return response.text

    @staticmethod
    def get_id_from_cif(cif):
        """
        Extract the entry id from the string formatted cif response of the MPDS API

        :param cif: string representation of the cif file
        :returns: entry id of the cif file or None if could not be found
        """
        entry_id = None

        for line in cif.split('\n'):
            if CIF_ENTRY_ID_TAG in line:
                entry_id = line.split()[1]
                break

        return entry_id


class StructuresCollection:
    """Collection of structures."""

    def __init__(self, engine):
        self._engine = engine

    @property
    def engine(self):
        """
        Return the query engine
        """
        return self._engine

    def find(self, query, fmt=DEFAULT_API_FORMAT):
        """
        Query the structures collection with a given dictionary of query parameters

        :param query: a dictionary with the query parameters
        """
        for result in self.engine.find(query, fmt=fmt):

            if fmt != ApiFormat.CIF and ('object_type' not in result or result['object_type'] != 'S'):
                continue

            yield result


class MpdsEntry(DbEntry):
    """
    Represents an MPDS database entry
    """

    def __init__(self, _, **kwargs):
        """
        Set the class license from the source dictionary
        """
        license = kwargs.pop('license', None)  # pylint: disable=redefined-builtin

        if license is not None:
            self._license = license

        super().__init__(**kwargs)


class MpdsCifEntry(CifEntry, MpdsEntry):  # pylint: disable=abstract-method
    """
    An extension of the MpdsEntry class with the CifEntry class, which will treat
    the contents property through the URI as a cif file
    """

    def __init__(self, url, **kwargs):
        """
        The DbSearchResults base class instantiates a new DbEntry by explicitly passing the url
        of the entry as an argument. In this case it is the same as the 'uri' value that is
        already contained in the source dictionary so we just copy it
        """
        cif = kwargs.pop('cif', None)
        kwargs['uri'] = url
        super().__init__(url, **kwargs)

        if cif is not None:
            self.cif = cif


class MpdsSearchResults(DbSearchResults):  # pylint: disable=abstract-method
    """Collection of MpdsEntry query result entries."""

    _db_name = 'Materials Platform for Data Science'
    _db_uri = 'https://mpds.io/'
    _return_class = MpdsEntry

    def __init__(self, results, return_class=None):
        if return_class is not None:
            self._return_class = return_class
        super().__init__(results)

    def _get_source_dict(self, result_dict):
        """
        Return the source information dictionary of an MPDS query result entry

        :param result_dict: query result entry dictionary
        """
        source_dict = {
            'db_name': self._db_name,
            'db_uri': self._db_uri,
            'id': result_dict['entry'],
            'license': result_dict['license'],
            'uri': result_dict['reference'],
            'version': result_dict['version'],
        }

        if 'cif' in result_dict:
            source_dict['cif'] = result_dict['cif']

        return source_dict

    def _get_url(self, result_dict):
        """
        Return the permanent URI of the result entry

        :param result_dict: query result entry dictionary
        """
        return result_dict['reference']
