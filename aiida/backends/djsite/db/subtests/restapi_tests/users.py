import json
from aiida.backends.djsite.db.subtests.restapi_tests import RESTApiTestCase


"""
Testcases for User REST API
"""


class UsersRESTApiTestCase(RESTApiTestCase):
    @classmethod
    def setUpClass(cls):
        super(RESTApiTestCase, cls).setUpClass()

        # add dummy users in test database
        from aiida.backends.djsite.db.models import DbUser

        dummyusers = [
            {
                "email": "Dorla@epfl.ch",
                "first_name": "Dorla",
                "last_name": "Utz",
                "institution": "EPFL",
            },
            {
                "email": "Alvina@epfl.ch",
                "first_name": "Alvina",
                "last_name": "Derose",
                "institution": "EPFL",
            },
            {
                "email": "Caroline@epfl.ch",
                "first_name": "Caroline",
                "last_name": "Bach",
                "institution": "ETH",
            },
            {
                "email": "Marni@epfl.ch",
                "first_name": "Marni",
                "last_name": "Bach",
                "institution": "ETH",
            },
        ]

        for user in dummyusers:
            DbUser.objects.create_user(**user)

        # this list is used in all other user test cases
        # so to make it same as users added in test database
        # insert user which was added in testbase
        # at 0th position in list
        from aiida.common.utils import get_configured_user_email

        dummyusers.insert(0, {
            "email": get_configured_user_email(),
            "first_name": "",
            "last_name": "",
            "institution": "",
        })

        RESTApiTestCase.dummydata["users"] = dummyusers

    ############### single user ########################
    def test_users_details(self):
        """
        Requests the details of single user
        """
        RESTApiTestCase.node_list(self, "users", "/users/1",
                                  expected_list_ids=[0], pk=1)

    ############### full list with limit, offset, page, perpage ##################
    def test_users_list(self):
        """
        Get the full list of users from database
        """
        RESTApiTestCase.node_list(self, "users", "/users", full_list=True)

    def test_users_list_limit_offset(self):
        """
        Get the list of users from database using limit
        and offset parameter.
        It should return the no of rows specified in limit from
        database starting from the no. specified in offset
        """
        RESTApiTestCase.node_list(self, "users", "/users?limit=2&offset=2",
                                  expected_range=[2, 4])

    def test_users_list_limit_only(self):
        """
        Get the list of users from database using limit
        parameter.
        It should return the no of rows specified in limit from
        database.
        """
        RESTApiTestCase.node_list(self, "users", "/users?limit=2",
                                  expected_range=[None,2])


    def test_users_list_offset_only(self):
        """
        Get the list of users from database using offset
        parameter
        It should return all the rows from database starting from
        the no. specified in offset
        """
        RESTApiTestCase.node_list(self, "users", "/users?offset=2",
                                  expected_range=[2,None])


    def test_users_list_limit_offset_perpage(self):
        """
        If we pass the limit, offset and perpage at same time, it
        would return the error message.
        """
        expected_error = "perpage key is incompatible with limit and offset"
        RESTApiTestCase.node_list(self, "users", "/users?offset=2&limit=1&perpage=2",
                                  expected_errormsg=expected_error)

    def test_users_list_page_limit_offset(self):
        """
        If we use the page, limit and offset at same time, it
        would return the error message.
        """
        expected_error = "requesting a specific page is incompatible with limit and offset"
        RESTApiTestCase.node_list(self, "users", "/users/page/2?offset=2&limit=1",
                                  expected_errormsg=expected_error)


    def test_users_list_page_limit_offset_perpage(self):
        """
        If we use the page, limit, offset and perpage at same time, it
        would return the error message.
        """
        expected_error = "perpage key is incompatible with limit and offset"
        RESTApiTestCase.node_list(self, "users", "/users/page/2?offset=2&limit=1&perpage=2",
                                  expected_errormsg=expected_error)


    def test_users_list_page_default(self):
        """
        it returns the no. of rows defined as default perpage option
        from database.

        **** no.of pages = total no. of users in database / perpage
        "/page" acts as "/page/1?perpage=default_value"

        """
        RESTApiTestCase.node_list(self, "users", "/users/page",
                                  full_list=True)


    def test_users_list_page_perpage(self):
        """
        **** no.of pages = total no. of users in database / perpage
        Using this formula it returns the no. of rows for requested page
        """
        RESTApiTestCase.node_list(self, "users", "/users/page/1?perpage=2",
                                  expected_range=[None,2])


    def test_users_list_page_perpage_exceed(self):
        """
        **** no.of pages = total no. of users in database / perpage

        If we request the page which exceeds the total no. of pages then
        it would return the error message.
        """
        expected_error = "Non existent page requested. The page range is [1 : 3]"
        RESTApiTestCase.node_list(self, "users", "/users/page/4?perpage=2",
                                  expected_errormsg=expected_error)

    ############### list filters ########################
    def test_users_filter_id1(self):
        """
        Add filter on the id of user and get the filtered user
        list (e.g. id=1)
        """
        RESTApiTestCase.node_list(self, "users", "/users?id=1",
                                  expected_list_ids=[0])

    def test_users_filter_id2(self):
        """
        Add filter on the id of user and get the filtered user
        list (e.g. id > 2)
        """
        RESTApiTestCase.node_list(self, "users", "/users?id>2",
                                  expected_range=[2, None])

    def test_users_filter_id3(self):
        """
        Add filter on the id of user and get the filtered user
        list (e.g. id >= 2)
        """
        RESTApiTestCase.node_list(self, "users", "/users?id>=2",
                                  expected_range=[1, None])

    def test_users_filter_id4(self):
        """
        Add filter on the id of user and get the filtered user
        list (e.g. id < 3)
        """
        RESTApiTestCase.node_list(self, "users", "/users?id<2",
                                  expected_range=[None, 1])

    def test_users_filter_id5(self):
        """
        Add filter on the id of user and get the filtered user
        list (e.g. id < 3)
        """
        RESTApiTestCase.node_list(self, "users", "/users?id<=2",
                                  expected_range=[None, 2])

    def test_users_filter_pk(self):
        """
        Add filter on the id of user and get the filtered user
        list (e.g. id=1)
        """
        RESTApiTestCase.node_list(self, "users", "/users?pk=1",
                                  expected_list_ids=[0])

    def test_users_filter_name(self):
        """
        Add filter for the name of user and get the filtered user
        list
        """
        RESTApiTestCase.node_list(self, "users", '/users?first_name="Dorla"',
                                  expected_list_ids=[1])

    def test_users_filter_institution(self):
        """
        Add filter for the institution of user and get the filtered user
        list
        """
        RESTApiTestCase.node_list(self, "users", '/users?institution="EPFL"',
                                  expected_list_ids=[1,2])

    def test_users_filter_email(self):
        """
        Add filter for the institution of user and get the filtered user
        list
        """
        RESTApiTestCase.node_list(self, "users", '/users?email="Alvina@epfl.ch"',
                                  expected_list_ids=[2])

    ############### list filter combinations #######################
    def test_users_filter_mixed1(self):
        """
        Add filter for the first_name and id of user and get the
        filtered user list
        """
        RESTApiTestCase.node_list(self, "users",
                                  '/users?id>1&first_name="Caroline"',
                                  expected_list_ids=[3])

    def test_users_filter_mixed2(self):
        """
        Add filter for the id, first_name and last_name of the user
        and get the filtered user list
        """
        RESTApiTestCase.node_list(self, "users",
                                  '/users?id>1&first_name="Caroline"&last_name="aaa"',
                                  empty_list=True)


    ############### list orderby ########################
    def test_users_orderby_id_asc(self):
        """
        Returns the users list ordered by "id" in ascending
        order
        """
        RESTApiTestCase.node_list(self, "users", "/users?orderby=id",
                                  full_list=True)

    def test_users_orderby_id_asc_sign(self):
        """
        Returns the users list ordered by "+id" in ascending
        order
        """
        RESTApiTestCase.node_list(self, "users", "/users?orderby=+id",
                                  full_list=True)

    def test_users_orderby_id_desc(self):
        """
        Returns the users list ordered by "id" in descending
        order
        """
        RESTApiTestCase.node_list(self, "users", "/users?orderby=-id",
                                  expected_list_ids=[4, 3, 2, 1, 0])

    def test_users_orderby_first_name_asc(self):
        """
        Returns the users list ordered by "first_name" in ascending
        order
        """
        RESTApiTestCase.node_list(self, "users", "/users?orderby=first_name",
                                  expected_list_ids=[0,2,3,1,4])

    def test_users_orderby_first_name_asc_sign(self):
        """
        Returns the users list ordered by "+first_name" in ascending
        order
        """
        RESTApiTestCase.node_list(self, "users", "/users?orderby=+first_name",
                                  expected_list_ids=[0, 2, 3, 1, 4])

    def test_users_orderby_first_name_desc(self):
        """
        Returns the users list ordered by "first_name" in descending
        order
        """
        RESTApiTestCase.node_list(self, "users", "/users?orderby=-first_name",
                                  expected_list_ids=[4,1,3,2,0])

    def test_users_orderby_email_asc(self):
        """
        Returns the users list ordered by "email" in ascending
        order
        """

        RESTApiTestCase.node_list(self, "users",
                                  "/users?orderby=email",
                                  expected_list_ids=[2,3,1,4,0])

    def test_users_orderby_email_asc_sign(self):
        """
        Returns the users list ordered by "+email" in ascending
        order
        """

        RESTApiTestCase.node_list(self, "users",
                                  "/users?orderby=+email",
                                  expected_list_ids=[2,3,1,4,0])

    def test_users_orderby_email_desc(self):
        """
        Returns the users list ordered by "email" in descending
        order
        """

        RESTApiTestCase.node_list(self, "users",
                                  "/users?orderby=-email",
                                  expected_list_ids=[0,4,1,3,2])

        ############### list orderby combinations #######################
        def test_users_orderby_mixed1(self):
            """
            Returns the users list
            - first order by "last_name" in descending order
            - if it is having same last_name, order it by "first_name",
            - if first_name and last_name both are same, order by "id"
            """
            RESTApiTestCase.node_list(self, "users",
                                      "/users?orderby=-lastname,first_name,id",
                                      expected_list_ids=[1,2,3,4,0])

        ############### list filter combinations #######################
        def test_users_filter_mixed1(self):
            """
            Add filter for the first_name and id of user and get the
            filtered user list
            """
            RESTApiTestCase.node_list(self, "users",
                                      '/users?id>1&first_name="Dorla"',
                                      expected_list_ids=[1])

        def test_users_filter_mixed2(self):
            """
            Add filter for the id, hostname and transport_type of the user
            and get the filtered user list
            """
            RESTApiTestCase.node_list(self, "users",
                                      '/users?id>=1&institution="EPFL"',
                                      expected_list_ids=[1,2])

        ############### list all parameter combinations #######################
        def test_users_mixed1(self):
            """
            url parameters: id, limit and offset
            """
            RESTApiTestCase.node_list(self, "users",
                                      "/users?id>1&limit=2&offset=3",
                                      expected_list_ids=[4])

        def test_users_mixed2(self):
            """
            url parameters: id, page, perpage
            """
            RESTApiTestCase.node_list(self, "users",
                                      "/users/page/2?id>1&perpage=2",
                                      expected_list_ids=[3, 4])

        def test_users_mixed3(self):
            """
            url parameters: id, transport_type, orderby
            """
            RESTApiTestCase.node_list(self, "users",
                                      '/users?id>=1&institution="EPFL"&orderby=-id&limit=2',
                                      expected_list_ids=[2,1])

        ########## pass unknown url parameter ###########
        def test_users_unknown_param(self):
            """
            url parameters: id, limit and offset
            """
            from aiida.common.exceptions import InputValidationError
            RESTApiTestCase.node_exception(self, "/users?aa=bb&id=2",
                                           InputValidationError)






