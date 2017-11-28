from aiida.orm.calculation import Calculation
from aiida.backends.testbase import AiidaTestCase


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
