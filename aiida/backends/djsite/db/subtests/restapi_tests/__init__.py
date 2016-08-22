# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."

import aiida.restapi.api as frestapp
from aiida.backends.djsite.db.testbase import AiidaTestCase
import tempfile
import os
import json

"""
Testcases to test AiiDA REST API
"""

class RESTApiTestCase(AiidaTestCase):

    dummydata = {}
    _url_prefix = "/api/v2"

    def setUp(self):
        """
        Create test client
        """
        self.db_fd, frestapp.app.config['DATABASE'] = tempfile.mkstemp()
        frestapp.app.config['TESTING'] = True
        self.app = frestapp.app.test_client()


    def tearDown(self):
        """close and unlink app db if any created in setUp"""
        os.close(self.db_fd)
        os.unlink(frestapp.app.config['DATABASE'])

    @classmethod
    def setUpClass(cls):
        super(AiidaTestCase, cls).setUpClass()

    def split_path(self, url):
        """
        Split the url with "?" to get url path and it's parameters
        :param url: Web url
        :return: url path and url parameters
        """
        parts = url.split("?")
        path = ""
        query_string = ""
        if len(parts) > 0:
            path = parts[0]
        if len(parts) > 1:
            query_string = parts[1]

        return path, query_string

    def compare_extra_response_data(self, node_type, url, response, pk=None):
        """
        In url response, we pass some extra information/data along with the node
        results. e.g. url method, node_type, path, pk, query_string, url, url_root,
        etc.

        :param node_type: url requested fot the type of the node
        :param url: web url
        :param response: url response
        :param pk: url requested for the node pk
        """
        path, query_string = self.split_path(url)

        self.assertEqual(response["method"], "GET")
        self.assertEqual(response["node_type"], node_type)
        self.assertEqual(response["path"], path)
        self.assertEqual(response["pk"], pk)
        self.assertEqual(response["query_string"], query_string)
        self.assertEqual(response["url"], "http://localhost" + url)
        self.assertEqual(response["url_root"], "http://localhost/")



    ###### node details and list with limit, offset, page, perpage ####
    def node_list(self, node_type, url, full_list=False, empty_list=False,
                  expected_list_ids=[], expected_range=[],
                  expected_errormsg=None, pk=None):
        """
        Get the full list of nodes from database
        :param node_type: url requested fot the type of the node
        :param url: web url
        :param full_list: if url is requested to get full list
        :param empty_list: if the response list is empty
        :param expected_list_ids: list of expected ids from dummydata
        :param expected_range: [start, stop] range of expected ids from dummydata
        :param expected_errormsg: expected error message in response
        :param pk: url requested for the node pk
        """
        url = RESTApiTestCase._url_prefix + url
        rv = self.app.get(url)
        response = json.loads(rv.data)

        if expected_errormsg:
            self.assertEqual(response["message"],expected_errormsg)
        else:
            if full_list:
                expected_data = RESTApiTestCase.dummydata[node_type]
            elif empty_list:
                expected_data = []
            elif len(expected_list_ids)>0:
                expected_data = [RESTApiTestCase.dummydata[node_type][i]
                             for i in expected_list_ids]
            elif expected_range != []:
                expected_data = RESTApiTestCase.dummydata[node_type][expected_range[0]
                :expected_range[1]]
            else:
                from aiida.common.exceptions import InputValidationError
                raise InputValidationError("Pass the expected range of the dummydata")

            self.assertTrue(len(response["data"]) == len(expected_data))

            for expected_node, response_node in zip(expected_data,
                                                   response["data"]):
                 self.assertTrue(all(item in response_node.items()
                                     for item in expected_node.items()))

            self.compare_extra_response_data(node_type, url, response, pk)


    ######## check exception #########
    def node_exception(self, url, exception_type):
        """
        Assert exception if any unknown parameter is passed in url
        :param url: web url
        :param exception_type: exception to be thrown
        :return:
        """
        self.assertRaises(exception_type, self.app.get(url))







