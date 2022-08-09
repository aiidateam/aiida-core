# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi profile`."""
import os
import tempfile

from pgtest.pgtest import PGTest
import pytest

from aiida import orm
from aiida.cmdline.commands import cmd_setup
from aiida.manage import configuration
from aiida.manage.external.postgres import Postgres


@pytest.fixture(scope='class')
def pg_test_cluster():
    """Create a standalone Postgres cluster, for setup tests."""
    pg_test = PGTest()
    yield pg_test
    pg_test.close()


class TestVerdiSetup:
    """Tests for `verdi setup` and `verdi quicksetup`."""

    @pytest.fixture(autouse=True)
    def init_profile(self, pg_test_cluster, empty_config, run_cli_command):  # pylint: disable=redefined-outer-name,unused-argument
        """Initialize the profile."""
        # pylint: disable=attribute-defined-outside-init
        self.storage_backend_name = 'core.psql_dos'
        self.pg_test = pg_test_cluster
        self.cli_runner = run_cli_command

    def test_help(self):
        """Check that the `--help` option is eager, is not overruled and will properly display the help message.

        If this test hangs, most likely the `--help` eagerness is overruled by another option that has started the
        prompt cycle, which by waiting for input, will block the test from continuing.
        """
        self.cli_runner(cmd_setup.setup, ['--help'], catch_exceptions=False)
        self.cli_runner(cmd_setup.quicksetup, ['--help'], catch_exceptions=False)

    def test_quicksetup(self):
        """Test `verdi quicksetup`."""
        profile_name = 'testing'
        user_email = 'some@email.com'
        user_first_name = 'John'
        user_last_name = 'Smith'
        user_institution = 'ECMA'

        options = [
            '--non-interactive', '--profile', profile_name, '--email', user_email, '--first-name', user_first_name,
            '--last-name', user_last_name, '--institution', user_institution, '--db-port', self.pg_test.dsn['port'],
            '--db-backend', self.storage_backend_name
        ]

        self.cli_runner(cmd_setup.quicksetup, options)

        config = configuration.get_config()
        assert profile_name in config.profile_names

        profile = config.get_profile(profile_name)
        profile.default_user_email = user_email

        # Verify that the backend type of the created profile matches that of the profile for the current test session
        assert self.storage_backend_name == profile.storage_backend

        user = orm.User.collection.get(email=user_email)
        assert user.first_name == user_first_name
        assert user.last_name == user_last_name
        assert user.institution == user_institution

        # Check that the repository UUID was stored in the database
        backend = profile.storage_cls(profile)
        assert backend.get_global_variable('repository|uuid') == backend.get_repository().uuid

    def test_quicksetup_from_config_file(self):
        """Test `verdi quicksetup` from configuration file."""
        with tempfile.NamedTemporaryFile('w') as handle:
            handle.write(
                f"""---
profile: testing
first_name: Leopold
last_name: Talirz
institution: EPFL
db_backend: {self.storage_backend_name}
db_port: {self.pg_test.dsn['port']}
email: 123@234.de"""
            )
            handle.flush()
            self.cli_runner(cmd_setup.quicksetup, ['--config', os.path.realpath(handle.name)])

    def test_quicksetup_wrong_port(self):
        """Test `verdi quicksetup` exits if port is wrong."""
        profile_name = 'testing'
        user_email = 'some@email.com'
        user_first_name = 'John'
        user_last_name = 'Smith'
        user_institution = 'ECMA'

        options = [
            '--non-interactive', '--profile', profile_name, '--email', user_email, '--first-name', user_first_name,
            '--last-name', user_last_name, '--institution', user_institution, '--db-port',
            self.pg_test.dsn['port'] + 100
        ]

        self.cli_runner(cmd_setup.quicksetup, options, raises=True)

    def test_setup(self):
        """Test `verdi setup` (non-interactive)."""
        postgres = Postgres(interactive=False, quiet=True, dbinfo=self.pg_test.dsn)
        postgres.determine_setup()
        db_name = 'aiida_test_setup'
        db_user = 'aiida_test_setup'
        db_pass = 'aiida_test_setup'
        postgres.create_dbuser(db_user, db_pass)
        postgres.create_db(db_user, db_name)

        profile_name = 'testing'
        user_email = 'some@email.com'
        user_first_name = 'John'
        user_last_name = 'Smith'
        user_institution = 'ECMA'

        # Keep the `--profile` option last as a regression test for #2897 and #2907. Some of the other options have
        # defaults, callbacks and or contextual defaults that might depend on it, but should not fail if they are parsed
        # before the profile option is parsed.
        options = [
            '--non-interactive', '--email', user_email, '--first-name', user_first_name, '--last-name', user_last_name,
            '--institution', user_institution, '--db-name', db_name, '--db-username', db_user, '--db-password', db_pass,
            '--db-port', self.pg_test.dsn['port'], '--db-backend', self.storage_backend_name, '--profile', profile_name
        ]

        self.cli_runner(cmd_setup.setup, options)

        config = configuration.get_config()
        assert profile_name in config.profile_names

        profile = config.get_profile(profile_name)
        profile.default_user_email = user_email

        # Verify that the backend type of the created profile matches that of the profile for the current test session
        assert self.storage_backend_name == profile.storage_backend

        user = orm.User.collection.get(email=user_email)
        assert user.first_name == user_first_name
        assert user.last_name == user_last_name
        assert user.institution == user_institution

        # Check that the repository UUID was stored in the database
        backend = profile.storage_cls(profile)
        assert backend.get_global_variable('repository|uuid') == backend.get_repository().uuid
