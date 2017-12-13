from aiida.orm.calculation import Calculation
from aiida.backends.testbase import AiidaTestCase
from aiida.orm.data import Data
from aiida.common.links import LinkType



class TestParsers(AiidaTestCase):
    def test_mutable_attributes(self):
        c = Calculation()
        c._set_attr('a', 1)
        c._set_attr('b', 2)
        c._del_attr('a')
        c.store()
        self.assertRaises(Exception, c._set_attr, 'c', 3)
        self.assertRaises(Exception, c._del_attr, 'b')

    def test_immutable_attributes(self):
        c = Calculation()
        c._updatable_attributes = ('a', 'b', 'c', 'd')
        c._set_attr('a', 1)
        c._set_attr('b', 2)
        c._del_attr('a')
        c.store()
        c._set_attr('c', 3)
        c._del_attr('b')
        c.seal()
        self.assertRaises(Exception, c._del_attr, 'c')
        self.assertRaises(Exception, c._set_attr, 'd', 4)
    
    def test_output_links(self):
        """
        Output links from sealed calculations should not be allowed
        """
        c = Calculation()
        c.store()
        c.seal()
        d = Data()
        self.assertRaises(Exception, d.add_link_from, c, label="test", link_type=LinkType.CREATE)
    
    def test_input_links(self):
        """
        Input links to sealed calculations should not be allowed
        """
        d = Data()
        c = Calculation()
        c.store()
        c.seal()
        self.assertRaises(Exception, c.add_link_from, d, label="test")
