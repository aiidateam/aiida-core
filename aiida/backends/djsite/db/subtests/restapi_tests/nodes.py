import json
from aiida.backends.djsite.db.subtests.restapi_tests import RESTApiTestCase
from aiida.backends.djsite.db.testbase import AiidaTestCase

"""
Testcases for Computer REST API
"""


class NodesRESTApiTestCase(RESTApiTestCase):
    @classmethod
    def setUpClass(cls):
        super(RESTApiTestCase, cls).setUpClass()

        from aiida.orm import DataFactory

        KpointsData = DataFactory("array.kpoints")
        kpoints = KpointsData()
        kpoints_mesh = 2
        kpoints.set_kpoints_mesh([kpoints_mesh, kpoints_mesh, kpoints_mesh])
        kpoints.store()

        """
        # add dummy nodes in test database
        from aiida.orm import JobCalculation, CalculationFactory, Data, \
            DataFactory
        from aiida.orm.node import Node

        extra_name = cls.__name__ + "/test_with_subclasses"
        calc_params = {
            'computer': AiidaTestCase.computer,
            'resources': {'num_machines': 1,
                          'num_mpiprocs_per_machine': 1}
        }

        TemplateReplacerCalc = CalculationFactory(
            'simpleplugins.templatereplacer')
        ParameterData = DataFactory('parameter')

        a1 = JobCalculation(**calc_params).store()
        # To query only these nodes later
        a1.set_extra(extra_name, True)
        a2 = TemplateReplacerCalc(**calc_params).store()
        # To query only these nodes later
        a2.set_extra(extra_name, True)
        a3 = Data().store()
        a3.set_extra(extra_name, True)
        a4 = ParameterData(dict={'a': 'b'}).store()
        a4.set_extra(extra_name, True)
        a5 = Node().store()
        a5.set_extra(extra_name, True)
        # I don't set the extras, just to be sure that the filtering works
        # The filtering is needed because other tests will put stuff int he DB
        a6 = JobCalculation(**calc_params)
        a6.store()
        a7 = Node()
        a7.store()
        """