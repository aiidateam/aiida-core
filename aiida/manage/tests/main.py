# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Testing infrastructure for easy testing of AiiDA plugins.

"""
import contextlib
import os
import shutil
import tempfile
import warnings

from aiida.common.log import override_log_level
from aiida.common.warnings import warn_deprecation
from aiida.manage import configuration, get_manager
from aiida.manage.configuration import settings
from aiida.manage.external.postgres import Postgres
from aiida.orm import User

__all__ = (
    'get_test_profile_name',
    'get_test_backend_name',
    'test_manager',
    'TestManager',
    'TestManagerError',
    'ProfileManager',
    'TemporaryProfileManager',
)

_DEFAULT_PROFILE_INFO = {
    'name': 'test_profile',
    'email': 'tests@aiida.mail',
    'first_name': 'AiiDA',
    'last_name': 'Plugintest',
    'institution': 'aiidateam',
    'storage_backend': 'core.psql_dos',
    'database_engine': 'postgresql_psycopg2',
    'database_username': 'aiida',
    'database_password': 'aiida_pw',
    'database_name': 'aiida_db',
    'repo_dir': 'test_repo',
    'config_dir': '.aiida',
    'root_path': '',
    'broker_protocol': 'amqp',
    'broker_username': 'guest',
    'broker_password': 'guest',
    'broker_host': '127.0.0.1',
    'broker_port': 5672,
    'broker_virtual_host': '',
    'test_profile': True,
}

warn_deprecation(
    'This module is deprecated; use the fixtures from `aiida.manage.tests.pytest_fixtures` instead', version=3
)


class TestManagerError(Exception):
    """Raised by TestManager in situations that may lead to inconsistent behaviour."""

    def __init__(self, msg):
        super().__init__()
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class TestManager:
    """
    Test manager for plugin tests.

    Uses either ProfileManager for wrapping an existing profile or TemporaryProfileManager for setting up a complete
    temporary AiiDA environment.

    For usage with pytest, see :py:class:`~aiida.manage.tests.pytest_fixtures`.
    """

    def __init__(self):
        self._manager = None

    @property
    def manager(self) -> 'ProfileManager':
        assert self._manager is not None
        return self._manager

    def use_temporary_profile(self, backend=None, pgtest=None):
        """Set up Test manager to use temporary AiiDA profile.

         Uses :py:class:`aiida.manage.tests.main.TemporaryProfileManager` internally.

        :param backend: Backend to use.
        :param pgtest: a dictionary of arguments to be passed to PGTest() for starting the postgresql cluster,
           e.g. {'pg_ctl': '/somepath/pg_ctl'}. Should usually not be necessary.

        """
        if configuration.get_profile() is not None:
            raise TestManagerError('An AiiDA profile must not be loaded before setting up a test profile.')
        if self._manager is not None:
            raise TestManagerError('Profile manager already loaded.')

        mngr = TemporaryProfileManager(backend=backend, pgtest=pgtest)
        mngr.create_profile()
        self._manager = mngr  # don't assign before profile has actually been created!

    def use_profile(self, profile_name):
        """Set up Test manager to use existing profile.

         Uses :py:class:`aiida.manage.tests.main.ProfileManager` internally.

        :param profile_name: Name of existing test profile to use.
        """
        if configuration.get_profile() is not None:
            raise TestManagerError('an AiiDA profile must not be loaded before setting up a test profile.')
        if self._manager is not None:
            raise TestManagerError('Profile manager already loaded.')

        self._manager = ProfileManager(profile_name=profile_name)

    def has_profile_open(self):
        return self._manager and self._manager.has_profile_open()

    def reset_db(self):
        warn_deprecation('reset_db() is deprecated, use clear_profile() instead', version=3)
        return self._manager.clear_profile()

    def clear_profile(self):
        """Reset the global profile, clearing all its data and closing any open resources."""
        return self._manager.clear_profile()

    def destroy_all(self):
        if self._manager:
            self._manager.destroy_all()
        self._manager = None


class ProfileManager:
    """
    Wraps existing AiiDA profile.
    """

    def __init__(self, profile_name):
        """
        Use an existing profile.

        :param profile_name: Name of the profile to be loaded
        """
        from aiida import load_profile

        self._profile = None
        try:
            self._profile = load_profile(profile_name)
        except Exception:
            raise TestManagerError(f'Unable to load test profile `{profile_name}`.')
        if self._profile is None:
            raise TestManagerError(f'Unable to load test profile `{profile_name}`.')
        if not self._profile.is_test_profile:
            raise TestManagerError(f'Profile `{profile_name}` is not a valid test profile.')

    def ensure_default_user(self):
        """Ensure that the default user defined by the profile exists in the database."""
        created, user = User.collection.get_or_create(self._profile.default_user_email)
        if created:
            user.store()

    def clear_profile(self):
        """Reset the global profile, clearing all its data and closing any open resources.

        If the daemon is running, it will be stopped because it might be holding on to entities that will be cleared
        from the storage backend.
        """
        from aiida.engine.daemon.client import get_daemon_client

        daemon_client = get_daemon_client()

        if daemon_client.is_daemon_running:
            daemon_client.stop_daemon(wait=True)

        manager = get_manager()
        manager.get_profile_storage()._clear()  # pylint: disable=protected-access
        manager.get_profile_storage()  # reload the storage connection
        manager.reset_communicator()
        manager.reset_runner()

        self.ensure_default_user()

    def has_profile_open(self):
        return self._profile is not None

    def destroy_all(self):  # pylint: disable=no-self-use
        manager = get_manager()
        manager.reset_profile()


class TemporaryProfileManager(ProfileManager):
    """
    Manage the life cycle of a completely separated and temporary AiiDA environment.

     * No profile / database setup required
     * Tests run via the TemporaryProfileManager never pollute the user's working environment

    Filesystem:

        * temporary ``.aiida`` configuration folder
        * temporary repository folder

    Database:

        * temporary database cluster (via the ``pgtest`` package)
        * with ``aiida`` database user
        * with ``aiida_db`` database

    AiiDA:

        * configured to use the temporary configuration
        * sets up a temporary profile for tests

    All of this happens automatically when using the corresponding tests classes & tests runners (unittest)
    or fixtures (pytest).

    Example::

        tests = TemporaryProfileManager(backend=backend)
        tests.create_aiida_db()  # set up only the database
        tests.create_profile()  # set up a profile (creates the db too if necessary)

        # ready for tests

        # run tests 1

        tests.clear_profile()
        # database ready for independent tests 2

        # run tests 2

        tests.destroy_all()
        # everything cleaned up

    """

    def __init__(self, backend='core.psql_dos', pgtest=None):  # pylint: disable=super-init-not-called
        """Construct a TemporaryProfileManager

        :param backend: a database backend
        :param pgtest: a dictionary of arguments to be passed to PGTest() for starting the postgresql cluster,
           e.g. {'pg_ctl': '/somepath/pg_ctl'}. Should usually not be necessary.

        """
        self.dbinfo = {}
        self.profile_info = _DEFAULT_PROFILE_INFO
        self.profile_info['storage_backend'] = backend
        self._pgtest = pgtest or {}

        self.pg_cluster = None
        self.postgres = None
        self._profile = None
        self._has_test_db = False
        self._backup = {
            'config': configuration.CONFIG,
            'config_dir': settings.AIIDA_CONFIG_FOLDER,
            settings.DEFAULT_AIIDA_PATH_VARIABLE: os.environ.get(settings.DEFAULT_AIIDA_PATH_VARIABLE, None)
        }

    @property
    def profile_dictionary(self):
        """Profile parameters.

        Used to set up AiiDA profile from self.profile_info dictionary.
        """
        dictionary = {
            'default_user_email': 'test@aiida.net',
            'test_profile': True,
            'storage': {
                'backend': self.profile_info.get('storage_backend'),
                'config': {
                    'database_engine': self.profile_info.get('database_engine'),
                    'database_port': self.profile_info.get('database_port'),
                    'database_hostname': self.profile_info.get('database_hostname'),
                    'database_name': self.profile_info.get('database_name'),
                    'database_username': self.profile_info.get('database_username'),
                    'database_password': self.profile_info.get('database_password'),
                    'repository_uri': f'file://{self.repo}',
                }
            },
            'process_control': {
                'backend': 'rabbitmq',
                'config': {
                    'broker_protocol': self.profile_info.get('broker_protocol'),
                    'broker_username': self.profile_info.get('broker_username'),
                    'broker_password': self.profile_info.get('broker_password'),
                    'broker_host': self.profile_info.get('broker_host'),
                    'broker_port': self.profile_info.get('broker_port'),
                    'broker_virtual_host': self.profile_info.get('broker_virtual_host'),
                }
            }
        }
        return dictionary

    def create_db_cluster(self):
        """
        Create the database cluster using PGTest.
        """
        from pgtest.pgtest import PGTest

        if self.pg_cluster is not None:
            raise TestManagerError(
                'Running temporary postgresql cluster detected.Use destroy_all() before creating a new cluster.'
            )
        self.pg_cluster = PGTest(**self._pgtest)
        self.dbinfo.update(self.pg_cluster.dsn)

    def create_aiida_db(self):
        """
        Create the necessary database on the temporary postgres instance.
        """
        if configuration.get_profile() is not None:
            raise TestManagerError('An AiiDA profile can not be loaded while creating a tests db environment')
        if self.pg_cluster is None:
            self.create_db_cluster()
        self.postgres = Postgres(interactive=False, quiet=True, dbinfo=self.dbinfo)
        # Note: We give the user CREATEDB privileges here, only since they are required for the migration tests
        self.postgres.create_dbuser(
            self.profile_info['database_username'], self.profile_info['database_password'], 'CREATEDB'
        )
        self.postgres.create_db(self.profile_info['database_username'], self.profile_info['database_name'])
        self.dbinfo = self.postgres.dbinfo
        self.profile_info['database_hostname'] = self.postgres.host_for_psycopg2
        self.profile_info['database_port'] = self.postgres.port_for_psycopg2
        self._has_test_db = True

    def create_profile(self):
        """
        Set AiiDA to use the tests config dir and create a default profile there

        Warning: the AiiDA dbenv must not be loaded when this is called!
        """
        from aiida.manage.configuration import Profile

        manager = get_manager()

        if not self._has_test_db:
            self.create_aiida_db()

        if not self.root_dir:
            self.root_dir = tempfile.TemporaryDirectory().name  # pylint: disable=consider-using-with
        configuration.CONFIG = None

        os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE] = self.config_dir

        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=UserWarning)
            # This will raise a warning that the ``.aiida`` configuration directory is created.
            settings.set_configuration_directory()

        manager.unload_profile()
        profile_name = self.profile_info['name']
        config = configuration.get_config(create=True)
        profile = Profile(profile_name, self.profile_dictionary)
        config.add_profile(profile)
        config.set_default_profile(profile_name).store()
        self._profile = profile

        # Load the new profile and initialize the profile storage
        with override_log_level():
            profile = manager.load_profile(profile_name)
            profile.storage_cls.initialise(profile, reset=True)

        # Set options to suppress certain warnings
        config.set_option('warnings.development_version', False)
        config.set_option('warnings.rabbitmq_version', False)

        config.store()

        self.ensure_default_user()

    def repo_ok(self):
        return bool(self.repo and os.path.isdir(os.path.dirname(self.repo)))

    @property
    def repo(self):
        return self._return_dir(self.profile_info['repo_dir'])

    def _return_dir(self, dir_path):
        """Return a path to a directory from the fs environment"""
        if os.path.isabs(dir_path):
            return dir_path
        return os.path.join(self.root_dir, dir_path)

    @property
    def backend(self):
        return self.profile_info['backend']

    @backend.setter
    def backend(self, backend):
        if self.has_profile_open():
            raise TestManagerError('backend cannot be changed after setting up the environment')

        valid_backends = ['core.psql_dos']
        if backend not in valid_backends:
            raise ValueError(f'invalid backend {backend}, must be one of {valid_backends}')
        self.profile_info['backend'] = backend

    @property
    def config_dir_ok(self):
        return bool(self.config_dir and os.path.isdir(self.config_dir))

    @property
    def config_dir(self):
        return self._return_dir(self.profile_info['config_dir'])

    @property
    def root_dir(self):
        return self.profile_info['root_path']

    @root_dir.setter
    def root_dir(self, root_dir):
        self.profile_info['root_path'] = root_dir

    @property
    def root_dir_ok(self):
        return bool(self.root_dir and os.path.isdir(self.root_dir))

    def destroy_all(self):
        """Remove all traces of the tests run"""
        super().destroy_all()
        if self.root_dir:
            shutil.rmtree(self.root_dir)
            self.root_dir = None
        if self.pg_cluster:
            self.pg_cluster.close()
            self.pg_cluster = None
        self._has_test_db = False
        self._profile = None

        if 'config' in self._backup:
            configuration.CONFIG = self._backup['config']
        if 'config_dir' in self._backup:
            settings.AIIDA_CONFIG_FOLDER = self._backup['config_dir']

        if settings.DEFAULT_AIIDA_PATH_VARIABLE in self._backup and self._backup[settings.DEFAULT_AIIDA_PATH_VARIABLE]:
            os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE] = self._backup[settings.DEFAULT_AIIDA_PATH_VARIABLE]

    def has_profile_open(self):
        return self._profile is not None


_GLOBAL_TEST_MANAGER = TestManager()


@contextlib.contextmanager
def test_manager(backend='core.psql_dos', profile_name=None, pgtest=None):
    """ Context manager for TestManager objects.

    Sets up temporary AiiDA environment for testing or reuses existing environment,
    if `AIIDA_TEST_PROFILE` environment variable is set.

    Example pytest fixture::

        def aiida_profile():
            with test_manager(backend) as test_mgr:
                yield fixture_mgr

    Example unittest test runner::

        with test_manager(backend) as test_mgr:
            # ready for tests
        # everything cleaned up


    :param backend: storage backend type name
    :param profile_name: name of test profile to be used or None (to use temporary profile)
    :param pgtest: a dictionary of arguments to be passed to PGTest() for starting the postgresql cluster,
       e.g. {'pg_ctl': '/somepath/pg_ctl'}. Should usually not be necessary.
    """
    from aiida.common.log import configure_logging
    from aiida.common.utils import Capturing

    try:
        if not _GLOBAL_TEST_MANAGER.has_profile_open():
            if profile_name:
                _GLOBAL_TEST_MANAGER.use_profile(profile_name=profile_name)
            else:
                with Capturing():  # capture output of AiiDA DB setup
                    _GLOBAL_TEST_MANAGER.use_temporary_profile(backend=backend, pgtest=pgtest)
        configure_logging(with_orm=True)
        yield _GLOBAL_TEST_MANAGER
    finally:
        _GLOBAL_TEST_MANAGER.destroy_all()


def get_test_backend_name() -> str:
    """ Read name of storage backend from environment variable or the specified test profile.

    Reads storage backend from 'AIIDA_TEST_BACKEND' environment variable,
    or the backend configured for the 'AIIDA_TEST_PROFILE'.

    :returns: name of storage backend
    :raises: ValueError if unknown backend name detected.
    :raises: ValueError if both 'AIIDA_TEST_BACKEND' and 'AIIDA_TEST_PROFILE' are set, and the two
        backends do not match.
    """
    test_profile_name = get_test_profile_name()
    backend_env = os.environ.get('AIIDA_TEST_BACKEND', None)
    if test_profile_name is not None:
        backend_profile = configuration.get_config().get_profile(test_profile_name).storage_backend
        if backend_env is not None and backend_env != backend_profile:
            raise ValueError(
                "The backend '{}' read from AIIDA_TEST_BACKEND does not match the backend '{}' "
                "of AIIDA_TEST_PROFILE '{}'".format(backend_env, backend_profile, test_profile_name)
            )
        backend_res = backend_profile
    else:
        backend_res = backend_env or 'core.psql_dos'

    if backend_res in ('core.psql_dos',):
        return backend_res
    raise ValueError(f"Unknown backend '{backend_res}' read from AIIDA_TEST_BACKEND environment variable")


def get_test_profile_name():
    """ Read name of test profile from environment variable.

    Reads name of existing test profile 'AIIDA_TEST_PROFILE' environment variable.
    If specified, this profile is used for running the tests (instead of setting up a temporary profile).

    :returns: content of environment variable or `None`
    """
    return os.environ.get('AIIDA_TEST_PROFILE', None)
