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
from __future__ import absolute_import
from aiida.backends.testbase import AiidaTestCase
from aiida.transport import TransportFactory
from aiida.common.exceptions import NotExistent


class TestComputer(AiidaTestCase):

    def test_get_transport(self):
        """
        Test the get_transport method of Computer
        """
        import tempfile

        new_comp = self.backend.computers.create(name='bbb', hostname='localhost', transport_type='local',
                                                 scheduler_type='direct', workdir='/tmp/aiida')
        new_comp.store()

        # Configure the computer - no parameters for local transport
        authinfo = self.backend.authinfos.create(
            computer=new_comp,
            user=self.backend.users.get_automatic_user())
        authinfo.store()

        transport = new_comp.get_transport()

        # It's on localhost, so I see files that I create
        with transport:
            with tempfile.NamedTemporaryFile() as f:
                self.assertEquals(transport.isfile(f.name), True)
            # Here the file should have been deleted
            self.assertEquals(transport.isfile(f.name), False)

    def test_delete(self):
        new_comp = self.backend.computers.create(name='aaa', hostname='aaa', transport_type='local',
                                                 scheduler_type='pbspro', workdir='/tmp/aiida')
        new_comp.store()

        comp_pk = new_comp.pk

        check_computer = self.backend.computers.get(comp_pk)
        self.assertEquals(comp_pk, check_computer.pk)

        self.backend.computers.delete(comp_pk)

        with self.assertRaises(NotExistent):
            self.backend.computers.get(comp_pk)
