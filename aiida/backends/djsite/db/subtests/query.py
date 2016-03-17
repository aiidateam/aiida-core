from aiida.backends.djsite.db.testbase import AiidaTestCase
#~ from aiida.orm import CalculationFactory, DataFactory
#~ from aiida.orm.calculation.inline import InlineCalculation
#~ from aiida.backends.querybuild.querybuilder_django import QueryBuilder
#~ from aiida.orm.computer import Computer
#~ 
#~ from aiida.orm import Node


#~ newcomputer.store()
#from time import sleep

class TestQueryBuilder(AiidaTestCase):
    def test_query_django(self):
        """
        Testing a simple query
        """
        from aiida.backends.querybuild.querybuilder_django import QueryBuilder
        from aiida.backends.querybuild.dummy_model import DbNode, DbLink, session

        n0 = DbNode(label = 'hello')
        n1 = DbNode(label = 'bye')
        n2 = DbNode(label = 'retried')
        n3 = DbNode(label = 'HeLLo')
        
        
        return

        print list(QueryBuilder(**queryhelp).get_results_dict())
        
