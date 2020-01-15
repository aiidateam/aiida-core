# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-lines
"""Unittests for REST API."""

import tempfile

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common import json
from aiida.common.links import LinkType
from aiida.restapi.api import App, AiidaApi


class RESTApiTestCase(AiidaTestCase):
    """
    Setup of the tests for the AiiDA RESTful-api
    """
    _url_prefix = '/api/v4'
    _dummy_data = {}
    _PERPAGE_DEFAULT = 20
    _LIMIT_DEFAULT = 400

    @classmethod
    def setUpClass(cls, *args, **kwargs):  # pylint: disable=too-many-locals, too-many-statements
        """
        Basides the standard setup we need to add few more objects in the
        database to be able to explore different requests/filters/orderings etc.
        """
        # call parent setUpClass method
        super().setUpClass()

        # connect the app and the api
        # Init the api by connecting it the the app (N.B. respect the following
        # order, api.__init__)
        kwargs = dict(PREFIX=cls._url_prefix, PERPAGE_DEFAULT=cls._PERPAGE_DEFAULT, LIMIT_DEFAULT=cls._LIMIT_DEFAULT)

        cls.app = App(__name__)
        cls.app.config['TESTING'] = True
        AiidaApi(cls.app, **kwargs)

        # create test inputs
        cell = ((2., 0., 0.), (0., 2., 0.), (0., 0., 2.))
        structure = orm.StructureData(cell=cell)
        structure.append_atom(position=(0., 0., 0.), symbols=['Ba'])
        structure.store()
        structure.add_comment('This is test comment.')
        structure.add_comment('Add another comment.')

        cif = orm.CifData(ase=structure.get_ase())
        cif.store()

        parameter1 = orm.Dict(dict={'a': 1, 'b': 2})
        parameter1.store()

        parameter2 = orm.Dict(dict={'c': 3, 'd': 4})
        parameter2.store()

        kpoint = orm.KpointsData()
        kpoint.set_kpoints_mesh([4, 4, 4])
        kpoint.store()

        resources = {'num_machines': 1, 'num_mpiprocs_per_machine': 1}

        calcfunc = orm.CalcFunctionNode(computer=cls.computer)
        calcfunc.store()

        calc = orm.CalcJobNode(computer=cls.computer)
        calc.set_option('resources', resources)
        calc.set_attribute('attr1', 'OK')
        calc.set_attribute('attr2', 'OK')
        calc.set_extra('extra1', False)
        calc.set_extra('extra2', 'extra_info')

        calc.add_incoming(structure, link_type=LinkType.INPUT_CALC, link_label='link_structure')
        calc.add_incoming(parameter1, link_type=LinkType.INPUT_CALC, link_label='link_parameter')

        aiida_in = 'The input file\nof the CalcJob node'
        # Add the calcjob_inputs folder with the aiida.in file to the CalcJobNode repository
        with tempfile.NamedTemporaryFile(mode='w+') as handle:
            handle.write(aiida_in)
            handle.flush()
            handle.seek(0)
            calc.put_object_from_filelike(handle, key='calcjob_inputs/aiida.in', force=True)
        calc.store()

        # create log message for calcjob
        import logging
        from aiida.common.log import LOG_LEVEL_REPORT
        from aiida.common.timezone import now
        from aiida.orm import Log

        log_record = {
            'time': now(),
            'loggername': 'loggername',
            'levelname': logging.getLevelName(LOG_LEVEL_REPORT),
            'dbnode_id': calc.id,
            'message': 'This is a template record message',
            'metadata': {
                'content': 'test'
            },
        }
        Log(**log_record)

        aiida_out = 'The output file\nof the CalcJob node'
        retrieved_outputs = orm.FolderData()
        # Add the calcjob_outputs folder with the aiida.out file to the FolderData node
        with tempfile.NamedTemporaryFile(mode='w+') as handle:
            handle.write(aiida_out)
            handle.flush()
            handle.seek(0)
            retrieved_outputs.put_object_from_filelike(handle, key='calcjob_outputs/aiida.out', force=True)
        retrieved_outputs.store()
        retrieved_outputs.add_incoming(calc, link_type=LinkType.CREATE, link_label='retrieved')

        kpoint.add_incoming(calc, link_type=LinkType.CREATE, link_label='create')

        calc1 = orm.CalcJobNode(computer=cls.computer)
        calc1.set_option('resources', resources)
        calc1.store()

        dummy_computers = [{
            'name': 'test1',
            'hostname': 'test1.epfl.ch',
            'transport_type': 'ssh',
            'scheduler_type': 'pbspro',
        }, {
            'name': 'test2',
            'hostname': 'test2.epfl.ch',
            'transport_type': 'ssh',
            'scheduler_type': 'torque',
        }, {
            'name': 'test3',
            'hostname': 'test3.epfl.ch',
            'transport_type': 'local',
            'scheduler_type': 'slurm',
        }, {
            'name': 'test4',
            'hostname': 'test4.epfl.ch',
            'transport_type': 'ssh',
            'scheduler_type': 'slurm',
        }]

        for dummy_computer in dummy_computers:
            computer = orm.Computer(**dummy_computer)
            computer.store()

        # Prepare typical REST responses
        cls.process_dummy_data()

    def get_dummy_data(self):
        return self._dummy_data

    def get_url_prefix(self):
        return self._url_prefix

    @classmethod
    def process_dummy_data(cls):
        # pylint: disable=fixme
        """
        This functions prepare atomic chunks of typical responses from the
        RESTapi and puts them into class attributes

        """
        # TODO: Storing the different nodes as lists and accessing them
        # by their list index is very fragile and a pain to debug.
        # Please change this!
        computer_projections = ['id', 'uuid', 'name', 'hostname', 'transport_type', 'scheduler_type']
        computers = orm.QueryBuilder().append(orm.Computer, tag='comp', project=computer_projections).order_by({
            'comp': [{
                'id': {
                    'order': 'asc'
                }
            }]
        }).dict()

        # Cast UUID into a string (e.g. in sqlalchemy it comes as a UUID object)
        computers = [_['comp'] for _ in computers]
        for comp in computers:
            if comp['uuid'] is not None:
                comp['uuid'] = str(comp['uuid'])
        cls._dummy_data['computers'] = computers

        calculation_projections = ['id', 'uuid', 'user_id', 'node_type']
        calculations = orm.QueryBuilder().append(orm.CalculationNode, tag='calc',
                                                 project=calculation_projections).order_by({
                                                     'calc': [{
                                                         'id': {
                                                             'order': 'desc'
                                                         }
                                                     }]
                                                 }).dict()

        calculations = [_['calc'] for _ in calculations]
        for calc in calculations:
            if calc['uuid'] is not None:
                calc['uuid'] = str(calc['uuid'])
        cls._dummy_data['calculations'] = calculations

        data_projections = ['id', 'uuid', 'user_id', 'node_type']
        data_types = {
            'cifdata': orm.CifData,
            'parameterdata': orm.Dict,
            'structuredata': orm.StructureData,
            'data': orm.Data,
        }
        for label, dataclass in data_types.items():
            data = orm.QueryBuilder().append(dataclass, tag='data', project=data_projections).order_by({
                'data': [{
                    'id': {
                        'order': 'desc'
                    }
                }]
            }).dict()
            data = [_['data'] for _ in data]

            for datum in data:
                if datum['uuid'] is not None:
                    datum['uuid'] = str(datum['uuid'])

            cls._dummy_data[label] = data

    def split_path(self, url):
        # pylint: disable=no-self-use
        """
        Split the url with "?" to get url path and it's parameters
        :param url: Web url
        :return: url path and url parameters
        """
        parts = url.split('?')
        path = ''
        query_string = ''
        if parts:
            path = parts[0]
        if len(parts) > 1:
            query_string = parts[1]

        return path, query_string

    def compare_extra_response_data(self, node_type, url, response, uuid=None):
        """
        In url response, we pass some extra information/data along with the node
        results. e.g. url method, node_type, path, pk, query_string, url,
        url_root,
        etc.

        :param node_type: url requested fot the type of the node
        :param url: web url
        :param response: url response
        :param uuid: url requested for the node pk
        """
        path, query_string = self.split_path(url)

        self.assertEqual(response['method'], 'GET')
        self.assertEqual(response['resource_type'], node_type)
        self.assertEqual(response['path'], path)
        self.assertEqual(response['id'], uuid)
        self.assertEqual(response['query_string'], query_string)
        self.assertEqual(response['url'], 'http://localhost' + url)
        self.assertEqual(response['url_root'], 'http://localhost/')

    # node details and list with limit, offset, page, perpage
    def process_test(
        self,
        entity_type,
        url,
        full_list=False,
        empty_list=False,
        expected_list_ids=None,
        expected_range=None,
        expected_errormsg=None,
        uuid=None,
        result_node_type=None,
        result_name=None
    ):
        # pylint: disable=too-many-arguments
        """
        Check whether response matches expected values.

        :param entity_type: url requested fot the type of the node
        :param url: web url
        :param full_list: if url is requested to get full list
        :param empty_list: if the response list is empty
        :param expected_list_ids: list of expected ids from data
        :param expected_range: [start, stop] range of expected ids from data
        :param expected_errormsg: expected error message in response
        :param uuid: url requested for the node pk
        :param result_node_type: node type in response data
        :param result_name: result name in response e.g. incoming, outgoing
        """

        if expected_list_ids is None:
            expected_list_ids = []

        if expected_range is None:
            expected_range = []

        if result_node_type is None and result_name is None:
            result_node_type = entity_type
            result_name = entity_type

        url = self._url_prefix + url

        with self.app.test_client() as client:
            rv_response = client.get(url)
            response = json.loads(rv_response.data)

            if expected_errormsg:
                self.assertEqual(response['message'], expected_errormsg)
            else:
                if full_list:
                    expected_data = self._dummy_data[result_node_type]
                elif empty_list:
                    expected_data = []
                elif expected_list_ids:
                    expected_data = [self._dummy_data[result_node_type][i] for i in expected_list_ids]
                elif expected_range != []:
                    expected_data = self._dummy_data[result_node_type][expected_range[0]:expected_range[1]]
                else:
                    from aiida.common.exceptions import InputValidationError
                    raise InputValidationError('Pass the expected range of the dummydata')

                expected_node_uuids = [node['uuid'] for node in expected_data]
                result_node_uuids = [node['uuid'] for node in response['data'][result_name]]
                self.assertEqual(expected_node_uuids, result_node_uuids)

                self.compare_extra_response_data(entity_type, url, response, uuid)


