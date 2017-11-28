from aiida.orm.data import Data
from aiida.backends.testbase import AiidaTestCase


class TestParsers(AiidaTestCase):
    def test_attributes(self):
        d = Data()
        d._set_attr('a', 1)
        d.store()
        self.assertRaises(Exception, d._set_attr, 'b', 2)
