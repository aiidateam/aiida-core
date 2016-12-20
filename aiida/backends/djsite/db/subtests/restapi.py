from aiida.backends.djsite.db.testbase import AiidaTestCase
from aiida.backends.tests.restapi import ImportDataSetUp, RESTApiTestSuit

class LocalSetup(AiidaTestCase, ImportDataSetUp):
    """

    """
    @classmethod
    def setUpClass(cls):
        for base in LocalSetup.__bases__:
            base.setUpClass()

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
            cls.computer = Computer(**dummy_computer)
            cls.computer.store()

class RESTApiTestSuitDjango(LocalSetup, RESTApiTestSuit):
    """
    """
    pass
