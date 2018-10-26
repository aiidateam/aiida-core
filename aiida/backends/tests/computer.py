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
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import NotExistent

from aiida.orm import Computer, User


class TestComputer(AiidaTestCase):

    def test_get_transport(self):
        """
        Test the get_transport method of Computer
        """
        import tempfile

        new_comp = Computer(
            name='bbb',
            hostname='localhost',
            transport_type='local',
            scheduler_type='direct',
            workdir='/tmp/aiida').store()

        # Configure the computer - no parameters for local transport
        authinfo = self.backend.authinfos.create(computer=new_comp, user=User.objects.get_default())
        authinfo.store()

        transport = new_comp.get_transport()

        # It's on localhost, so I see files that I create
        with transport:
            with tempfile.NamedTemporaryFile() as f:
                self.assertEquals(transport.isfile(f.name), True)
            # Here the file should have been deleted
            self.assertEquals(transport.isfile(f.name), False)

    def test_delete(self):
        new_comp = Computer(
            name='aaa',
            hostname='aaa',
            transport_type='local',
            scheduler_type='pbspro',
            workdir='/tmp/aiida',
            backend=self.backend).store()

        comp_pk = new_comp.pk

        check_computer = Computer.objects.get(comp_pk)
        self.assertEquals(comp_pk, check_computer.pk)

        Computer.objects.delete(comp_pk)

        with self.assertRaises(NotExistent):
            Computer.get(comp_pk)


class TestComputerConfigure(AiidaTestCase):

    def setUp(self):
        """Prepare current user and computer builder with common properties."""
        from aiida.control.computer import ComputerBuilder

        backend = self.backend
        self.comp_builder = ComputerBuilder(label='test', description='Test Computer', enabled=True,
                                            hostname='localhost')
        self.comp_builder.scheduler = 'direct'
        self.comp_builder.work_dir = '/tmp/aiida'
        self.comp_builder.prepend_text = ''
        self.comp_builder.append_text = ''
        self.comp_builder.mpiprocs_per_machine = 8
        self.comp_builder.mpirun_command = 'mpirun'
        self.comp_builder.shebang = '#!xonsh'
        self.user = User.objects.get_default()

    def test_configure_local(self):
        """Configure a computer for local transport and check it is configured."""
        self.comp_builder.label = 'test_configure_local'
        self.comp_builder.transport = 'local'
        comp = self.comp_builder.new()
        comp.store()

        comp.configure()
        self.assertTrue(comp.is_user_configured(self.user))

    def test_configure_ssh(self):
        """Configure a computer for ssh transport and check it is configured."""
        self.comp_builder.label = 'test_configure_ssh'
        self.comp_builder.transport = 'ssh'
        comp = self.comp_builder.new()
        comp.store()

        comp.configure(username='radames', port='22')
        self.assertTrue(comp.is_user_configured(self.user))

    def test_configure_ssh_invalid(self):
        """Try to configure computer with invalid auth params and check it fails."""
        self.comp_builder.label = 'test_configure_ssh_invalid'
        self.comp_builder.transport = 'ssh'
        comp = self.comp_builder.new()
        comp.store()

        with self.assertRaises(ValueError):
            comp.configure(username='radames', invalid_auth_param='TEST')
