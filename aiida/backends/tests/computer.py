# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Tests for the NWChem input plugins.
"""
from aiida.backends.testbase import AiidaTestCase
from aiida.transport import TransportFactory
from aiida.common.exceptions import NotExistent




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

