# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Computer control module unit tests."""
from __future__ import absolute_import
from aiida.backends.testbase import AiidaTestCase
from aiida.control.computer import ComputerBuilder, configure_computer


class TestComputerControl(AiidaTestCase):

    def setUp(self):
        """Prepare current user and computer builder with common properties."""
        from aiida.orm.backend import construct_backend
        from aiida.scheduler import SchedulerFactory
        backend = construct_backend()
        self.comp_builder = ComputerBuilder(label='test', description='Test Computer', enabled=True, hostname='localhost')
        self.comp_builder.scheduler = 'direct'
        self.comp_builder.work_dir = '/tmp/aiida'
        self.comp_builder.prepend_text = ''
        self.comp_builder.append_text = ''
        self.comp_builder.mpiprocs_per_machine = 8
        self.comp_builder.mpirun_command = 'mpirun'
        self.comp_builder.shebang = '#!xonsh'
        self.user = backend.users.get_automatic_user()

    def test_configure_local(self):
        """Configure a computer for local transport and check it is configured."""
        self.comp_builder.label = 'test_configure_local'
        self.comp_builder.transport = 'local'
        comp = self.comp_builder.new()
        comp.store()

        configure_computer(comp)
        self.assertTrue(comp.is_user_configured(self.user))

    def test_configure_ssh(self):
        """Configure a computer for ssh transport and check it is configured."""
        self.comp_builder.label = 'test_configure_ssh'
        self.comp_builder.transport = 'ssh'
        comp = self.comp_builder.new()
        comp.store()

        configure_computer(comp, username='radames', port='22')
        self.assertTrue(comp.is_user_configured(self.user))

    def test_configure_ssh_invalid(self):
        """Try to configure computer with invalid auth params and check it fails."""
        self.comp_builder.label = 'test_configure_ssh_invalid'
        self.comp_builder.transport = 'ssh'
        comp = self.comp_builder.new()
        comp.store()

        with self.assertRaises(ValueError):
            configure_computer(comp, username='radames', invalid_auth_param='TEST')
