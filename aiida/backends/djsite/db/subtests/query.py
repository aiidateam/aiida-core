from aiida.backends.djsite.db.testbase import AiidaTestCase
from aiida.orm import CalculationFactory, DataFactory
from aiida.orm.calculation.inline import InlineCalculation
from aiida.backends.querybuild.querybuilder_django import QueryBuilder
from aiida.orm.computer import Computer

from aiida.orm import Node

StructureData  = DataFactory('structure')
ParameterData  = DataFactory('parameter')
KpointsData    = DataFactory('array.kpoints')
TrajectoryData = DataFactory('array.trajectory')
QECalc         = CalculationFactory('quantumespresso.pw')

#~ newcomputer.store()
from time import sleep

class TestQueryBuilder(AiidaTestCase):
    def test_simple_query(self):
        """
        Testing a simple query
        """
        struc1  = StructureData()
        param1  = ParameterData()
        param2  = ParameterData()
        qecalc1 = QECalc(computer = self.computer)
        traj1   = TrajectoryData()

        qecalc1.use_structure(struc1)
        qecalc1.use_parameters(param1)
        qecalc1.set_resources({'num_mpiprocs_per_machine':1,'num_machines':1})
        qecalc1.store_all()

        print Node.query().all()
        
        queryhelp  = {
            'path':[
                StructureData,
                QECalc
            ]
        }
        raw_input()

        print list(QueryBuilder(**queryhelp).get_results_dict())
        
