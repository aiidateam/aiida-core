# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""""Implementation of `DbImporter` for the Materials Project database."""
import datetime
import os

from pymatgen.ext.matproj import MPRester
import requests

from aiida.tools.dbimporters.baseclasses import CifEntry, DbImporter, DbSearchResults


class MaterialsProjectImporter(DbImporter):
    """
    Database importer for the Materials Project.
    """

    _properties = 'structure'
    _supported_keywords = None

    def __init__(self, **kwargs):
        """
        Instantiate the MaterialsProjectImporter by setting up the Materials API (MAPI)
        connection details.
        """
        self.setup_db(**kwargs)

    def setup_db(self, **kwargs):
        """
        Setup the required parameters to the REST API
        """
        try:
            api_key = kwargs['api_key']
        except KeyError:
            try:
                api_key = os.environ['PMG_MAPI_KEY']
            except KeyError as exception:
                raise KeyError(
                    'API key not supplied and PMG_MAPI_KEY environment variable not set. Either pass it when '
                    'initializing the class, or set the environment variable PMG_MAPI_KEY to your API key.'
                ) from exception
            api_key = None

        self._api_key = api_key
        self._verify_api_key()
        self._mpr = MPRester(self._api_key)

    def _verify_api_key(self):
        """
        Verify the supplied API key by issuing a request to Materials Project.
        """
        response = requests.get(
            'https://www.materialsproject.org/rest/v1/api_check', headers={'X-API-KEY': self._api_key}
        )
        response_content = response.json()  # a dict
        if 'error' in response_content:
            raise RuntimeError(response_content['error'])
        if not response_content['valid_response']:
            raise RuntimeError('Materials Project did not give a valid response for the API key check.')
        if not response_content['api_key_valid']:
            raise RuntimeError('Your API key for Materials Project is not valid.')

    @property
    def api_key(self):
        """
        Return the API key configured for the importer
        """
        return self._api_key

    @property
    def properties(self):
        """
        Return the properties that will be queried
        """
        return self._properties

    def get_supported_keywords(self):
        """
        Returns the list of all supported query keywords

        :return: list of strings
        """
        return self._supported_keywords

    def query(self, **kwargs):
        """
        Query the database with a given dictionary of query parameters for a given properties

        :param query: a dictionary with the query parameters
        :param properties: the properties to query
        """
        try:
            query = kwargs['query']
        except AttributeError:
            raise AttributeError(
                'Make sure the supplied dictionary has `query` as a key. This '
                'should contain a dictionary with the right query needed.'
            )
        try:
            properties = kwargs['properties']
        except AttributeError:
            raise AttributeError('Make sure the supplied dictionary has `properties` as a key.')

        if not isinstance(query, dict):
            raise TypeError('The query argument should be a dictionary')

        if properties is None:
            properties = self._properties

        if properties != 'structure':
            raise ValueError(f'Unsupported properties: {properties}')

        results = []
        properties_list = ['material_id', 'cif']
        for entry in self._find(query, properties_list):
            results.append(entry)
        search_results = MaterialsProjectSearchResults(results, return_class=MaterialsProjectCifEntry)

        return search_results

    def _find(self, query, properties):
        """
        Query the database with a given dictionary of query parameters

        :param query: a dictionary with the query parameters
        """
        for entry in self._mpr.query(criteria=query, properties=properties):
            yield entry


class MaterialsProjectCifEntry(CifEntry):  # pylint: disable=abstract-method
    """
    A Materials Project entry class which extends the DbEntry class with a CifEntry class.

    """

    _license = 'Materials Project'

    def __init__(self, url, **kwargs):
        """
        The DbSearchResults base class instantiates a new DbEntry by explicitly passing the url
        of the entry as an argument. In this case it is the same as the 'uri' value that is
        already contained in the source dictionary so we just copy it
        """
        cif = kwargs.pop('cif', None)
        kwargs['uri'] = url
        super().__init__(**kwargs)

        if cif is not None:
            self.cif = cif


class MaterialsProjectSearchResults(DbSearchResults):  # pylint: disable=abstract-method
    """
    A collection of MaterialsProjectEntry query result entries.

    :param results: query result entry dictionary
    :return_class: the class associated with each
    """

    _db_name = 'Materials Project'
    _db_uri = 'https://materialsproject.org'
    _material_base_url = 'https://materialsproject.org/materials/'
    _version = str(datetime.datetime.now())

    def __init__(self, results, return_class):
        self._return_class = return_class
        super().__init__(results)

    def _get_source_dict(self, result_dict):
        """
        Return the source information dictionary of an Materials Project query result entry

        :param result_dict: query result entry dictionary
        """
        source_dict = {
            'db_name': self._db_name,
            'db_uri': self._db_uri,
            'id': result_dict['material_id'],
            'uri': self._get_url(result_dict),
            'version': self._version,
        }

        if 'cif' in result_dict:
            source_dict['cif'] = result_dict['cif']

        return source_dict

    def _get_url(self, result_dict):
        """
        Return the permanent URI of the result entry

        :param result_dict: query result entry dictionary
        """
        return self._material_base_url + result_dict['material_id']
