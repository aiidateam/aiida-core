# -*- coding: utf-8 -*-
"""
Tests for the NWChem input plugins.
"""
from aiida.backends.testbase import AiidaTestCase
from aiida.transport import TransportFactory
from aiida.common.exceptions import NotExistent

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1"
__authors__ = "The AiiDA team."



class TestComputer(AiidaTestCase):

    def test_delete(self):
        from aiida.orm import Computer
        new_comp = Computer(name='aaa',
                                hostname='aaa',
                                transport_type='local',
                                scheduler_type='pbspro',
                                workdir='/tmp/aiida')
        new_comp.store()

        comp_pk = new_comp.pk

        check_computer = Computer.get(comp_pk)
        self.assertEquals(comp_pk, check_computer.pk)
        
        from aiida.orm.computer import delete_computer
        delete_computer(pk=comp_pk)

        with self.assertRaises(NotExistent):
            Computer.get(comp_pk)

