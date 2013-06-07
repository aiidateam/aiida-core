"""
Tests for the pw input plugin.
"""
from aiida.djsite.db.testbase import AiidaTestCase
from aiida.orm import CalculationFactory

QECalc = CalculationFactory('quantumespresso.pw')

class QETestCase(AiidaTestCase):

    @classmethod
    def setUpClass(cls):
        super(QETestCase,cls).setUpClass()
        cls.calc_params = {
                           'computer': cls.computer,
                           'num_machines': 1,
                           'num_cpus_per_machine': 1}

class TestQEPWInputGeneration(QETestCase):
    """
    Test if the input is correctly generated
    """
    def test_inputs(self):        
        c = QECalc(**self.calc_params).store()
        