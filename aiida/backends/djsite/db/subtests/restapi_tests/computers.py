import json
from aiida.backends.djsite.db.subtests.restapi_tests import RESTApiTestCase

"""
Testcases for Computer REST API
"""



class ComputersRESTApiTestCase(RESTApiTestCase):

    @classmethod
    def setUpClass(cls):
        super(RESTApiTestCase, cls).setUpClass()
        
        # add dummy computers in test database
        from aiida.orm.computer import Computer
        dummycom = [
            {
                "name": "test1",
                "hostname": "test1.epfl.ch",
                "description": "test1 machine",
                "transport_type": "ssh",
                "scheduler_type": "pbspro",
            },
            {
                "name": "test2",
                "hostname": "test2.epfl.ch",
                "description": "test2 machine",
                "transport_type": "ssh",
                "scheduler_type": "torque",
            },
            {
                "name": "test3",
                "hostname": "test3.epfl.ch",
                "description": "test3 machine",
                "transport_type": "local",
                "scheduler_type": "slurm",
            },
            {
                "name": "test4",
                "hostname": "test4.epfl.ch",
                "description": "test4 machine",
                "transport_type": "ssh",
                "scheduler_type": "slurm",
            },
        ]

        for computer in dummycom:
            computer = Computer(**computer)
            computer.store()

        # this list is used in all other computer test cases
        # so to make it same as computers added in test database
        # insert computer "localhost" which was added in testbase
        # at 0th position in list
        dummycom.insert(0, {
            "name": "localhost",
            "hostname": "localhost",
            "transport_type": "local",
            "scheduler_type": "pbspro",
        })

        RESTApiTestCase.dummydata["computers"] = dummycom

    ############### single computer ########################
    def test_computers_details(self):
        """
        Requests the details of single computer
        """
        RESTApiTestCase.node_list(self, "computers", "/computers/1",
                                  expected_list_ids=[0], pk=1)

    ############### full list with limit, offset, page, perpage #############
    def test_computers_list(self):
        """
        Get the full list of computers from database
        """
        RESTApiTestCase.node_list(self, "computers", "/computers", full_list=True)

    def test_computers_list_limit_offset(self):
        """
        Get the list of computers from database using limit
        and offset parameter.
        It should return the no of rows specified in limit from
        database starting from the no. specified in offset
        """
        RESTApiTestCase.node_list(self, "computers", "/computers?limit=2&offset=2",
                                  expected_range=[2,4])

    def test_computers_list_limit_only(self):
        """
        Get the list of computers from database using limit
        parameter.
        It should return the no of rows specified in limit from
        database.
        """
        RESTApiTestCase.node_list(self, "computers", "/computers?limit=2",
                                  expected_range=[None,2])


    def test_computers_list_offset_only(self):
        """
        Get the list of computers from database using offset
        parameter
        It should return all the rows from database starting from
        the no. specified in offset
        """
        RESTApiTestCase.node_list(self, "computers", "/computers?offset=2",
                                  expected_range=[2,None])


    def test_computers_list_limit_offset_perpage(self):
        """
        If we pass the limit, offset and perpage at same time, it
        would return the error message.
        """
        expected_error = "perpage key is incompatible with limit and offset"
        RESTApiTestCase.node_list(self, "computers", "/computers?offset=2&limit=1&perpage=2",
                                  expected_errormsg=expected_error)

    def test_computers_list_page_limit_offset(self):
        """
        If we use the page, limit and offset at same time, it
        would return the error message.
        """
        expected_error = "requesting a specific page is incompatible with limit and offset"
        RESTApiTestCase.node_list(self, "computers", "/computers/page/2?offset=2&limit=1",
                                  expected_errormsg=expected_error)


    def test_computers_list_page_limit_offset_perpage(self):
        """
        If we use the page, limit, offset and perpage at same time, it
        would return the error message.
        """
        expected_error = "perpage key is incompatible with limit and offset"
        RESTApiTestCase.node_list(self, "computers", "/computers/page/2?offset=2&limit=1&perpage=2",
                                  expected_errormsg=expected_error)


    def test_computers_list_page_default(self):
        """
        it returns the no. of rows defined as default perpage option
        from database.

        **** no.of pages = total no. of computers in database / perpage
        "/page" acts as "/page/1?perpage=default_value"

        """
        RESTApiTestCase.node_list(self, "computers", "/computers/page",
                                  full_list=True)


    def test_computers_list_page_perpage(self):
        """
        **** no.of pages = total no. of computers in database / perpage
        Using this formula it returns the no. of rows for requested page
        """
        RESTApiTestCase.node_list(self, "computers", "/computers/page/1?perpage=2",
                                  expected_range=[None,2])


    def test_computers_list_page_perpage_exceed(self):
        """
        **** no.of pages = total no. of computers in database / perpage

        If we request the page which exceeds the total no. of pages then
        it would return the error message.
        """
        expected_error = "Non existent page requested. The page range is [1 : 3]"
        RESTApiTestCase.node_list(self, "computers", "/computers/page/4?perpage=2",
                                  expected_errormsg=expected_error)

    ############### list filters ########################
    def test_computers_filter_id1(self):
        """
        Add filter on the id of computer and get the filtered computer
        list (e.g. id=1)
        """
        RESTApiTestCase.node_list(self, "computers", "/computers?id=1",
                                  expected_list_ids=[0])

    def test_computers_filter_id2(self):
        """
        Add filter on the id of computer and get the filtered computer
        list (e.g. id > 2)
        """
        RESTApiTestCase.node_list(self, "computers", "/computers?id>2",
                                  expected_range=[2,None])


    def test_computers_filter_id3(self):
        """
        Add filter on the id of computer and get the filtered computer
        list (e.g. id >= 2)
        """
        RESTApiTestCase.node_list(self, "computers", "/computers?id>=2",
                                  expected_range=[1, None])


    def test_computers_filter_id4(self):
        """
        Add filter on the id of computer and get the filtered computer
        list (e.g. id < 3)
        """
        RESTApiTestCase.node_list(self, "computers", "/computers?id<2",
                                  expected_range=[None,1])

    def test_computers_filter_id5(self):
        """
        Add filter on the id of computer and get the filtered computer
        list (e.g. id < 3)
        """
        RESTApiTestCase.node_list(self, "computers", "/computers?id<=2",
                                  expected_range=[None,2])

    def test_computers_filter_pk(self):
        """
        Add filter on the id of computer and get the filtered computer
        list (e.g. id=1)
        """
        RESTApiTestCase.node_list(self, "computers", "/computers?pk=1",
                                  expected_list_ids=[0])


    def test_computers_filter_name(self):
        """
        Add filter for the name of computer and get the filtered computer
        list
        """
        RESTApiTestCase.node_list(self, "computers", '/computers?name="test2"',
                                  expected_list_ids=[2])


    def test_computers_filter_hostname(self):
        """
        Add filter for the hostname of computer and get the filtered computer
        list
        """
        RESTApiTestCase.node_list(self, "computers", '/computers?hostname="test3.epfl.ch"',
                                  expected_list_ids=[3])


    def test_computers_filter_transport_type(self):
        """
        Add filter for the transport_type of computer and get the filtered computer
        list
        """
        RESTApiTestCase.node_list(self, "computers", '/computers?transport_type="local"',
                                  expected_list_ids=[0,3])


    ############### list orderby ########################
    def test_computers_orderby_id_asc(self):
        """
        Returns the computers list ordered by "id" in ascending
        order
        """
        RESTApiTestCase.node_list(self, "computers", "/computers?orderby=id",
                                  full_list=True)


    def test_computers_orderby_id_asc_sign(self):
        """
        Returns the computers list ordered by "+id" in ascending
        order
        """
        RESTApiTestCase.node_list(self, "computers", "/computers?orderby=+id",
                                  full_list=True)

    def test_computers_orderby_id_desc(self):
        """
        Returns the computers list ordered by "id" in descending
        order
        """
        RESTApiTestCase.node_list(self, "computers", "/computers?orderby=-id",
                                  expected_list_ids=[4,3,2,1,0])

    def test_computers_orderby_name_asc(self):
        """
        Returns the computers list ordered by "name" in ascending
        order
        """
        RESTApiTestCase.node_list(self, "computers", "/computers?orderby=name",
                                  full_list=True)

    def test_computers_orderby_name_asc_sign(self):
        """
        Returns the computers list ordered by "+name" in ascending
        order
        """
        RESTApiTestCase.node_list(self, "computers", "/computers?orderby=+name",
                                  full_list=True)

    def test_computers_orderby_name_desc(self):
        """
        Returns the computers list ordered by "name" in descending
        order
        """
        RESTApiTestCase.node_list(self, "computers", "/computers?orderby=-name",
                                  expected_list_ids=[4, 3, 2, 1, 0])

    def test_computers_orderby_scheduler_type_asc(self):
        """
        Returns the computers list ordered by "scheduler_type" in ascending
        order
        """
        RESTApiTestCase.node_list(self, "computers",
                                  "/computers?orderby=scheduler_type",
                                  expected_list_ids=[0,1,3,4,2])


    def test_computers_orderby_scheduler_type_asc_sign(self):
        """
        Returns the computers list ordered by "+scheduler_type" in ascending
        order
        """
        RESTApiTestCase.node_list(self, "computers",
                                  "/computers?orderby=+scheduler_type",
                                  expected_list_ids=[0, 1, 3, 4, 2])

    def test_computers_orderby_scheduler_type_desc(self):
        """
        Returns the computers list ordered by "scheduler_type" in descending
        order
        """
        RESTApiTestCase.node_list(self, "computers",
                                  "/computers?orderby=-scheduler_type",
                                  expected_list_ids=[2,3,4,0,1])

    ############### list orderby combinations #######################
    def test_computers_orderby_mixed1(self):
        """
        Returns the computers list first order by "transport_type" in
        ascending order and if it is having same transport_type, order it
        by "id"
        """
        RESTApiTestCase.node_list(self, "computers",
                                  "/computers?orderby=transport_type,id",
                                  expected_list_ids=[0,3,1,2,4])


    def test_computers_orderby_mixed2(self):
        """
        Returns the computers list first order by "scheduler_type" in
        descending order and if it is having same scheduler_type, order it
        by "name"
        """
        RESTApiTestCase.node_list(self, "computers",
                                  "/computers?orderby=-scheduler_type,name",
                                  expected_list_ids=[2,3,4,0,1])

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


        RESTApiTestCase.node_list(self, "computers",
                                  "/computers?orderby=+scheduler_type,-hostname",
                                  expected_list_ids=[1,0,4,3,2])
        """
        pass


    ############### list filter combinations #######################
    def test_computers_filter_mixed1(self):
        """
        Add filter for the hostname and id of computer and get the
        filtered computer list
        """
        RESTApiTestCase.node_list(self, "computers",
                                  '/computers?id>1&hostname="test3.epfl.ch"',
                                  expected_list_ids=[3])


    def test_computers_filter_mixed2(self):
        """
        Add filter for the id, hostname and transport_type of the computer
        and get the filtered computer list
        """
        RESTApiTestCase.node_list(self, "computers",
                                  '/computers?id>1&hostname="test3.epfl.ch"&transport_type="ssh"',
                                  empty_list=True)



    ############### list all parameter combinations #######################
    def test_computers_mixed1(self):
        """
        url parameters: id, limit and offset
        """
        RESTApiTestCase.node_list(self, "computers",
                                  "/computers?id>1&limit=2&offset=3",
                                  expected_list_ids=[4])

    def test_computers_mixed2(self):
        """
        url parameters: id, page, perpage
        """
        RESTApiTestCase.node_list(self, "computers",
                                  "/computers/page/2?id>1&perpage=2",
                                  expected_list_ids=[3,4])


    def test_computers_mixed3(self):
        """
        url parameters: id, transport_type, orderby
        """
        RESTApiTestCase.node_list(self, "computers",
                                  '/computers?id>=1&transport_type="ssh"&orderby=-id&limit=2',
                                  expected_list_ids=[4,2])

    ########## pass unknown url parameter ###########
    def test_computers_unknown_param(self):
        """
        url parameters: id, limit and offset

        from aiida.common.exceptions import InputValidationError
        RESTApiTestCase.node_exception(self, "/computers?aa=bb&id=2",
                                       InputValidationError)
        """
        pass

