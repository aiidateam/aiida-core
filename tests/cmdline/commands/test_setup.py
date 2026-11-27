###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``verdi setup``."""

import uuid

import pytest
from pgtest.pgtest import PGTest

from aiida import orm
from aiida.cmdline.commands import cmd_setup
from aiida.manage import configuration
from aiida.manage.external.postgres import Postgres

pytestmark = pytest.mark.requires_psql


@pytest.fixture(scope='class')
def pg_test_cluster():
    """Create a standalone Postgres cluster, for setup tests."""
    pg_test = PGTest()
    yield pg_test
    pg_test.close()


class TestVerdiSetup:
    """Tests for `verdi setup`."""

    @pytest.fixture(autouse=True)
    def init_profile(self, pg_test_cluster, empty_config, run_cli_command):
        """Initialize the profile."""
        self.storage_backend_name = 'core.psql_dos'
        self.pg_test = pg_test_cluster
        self.cli_runner = run_cli_command

    def test_setup_deprecation(self):
        """Checks if a deprecation warning is printed in stdout and stderr."""
        # Checks if the deprecation warning is present when invoking the help page
        result = self.cli_runner(cmd_setup.setup, ['--help'])
        assert 'Deprecated:' in result.output
        assert 'Deprecated:' in result.stderr

        # Checks if the deprecation warning is present when invoking the command
        # Runs setup in interactive mode and sends Ctrl+D (\x04) as input so we exit the prompts.
        # This way we can check if the deprecation warning was printed with the first prompt.
        result = self.cli_runner(cmd_setup.setup, user_input='\x04', use_subprocess=True, raises=True)
        assert 'Deprecated:' in result.output
        assert 'Deprecated:' in result.stderr

    def test_help(self):
        """Check that the `--help` option is eager, is not overruled and will properly display the help message.

        If this test hangs, most likely the `--help` eagerness is overruled by another option that has started the
        prompt cycle, which by waiting for input, will block the test from continuing.
        """
        self.cli_runner(cmd_setup.setup, ['--help'])

    def test_setup(self, monkeypatch):
        """Require confirmation before creating the profile, even with --non-interactive."""
        monkeypatch.setattr('aiida.__version__', '3.0.0.dev0')
        postgres = Postgres(interactive=False, quiet=True, dbinfo=self.pg_test.dsn)
        postgres.determine_setup()
        db_name = 'aiida_test_setup'
        db_user = 'aiida_test_setup'
        db_pass = '@aiida_test_setup'
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
            '--non-interactive',
            '--email',
            user_email,
            '--first-name',
            user_first_name,
            '--last-name',
            user_last_name,
            '--institution',
            user_institution,
            '--db-name',
            db_name,
            '--db-username',
            db_user,
            '--db-password',
            db_pass,
            '--db-port',
            self.pg_test.dsn['port'],
            '--db-backend',
            self.storage_backend_name,
            '--profile',
            profile_name,
        ]

        prompt = 'Continue with this development version? [y/N]'
        result = self.cli_runner(cmd_setup.setup, options, user_input='n\n', raises=True)
        assert prompt in result.stderr
        assert profile_name not in configuration.get_config().profile_names

        result = self.cli_runner(cmd_setup.setup, options, user_input='y\n')
        assert prompt in result.stderr
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
        try:
            assert backend.get_global_variable('repository|uuid') == backend.get_repository().uuid
        finally:
            backend.close()

    def test_setup_profile_uuid(self):
        """Test ``verdi setup`` explicitly defining the ``--profile-uuid`` option.

        This option intentionally does not work in interactive mode and should not be prompted for.
        """
        postgres = Postgres(interactive=False, quiet=True, dbinfo=self.pg_test.dsn)
        postgres.determine_setup()
        db_name = 'test_profile_uuid'
        db_user = 'test_profile_uuid'
        db_pass = 'test_profile_uuid'
        postgres.create_dbuser(db_user, db_pass)
        postgres.create_db(db_user, db_name)

        profile_name = 'profile-copy'
        user_email = 'some@email.com'
        user_first_name = 'John'
        user_last_name = 'Smith'
        user_institution = 'ECMA'
        profile_uuid = str(uuid.uuid4())
        options = [
            '--non-interactive',
            '--email',
            user_email,
            '--first-name',
            user_first_name,
            '--last-name',
            user_last_name,
            '--institution',
            user_institution,
            '--db-name',
            db_name,
            '--db-username',
            db_user,
            '--db-password',
            db_pass,
            '--db-port',
            self.pg_test.dsn['port'],
            '--db-backend',
            self.storage_backend_name,
            '--profile',
            profile_name,
            '--profile-uuid',
            profile_uuid,
        ]

        self.cli_runner(cmd_setup.setup, options, user_input='y\n')

        config = configuration.get_config()
        assert profile_name in config.profile_names

        profile = config.get_profile(profile_name)
        assert profile.uuid == profile_uuid
