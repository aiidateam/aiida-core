from aiida.orm import DataFactory
from aiida.orm.calculation.inline import InlineCalculation
from aiida.restapi.api import app
import json


StructureData = DataFactory('structure')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')

class ImportDataSetUp(object):
    """
    """

    @classmethod
    def setUpClass(cls):
        """
        """
        # create test inputs
        cell = ((2., 0., 0.), (0., 2., 0.), (0., 0., 2.))
        structure = StructureData(cell=cell)
        structure.append_atom(position=(0., 0., 0.), symbols=['Ba'])
        structure.store()

        parameter1 = ParameterData(dict={"a":1, "b":2})
        parameter1.store()

        parameter2 = ParameterData(dict={"c":3, "d":4})
        parameter2.store()

        kpoint = KpointsData()
        kpoint.set_kpoints_mesh([4, 4, 4])
        kpoint.store()

        #parameter2.add_link_from(structure)
        #parameter2.add_link_from(parameter1)
        #kpoint.add_link_from(parameter2)


class RESTApiTestCase(object):

    dummydata = {
                    "computers": [{
                        "name": "localhost",
                        "hostname": "localhost",
                        "transport_type": "local",
                        "scheduler_type": "pbspro",
                    },
                    {
                        "name": "test1",
                        "hostname": "test1.epfl.ch",
                        "transport_type": "ssh",
                        "scheduler_type": "torque",
                    }],
                    "data": [{
                        }]
                }
    _url_prefix = "/api/v2"

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
        self.assertEqual(response["resource_type"], node_type)
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
        app.config['TESTING'] = True
        with app.test_client() as client:
            rv = client.get(url)
            response = json.loads(rv.data)
            print "res: ", response

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
                    expected_data = RESTApiTestCase.dummydata[node_type][expected_range[0]:expected_range[1]]
                else:
                    from aiida.common.exceptions import InputValidationError
                    raise InputValidationError("Pass the expected range of the dummydata")

                self.assertTrue(len(response["data"][node_type]) == len(expected_data))

                for expected_node, response_node in zip(expected_data,
                                                   response["data"][node_type]):
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


class RESTApiTestSuit(RESTApiTestCase):
    """

    """
    ############### full list with limit, offset, page, perpage #############
    def test_computers_list(self):
        """
        Get the full list of computers from database
        """
        self.node_list("computers", "/computers", full_list=True)

    ############### full list with limit, offset, page, perpage #############
    def test_calculations_list(self):
        """
        Get the full list of calculations from database
        """
        #self.node_list("data", "/data", full_list=True)
        pass
