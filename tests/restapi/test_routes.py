###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unittests for REST API."""

import io
import json
from datetime import date

import numpy as np
import pytest
from flask_cors.core import ACL_ORIGIN

from aiida import orm
from aiida.common.links import LinkType
from aiida.manage import get_manager
from aiida.orm.nodes.data.array.array import clean_array
from aiida.restapi.run_api import configure_api


class TestRestApi:
    """Setup of the tests for the AiiDA RESTful-api"""

    _url_prefix = '/api/v4'
    _dummy_data: dict = {}
    _PERPAGE_DEFAULT = 20
    _LIMIT_DEFAULT = 400

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_profile_clean, aiida_localhost):
        """Initialize the profile."""
        api = configure_api(catch_internal_server=True)
        self.app = api.app
        self.app.config['TESTING'] = True

        self.user = orm.User.collection.get_default()

        # create test inputs
        cell = ((2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0))
        structure = orm.StructureData(cell=cell)
        structure.append_atom(position=(0.0, 0.0, 0.0), symbols=['Ba'])
        structure.store()
        structure.base.comments.add('This is test comment.')
        structure.base.comments.add('Add another comment.')

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

        self.computer = aiida_localhost
        calcfunc = orm.CalcFunctionNode(computer=self.computer)
        calcfunc.store()

        calc = orm.CalcJobNode(computer=self.computer)
        calc.set_option('resources', resources)

        calc.base.extras.set('extra1', False)
        calc.base.extras.set('extra2', 'extra_info')
        calc.base.attributes.set('attr1', 'OK')
        calc.base.attributes.set('attr2', 'OK')

        calc.base.links.add_incoming(structure, link_type=LinkType.INPUT_CALC, link_label='link_structure')
        calc.base.links.add_incoming(parameter1, link_type=LinkType.INPUT_CALC, link_label='link_parameter')
        calc.base.repository.put_object_from_filelike(
            io.BytesIO(b'The input file\nof the CalcJob node'), 'calcjob_inputs/aiida.in'
        )
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
            'dbnode_id': calc.pk,
            'message': 'This is a template record message',
            'metadata': {'content': 'test'},
        }
        Log(**log_record)

        retrieved_outputs = orm.FolderData()
        stream = io.BytesIO(b'The output file\nof the CalcJob node')
        retrieved_outputs.base.repository.put_object_from_filelike(stream, 'calcjob_outputs/aiida.out')
        retrieved_outputs.store()
        retrieved_outputs.base.links.add_incoming(calc, link_type=LinkType.CREATE, link_label='retrieved')

        kpoint.base.links.add_incoming(calc, link_type=LinkType.CREATE, link_label='create')

        calc1 = orm.CalcJobNode(computer=self.computer)
        calc1.set_option('resources', resources)
        calc1.store()

        dummy_computers = [
            {
                'label': 'test1',
                'hostname': 'test1.epfl.ch',
                'transport_type': 'core.ssh',
                'scheduler_type': 'core.pbspro',
            },
            {
                'label': 'test2',
                'hostname': 'test2.epfl.ch',
                'transport_type': 'core.ssh',
                'scheduler_type': 'core.torque',
            },
            {
                'label': 'test3',
                'hostname': 'test3.epfl.ch',
                'transport_type': 'core.local',
                'scheduler_type': 'core.slurm',
            },
            {
                'label': 'test4',
                'hostname': 'test4.epfl.ch',
                'transport_type': 'core.ssh',
                'scheduler_type': 'core.slurm',
            },
        ]

        for dummy_computer in dummy_computers:
            computer = orm.Computer(**dummy_computer)
            computer.store()

        # Setting array data for the tests
        array = orm.ArrayData()
        array.set_array('array_clean', np.asarray([[4, 5, 7], [9, 5, 1], [3, 4, 4]]))
        array.set_array('array_dirty', np.asarray([[4, 5, np.nan], [9, np.inf, -1 * np.inf], [np.nan, 4, 4]]))
        array.store()

        # Prepare typical REST responses
        self.process_dummy_data()

        yield

        # because the `close_thread_connection` decorator, currently, directly closes the SQLA session,
        # the default user will be detached from the session, and the `_clean` method will fail.
        # So, we need to reattach the default user to the session.
        get_manager().get_profile_storage().get_session().add(self.user.backend_entity.bare_model)

    def get_dummy_data(self):
        return self._dummy_data

    def get_url_prefix(self):
        return self._url_prefix

    def process_dummy_data(self):
        """This functions prepare atomic chunks of typical responses from the
        RESTapi and puts them into class attributes

        """
        # TODO: Storing the different nodes as lists and accessing them
        # by their list index is very fragile and a pain to debug.
        # Please change this!
        computer_projections = ['id', 'uuid', 'label', 'hostname', 'transport_type', 'scheduler_type']
        computers = (
            orm.QueryBuilder()
            .append(orm.Computer, tag='comp', project=computer_projections)
            .order_by({'comp': [{'id': {'order': 'asc'}}]})
            .dict()
        )

        # Cast UUID into a string (e.g. in sqlalchemy it comes as a UUID object)
        computers = [_['comp'] for _ in computers]
        for comp in computers:
            if comp['uuid'] is not None:
                comp['uuid'] = str(comp['uuid'])
        self._dummy_data['computers'] = computers

        calculation_projections = ['id', 'uuid', 'user_id', 'node_type']
        calculations = (
            orm.QueryBuilder()
            .append(orm.CalculationNode, tag='calc', project=calculation_projections)
            .order_by({'calc': [{'id': {'order': 'desc'}}]})
            .dict()
        )

        calculations = [_['calc'] for _ in calculations]
        for calc in calculations:
            if calc['uuid'] is not None:
                calc['uuid'] = str(calc['uuid'])
        self._dummy_data['calculations'] = calculations

        data_projections = ['id', 'uuid', 'user_id', 'node_type']
        data_types = {
            'cifdata': orm.CifData,
            'parameterdata': orm.Dict,
            'structuredata': orm.StructureData,
            'data': orm.Data,
            'arraydata': orm.ArrayData,
        }
        for label, dataclass in data_types.items():
            data = (
                orm.QueryBuilder()
                .append(dataclass, tag='data', project=data_projections)
                .order_by({'data': [{'id': {'order': 'desc'}}]})
                .dict()
            )
            data = [_['data'] for _ in data]

            for datum in data:
                if datum['uuid'] is not None:
                    datum['uuid'] = str(datum['uuid'])

            self._dummy_data[label] = data

    def split_path(self, url):
        """Split the url with "?" to get url path and it's parameters
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
        """In url response, we pass some extra information/data along with the node
        results. e.g. url method, node_type, path, pk, query_string, url,
        url_root,
        etc.

        :param node_type: url requested fot the type of the node
        :param url: web url
        :param response: url response
        :param uuid: url requested for the node pk
        """
        path, query_string = self.split_path(url)

        assert response['method'] == 'GET'
        assert response['resource_type'] == node_type
        assert response['path'] == path
        assert response['id'] == uuid
        assert response['query_string'] == query_string
        assert response['url'] == f'http://localhost{url}'
        assert response['url_root'] == 'http://localhost/'

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
        result_name=None,
    ):
        """Check whether response matches expected values.

        :param entity_type: url requested for the type of the node
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
                assert response['message'] == expected_errormsg
            else:
                if full_list:
                    expected_data = self._dummy_data[result_node_type]
                elif empty_list:
                    expected_data = []
                elif expected_list_ids:
                    expected_data = [self._dummy_data[result_node_type][i] for i in expected_list_ids]
                elif expected_range != []:
                    expected_data = self._dummy_data[result_node_type][expected_range[0] : expected_range[1]]
                else:
                    from aiida.common.exceptions import InputValidationError

                    raise InputValidationError('Pass the expected range of the dummydata')
                expected_node_uuids = [node['uuid'] for node in expected_data]
                result_node_uuids = [node['uuid'] for node in response['data'][result_name]]
                assert expected_node_uuids == result_node_uuids

                self.compare_extra_response_data(entity_type, url, response, uuid)

    ############### generic endpoints ########################

    def test_server(self):
        """Test that /server endpoint returns AiiDA version"""
        url = f'{self.get_url_prefix()}/server'
        from aiida import __version__

        with self.app.test_client() as client:
            response = client.get(url)
            data = json.loads(response.data)['data']

            assert __version__ == data['AiiDA_version']
            assert self.get_url_prefix() == data['API_prefix']

    def test_base_url(self):
        """Test that / returns list of endpoints"""
        with self.app.test_client() as client:
            data_base = json.loads(client.get(self.get_url_prefix() + '/').data)['data']
            data_server = json.loads(client.get(self.get_url_prefix() + '/server/endpoints').data)['data']

            assert len(data_base['available_endpoints']) > 0
            assert data_base == data_server

    def test_cors_headers(self):
        """Test that REST API sets cross-origin resource sharing headers"""
        url = f'{self.get_url_prefix()}/server'

        with self.app.test_client() as client:
            response = client.get(url)
            headers = response.headers
            assert headers.get(ACL_ORIGIN) == '*'

    ############### computers endpoint ########################

    def test_computers_details(self):
        """Requests the details of single computer"""
        node_uuid = self.get_dummy_data()['computers'][1]['uuid']
        self.process_test('computers', f'/computers/{node_uuid!s}', expected_list_ids=[1], uuid=node_uuid)

    def test_computers_list(self):
        """Get the full list of computers from database"""
        self.process_test('computers', '/computers?orderby=+id', full_list=True)

    def test_computers_list_limit_offset(self):
        """Get the list of computers from database using limit
        and offset parameter.
        It should return the no of rows specified in limit from
        database starting from the no. specified in offset
        """
        self.process_test('computers', '/computers?limit=2&offset=2&orderby=+id', expected_range=[2, 4])

    def test_computers_list_limit_only(self):
        """Get the list of computers from database using limit
        parameter.
        It should return the no of rows specified in limit from
        database.
        """
        self.process_test('computers', '/computers?limit=2&orderby=+id', expected_range=[None, 2])

    def test_computers_list_offset_only(self):
        """Get the list of computers from database using offset
        parameter
        It should return all the rows from database starting from
        the no. specified in offset
        """
        self.process_test('computers', '/computers?offset=2&orderby=+id', expected_range=[2, None])

    def test_computers_list_limit_offset_perpage(self):
        """If we pass the limit, offset and perpage at same time, it
        would return the error message.
        """
        expected_error = 'perpage key is incompatible with limit and offset'
        self.process_test(
            'computers', '/computers?offset=2&limit=1&perpage=2&orderby=+id', expected_errormsg=expected_error
        )

    def test_computers_list_page_limit_offset(self):
        """If we use the page, limit and offset at same time, it
        would return the error message.
        """
        expected_error = 'requesting a specific page is incompatible with ' 'limit and offset'
        self.process_test(
            'computers', '/computers/page/2?offset=2&limit=1&orderby=+id', expected_errormsg=expected_error
        )

    def test_complist_pagelimitoffset_perpage(self):
        """If we use the page, limit, offset and perpage at same time, it
        would return the error message.
        """
        expected_error = 'perpage key is incompatible with limit and offset'
        self.process_test(
            'computers', '/computers/page/2?offset=2&limit=1&perpage=2&orderby=+id', expected_errormsg=expected_error
        )

    def test_computers_list_page_default(self):
        """It returns the no. of rows defined as default perpage option
        from database.

        no.of pages = total no. of computers in database / perpage
        "/page" acts as "/page/1?perpage=default_value"

        """
        self.process_test('computers', '/computers/page?orderby=+id', full_list=True)

    def test_computers_list_page_perpage(self):
        """no.of pages = total no. of computers in database / perpage
        Using this formula it returns the no. of rows for requested page
        """
        self.process_test('computers', '/computers/page/1?perpage=2&orderby=+id', expected_range=[None, 2])

    def test_computers_list_page_perpage_exceed(self):
        """no.of pages = total no. of computers in database / perpage

        If we request the page which exceeds the total no. of pages then
        it would return the error message.
        """
        expected_error = 'Non existent page requested. The page range is [1 : ' '3]'
        self.process_test('computers', '/computers/page/4?perpage=2&orderby=+id', expected_errormsg=expected_error)

    ############### list filters ########################
    def test_computers_filter_id1(self):
        """Add filter on the id of computer and get the filtered computer
        list (e.g. id=1)
        """
        node_pk = self.get_dummy_data()['computers'][1]['id']

        self.process_test('computers', f'/computers?id={node_pk!s}', expected_list_ids=[1])

    def test_computers_filter_id2(self):
        """Add filter on the id of computer and get the filtered computer
        list (e.g. id > 2)
        """
        node_pk = self.get_dummy_data()['computers'][1]['id']
        self.process_test('computers', f'/computers?id>{node_pk!s}&orderby=+id', expected_range=[2, None])

    def test_computers_filter_pk(self):
        """Add filter on the id of computer and get the filtered computer
        list (e.g. id=1)
        """
        node_pk = self.get_dummy_data()['computers'][1]['id']
        self.process_test('computers', f'/computers?pk={node_pk!s}', expected_list_ids=[1])

    def test_computers_filter_name(self):
        """Add filter for the label of computer and get the filtered computer
        list
        """
        self.process_test('computers', '/computers?label="test1"', expected_list_ids=[1])

    def test_computers_filter_hostname(self):
        """Add filter for the hostname of computer and get the filtered computer
        list
        """
        self.process_test('computers', '/computers?hostname="test1.epfl.ch"', expected_list_ids=[1])

    def test_computers_filter_transport_type(self):
        """Add filter for the transport_type of computer and get the filtered
        computer
        list
        """
        self.process_test(
            'computers', '/computers?transport_type="core.local"&label="test3"&orderby=+id', expected_list_ids=[3]
        )

    ############### list orderby ########################
    def test_computers_orderby_id_asc(self):
        """Returns the computers list ordered by "id" in ascending
        order
        """
        self.process_test('computers', '/computers?orderby=id', full_list=True)

    def test_computers_orderby_id_asc_sign(self):
        """Returns the computers list ordered by "+id" in ascending
        order
        """
        self.process_test('computers', '/computers?orderby=+id', full_list=True)

    def test_computers_orderby_id_desc(self):
        """Returns the computers list ordered by "id" in descending
        order
        """
        self.process_test('computers', '/computers?orderby=-id', expected_list_ids=[4, 3, 2, 1, 0])

    def test_computers_orderby_label_asc(self):
        """Returns the computers list ordered by "label" in ascending
        order
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        self.process_test('computers', f'/computers?pk>{node_pk!s}&orderby=label', expected_list_ids=[1, 2, 3, 4])

    def test_computers_orderby_label_asc_sign(self):
        """Returns the computers list ordered by "+label" in ascending
        order
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        self.process_test('computers', f'/computers?pk>{node_pk!s}&orderby=+label', expected_list_ids=[1, 2, 3, 4])

    def test_computers_orderby_label_desc(self):
        """Returns the computers list ordered by "label" in descending
        order
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        self.process_test('computers', f'/computers?pk>{node_pk!s}&orderby=-label', expected_list_ids=[4, 3, 2, 1])

    def test_computers_orderby_scheduler_type_asc(self):
        """Returns the computers list ordered by "scheduler_type" in ascending
        order
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        self.process_test(
            'computers',
            f'/computers?transport_type="core.ssh"&pk>{node_pk!s}&orderby=scheduler_type',
            expected_list_ids=[1, 4, 2],
        )

    def test_comp_orderby_scheduler_ascsign(self):
        """Returns the computers list ordered by "+scheduler_type" in ascending
        order
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        self.process_test(
            'computers',
            f'/computers?transport_type="core.ssh"&pk>{node_pk!s}&orderby=+scheduler_type',
            expected_list_ids=[1, 4, 2],
        )

    def test_computers_orderby_schedulertype_desc(self):
        """Returns the computers list ordered by "scheduler_type" in descending
        order
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        self.process_test(
            'computers',
            f'/computers?pk>{node_pk!s}&transport_type="core.ssh"&orderby=-scheduler_type',
            expected_list_ids=[2, 4, 1],
        )

    ############### list orderby combinations #######################
    def test_computers_orderby_mixed1(self):
        """Returns the computers list first order by "transport_type" in
        ascending order and if it is having same transport_type, order it
        by "id"
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        self.process_test(
            'computers', f'/computers?pk>{node_pk!s}&orderby=transport_type,id', expected_list_ids=[3, 1, 2, 4]
        )

    def test_computers_orderby_mixed2(self):
        """Returns the computers list first order by "scheduler_type" in
        descending order and if it is having same scheduler_type, order it
        by "name"
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        self.process_test(
            'computers', f'/computers?pk>{node_pk!s}&orderby=-scheduler_type,label', expected_list_ids=[2, 3, 4, 1]
        )

    def test_computers_orderby_mixed3(self):
        """Returns the computers list first order by "scheduler_type" in
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


        self.process_test("computers",
                                  "/computers?orderby=+scheduler_type,
                                  -hostname",
                                  expected_list_ids=[1,0,4,3,2])
        """

    ############### list filter combinations #######################
    def test_computers_filter_mixed1(self):
        """Add filter for the hostname and id of computer and get the
        filtered computer list
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        self.process_test('computers', f'/computers?id>{node_pk!s}&hostname="test1.epfl.ch"', expected_list_ids=[1])

    def test_computers_filter_mixed2(self):
        """Add filter for the id, hostname and transport_type of the computer
        and get the filtered computer list
        """
        node_pk = self.get_dummy_data()['computers'][0]['id']
        self.process_test(
            'computers',
            f'/computers?id>{node_pk!s}&hostname="test3.epfl.ch"&transport_type="core.ssh"',
            empty_list=True,
        )

    ############### list all parameter combinations #######################
    def test_computers_mixed1(self):
        """Url parameters: id, limit and offset"""
        node_pk = self.get_dummy_data()['computers'][0]['id']
        self.process_test('computers', f'/computers?id>{node_pk!s}&limit=2&offset=3&orderby=+id', expected_list_ids=[4])

    def test_computers_mixed2(self):
        """Url parameters: id, page, perpage"""
        node_pk = self.get_dummy_data()['computers'][0]['id']
        self.process_test(
            'computers', f'/computers/page/2?id>{node_pk!s}&perpage=2&orderby=+id', expected_list_ids=[3, 4]
        )

    def test_computers_mixed3(self):
        """Url parameters: id, transport_type, orderby"""
        node_pk = self.get_dummy_data()['computers'][0]['id']
        self.process_test(
            'computers',
            f'/computers?id>={node_pk!s}&transport_type="core.ssh"&orderby=-id&limit=2',
            expected_list_ids=[4, 2],
        )

    ########## pass unknown url parameter ###########
    def test_computers_unknown_param(self):
        """Url parameters: id, limit and offset

        from aiida.common.exceptions import InputValidationError
        self.node_exception("/computers?aa=bb&id=2", InputValidationError)
        """

    ############### calculation retrieved_inputs and retrieved_outputs  #############
    def test_calculation_retrieved_inputs(self):
        """Get the list of given calculation retrieved_inputs"""
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        url = f'{self.get_url_prefix()}/calcjobs/{node_uuid!s}/input_files'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            assert response['data'] == [{'name': 'calcjob_inputs', 'type': 'DIRECTORY'}]

    def test_calculation_retrieved_outputs(self):
        """Get the list of given calculation retrieved_outputs"""
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        url = f'{self.get_url_prefix()}/calcjobs/{node_uuid!s}/output_files'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            assert response['data'] == [{'name': 'calcjob_outputs', 'type': 'DIRECTORY'}]

    ############### calculation incoming  #############
    def test_calculation_inputs(self):
        """Get the list of give calculation incoming"""
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        self.process_test(
            'nodes',
            f'/nodes/{node_uuid!s}/links/incoming?orderby=id',
            expected_list_ids=[6, 4],
            uuid=node_uuid,
            result_node_type='data',
            result_name='incoming',
        )

    def test_calculation_input_filters(self):
        """Get filtered incoming list for given calculations"""
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        self.process_test(
            'nodes',
            f'/nodes/{node_uuid!s}/links/incoming?node_type="data.core.dict.Dict."',
            expected_list_ids=[4],
            uuid=node_uuid,
            result_node_type='data',
            result_name='incoming',
        )

    def test_calculation_iotree(self):
        """Get filtered incoming list for given calculations"""
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        url = f'{self.get_url_prefix()}/nodes/{node_uuid!s}/links/tree?in_limit=1&out_limit=1'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            assert len(response['data']['nodes']) == 1
            assert len(response['data']['nodes'][0]['incoming']) == 1
            assert len(response['data']['nodes'][0]['outgoing']) == 1
            assert len(response['data']['metadata']) == 1
            expected_attr = [
                'ctime',
                'mtime',
                'id',
                'node_label',
                'node_type',
                'uuid',
                'description',
                'incoming',
                'outgoing',
            ]
            received_attr = response['data']['nodes'][0].keys()
            for attr in expected_attr:
                assert attr in received_attr
            self.compare_extra_response_data('nodes', url, response, uuid=node_uuid)

    ############### calculation attributes #############
    def test_calculation_attributes(self):
        """Get list of calculation attributes"""
        attributes = {
            'attr1': 'OK',
            'attr2': 'OK',
            'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1},
        }
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        url = f'{self.get_url_prefix()}/nodes/{node_uuid!s}/contents/attributes'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
            response = json.loads(rv_obj.data)
            assert 'message' not in response
            assert response['data']['attributes'] == attributes
            self.compare_extra_response_data('nodes', url, response, uuid=node_uuid)

    def test_contents_attributes_filter(self):
        """Get list of calculation attributes with filter attributes_filter"""
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        url = f'{self.get_url_prefix()}/nodes/{node_uuid!s}/contents/attributes?attributes_filter="attr1"'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
            response = json.loads(rv_obj.data)
            assert 'message' not in response
            assert response['data']['attributes'] == {'attr1': 'OK'}
            self.compare_extra_response_data('nodes', url, response, uuid=node_uuid)

    ############### calculation node attributes filter  #############
    def test_calculation_attributes_filter(self):
        """Get the list of given calculation attributes filtered"""
        attributes = {
            'attr1': 'OK',
            'attr2': 'OK',
            'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1},
        }
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        url = f'{self.get_url_prefix()}/nodes/{node_uuid!s}?attributes=true'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            assert response['data']['nodes'][0]['attributes'] == attributes

    ############### calculation node extras_filter  #############
    def test_calculation_extras_filter(self):
        """Get the list of given calculation extras filtered"""
        extras = {'extra1': False, 'extra2': 'extra_info'}
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        url = f'{self.get_url_prefix()}/nodes/{node_uuid!s}?extras=true&extras_filter=extra1,extra2'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            assert response['data']['nodes'][0]['extras']['extra1'] == extras['extra1']
            assert response['data']['nodes'][0]['extras']['extra2'] == extras['extra2']

    ############### structure node attributes filter #############
    def test_structure_attributes_filter(self):
        """Get the list of given calculation attributes filtered"""
        cell = [[2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0]]
        node_uuid = self.get_dummy_data()['structuredata'][0]['uuid']
        url = f'{self.get_url_prefix()}/nodes/{node_uuid!s}?attributes=true&attributes_filter=cell'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
            response = json.loads(rv_obj.data)
            assert response['data']['nodes'][0]['attributes']['cell'] == cell

    ############### node attributes_filter with pagination #############
    def test_node_attributes_filter_pagination(self):
        """Check that node attributes specified in attributes_filter are
        returned as a dictionary when pagination is set
        """
        expected_attributes = ['resources', 'cell']
        url = f'{self.get_url_prefix()}/nodes/page/1?perpage=10&attributes=true&attributes_filter=resources,cell'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            assert len(response['data']['nodes']) != 0
            for node in response['data']['nodes']:
                assert 'attributes' in node
                assert 'attributes.resources' not in node
                assert 'attributes.cell' not in node
                assert len(node['attributes']) == len(expected_attributes)
                for attr in expected_attributes:
                    assert attr in node['attributes']

    ############### node get one attributes_filter with pagination #############
    def test_node_single_attributes_filter(self):
        """Check that when only one node attribute is specified in attributes_filter
        only this attribute is returned as a dictionary when pagination is set
        """
        expected_attribute = ['resources']
        url = f'{self.get_url_prefix()}/nodes/page/1?perpage=10&attributes=true&attributes_filter=resources'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            assert len(response['data']['nodes']) != 0
            for node in response['data']['nodes']:
                assert list(node['attributes'].keys()) == expected_attribute

    ############### node extras_filter with pagination #############
    def test_node_extras_filter_pagination(self):
        """Check that node extras specified in extras_filter are
        returned as a dictionary when pagination is set
        """
        expected_extras = ['extra1', 'extra2']
        url = f'{self.get_url_prefix()}/nodes/page/1?perpage=10&extras=true&extras_filter=extra1,extra2'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            assert len(response['data']['nodes']) != 0
            for node in response['data']['nodes']:
                assert 'extras' in node
                assert 'extras.extra1' not in node
                assert 'extras.extra2' not in node
                assert len(node['extras']) == len(expected_extras)
                for extra in expected_extras:
                    assert extra in node['extras']

    ############### node get one extras_filter with pagination #############
    def test_node_single_extras_filter(self):
        """Check that when only one node extra is specified in extras_filter
        only this extra is returned as a dictionary when pagination is set
        """
        expected_extra = ['extra2']
        url = f'{self.get_url_prefix()}/nodes/page/1?perpage=10&extras=true&extras_filter=extra2'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            assert len(response['data']['nodes']) != 0
            for node in response['data']['nodes']:
                assert list(node['extras'].keys()) == expected_extra

    ############### node full_type filter #############
    def test_nodes_full_type_filter(self):
        """Get the list of nodes filtered by full_type"""
        expected_node_uuids = []
        for calc in self.get_dummy_data()['calculations']:
            if calc['node_type'] == 'process.calculation.calcjob.CalcJobNode.':
                expected_node_uuids.append(calc['uuid'])

        url = f'{self.get_url_prefix()}/nodes/?full_type="process.calculation.calcjob.CalcJobNode.|"'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
            response = json.loads(rv_obj.data)
            for node in response['data']['nodes']:
                assert node['uuid'] in expected_node_uuids

    def test_nodes_time_filters(self):
        """Get the list of node filtered by time"""
        today = date.today().strftime('%Y-%m-%d')

        expected_node_uuids = []
        data = self.get_dummy_data()
        for calc in data['calculations']:
            expected_node_uuids.append(calc['uuid'])

        # ctime filter test
        url = f'{self.get_url_prefix()}/nodes/?ctime={today}&full_type="process.calculation.calcjob.CalcJobNode.|"'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
            response = json.loads(rv_obj.data)
            for node in response['data']['nodes']:
                assert node['uuid'] in expected_node_uuids

        # mtime filter test
        url = f'{self.get_url_prefix()}/nodes/?mtime={today}&full_type="process.calculation.calcjob.CalcJobNode.|"'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
            response = json.loads(rv_obj.data)
            for node in response['data']['nodes']:
                assert node['uuid'] in expected_node_uuids

    ############### Structure visualization and download #############
    def test_structure_derived_properties(self):
        """Get the list of give calculation incoming"""
        node_uuid = self.get_dummy_data()['structuredata'][0]['uuid']
        url = f'{self.get_url_prefix()}/nodes/{node_uuid!s}/contents/derived_properties'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
            response = json.loads(rv_obj.data)
            assert 'message' not in response
            assert response['data']['derived_properties']['dimensionality'] == {
                'dim': 3,
                'value': 8.0,
                'label': 'volume',
            }
            assert response['data']['derived_properties']['formula'] == 'Ba'
            self.compare_extra_response_data('nodes', url, response, uuid=node_uuid)

    def test_structure_download(self):
        """Test download of structure file"""
        from aiida.orm import load_node

        node_uuid = self.get_dummy_data()['structuredata'][0]['uuid']
        url = f'{self.get_url_prefix()}/nodes/{node_uuid}/download?download_format=xsf'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
        structure_data = load_node(node_uuid)._exportcontent('xsf')[0]
        assert rv_obj.data == structure_data

    @pytest.mark.parametrize('download', ['false', 'False'])
    def test_structure_download_false(self, download):
        """Test download=false that displays the content in the browser instead
        of downloading the structure file
        """
        from aiida.orm import load_node

        node_uuid = self.get_dummy_data()['structuredata'][0]['uuid']
        url = f'{self.get_url_prefix()}/nodes/{node_uuid}/download?download_format=xsf&download={download}'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
            response = json.loads(rv_obj.data)
        structure_data = load_node(node_uuid)._exportcontent('xsf')[0]
        assert response['data']['download']['data'] == structure_data.decode('utf-8')

    def test_cif(self):
        """Test download of cif file"""
        from aiida.orm import load_node

        node_uuid = self.get_dummy_data()['cifdata'][0]['uuid']
        url = f'{self.get_url_prefix()}/nodes/{node_uuid}/download?download_format=cif'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
        cif = load_node(node_uuid)._prepare_cif()[0]
        assert rv_obj.data == cif

    ############### projectable_properties #############
    def test_projectable_properties(self):
        """Test projectable_properties endpoint"""
        for nodetype in ['nodes', 'processes', 'computers', 'users', 'groups']:
            url = f'{self.get_url_prefix()}/{nodetype}/projectable_properties'
            with self.app.test_client() as client:
                rv_obj = client.get(url)
                response = json.loads(rv_obj.data)
                assert 'message' not in response

                expected_keys = ['display_name', 'help_text', 'is_display', 'is_foreign_key', 'type']

                # check fields
                for _, pinfo in response['data']['fields'].items():
                    available_keys = pinfo.keys()
                    for prop in expected_keys:
                        assert prop in available_keys

                # check order
                available_properties = response['data']['fields'].keys()
                for prop in response['data']['ordering']:
                    assert prop in available_properties

    def test_node_namespace(self):
        """Test the rest api call to get list of available node namespace"""
        endpoint_datakeys = {
            '/nodes/full_types': ['path', 'namespace', 'subspaces', 'label', 'full_type'],
            '/nodes/full_types_count': ['path', 'namespace', 'subspaces', 'label', 'full_type', 'counter'],
        }

        for endpoint_suffix, expected_data_keys in endpoint_datakeys.items():
            url = f'{self.get_url_prefix()}{endpoint_suffix}'
            with self.app.test_client() as client:
                rv_obj = client.get(url)
                response = json.loads(rv_obj.data)
                response_keys = response['data'].keys()
                for dkay in expected_data_keys:
                    assert dkay in response_keys
                self.compare_extra_response_data('nodes', url, response)

    def test_comments(self):
        """Get the node comments"""
        node_uuid = self.get_dummy_data()['structuredata'][0]['uuid']
        url = f'{self.get_url_prefix()}/nodes/{node_uuid!s}/contents/comments'
        with self.app.test_client() as client:
            rv_obj = client.get(url)
            response = json.loads(rv_obj.data)['data']['comments']
            all_comments = []
            for comment in response:
                all_comments.append(comment['message'])
            assert sorted(all_comments) == sorted(['This is test comment.', 'Add another comment.'])

    def test_repo(self):
        """Test to get repo list or repo file contents for given node"""
        from aiida.orm import load_node

        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        url = f'{self.get_url_prefix()}/nodes/{node_uuid!s}/repo/list?filename="calcjob_inputs"'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)
            assert response['data']['repo_list'] == [{'type': 'FILE', 'name': 'aiida.in'}]

        url = f'{self.get_url_prefix()}/nodes/{node_uuid!s}/repo/contents?filename="calcjob_inputs/aiida.in"'
        with self.app.test_client() as client:
            response_obj = client.get(url)
            input_file = load_node(node_uuid).base.repository.get_object_content('calcjob_inputs/aiida.in', mode='rb')
            assert response_obj.data == input_file

    def test_process_report(self):
        """Test process report"""
        node_uuid = self.get_dummy_data()['calculations'][1]['uuid']
        url = f'{self.get_url_prefix()}/processes/{node_uuid!s}/report'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)

            expected_keys = response['data'].keys()
            for key in ['logs']:
                assert key in expected_keys

            expected_log_keys = response['data']['logs'][0].keys()
            for key in ['time', 'loggername', 'levelname', 'dbnode_id', 'message']:
                assert key in expected_log_keys

    def test_download_formats(self):
        """Test for download format endpoint"""
        url = f'{self.get_url_prefix()}/nodes/download_formats'
        with self.app.test_client() as client:
            response_value = client.get(url)
            response = json.loads(response_value.data)

            for key in ['data.core.structure.StructureData.|', 'data.core.cif.CifData.|']:
                assert key in response['data'].keys()
            for key in ['cif', 'xsf', 'xyz']:
                assert key in response['data']['data.core.structure.StructureData.|']
            assert 'cif' in response['data']['data.core.cif.CifData.|']

    ############### querybuilder ###############
    def test_querybuilder(self):
        """Test POSTing a QueryBuilder dictionary as JSON to /querybuilder

        This also checks that `full_type` is _not_ included in the result no matter the entity.
        """
        query_dict = (
            orm.QueryBuilder()
            .append(
                orm.CalculationNode,
                tag='calc',
                project=['id', 'uuid', 'user_id'],
            )
            .order_by({'calc': [{'id': {'order': 'desc'}}]})
            .as_dict()
        )

        expected_node_uuids = []
        # dummy data already ordered 'desc' by 'id'
        for calc in self.get_dummy_data()['calculations']:
            if calc['node_type'].startswith('process.calculation.'):
                expected_node_uuids.append(calc['uuid'])

        with self.app.test_client() as client:
            response = client.post(f'{self.get_url_prefix()}/querybuilder', json=query_dict).json

        assert response.get('method', '') == 'POST'
        assert response.get('resource_type', '') == 'QueryBuilder'

        assert len(expected_node_uuids) == len(response.get('data', {}).get('calc', [])), json.dumps(response, indent=2)
        assert expected_node_uuids == [_.get('uuid', '') for _ in response.get('data', {}).get('calc', [])]
        for entities in response.get('data', {}).values():
            for entity in entities:
                # All are Nodes, but neither `node_type` or `process_type` are requested,
                # hence `full_type` should not be present.
                assert 'full_type' not in entity

    def test_get_querybuilder(self):
        """Test GETting the /querybuilder endpoint

        This should return with 405 Method Not Allowed.
        Otherwise, a "conventional" JSON response should be returned with a helpful message.
        """
        from aiida.restapi.resources import QueryBuilder as qb_api  # noqa: N813

        with self.app.test_client() as client:
            response_value = client.get(f'{self.get_url_prefix()}/querybuilder')
            response = response_value.json

        assert response_value.status_code == 405
        assert response_value.status == '405 METHOD NOT ALLOWED'

        assert response.get('method', '') == 'GET'
        assert response.get('resource_type', '') == 'QueryBuilder'
        assert qb_api.GET_MESSAGE == response.get('data', {}).get('message', '')

    def test_querybuilder_user(self):
        """Retrieve a User through the use of the /querybuilder endpoint

        This also checks that `full_type` is _not_ included in the result no matter the entity.
        """
        query_dict = (
            orm.QueryBuilder()
            .append(
                orm.CalculationNode,
                tag='calc',
                project=['id', 'user_id'],
            )
            .append(
                orm.User,
                tag='users',
                with_node='calc',
                project=['id', 'email'],
            )
            .order_by({'calc': [{'id': {'order': 'desc'}}]})
            .as_dict()
        )

        expected_user_ids = []
        for calc in self.get_dummy_data()['calculations']:
            if calc['node_type'].startswith('process.calculation.'):
                expected_user_ids.append(calc['user_id'])

        with self.app.test_client() as client:
            response = client.post(f'{self.get_url_prefix()}/querybuilder', json=query_dict).json

        assert response.get('method', '') == 'POST'
        assert response.get('resource_type', '') == 'QueryBuilder'

        assert len(expected_user_ids) == len(response.get('data', {}).get('users', [])), json.dumps(response, indent=2)
        assert expected_user_ids == [_.get('id', '') for _ in response.get('data', {}).get('users', [])]
        assert expected_user_ids == [_.get('user_id', '') for _ in response.get('data', {}).get('calc', [])]
        for entities in response.get('data', {}).values():
            for entity in entities:
                # User is not a Node (no full_type)
                assert 'full_type' not in entity

    def test_querybuilder_project_explicit(self):
        """Expliticly project everything from the resulting entities

        Here "project" will use the wildcard (*).
        This should result in both CalculationNodes and Data to be returned.
        """
        builder = (
            orm.QueryBuilder()
            .append(
                orm.CalculationNode,
                tag='calc',
                project='*',
            )
            .append(
                orm.Data,
                tag='data',
                with_incoming='calc',
                project='*',
            )
            .order_by({'data': [{'id': {'order': 'desc'}}]})
        )

        expected_calc_uuids = []
        expected_data_uuids = []
        for calc, data in builder.all():
            expected_calc_uuids.append(calc.uuid)
            expected_data_uuids.append(data.uuid)

        query_dict = builder.as_dict()

        with self.app.test_client() as client:
            response = client.post(f'{self.get_url_prefix()}/querybuilder', json=query_dict).json

        assert response.get('method', '') == 'POST'
        assert response.get('resource_type', '') == 'QueryBuilder'

        assert len(expected_calc_uuids) == len(response.get('data', {}).get('calc', [])), json.dumps(response, indent=2)
        assert len(expected_data_uuids) == len(response.get('data', {}).get('data', [])), json.dumps(response, indent=2)
        assert expected_calc_uuids == [_.get('uuid', '') for _ in response.get('data', {}).get('calc', [])]
        assert expected_data_uuids == [_.get('uuid', '') for _ in response.get('data', {}).get('data', [])]
        for entities in response.get('data', {}).values():
            for entity in entities:
                # All are Nodes, and all properties are projected, full_type should be present
                assert 'full_type' in entity
                assert 'attributes' in entity

    def test_querybuilder_project_implicit(self):
        """Implicitly project everything from the resulting entities

        Here "project" will be an empty list, resulting in only the Data node being returned.
        """
        builder = (
            orm.QueryBuilder()
            .append(orm.CalculationNode, tag='calc')
            .append(
                orm.Data,
                tag='data',
                with_incoming='calc',
            )
            .order_by({'data': [{'id': {'order': 'desc'}}]})
        )

        expected_data_uuids = []
        for data in builder.all(flat=True):
            expected_data_uuids.append(data.uuid)

        query_dict = builder.as_dict()

        with self.app.test_client() as client:
            response = client.post(f'{self.get_url_prefix()}/querybuilder', json=query_dict).json

        assert response.get('method', '') == 'POST'
        assert response.get('resource_type', '') == 'QueryBuilder'

        assert ['data'] == list(response.get('data', {}).keys())
        assert len(expected_data_uuids) == len(response.get('data', {}).get('data', [])), json.dumps(response, indent=2)
        assert expected_data_uuids == [_.get('uuid', '') for _ in response.get('data', {}).get('data', [])]
        for entities in response.get('data', {}).values():
            for entity in entities:
                # All are Nodes, and all properties are projected, full_type should be present
                assert 'full_type' in entity
                assert 'attributes' in entity

    def test_array_download(self):
        """Test download of arraydata as a json file"""
        from aiida.orm import load_node

        node_uuid = self.get_dummy_data()['arraydata'][0]['uuid']
        url = f'{self.get_url_prefix()}/nodes/{node_uuid}/download?download_format=json&download=False'
        with self.app.test_client() as client:
            rv_obj = client.get(url)

        data_json = json.loads(rv_obj.json['data']['download']['data'])

        assert json.dumps(data_json, allow_nan=False)

        data_array = load_node(node_uuid)
        array_names = data_array.get_arraynames()
        for name in array_names:
            if not np.isnan(data_array.get_array(name)).any():
                assert np.allclose(data_array.get_array(name), data_json[name])
            else:
                assert clean_array(data_array.get_array(name)) == data_json[name]
