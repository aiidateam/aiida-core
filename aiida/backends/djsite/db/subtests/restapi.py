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
        cls.computer = Computer(name='test1',
                                hostname='test1.epfl.ch',
                                transport_type='ssh',
                                scheduler_type='torque',
                                workdir='/tmp/aiida')
        cls.computer.store()


class DjangoRESTApiTestSuit(LocalSetup, RESTApiTestSuit):
    """

    """
    pass
