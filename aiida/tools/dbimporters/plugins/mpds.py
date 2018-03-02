# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import json
import os
import requests

from aiida.tools.dbimporters.baseclasses import CifEntry, DbEntry, DbImporter, DbSearchResults


class MpdsDbImporter(DbImporter):
    """
    Database importer for the Materials Platform for Data Science (MPDS)
    """

    _url = "https://api.mpds.io/v0/download/facet"
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

    def setup_db(self, url=None, api_key=None, collection=None):
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
    def supported_keywords(self):
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

    def query(self, query, collection=None):
        """
        Query the database with a given dictionary of query parameters for a given collection

        :param query: a dictionary with the query parameters
        :param collection: the collection to query
        """
        if collection is None:
            collection = self.collection

        results = []

        if collection == 'structures':
            for entry in self.structures.find(query):
                results.append(entry)
            search_results = MpdsSearchResults(results, return_class=MpdsCifEntry)
        else:
            raise ValueError('Unsupported collection: {}'.format(collection))

        return search_results

    def find(self, query):
        """
        Query the database with a given dictionary of query parameters

        :param query: a dictionary with the query parameters
        """
        if not isinstance(query, dict):
            raise TypeError('The query argument should be a dictionary')

        pagesize = self.pagesize

        response = self.get(q=json.dumps(query), pagesize=pagesize)
        content = self.get_response_content(response)

        count = content['count']
        npages = content['npages']

        for page in range(0, npages):

            response = self.get(q=json.dumps(query), pagesize=pagesize, page=page)
            content = self.get_response_content(response)

            if (page + 1) * pagesize > count:
                last = count - (page * pagesize)
            else:
                last = pagesize

            for i in range(0, last):
                result = content['out'][i]
                result['license'] = content['disclaimer']

                yield result

    def get(self, fmt='json', **kwargs):
        """
        Perform a GET request to the REST API using the kwargs as request parameters
        The url and API key will be used that were set upon construction

        :param fmt: the format of the response, 'cif' or json' (default)
        :param kwargs: parameters for the GET request
        """
        kwargs['fmt'] = fmt
        return requests.get(url=self.url, params=kwargs, headers={'Key': self.api_key})

    def get_response_content(self, response):
        """
        Analyze the response of an HTTP GET request, verify that the response code is OK
        and return the json loaded response text

        :param response: HTTP response
        :raises RuntimeError: HTTP response is not 200
        :raises ValueError: HTTP response 200 contained non zero error message
        """
        content = response.json()
        error = content.get('error', None)

        if not response.ok:
            raise RuntimeError('HTTP[{}] request failed: {}'.format(response.status_code, error))

        if error is not None:
            raise ValueError('Got error response: {}'.format(error))

        return content


class StructuresCollection(object):

    def __init__(self, engine):
        self._engine = engine

    @property
    def engine(self):
        """
        Return the query engine
        """
        return self._engine

    def find(self, query):
        """
        Query the structures collection with a given dictionary of query parameters

        :param query: a dictionary with the query parameters
        """
        for result in self.engine.find(query):

            if 'object_type' not in result or result['object_type'] != 'S':
                continue

            yield result


class MpdsEntry(DbEntry):
    """
    Represents an MPDS database entry
    """

    def __init__(self, url, **kwargs):
        """
        Set the class license from the source dictionary
        """
        license = kwargs.pop('license', None)

        if license is not None:
            self._license = license

        super(MpdsEntry, self).__init__(**kwargs)


class MpdsCifEntry(CifEntry, MpdsEntry):
    """
    An extension of the MpdsEntry class with the CifEntry class, which will treat
    the contents property through the URI as a cif file
    """

    def __init__(self, url, **kwargs):
        """
        Overwrite the permanent 'reference' URI with a URI that points to the CIF contents
        """
        kwargs['uri'] = url
        super(MpdsCifEntry, self).__init__(url, **kwargs)


class MpdsSearchResults(DbSearchResults):
    """
    A collection of MpdsEntry query result entries
    """

    _base_url ='https://api.mpds.io/v0/download/s'
    _db_name = 'Materials Platform for Data Science'
    _db_uri = 'https://mpds.io/'
    _return_class = MpdsEntry

    def __init__(self, results, return_class=None):
        if return_class is not None:
            self._return_class = return_class
        super(MpdsSearchResults, self).__init__(results)

    def _get_source_dict(self, result_dict):
        """
        Returns the source information dictionary of an MPDS query result entry

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

        return source_dict

    def _get_url(self, result_dict):
        """
        Return the URL that points to the raw CIF content of the entry 

        :param result_dict: query result entry dictionary
        """
        url = '{}?q={}&fmt=cif&export=1'.format(self._base_url, result_dict['entry'])
        return url