class RESTApiTestSuite(RESTApiTestCase):
    # pylint: disable=too-many-public-methods
    """
    Define unittests for rest api
    """

    def test_computers_details(self):
        """
        Requests the details of single computer
        """
        node_uuid = self.get_dummy_data()['computers'][1]['uuid']
        RESTApiTestCase.process_test(
            self, 'computers', '/computers/' + str(node_uuid), expected_list_ids=[1], uuid=node_uuid
        )

    def test_computers_list(self):
        """
        Get the full list of computers from database
        """
        RESTApiTestCase.process_test(self, 'computers', '/computers?orderby=+id', full_list=True)

    def test_computers_list_limit_offset(self):
        """
        Get the list of computers from database using limit
        and offset parameter.
        It should return the no of rows specified in limit from
        database starting from the no. specified in offset
        """
        RESTApiTestCase.process_test(
            self, 'computers', '/computers?limit=2&offset=2&orderby=+id', expected_range=[2, 4]
        )

    def test_computers_list_limit_only(self):
        """
        Get the list of computers from database using limit
        parameter.
        It should return the no of rows specified in limit from
        database.
        """
        RESTApiTestCase.process_test(self, 'computers', '/computers?limit=2&orderby=+id', expected_range=[None, 2])

    def test_computers_list_offset_only(self):
        """
        Get the list of computers from database using offset
        parameter
        It should return all the rows from database starting from
        the no. specified in offset
        """
        RESTApiTestCase.process_test(self, 'computers', '/computers?offset=2&orderby=+id', expected_range=[2, None])

    def test_computers_list_limit_offset_perpage(self):
        """
        If we pass the limit, offset and perpage at same time, it
        would return the error message.
        """
        expected_error = 'perpage key is incompatible with limit and offset'
        RESTApiTestCase.process_test(
            self, 'computers', '/computers?offset=2&limit=1&perpage=2&orderby=+id', expected_errormsg=expected_error
        )

    def test_computers_list_page_limit_offset(self):
        """
        If we use the page, limit and offset at same time, it
        would return the error message.
        """
        expected_error = 'requesting a specific page is incompatible with ' \
                         'limit and offset'
        RESTApiTestCase.process_test(
            self, 'computers', '/computers/page/2?offset=2&limit=1&orderby=+id', expected_errormsg=expected_error
        )

    def test_complist_pagelimitoffset_perpage(self):
        """
        If we use the page, limit, offset and perpage at same time, it
        would return the error message.
        """
        expected_error = 'perpage key is incompatible with limit and offset'
        RESTApiTestCase.process_test(
            self,
            'computers',
            '/computers/page/2?offset=2&limit=1&perpage=2&orderby=+id',
            expected_errormsg=expected_error
        )

    def test_computers_list_page_default(self):
        """
        it returns the no. of rows defined as default perpage option
        from database.

        no.of pages = total no. of computers in database / perpage
        "/page" acts as "/page/1?perpage=default_value"

        """
        RESTApiTestCase.process_test(self, 'computers', '/computers/page?orderby=+id', full_list=True)

    def test_computers_list_page_perpage(self):
        """
        no.of pages = total no. of computers in database / perpage
        Using this formula it returns the no. of rows for requested page
        """
        RESTApiTestCase.process_test(
            self, 'computers', '/computers/page/1?perpage=2&orderby=+id', expected_range=[None, 2]
        )

    def test_computers_list_page_perpage_exceed(self):
        """
        no.of pages = total no. of computers in database / perpage

        If we request the page which exceeds the total no. of pages then
        it would return the error message.
        """
        expected_error = 'Non existent page requested. The page range is [1 : ' \
                         '3]'
        RESTApiTestCase.process_test(
            self, 'computers', '/computers/page/4?perpage=2&orderby=+id', expected_errormsg=expected_error
        )

    ############### list filters ########################
    def test_computers_filter_id1(self):
        """
        Add filter on the id of computer and get the filtered computer
        list (e.g. id=1)
        """
        node_pk = self.get_dummy_data()['computers'][1]['id']

        RESTApiTestCase.process_test(self, 'computers', '/computers?id=' + str(node_pk), expected_list_ids=[1])

    def test_computers_filter_id2(self):
        """
        Add filter on the id of computer and get the filtered computer
        list (e.g. id > 2)
        """
        node_pk = self.get_dummy_data()['computers'][1]['id']
        RESTApiTestCase.process_test(
            self, 'computers', '/computers?id>' + str(node_pk) + '&orderby=+id', expected_range=[2, None]
        )

    def test_computers_filter_pk(self):
        """
        Add filter on the id of computer and get the filtered computer
        list (e.g. id=1)
        """
        node_pk = self.get_dummy_data()['computers'][1]['id']
        RESTApiTestCase.process_test(self, 'computers', '/computers?pk=' + str(node_pk), expected_list_ids=[1])

    def test_computers_filter_name(self):
        """
        Add filter for the name of computer and get the filtered computer
        list
        """
        RESTApiTestCase.process_test(self, 'computers', '/computers?name="test1"', expected_list_ids=[1])

    def test_computers_filter_hostname(self):
        """
        Add filter for the hostname of computer and get the filtered computer
        list
        """
        RESTApiTestCase.process_test(self, 'computers', '/computers?hostname="test1.epfl.ch"', expected_list_ids=[1])

    def test_computers_filter_transport_type(self):
        """
        Add filter for the transport_type of computer and get the filtered
        computer
        list
        """
        RESTApiTestCase.process_test(
            self, 'computers', '/computers?transport_type="local"&name="test3"&orderby=+id', expected_list_ids=[3]
        )

    ############### list orderby ########################
    def test_computers_orderby_id_asc(self):
        """
        Returns the computers list ordered by "id" in ascending
        order
        """
        RESTApiTestCase.process_test(self, 'computers', '/computers?orderby=id', full_list=True)

    def test_computers_orderby_id_asc_sign(self):
        """
        Returns the computers list ordered by "+id" in ascending
        order
        """
        RESTApiTestCase.process_test(self, 'computers', '/computers?orderby=+id', full_list=True)

    def test_computers_orderby_id_desc(self):
        """
        Returns the computers list ordered by "id" in descending
        order
        """
        RESTApiTestCase.process_test(self, 'computers', '/computers?orderby=-id', expected_list_ids=[4, 3, 2, 1, 0])

    def test_computers_orderby_name_asc(self):
        """
        Returns the computers list ordered by "name" in ascending
        order
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        RESTApiTestCase.process_test(
            self, 'computers', '/computers?pk>' + str(node_pk) + '&orderby=name', expected_list_ids=[1, 2, 3, 4]
        )

    def test_computers_orderby_name_asc_sign(self):
        """
        Returns the computers list ordered by "+name" in ascending
        order
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        RESTApiTestCase.process_test(
            self, 'computers', '/computers?pk>' + str(node_pk) + '&orderby=+name', expected_list_ids=[1, 2, 3, 4]
        )

    def test_computers_orderby_name_desc(self):
        """
        Returns the computers list ordered by "name" in descending
        order
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        RESTApiTestCase.process_test(
            self, 'computers', '/computers?pk>' + str(node_pk) + '&orderby=-name', expected_list_ids=[4, 3, 2, 1]
        )

    def test_computers_orderby_scheduler_type_asc(self):
        """
        Returns the computers list ordered by "scheduler_type" in ascending
        order
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        RESTApiTestCase.process_test(
            self,
            'computers',
            '/computers?transport_type="ssh"&pk>' + str(node_pk) + '&orderby=scheduler_type',
            expected_list_ids=[1, 4, 2]
        )

    def test_comp_orderby_scheduler_ascsign(self):
        """
        Returns the computers list ordered by "+scheduler_type" in ascending
        order
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        RESTApiTestCase.process_test(
            self,
            'computers',
            '/computers?transport_type="ssh"&pk>' + str(node_pk) + '&orderby=+scheduler_type',
            expected_list_ids=[1, 4, 2]
        )

    def test_computers_orderby_schedulertype_desc(self):
        """
        Returns the computers list ordered by "scheduler_type" in descending
        order
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        RESTApiTestCase.process_test(
            self,
            'computers',
            '/computers?pk>' + str(node_pk) + '&transport_type="ssh"&orderby=-scheduler_type',
            expected_list_ids=[2, 4, 1]
        )

    ############### list orderby combinations #######################
    def test_computers_orderby_mixed1(self):
        """
        Returns the computers list first order by "transport_type" in
        ascending order and if it is having same transport_type, order it
        by "id"
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        RESTApiTestCase.process_test(
            self,
            'computers',
            '/computers?pk>' + str(node_pk) + '&orderby=transport_type,id',
            expected_list_ids=[3, 1, 2, 4]
        )

    def test_computers_orderby_mixed2(self):
        """
        Returns the computers list first order by "scheduler_type" in
        descending order and if it is having same scheduler_type, order it
        by "name"
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        RESTApiTestCase.process_test(
            self,
            'computers',
            '/computers?pk>' + str(node_pk) + '&orderby=-scheduler_type,name',
            expected_list_ids=[2, 3, 4, 1]
        )

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

    ############### list filter combinations #######################
    def test_computers_filter_mixed1(self):
        """
        Add filter for the hostname and id of computer and get the
        filtered computer list
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        RESTApiTestCase.process_test(
            self, 'computers', '/computers?id>' + str(node_pk) + '&hostname="test1.epfl.ch"', expected_list_ids=[1]
        )

    def test_computers_filter_mixed2(self):
        """
        Add filter for the id, hostname and transport_type of the computer
        and get the filtered computer list
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        RESTApiTestCase.process_test(
            self,
            'computers',
            '/computers?id>' + str(node_pk) + '&hostname="test3.epfl.ch"&transport_type="ssh"',
            empty_list=True
        )

    ############### list all parameter combinations #######################
    def test_computers_mixed1(self):
        """
        url parameters: id, limit and offset
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        RESTApiTestCase.process_test(
            self, 'computers', '/computers?id>' + str(node_pk) + '&limit=2&offset=3&orderby=+id', expected_list_ids=[4]
        )

    def test_computers_mixed2(self):
        """
        url parameters: id, page, perpage
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        RESTApiTestCase.process_test(
            self,
            'computers',
            '/computers/page/2?id>' + str(node_pk) + '&perpage=2&orderby=+id',
            expected_list_ids=[3, 4]
        )

    def test_computers_mixed3(self):
        """
        url parameters: id, transport_type, orderby
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        RESTApiTestCase.process_test(
            self,
            'computers',
            '/computers?id>=' + str(node_pk) + '&transport_type="ssh"&orderby=-id&limit=2',
            expected_list_ids=[4, 2]
        )

    ########## pass unknown url parameter ###########
    def test_computers_unknown_param(self):
        """
        url parameters: id, limit and offset

        from aiida.common.exceptions import InputValidationError
        RESTApiTestCase.node_exception(self, "/computers?aa=bb&id=2", InputValidationError)
        """

    ############### calculation retrieved_inputs and retrieved_outputs  #############
    def test_calculation_retrieved_inputs(self):
        """
        Get the list of given calculation retrieved_inputs
        """
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        url = self.get_url_prefix() + '/calcjobs/' + str(node_uuid) + '/input_files'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            self.assertEqual(response['data'], [{'name': 'calcjob_inputs', 'type': 'DIRECTORY'}])

    def test_calculation_retrieved_outputs(self):
        """
        Get the list of given calculation retrieved_outputs
        """
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        url = self.get_url_prefix() + '/calcjobs/' + str(node_uuid) + '/output_files'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            self.assertEqual(response['data'], [{'name': 'calcjob_outputs', 'type': 'DIRECTORY'}])

    ############### calculation incoming  #############
    def test_calculation_inputs(self):
        """
        Get the list of give calculation incoming
        """
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        self.process_test(
            'nodes',
            '/nodes/' + str(node_uuid) + '/links/incoming?orderby=id',
            expected_list_ids=[5, 3],
            uuid=node_uuid,
            result_node_type='data',
            result_name='incoming'
        )

    def test_calculation_input_filters(self):
        """
        Get filtered incoming list for given calculations
        """
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        self.process_test(
            'nodes',
            '/nodes/' + str(node_uuid) + '/links/incoming?node_type="data.dict.Dict."',
            expected_list_ids=[3],
            uuid=node_uuid,
            result_node_type='data',
            result_name='incoming'
        )

    def test_calculation_iotree(self):
        """
        Get filtered incoming list for given calculations
        """
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        url = self.get_url_prefix() + '/nodes/' + str(node_uuid) + '/links/tree?in_limit=1&out_limit=1'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            self.assertEqual(len(response['data']['nodes']), 1)
            self.assertEqual(len(response['data']['nodes'][0]['incoming']), 1)
            self.assertEqual(len(response['data']['nodes'][0]['outgoing']), 1)
            self.assertEqual(len(response['data']['metadata']), 1)
            expected_attr = [
                'ctime', 'mtime', 'id', 'node_label', 'node_type', 'uuid', 'description', 'incoming', 'outgoing'
            ]
            received_attr = response['data']['nodes'][0].keys()
            for attr in expected_attr:
                self.assertIn(attr, received_attr)
            RESTApiTestCase.compare_extra_response_data(self, 'nodes', url, response, uuid=node_uuid)

    ############### calculation attributes #############
    def test_calculation_attributes(self):
        """
        Get list of calculation attributes
        """
        attributes = {
            'attr1': 'OK',
            'attr2': 'OK',
            'resources': {
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            },
        }
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        url = self.get_url_prefix() + '/nodes/' + str(node_uuid) + '/contents/attributes'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
            response = json.loads(rv_obj.data)
            self.assertNotIn('message', response)
            self.assertEqual(response['data']['attributes'], attributes)
            RESTApiTestCase.compare_extra_response_data(self, 'nodes', url, response, uuid=node_uuid)

    def test_contents_attributes_filter(self):
        """
        Get list of calculation attributes with filter attributes_filter
        """
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        url = self.get_url_prefix() + '/nodes/' + str(node_uuid) + '/contents/attributes?attributes_filter="attr1"'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
            response = json.loads(rv_obj.data)
            self.assertNotIn('message', response)
            self.assertEqual(response['data']['attributes'], {'attr1': 'OK'})
            RESTApiTestCase.compare_extra_response_data(self, 'nodes', url, response, uuid=node_uuid)

    ############### calculation node attributes filter  #############
    def test_calculation_attributes_filter(self):
        """
        Get the list of given calculation attributes filtered
        """
        attributes = {
            'attr1': 'OK',
            'attr2': 'OK',
            'resources': {
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            },
        }
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        url = self.get_url_prefix() + '/nodes/' + str(node_uuid) + '?attributes=true'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            self.assertEqual(response['data']['nodes'][0]['attributes'], attributes)

    ############### calculation node extras_filter  #############
    def test_calculation_extras_filter(self):
        """
        Get the list of given calculation extras filtered
        """
        extras = {'extra1': False, 'extra2': 'extra_info'}
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        url = self.get_url_prefix() + '/nodes/' + str(node_uuid) + '?extras=true&extras_filter=extra1,extra2'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            self.assertEqual(response['data']['nodes'][0]['extras']['extra1'], extras['extra1'])
            self.assertEqual(response['data']['nodes'][0]['extras']['extra2'], extras['extra2'])

    ############### structure node attributes filter #############
    def test_structure_attributes_filter(self):
        """
        Get the list of given calculation attributes filtered
        """
        cell = [[2., 0., 0.], [0., 2., 0.], [0., 0., 2.]]
        node_uuid = self.get_dummy_data()['structuredata'][0]['uuid']
        url = self.get_url_prefix() + '/nodes/' + str(node_uuid) + '?attributes=true&attributes_filter=cell'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
            response = json.loads(rv_obj.data)
            self.assertEqual(response['data']['nodes'][0]['attributes']['cell'], cell)

    ############### node attributes_filter with pagination #############
    def test_node_attributes_filter_pagination(self):
        """
        Check that node attributes specified in attributes_filter are
        returned as a dictionary when pagination is set
        """
        expected_attributes = ['resources', 'cell']
        url = self.get_url_prefix() + '/nodes/page/1?perpage=10&attributes=true&attributes_filter=resources,cell'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            self.assertNotEqual(len(response['data']['nodes']), 0)
            for node in response['data']['nodes']:
                self.assertIn('attributes', node)
                self.assertNotIn('attributes.resources', node)
                self.assertNotIn('attributes.cell', node)
                self.assertEqual(len(node['attributes']), len(expected_attributes))
                for attr in expected_attributes:
                    self.assertIn(attr, node['attributes'])

    ############### node get one attributes_filter with pagination #############
    def test_node_single_attributes_filter(self):
        """
        Check that when only one node attribute is specified in attributes_filter
        only this attribute is returned as a dictionary when pagination is set
        """
        expected_attribute = ['resources']
        url = self.get_url_prefix() + '/nodes/page/1?perpage=10&attributes=true&attributes_filter=resources'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            self.assertNotEqual(len(response['data']['nodes']), 0)
            for node in response['data']['nodes']:
                self.assertEqual(list(node['attributes'].keys()), expected_attribute)

    ############### node extras_filter with pagination #############
    def test_node_extras_filter_pagination(self):
        """
        Check that node extras specified in extras_filter are
        returned as a dictionary when pagination is set
        """
        expected_extras = ['extra1', 'extra2']
        url = self.get_url_prefix() + '/nodes/page/1?perpage=10&extras=true&extras_filter=extra1,extra2'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            self.assertNotEqual(len(response['data']['nodes']), 0)
            for node in response['data']['nodes']:
                self.assertIn('extras', node)
                self.assertNotIn('extras.extra1', node)
                self.assertNotIn('extras.extra2', node)
                self.assertEqual(len(node['extras']), len(expected_extras))
                for extra in expected_extras:
                    self.assertIn(extra, node['extras'])

    ############### node get one extras_filter with pagination #############
    def test_node_single_extras_filter(self):
        """
        Check that when only one node extra is specified in extras_filter
        only this extra is returned as a dictionary when pagination is set
        """
        expected_extra = ['extra2']
        url = self.get_url_prefix() + '/nodes/page/1?perpage=10&extras=true&extras_filter=extra2'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            self.assertNotEqual(len(response['data']['nodes']), 0)
            for node in response['data']['nodes']:
                self.assertEqual(list(node['extras'].keys()), expected_extra)

    ############### node full_type filter #############
    def test_nodes_full_type_filter(self):
        """
        Get the list of nodes filtered by full_type
        """
        expected_node_uuids = []
        for calc in self.get_dummy_data()['calculations']:
            if calc['node_type'] == 'process.calculation.calcjob.CalcJobNode.':
                expected_node_uuids.append(calc['uuid'])

        url = self.get_url_prefix() + '/nodes/' + '?full_type="process.calculation.calcjob.CalcJobNode.|"'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
            response = json.loads(rv_obj.data)
            for node in response['data']['nodes']:
                self.assertIn(node['uuid'], expected_node_uuids)

    ############### Structure visualization and download #############
    def test_structure_derived_properties(self):
        """
        Get the list of give calculation incoming
        """
        node_uuid = self.get_dummy_data()['structuredata'][0]['uuid']
        url = self.get_url_prefix() + '/nodes/' + str(node_uuid) + '/contents/derived_properties'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
            response = json.loads(rv_obj.data)
            self.assertNotIn('message', response)
            self.assertEqual(
                response['data']['derived_properties']['dimensionality'], {
                    'dim': 3,
                    'value': 8.0,
                    'label': 'volume'
                }
            )
            self.assertEqual(response['data']['derived_properties']['formula'], 'Ba')
            RESTApiTestCase.compare_extra_response_data(self, 'nodes', url, response, uuid=node_uuid)

    def test_structure_download(self):
        """
        Test download of structure file
        """
        from aiida.orm import load_node

        node_uuid = self.get_dummy_data()['structuredata'][0]['uuid']
        url = self.get_url_prefix() + '/nodes/' + node_uuid + '/download?download_format=xsf'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
        structure_data = load_node(node_uuid)._exportcontent('xsf')[0]  # pylint: disable=protected-access
        self.assertEqual(rv_obj.data, structure_data)

    def test_cif(self):
        """
        Test download of cif file
        """
        from aiida.orm import load_node

        node_uuid = self.get_dummy_data()['cifdata'][0]['uuid']
        url = self.get_url_prefix() + '/nodes/' + node_uuid + '/download?download_format=cif'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
        cif = load_node(node_uuid)._prepare_cif()[0]  # pylint: disable=protected-access
        self.assertEqual(rv_obj.data, cif)

    ############### projectable_properties #############
    def test_projectable_properties(self):
        """
        test projectable_properties endpoint
        """
        for nodetype in ['nodes', 'processes', 'computers', 'users', 'groups']:
            url = self.get_url_prefix() + '/' + nodetype + '/projectable_properties'
            with self.app.test_client() as client:
                rv_obj = client.get(url)
                response = json.loads(rv_obj.data)
                self.assertNotIn('message', response)

                expected_keys = ['display_name', 'help_text', 'is_display', 'is_foreign_key', 'type']

                # check fields
                for _, pinfo in response['data']['fields'].items():
                    available_keys = pinfo.keys()
                    for prop in expected_keys:
                        self.assertIn(prop, available_keys)

                # check order
                available_properties = response['data']['fields'].keys()
                for prop in response['data']['ordering']:
                    self.assertIn(prop, available_properties)

    def test_node_namespace(self):
        """
        Test the rest api call to get list of available node namespace
        """
        url = self.get_url_prefix() + '/nodes/full_types'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
            response = json.loads(rv_obj.data)
            expected_data_keys = ['path', 'namespace', 'subspaces', 'label', 'full_type']
            response_keys = response['data'].keys()
            for dkay in expected_data_keys:
                self.assertIn(dkay, response_keys)
            RESTApiTestCase.compare_extra_response_data(self, 'nodes', url, response)

    def test_comments(self):
        """
        Get the node comments
        """
        node_uuid = self.get_dummy_data()['structuredata'][0]['uuid']
        url = self.get_url_prefix() + '/nodes/' + str(node_uuid) + '/contents/comments'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
            response = json.loads(rv_obj.data)['data']['comments']
            all_comments = []
            for comment in response:
                all_comments.append(comment['message'])
            self.assertEqual(sorted(all_comments), sorted(['This is test comment.', 'Add another comment.']))

    def test_repo(self):
        """
        Test to get repo list or repo file contents for given node
        """
        from aiida.orm import load_node

        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        url = self.get_url_prefix() + '/nodes/' + str(node_uuid) + '/repo/list?filename="calcjob_inputs"'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            self.assertEqual(response['data']['repo_list'], [{'type': 'FILE', 'name': 'aiida.in'}])

        url = self.get_url_prefix() + '/nodes/' + str(node_uuid) + '/repo/contents?filename="calcjob_inputs/aiida.in"'
        with self.app.test_client() as client:
            response_obj = client.get(url)
            input_file = load_node(node_uuid).get_object_content('calcjob_inputs/aiida.in', mode='rb')
            self.assertEqual(response_obj.data, input_file)

    def test_process_report(self):
        """
        Test process report
        """
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        url = self.get_url_prefix() + '/processes/' + str(node_uuid) + '/report'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)

            expected_keys = response['data'].keys()
            for key in ['logs']:
                self.assertIn(key, expected_keys)

            expected_log_keys = response['data']['logs'][0].keys()
            for key in ['time', 'loggername', 'levelname', 'dbnode_id', 'message']:
                self.assertIn(key, expected_log_keys)

    def test_download_formats(self):
        """
        test for download format endpoint
        """
        url = self.get_url_prefix() + '/nodes/download_formats'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)

            for key in ['data.structure.StructureData.|', 'data.cif.CifData.|']:
                self.assertIn(key, response['data'].keys())
            for key in ['cif', 'xsf', 'xyz']:
                self.assertIn(key, response['data']['data.structure.StructureData.|'])
            self.assertIn('cif', response['data']['data.cif.CifData.|'])
