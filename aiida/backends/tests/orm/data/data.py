from aiida.orm.data import Data
from aiida.orm.calculation import Calculation
from aiida.backends.testbase import AiidaTestCase


class TestParsers(AiidaTestCase):
    def test_attributes(self):
        """
        It is allowed to set an attribute to the unstored Data object
        """
        d = Data()
        d._set_attr('a', 1)
        d.store()
        self.assertRaises(Exception, d._set_attr, 'b', 2)
    def test_data_data_links(self):
        """
        It is not allowed to create a link between two Data objects
        """
        d1=Data()
        d2=Data()
        self.assertRaises(Exception, d2.add_link_from, d1, label="test")

