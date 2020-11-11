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
import tempfile
import shutil
import os
from contextlib import contextmanager

from aiida.backends import BACKEND_DJANGO, BACKEND_SQLA
from aiida.common import exceptions
from aiida.manage import configuration
from aiida.manage.configuration.settings import create_instance_directories
from aiida.manage import manager
from aiida.manage.external.postgres import Postgres

__all__ = ('TestManager', 'TestManagerError', 'ProfileManager', 'TemporaryProfileManager', '_GLOBAL_TEST_MANAGER')

_DEFAULT_PROFILE_INFO = {
    'name': 'test_profile',
    'email': 'tests@aiida.mail',
    'first_name': 'AiiDA',
    'last_name': 'Plugintest',
    'institution': 'aiidateam',
    'database_engine': 'postgresql_psycopg2',
    'database_backend': 'django',
    'database_username': 'aiida',
    'database_password': 'aiida_pw',
    'database_name': 'aiida_db',
    'repo_dir': 'test_repo',
    'config_dir': '.aiida',
    'root_path': '',
}


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
    For usage with unittest, see :py:class:`~aiida.manage.tests.unittest_classes`.
    """

    def __init__(self):
        self._manager = None

    def use_temporary_profile(self, backend=None, pgtest=None):
        """Set up Test manager to use temporary AiiDA profile.

         Uses :py:class:`aiida.manage.tests.TemporaryProfileManager` internally.

        :param backend: Backend to use.
        :param pgtest: a dictionary of arguments to be passed to PGTest() for starting the postgresql cluster,
           e.g. {'pg_ctl': '/somepath/pg_ctl'}. Should usually not be necessary.

        """
        if configuration.PROFILE is not None:
            raise TestManagerError('AiiDA dbenv must not be loaded before setting up a test profile.')
        if self._manager is not None:
            raise TestManagerError('Profile manager already loaded.')

        mngr = TemporaryProfileManager(backend=backend, pgtest=pgtest)
        mngr.create_profile()
        self._manager = mngr  # don't assign before profile has actually been created!

    def use_profile(self, profile_name):
        """Set up Test manager to use existing profile.

         Uses :py:class:`aiida.manage.tests.ProfileManager` internally.

        :param profile_name: Name of existing test profile to use.
        """
        if configuration.PROFILE is not None:
            raise TestManagerError('AiiDA dbenv must not be loaded before setting up a test profile.')
        if self._manager is not None:
            raise TestManagerError('Profile manager already loaded.')

        self._manager = ProfileManager(profile_name=profile_name)
        self._manager.init_db()

    def has_profile_open(self):
        return self._manager and self._manager.has_profile_open()

    def reset_db(self):
        return self._manager.reset_db()

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
        from aiida.backends.testbase import check_if_tests_can_run

        self._profile = None
        self._user = None

        try:
            self._profile = load_profile(profile_name)
            manager.get_manager()._load_backend(schema_check=False)  # pylint: disable=protected-access
        except Exception:
            raise TestManagerError('Unable to load test profile \'{}\'.'.format(profile_name))
        check_if_tests_can_run()

        self._select_db_test_case(backend=self._profile.database_backend)

    def _select_db_test_case(self, backend):
        """
        Selects tests case for the correct database backend.
        """
        if backend == BACKEND_DJANGO:
            from aiida.backends.djsite.db.testbase import DjangoTests
            self._test_case = DjangoTests()
        elif backend == BACKEND_SQLA:
            from aiida.backends.sqlalchemy.testbase import SqlAlchemyTests
            from aiida.backends.sqlalchemy import get_scoped_session

            self._test_case = SqlAlchemyTests()
            self._test_case.test_session = get_scoped_session()

    def reset_db(self):
        self._test_case.clean_db()  # will drop all users
        manager.reset_manager()
        self.init_db()

    def init_db(self):
        """Initialise the database state for running of tests.

        Adds default user if necessary.
        """
        from aiida.orm import User
        from aiida.cmdline.commands.cmd_user import set_default_user

        if not User.objects.get_default():
            user_dict = get_user_dict(_DEFAULT_PROFILE_INFO)
            try:
                user = User(**user_dict)
                user.store()
            except exceptions.IntegrityError:
                # The user already exists, no problem
                user = User.objects.get(**user_dict)

            set_default_user(self._profile, user)
            User.objects.reset()  # necessary to pick up new default user

    def has_profile_open(self):
        return self._profile is not None

    def destroy_all(self):
        pass


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

        tests.reset_db()
        # database ready for independent tests 2

        # run tests 2

        tests.destroy_all()
        # everything cleaned up

    """

    _test_case = None

    def __init__(self, backend=BACKEND_DJANGO, pgtest=None):  # pylint: disable=super-init-not-called
        """Construct a TemporaryProfileManager

        :param backend: a database backend
        :param pgtest: a dictionary of arguments to be passed to PGTest() for starting the postgresql cluster,
           e.g. {'pg_ctl': '/somepath/pg_ctl'}. Should usually not be necessary.

        """
        from aiida.manage.configuration import settings

        self.dbinfo = {}
        self.profile_info = _DEFAULT_PROFILE_INFO
        self.profile_info['database_backend'] = backend
        self._pgtest = pgtest or {}

        self.pg_cluster = None
        self.postgres = None
        self._profile = None
        self._has_test_db = False
        self._backup = {
            'config': configuration.CONFIG,
            'config_dir': settings.AIIDA_CONFIG_FOLDER,
            'profile': configuration.PROFILE,
        }

    @property
    def profile_dictionary(self):
        """Profile parameters.

        Used to set up AiiDA profile from self.profile_info dictionary.
        """
        dictionary = {
            'database_engine': self.profile_info.get('database_engine'),
            'database_backend': self.profile_info.get('database_backend'),
            'database_port': self.profile_info.get('database_port'),
            'database_hostname': self.profile_info.get('database_hostname'),
            'database_name': self.profile_info.get('database_name'),
            'database_username': self.profile_info.get('database_username'),
            'database_password': self.profile_info.get('database_password'),
            'broker_protocol': self.profile_info.get('broker_protocol'),
            'broker_username': self.profile_info.get('broker_username'),
            'broker_password': self.profile_info.get('broker_password'),
            'broker_host': self.profile_info.get('broker_host'),
            'broker_port': self.profile_info.get('broker_port'),
            'broker_virtual_host': self.profile_info.get('broker_virtual_host'),
            'repository_uri': f'file://{self.repo}',
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
        if configuration.PROFILE is not None:
            raise TestManagerError('AiiDA dbenv can not be loaded while creating a tests db environment')
        if self.pg_cluster is None:
            self.create_db_cluster()
        self.postgres = Postgres(interactive=False, quiet=True, dbinfo=self.dbinfo)
        # note: not using postgres.create_dbuser_db_safe here since we don't want prompts
        self.postgres.create_dbuser(self.profile_info['database_username'], self.profile_info['database_password'])
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
        from aiida.manage.configuration import settings, load_profile, Profile

        if not self._has_test_db:
            self.create_aiida_db()

        if not self.root_dir:
            self.root_dir = tempfile.mkdtemp()
        configuration.CONFIG = None
        settings.AIIDA_CONFIG_FOLDER = self.config_dir
        configuration.PROFILE = None
        create_instance_directories()
        profile_name = self.profile_info['name']
        config = configuration.get_config(create=True)
        profile = Profile(profile_name, self.profile_dictionary)
        config.add_profile(profile)
        config.set_default_profile(profile_name).store()
        self._profile = profile

        load_profile(profile_name)
        backend = manager.get_manager()._load_backend(schema_check=False)
        backend.migrate()

        self._select_db_test_case(backend=self._profile.database_backend)
        self.init_db()

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

        valid_backends = [BACKEND_DJANGO, BACKEND_SQLA]
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
        from aiida.manage.configuration import settings
        if self.root_dir:
            shutil.rmtree(self.root_dir)
            self.root_dir = None
        if self.pg_cluster:
            self.pg_cluster.close()
            self.pg_cluster = None
        self._has_test_db = False
        self._profile = None
        self._user = None

        if 'config' in self._backup:
            configuration.CONFIG = self._backup['config']
        if 'config_dir' in self._backup:
            settings.AIIDA_CONFIG_FOLDER = self._backup['config_dir']
        if 'profile' in self._backup:
            configuration.PROFILE = self._backup['profile']

    def has_profile_open(self):
        return self._profile is not None


_GLOBAL_TEST_MANAGER = TestManager()


@contextmanager
def test_manager(backend=BACKEND_DJANGO, profile_name=None, pgtest=None):
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


    :param backend: database backend, either BACKEND_SQLA or BACKEND_DJANGO
    :param profile_name: name of test profile to be used or None (to use temporary profile)
    :param pgtest: a dictionary of arguments to be passed to PGTest() for starting the postgresql cluster,
       e.g. {'pg_ctl': '/somepath/pg_ctl'}. Should usually not be necessary.
    """
    from aiida.common.utils import Capturing
    from aiida.common.log import configure_logging

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


def get_test_backend_name():
    """ Read name of database backend from environment variable or the specified test profile.

    Reads database backend ('django' or 'sqlalchemy') from 'AIIDA_TEST_BACKEND' environment variable,
    or the backend configured for the 'AIIDA_TEST_PROFILE'.
    Defaults to django backend.

    :returns: content of environment variable or `BACKEND_DJANGO`
    :raises: ValueError if unknown backend name detected.
    :raises: ValueError if both 'AIIDA_TEST_BACKEND' and 'AIIDA_TEST_PROFILE' are set, and the two
        backends do not match.
    """
    test_profile_name = get_test_profile_name()
    backend_env = os.environ.get('AIIDA_TEST_BACKEND', None)
    if test_profile_name is not None:
        backend_profile = configuration.get_config().get_profile(test_profile_name).database_backend
        if backend_env is not None and backend_env != backend_profile:
            raise ValueError(
                "The backend '{}' read from AIIDA_TEST_BACKEND does not match the backend '{}' "
                "of AIIDA_TEST_PROFILE '{}'".format(backend_env, backend_profile, test_profile_name)
            )
        backend_res = backend_profile
    else:
        backend_res = backend_env or BACKEND_DJANGO

    if backend_res in (BACKEND_DJANGO, BACKEND_SQLA):
        return backend_res
    raise ValueError(f"Unknown backend '{backend_res}' read from AIIDA_TEST_BACKEND environment variable")


def get_test_profile_name():
    """ Read name of test profile from environment variable.

    Reads name of existing test profile 'AIIDA_TEST_PROFILE' environment variable.
    If specified, this profile is used for running the tests (instead of setting up a temporary profile).

    :returns: content of environment variable or `None`
    """
    return os.environ.get('AIIDA_TEST_PROFILE', None)


def get_user_dict(profile_dict):
    """Collect parameters required for creating users."""
    return {k: profile_dict[k] for k in ('email', 'first_name', 'last_name', 'institution')}
