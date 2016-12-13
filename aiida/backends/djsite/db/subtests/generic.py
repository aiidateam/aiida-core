# -*- coding: utf-8 -*-
"""
Generic tests that need the use of the DB
"""

from aiida.orm.node import Node
from aiida.backends.testbase import AiidaTestCase

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1"
__authors__ = "The AiiDA team."


class TestDbExtrasDjango(AiidaTestCase):
    """
    Test DbExtras (specific for Django).
    """
    def test_replacement_1(self):
        from aiida.backends.djsite.db.models import DbExtra

        n1 = Node().store()
        n2 = Node().store()

        DbExtra.set_value_for_node(n1.dbnode, "pippo", [1, 2, 'a'])
        DbExtra.set_value_for_node(n1.dbnode, "pippobis", [5, 6, 'c'])
        DbExtra.set_value_for_node(n2.dbnode, "pippo2", [3, 4, 'b'])

        self.assertEquals(n1.dbnode.extras, {'pippo': [1, 2, 'a'],
                                             'pippobis': [5, 6, 'c']})
        self.assertEquals(n2.dbnode.extras, {'pippo2': [3, 4, 'b']})

        new_attrs = {"newval1": "v", "newval2": [1, {"c": "d", "e": 2}]}

        DbExtra.reset_values_for_node(n1.dbnode, attributes=new_attrs)
        self.assertEquals(n1.dbnode.extras, new_attrs)
        self.assertEquals(n2.dbnode.extras, {'pippo2': [3, 4, 'b']})

        DbExtra.del_value_for_node(n1.dbnode, key='newval2')
        del new_attrs['newval2']
        self.assertEquals(n1.dbnode.extras, new_attrs)
        # Also check that other nodes were not damaged
        self.assertEquals(n2.dbnode.extras, {'pippo2': [3, 4, 'b']})