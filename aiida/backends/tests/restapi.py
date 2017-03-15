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

from aiida.backends.testbase import AiidaTestCase
from aiida.common.links import LinkType
from aiida.orm import DataFactory
from aiida.orm.calculation import Calculation
from aiida.orm.computer import Computer
from aiida.orm.data import Data
from aiida.orm.querybuilder import QueryBuilder
from aiida.restapi.api import App, AiidaApi

StructureData = DataFactory('structure')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')


class RESTApiTestCase(AiidaTestCase):
    """
    Setup of the tests for the AiiDA RESTful-api
    """
    _url_prefix = "/api/v2"
    _dummy_data = {}
    _PERPAGE_DEFAULT = 20
    _LIMIT_DEFAULT = 400

    @classmethod
    def setUpClass(cls):
        """
        Basides the standard setup we need to add few more objects in the
        database to be able to explore different requests/filters/orderings etc.
        """

        # call parent setUpClass method
        super(RESTApiTestCase, cls).setUpClass()

        # connect the app and the api
        # Init the api by connecting it the the app (N.B. respect the following
        # order, api.__init__)
        kwargs = dict(PREFIX=cls._url_prefix,
                      PERPAGE_DEFAULT=cls._PERPAGE_DEFAULT,
                      LIMIT_DEFAULT=cls._LIMIT_DEFAULT)

        cls.app = App(__name__)
        api = AiidaApi(cls.app, **kwargs)

        # create test inputs
        cell = ((2., 0., 0.), (0., 2., 0.), (0., 0., 2.))
        structure = StructureData(cell=cell)
        structure.append_atom(position=(0., 0., 0.), symbols=['Ba'])
        structure.store()

        parameter1 = ParameterData(dict={"a": 1, "b": 2})
        parameter1.store()

        parameter2 = ParameterData(dict={"c": 3, "d": 4})
        parameter2.store()

        kpoint = KpointsData()
        kpoint.set_kpoints_mesh([4, 4, 4])
        kpoint.store()

        calc = Calculation()
        calc._set_attr("attr1", "OK")
        calc._set_attr("attr2", "OK")
        calc.store()

        calc.add_link_from(structure)
        calc.add_link_from(parameter1)
        kpoint.add_link_from(calc, link_type=LinkType.CREATE)

        calc1 = Calculation()
        calc1.store()

        from aiida.orm.computer import Computer

        dummy_computers = [
            {
                "name": "test1",
                "hostname": "test1.epfl.ch",
                "transport_type": "ssh",
                "scheduler_type": "pbspro",
            },
            {
                "name": "test2",
                "hostname": "test2.epfl.ch",
                "transport_type": "ssh",
                "scheduler_type": "torque",
            },
            {
                "name": "test3",
                "hostname": "test3.epfl.ch",
                "transport_type": "local",
                "scheduler_type": "slurm",
            },
            {
                "name": "test4",
                "hostname": "test4.epfl.ch",
                "transport_type": "ssh",
                "scheduler_type": "slurm",
            }
        ]

        for dummy_computer in dummy_computers:
            computer = Computer(**dummy_computer)
            computer.store()

        # Prepare typical REST responses
        cls.process_dummy_data()

    def get_dummy_data(self):
        return self._dummy_data

    def get_url_prefix(self):
        return self._url_prefix

    @classmethod
    def process_dummy_data(cls):
        """
        This functions prepare atomic chunks of typical responses from the
        RESTapi and puts them into class attributes
        """
        computers = expected_data = QueryBuilder().append(Computer, tag="comp",
                                                          project=["id", "name",
                                                                   "hostname",
                                                                   "transport_type",
                                                                   "scheduler_type"]).order_by(
            {'comp': [{'name': {'order': 'asc'}}]}).all()
        calculations = QueryBuilder().append(Calculation, tag="calc",
                                             project=["id", "user_id",
                                                      "type"]).order_by(
            {'calc': [{'id': {'order': 'desc'}}]}).all()
        data = QueryBuilder().append(Data, tag="data", project=["id", "user_id",
                                                                "type"]).order_by(
            {'data': [{'id': {'order': 'desc'}}]}).all()

        cls._dummy_data["computers"] = []
        for c in computers:
            cls._dummy_data["computers"].append({
                "id": c[0],
                "name": c[1],
                "hostname": c[2],
                "transport_type": c[3],
                "scheduler_type": c[4]
            })

        cls._dummy_data["calculations"] = []
        for c in calculations:
            cls._dummy_data["calculations"].append({
                "id": c[0],
                "user_id": c[1],
                "type": c[2]
            })

        cls._dummy_data["data"] = []
        for c in data:
            cls._dummy_data["data"].append({
                "id": c[0],
                "user_id": c[1],
                "type": c[2]
            })

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
        results. e.g. url method, node_type, path, pk, query_string, url,
        url_root,
        etc.

        :param node_type: url requested fot the type of the node
        :param url: web url
        :param response: url response
        :param pk: url requested for the node pk
        """
        path, query_string = self.split_path(url)

        self.assertEqual(response["method"], "GET")
        self.assertEqual(response["resource_type"], node_type)
        self.assertEqual(response["path"], path)
        self.assertEqual(response["pk"], pk)
        self.assertEqual(response["query_string"], query_string)
        self.assertEqual(response["url"], "http://localhost" + url)
        self.assertEqual(response["url_root"], "http://localhost/")

    ###### node details and list with limit, offset, page, perpage ####
    def process_test(self, node_type, url, full_list=False, empty_list=False,
                     expected_list_ids=[], expected_range=[],
                     expected_errormsg=None, pk=None, result_node_type=None,
                     result_name=None):
        """
        Get the full list of nodes from database
        :param node_type: url requested fot the type of the node
        :param url: web url
        :param full_list: if url is requested to get full list
        :param empty_list: if the response list is empty
        :param expected_list_ids: list of expected ids from data
        :param expected_range: [start, stop] range of expected ids from data
        :param expected_errormsg: expected error message in response
        :param pk: url requested for the node pk
        :param result_node_type: node type in response data
        :param result_name: result name in response e.g. inputs, outputs
        """

        if result_node_type == None and result_name == None:
            result_node_type = node_type
            result_name = node_type
        url = self._url_prefix + url
        self.app.config['TESTING'] = True
        with self.app.test_client() as client:
            rv = client.get(url)
            response = json.loads(rv.data)
            if expected_errormsg:
                self.assertEqual(response["message"], expected_errormsg)
            else:
                if full_list:
                    expected_data = self._dummy_data[result_node_type]
                elif empty_list:
                    expected_data = []
                elif len(expected_list_ids) > 0:
                    expected_data = [self._dummy_data[result_node_type][i]
                                     for i in expected_list_ids]
                elif expected_range != []:
                    expected_data = self._dummy_data[result_node_type][
                                    expected_range[0]:expected_range[1]]
                else:
                    from aiida.common.exceptions import InputValidationError
                    raise InputValidationError(
                        "Pass the expected range of the dummydata")

                self.assertTrue(
                    len(response["data"][result_name]) == len(expected_data))

                for expected_node, response_node in zip(expected_data,
                                                        response["data"][
                                                            result_name]):
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


class RESTApiTestSuite(RESTApiTestCase):
    """
    """

    ############### single computer ########################
    def test_computers_details(self):
        """
        Requests the details of single computer
        """
        node_pk = self.get_dummy_data()["computers"][0]["id"]
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers/" + str(node_pk),
                                     expected_list_ids=[0], pk=node_pk)

    ############### full list with limit, offset, page, perpage #############
    def test_computers_list(self):
        """
        Get the full list of computers from database
        """
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers?orderby=+id", full_list=True)

    def test_computers_list_limit_offset(self):
        """
        Get the list of computers from database using limit
        and offset parameter.
        It should return the no of rows specified in limit from
        database starting from the no. specified in offset
        """
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers?limit=2&offset=2&orderby=+id",
                                     expected_range=[2, 4])

    def test_computers_list_limit_only(self):
        """
        Get the list of computers from database using limit
        parameter.
        It should return the no of rows specified in limit from
        database.
        """
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers?limit=2&orderby=+id",
                                     expected_range=[None, 2])

    def test_computers_list_offset_only(self):
        """
        Get the list of computers from database using offset
        parameter
        It should return all the rows from database starting from
        the no. specified in offset
        """
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers?offset=2&orderby=+id",
                                     expected_range=[2, None])

    def test_computers_list_limit_offset_perpage(self):
        """
        If we pass the limit, offset and perpage at same time, it
        would return the error message.
        """
        expected_error = "perpage key is incompatible with limit and offset"
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers?offset=2&limit=1&perpage=2&orderby=+id",
                                     expected_errormsg=expected_error)

    def test_computers_list_page_limit_offset(self):
        """
        If we use the page, limit and offset at same time, it
        would return the error message.
        """
        expected_error = "requesting a specific page is incompatible with " \
                         "limit and offset"
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers/page/2?offset=2&limit=1&orderby=+id",
                                     expected_errormsg=expected_error)

    def test_computers_list_page_limit_offset_perpage(self):
        """
        If we use the page, limit, offset and perpage at same time, it
        would return the error message.
        """
        expected_error = "perpage key is incompatible with limit and offset"
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers/page/2?offset=2&limit=1&perpage=2&orderby=+id",
                                     expected_errormsg=expected_error)

    def test_computers_list_page_default(self):
        """
        it returns the no. of rows defined as default perpage option
        from database.

        **** no.of pages = total no. of computers in database / perpage
        "/page" acts as "/page/1?perpage=default_value"

        """
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers/page?orderby=+id",
                                     full_list=True)

    def test_computers_list_page_perpage(self):
        """
        **** no.of pages = total no. of computers in database / perpage
        Using this formula it returns the no. of rows for requested page
        """
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers/page/1?perpage=2&orderby=+id",
                                     expected_range=[None, 2])

    def test_computers_list_page_perpage_exceed(self):
        """
        **** no.of pages = total no. of computers in database / perpage

        If we request the page which exceeds the total no. of pages then
        it would return the error message.
        """
        expected_error = "Non existent page requested. The page range is [1 : " \
                         "3]"
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers/page/4?perpage=2&orderby=+id",
                                     expected_errormsg=expected_error)

    ############### list filters ########################
    def test_computers_filter_id1(self):
        """
        Add filter on the id of computer and get the filtered computer
        list (e.g. id=1)
        """
        node_pk = self.get_dummy_data()["computers"][0]["id"]
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers?id=" + str(node_pk),
                                     expected_list_ids=[0])

    def test_computers_filter_id2(self):
        """
        Add filter on the id of computer and get the filtered computer
        list (e.g. id > 2)
        """
        node_pk = self.get_dummy_data()["computers"][1]["id"]
        RESTApiTestCase.process_test(self, "computers", "/computers?id>" + str(
            node_pk) + "&orderby=+id",
                                     expected_range=[2, None])

    def test_computers_filter_pk(self):
        """
        Add filter on the id of computer and get the filtered computer
        list (e.g. id=1)
        """
        node_pk = self.get_dummy_data()["computers"][0]["id"]
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers?pk=" + str(node_pk),
                                     expected_list_ids=[0])

    def test_computers_filter_name(self):
        """
        Add filter for the name of computer and get the filtered computer
        list
        """
        RESTApiTestCase.process_test(self, "computers",
                                     '/computers?name="test1"',
                                     expected_list_ids=[1])

    def test_computers_filter_hostname(self):
        """
        Add filter for the hostname of computer and get the filtered computer
        list
        """
        RESTApiTestCase.process_test(self, "computers",
                                     '/computers?hostname="test1.epfl.ch"',
                                     expected_list_ids=[1])

    def test_computers_filter_transport_type(self):
        """
        Add filter for the transport_type of computer and get the filtered
        computer
        list
        """
        RESTApiTestCase.process_test(self, "computers",
                                     '/computers?transport_type="local"&orderby=+id',
                                     expected_list_ids=[0, 3])

    ############### list orderby ########################
    def test_computers_orderby_id_asc(self):
        """
        Returns the computers list ordered by "id" in ascending
        order
        """
        RESTApiTestCase.process_test(self, "computers", "/computers?orderby=id",
                                     full_list=True)

    def test_computers_orderby_id_asc_sign(self):
        """
        Returns the computers list ordered by "+id" in ascending
        order
        """
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers?orderby=+id",
                                     full_list=True)

    def test_computers_orderby_id_desc(self):
        """
        Returns the computers list ordered by "id" in descending
        order
        """
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers?orderby=-id",
                                     expected_list_ids=[4, 3, 2, 1, 0])

    def test_computers_orderby_name_asc(self):
        """
        Returns the computers list ordered by "name" in ascending
        order
        """
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers?orderby=name",
                                     full_list=True)

    def test_computers_orderby_name_asc_sign(self):
        """
        Returns the computers list ordered by "+name" in ascending
        order
        """
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers?orderby=+name",
                                     full_list=True)

    def test_computers_orderby_name_desc(self):
        """
        Returns the computers list ordered by "name" in descending
        order
        """
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers?orderby=-name",
                                     expected_list_ids=[4, 3, 2, 1, 0])

    def test_computers_orderby_scheduler_type_asc(self):
        """
        Returns the computers list ordered by "scheduler_type" in ascending
        order
        """
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers?orderby=scheduler_type",
                                     expected_list_ids=[0, 1, 3, 4, 2])

    def test_computers_orderby_scheduler_type_asc_sign(self):
        """
        Returns the computers list ordered by "+scheduler_type" in ascending
        order
        """
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers?orderby=+scheduler_type",
                                     expected_list_ids=[0, 1, 3, 4, 2])

    def test_computers_orderby_scheduler_type_desc(self):
        """
        Returns the computers list ordered by "scheduler_type" in descending
        order
        """
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers?orderby=-scheduler_type",
                                     expected_list_ids=[2, 3, 4, 0, 1])

    ############### list orderby combinations #######################
    def test_computers_orderby_mixed1(self):
        """
        Returns the computers list first order by "transport_type" in
        ascending order and if it is having same transport_type, order it
        by "id"
        """
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers?orderby=transport_type,id",
                                     expected_list_ids=[0, 3, 1, 2, 4])

    def test_computers_orderby_mixed2(self):
        """
        Returns the computers list first order by "scheduler_type" in
        descending order and if it is having same scheduler_type, order it
        by "name"
        """
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers?orderby=-scheduler_type,name",
                                     expected_list_ids=[2, 3, 4, 0, 1])

    def test_computers_orderby_mixed3(self):
        """
        Returns the computers list first order by "scheduler_type" in
        ascending order and if it is having same scheduler_type, order it
        by "hostname" descending order

        Response::
        test4 slurm
        test3 slurm
        test2 torque
        test1 pbspro
        localhost pbspro
        ==========
        Expected::
        test1 pbspro
        localhost pbspro
        test4 slurm
        test3 slurm
        test2 torque
        test1 test4


        RESTApiTestCase.process_test(self, "computers",
                                  "/computers?orderby=+scheduler_type,
                                  -hostname",
                                  expected_list_ids=[1,0,4,3,2])
        """
        pass

    ############### list filter combinations #######################
    def test_computers_filter_mixed1(self):
        """
        Add filter for the hostname and id of computer and get the
        filtered computer list
        """
        node_pk = self.get_dummy_data()["computers"][0]["id"]
        RESTApiTestCase.process_test(self, "computers",
                                     '/computers?id>' + str(
                                         node_pk) + '&hostname="test1.epfl.ch"',
                                     expected_list_ids=[1])

    def test_computers_filter_mixed2(self):
        """
        Add filter for the id, hostname and transport_type of the computer
        and get the filtered computer list
        """
        node_pk = self.get_dummy_data()["computers"][0]["id"]
        RESTApiTestCase.process_test(self, "computers",
                                     '/computers?id>' + str(
                                         node_pk) +
                                     '&hostname="test3.epfl.ch"&transport_type="ssh"',
                                     empty_list=True)

    ############### list all parameter combinations #######################
    def test_computers_mixed1(self):
        """
        url parameters: id, limit and offset
        """
        node_pk = self.get_dummy_data()["computers"][0]["id"]
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers?id>" + str(
                                         node_pk) + "&limit=2&offset=3",
                                     expected_list_ids=[4])

    def test_computers_mixed2(self):
        """
        url parameters: id, page, perpage
        """
        node_pk = self.get_dummy_data()["computers"][0]["id"]
        RESTApiTestCase.process_test(self, "computers",
                                     "/computers/page/2?id>" + str(
                                         node_pk) + "&perpage=2&orderby=+id",
                                     expected_list_ids=[3, 4])

    def test_computers_mixed3(self):
        """
        url parameters: id, transport_type, orderby
        """
        node_pk = self.get_dummy_data()["computers"][0]["id"]
        RESTApiTestCase.process_test(self, "computers",
                                     '/computers?id>=' + str(
                                         node_pk) +
                                     '&transport_type="ssh"&orderby=-id&limit=2',
                                     expected_list_ids=[4, 2])

    ########## pass unknown url parameter ###########
    def test_computers_unknown_param(self):
        """
        url parameters: id, limit and offset

        from aiida.common.exceptions import InputValidationError
        RESTApiTestCase.node_exception(self, "/computers?aa=bb&id=2",
                                       InputValidationError)
        """
        pass

    ############### single calculation ########################
    def test_calculations_details(self):
        """
        Requests the details of single calculation
        """
        node_pk = self.get_dummy_data()["calculations"][0]["id"]
        RESTApiTestCase.process_test(self, "calculations",
                                     "/calculations/" + str(node_pk),
                                     expected_list_ids=[0], pk=node_pk)

    ############### full list with limit, offset, page, perpage #############
    def test_calculations_list(self):
        """ 
		Get the full list of calculations from database
        """
        RESTApiTestCase.process_test(self, "calculations",
                                     "/calculations?orderby=-id",
                                     full_list=True)

    def test_calculations_list_limit_offset(self):
        """
        Get the list of calculations from database using limit
        and offset parameter.
        It should return the no of rows specified in limit from
        database starting from the no. specified in offset
        """
        RESTApiTestCase.process_test(self, "calculations",
                                     "/calculations?limit=1&offset=1&orderby=+id",
                                     expected_list_ids=[0])

    ############### calculation inputs  #############
    def test_calculation_inputs(self):
        """
        Get the list of give calculation inputs
        """
        node_pk = self.get_dummy_data()["calculations"][1]["id"]
        self.process_test("calculations", "/calculations/" + str(
            node_pk) + "/io/inputs?orderby=id",
                          expected_list_ids=[3, 2], pk=node_pk,
                          result_node_type="data",
                          result_name="inputs")

    def test_calculation_input_filters(self):
        """
        Get filtered inputs list for given calculations
        """
        node_pk = self.get_dummy_data()["calculations"][1]["id"]
        self.process_test("calculations", '/calculations/' + str(
            node_pk) + '/io/inputs?type="data.parameter.ParameterData."',
                          expected_list_ids=[2], pk=node_pk,
                          result_node_type="data",
                          result_name="inputs")

    ############### calculation attributes #############
    def test_calculation_attributes(self):
        """
        Get list of calculation attributes
        """
        node_pk = self.get_dummy_data()["calculations"][1]["id"]
        url = self.get_url_prefix() + "/calculations/" + str(
            node_pk) + "/content/attributes"
        self.app.config['TESTING'] = True
        with self.app.test_client() as client:
            rv = client.get(url)
            response = json.loads(rv.data)
            self.assertEqual(response["data"]["attributes"],
                             {'attr2': 'OK', 'attr1': 'OK'})
            RESTApiTestCase.compare_extra_response_data(self, "calculations",
                                                        url,
                                                        response, pk=node_pk)

    def test_calculation_attributes_nalist_filter(self):
        """
        Get list of calculation attributes with filter nalist
        """
        node_pk = self.get_dummy_data()["calculations"][1]["id"]
        url = self.get_url_prefix() + '/calculations/' + str(
            node_pk) + '/content/attributes?nalist="attr1"'
        self.app.config['TESTING'] = True
        with self.app.test_client() as client:
            rv = client.get(url)
            response = json.loads(rv.data)
            self.assertEqual(response["data"]["attributes"], {'attr2': 'OK'})
            RESTApiTestCase.compare_extra_response_data(self, "calculations",
                                                        url,
                                                        response, pk=node_pk)

    def test_calculation_attributes_alist_filter(self):
        """
        Get list of calculation attributes with filter alist
        """
        node_pk = self.get_dummy_data()["calculations"][1]["id"]
        url = self.get_url_prefix() + '/calculations/' + str(
            node_pk) + '/content/attributes?alist="attr1"'
        self.app.config['TESTING'] = True
        with self.app.test_client() as client:
            rv = client.get(url)
            response = json.loads(rv.data)
            self.assertEqual(response["data"]["attributes"], {'attr1': 'OK'})
            RESTApiTestCase.compare_extra_response_data(self, "calculations",
                                                        url,
                                                        response, pk=node_pk)
