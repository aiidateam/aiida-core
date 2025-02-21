###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `Computer` ORM class."""

import uuid

import pytest

from aiida.common import exceptions
from aiida.orm import AuthInfo, Computer, User
from aiida.plugins import TransportFactory


class TestComputer:
    """Tests for the `Computer` ORM class."""

    def test_get_transport(self):
        """Test the get_transport method of Computer"""
        import tempfile

        new_comp = Computer(
            label='bbb',
            hostname='localhost',
            transport_type='core.local',
            scheduler_type='core.direct',
            workdir='/tmp/aiida',
        ).store()

        # Configure the computer - no parameters for local transport
        authinfo = AuthInfo(computer=new_comp, user=User.collection.get_default())
        authinfo.store()

        transport = new_comp.get_transport()

        # It's on localhost, so I see files that I create
        with transport:
            with tempfile.NamedTemporaryFile() as handle:
                assert transport.isfile(handle.name) is True
            # Here the file should have been deleted
            assert transport.isfile(handle.name) is False

    def test_delete(self):
        """Test the deletion of a `Computer` instance."""
        new_comp = Computer(
            label='aaa', hostname='aaa', transport_type='core.local', scheduler_type='core.pbspro', workdir='/tmp/aiida'
        ).store()

        comp_pk = new_comp.pk

        check_computer = Computer.collection.get(id=comp_pk)
        assert comp_pk == check_computer.pk

        Computer.collection.delete(comp_pk)

        with pytest.raises(exceptions.NotExistent):
            Computer.collection.get(id=comp_pk)

    def test_get_minimum_job_poll_interval(self):
        """Test the :meth:`aiida.orm.Computer.get_minimum_job_poll_interval` method."""
        computer = Computer()

        # No transport class defined: fall back on class default.
        assert computer.get_minimum_job_poll_interval() == Computer.PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL__DEFAULT

        # Transport class defined: use default of the transport class.
        transport = TransportFactory('core.local')
        computer.transport_type = 'core.local'
        assert computer.get_minimum_job_poll_interval() == transport.DEFAULT_MINIMUM_JOB_POLL_INTERVAL

        # Explicit value defined: use value of the instance.
        interval = -10
        computer.set_minimum_job_poll_interval(interval)
        assert computer.get_minimum_job_poll_interval() == interval


class TestComputerConfigure:
    """Tests for the configuring of instance of the `Computer` ORM class."""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Prepare current user and computer builder with common properties."""
        from aiida.orm.utils.builders.computer import ComputerBuilder

        self.comp_builder = ComputerBuilder(label='test', description='computer', hostname='localhost')
        self.comp_builder.scheduler = 'core.direct'
        self.comp_builder.work_dir = '/tmp/aiida'
        self.comp_builder.prepend_text = ''
        self.comp_builder.append_text = ''
        self.comp_builder.use_double_quotes = False
        self.comp_builder.mpiprocs_per_machine = 8
        self.comp_builder.default_memory_per_machine = 1000000
        self.comp_builder.mpirun_command = 'mpirun'
        self.comp_builder.shebang = '#!xonsh'
        self.user = User.collection.get_default()

    def test_is_configured(self):
        """Test the :meth:`aiida.orm.computers.Computer.is_configured`."""
        self.comp_builder.label = str(uuid.uuid4())
        self.comp_builder.transport = 'core.local'
        comp = self.comp_builder.new()
        comp.store()
        comp.configure()
        assert comp.is_configured

    def test_configure_local(self):
        """Configure a computer for local transport and check it is configured."""
        self.comp_builder.label = str(uuid.uuid4())
        self.comp_builder.transport = 'core.local'
        comp = self.comp_builder.new()
        comp.store()

        comp.configure()
        assert comp.is_user_configured(self.user)

    def test_configure_ssh(self):
        """Configure a computer for ssh transport and check it is configured."""
        self.comp_builder.label = str(uuid.uuid4())
        self.comp_builder.transport = 'core.ssh'
        comp = self.comp_builder.new()
        comp.store()

        comp.configure(username='radames', port='22')
        assert comp.is_user_configured(self.user)

    def test_configure_ssh_invalid(self):
        """Try to configure computer with invalid auth params and check it fails."""
        self.comp_builder.label = str(uuid.uuid4())
        self.comp_builder.transport = 'core.ssh'
        comp = self.comp_builder.new()
        comp.store()

        with pytest.raises(ValueError):
            comp.configure(username='radames', invalid_auth_param='TEST')

    def test_non_configure_error(self):
        """Configure a computer for local transport and check it is configured."""
        self.comp_builder.label = str(uuid.uuid4())
        self.comp_builder.transport = 'core.local'
        comp = self.comp_builder.new()
        comp.store()

        with pytest.raises(exceptions.NotExistent) as exc:
            comp.get_authinfo(self.user)

        assert str(comp.pk) in str(exc)
        assert comp.label in str(exc)
        assert self.user.get_short_name() in str(exc)
        assert str(self.user.pk) in str(exc)
        assert 'verdi computer configure' in str(exc)
