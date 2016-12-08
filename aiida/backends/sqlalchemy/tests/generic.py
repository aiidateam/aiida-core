# -*- coding: utf-8 -*-
"""
Generic tests that need the be specific to sqlalchemy
"""
from aiida.backends.testbase import AiidaTestCase
from aiida.orm.node import Node


class TestDbExtrasSqla(AiidaTestCase):
    """
     No characterization required (sqlachemy specific)
     """
    def test_replacement_1(self):

        n1 = Node().store()
        n2 = Node().store()

        n1.set_extra("pippo", [1, 2, u'a'])
        print "###First set####"
        print "n1 extra", n1.get_extras()
        print "n2 extra", n2.get_extras()

        n1.set_extra("pippobis", [5, 6, u'c'])

        print "###Second set####"
        print "n1 extra", n1.get_extras()
        print "n2 extra", n2.get_extras()

        n2.set_extra("pippo2", [3, 4, u'b'])

        print "###Third set####"
        print "n1 extra", n1.get_extras()
        print "n2 extra", n2.get_extras()


        self.assertEqual(n1.get_extras(),{'pippo': [1, 2, u'a'], 'pippobis': [5, 6, u'c']})

        self.assertEquals(n2.get_extras(), {'pippo2': [3, 4, 'b']})

        new_attrs = {"newval1": "v", "newval2": [1, {"c": "d", "e": 2}]}

        n1.set_extras(new_attrs)
        self.assertEquals(n1.get_extras(), new_attrs)
        self.assertEquals(n2.get_extras(), {'pippo2': [3, 4, 'b']})

        n1.del_extra('newval2')
        del new_attrs['newval2']
        self.assertEquals(n1.get_extras(), new_attrs)
        # Also check that other nodes were not damaged
        self.assertEquals(n2.get_extras(), {'pippo2': [3, 4, 'b']})