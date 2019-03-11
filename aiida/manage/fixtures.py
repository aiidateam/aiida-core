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
Testing tools for related projects like plugins.

Fixtures (pytest) and specific test classes & test runners (unittest)
that set up a complete temporary AiiDA environment for plugin tests.

Filesystem:

    * temporary config (``.aiida``) folder
    * temporary repository folder

Database:

    * temporary database cluster via the ``pgtest`` package
    * with aiida database user
    * with aiida_db database

AiiDA:

    * set to use the temporary config folder
    * create and configure a profile

"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
import unittest
import tempfile
import shutil
from os import path
from contextlib import contextmanager

from pgtest.pgtest import PGTest

from aiida import is_dbenv_loaded
from aiida.backends import settings as backend_settings
from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA
from aiida.common import exceptions
from aiida.manage.manager import get_manager, reset_manager
from aiida.manage.configuration.setup import create_instance_directories
from aiida.manage.configuration.utils import load_config
from aiida.manage.external.postgres import Postgres


class FixtureError(Exception):
    """Raised by FixtureManager, when it encounters a situation in which consistent behaviour can not be guaranteed"""

    def __init__(self, msg):
        super(FixtureError, self).__init__()
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class FixtureManager(object):  # pylint: disable=too-many-public-methods,useless-object-inheritance
    """
    Manage the life cycle of a completely separated and temporary AiiDA environment

    * No previously created database of profile is required to run tests using this environment
    * Tests using this environment will never pollute the user's work environment

    Example::

        fixtures = FixtureManager()
        fixtures.create_aiida_db()  # set up only the database
        fixtures.create_profile()  # set up a profile (creates the db too if necessary)

        # ready for testing

        # run test 1

        fixtures.reset_db()
        # database ready for independent test 2

        # run test 2

        fixtures.destroy_all()
        # everything cleaned up

    Usage (unittest): See the :py:class:`PluginTestCase` and the :py:class:`TestRunner`.


    Usage (pytest)::

        import pytest

        @pytest.fixture(scope='session')
        def aiida_profile():
            # set up a test profile for the duration of the tests
            with aiida.manage.fixtures.fixture_manager() as fixture_manager:
                yield fixture_manager

        @pytest.fixture(scope='function')
        def new_database(aiida_profile):
            # clear the database after each test
            yield aiida_profile
            aiida_profile.reset_db()

        def test_my_stuff(new_database):
            # run a test

    """

    _test_case = None

    def __init__(self):
        from aiida.manage import configuration
        from aiida.manage.configuration import settings as configuration_settings
        self.db_params = {}
        self.fs_env = {'repo': 'test_repo', 'config': '.aiida'}
        self.profile_info = {
            'backend': 'django',
            'email': 'test@aiida.mail',
            'first_name': 'AiiDA',
            'last_name': 'Plugintest',
            'institution': 'aiidateam',
            'db_user': 'aiida',
            'db_pass': 'aiida_pw',
            'db_name': 'aiida_db'
        }
        self.pg_cluster = None
        self.postgres = None
        self.__is_running_on_test_db = False
        self.__is_running_on_test_profile = False
        self._backup = {}
        self._backup['config'] = configuration.CONFIG
        self._backup['config_dir'] = configuration_settings.AIIDA_CONFIG_FOLDER
        self._backup['profile'] = backend_settings.AIIDADB_PROFILE
        self.__backend = None

    @property
    def _backend(self):
        """
        Get the backend
        """
        if self.__backend is None:
            # Lazy load the backend so we don't do it too early (i.e. before load_dbenv())
            self.__backend = get_manager().get_backend()
        return self.__backend

    def create_db_cluster(self):
        if not self.pg_cluster:
            self.pg_cluster = PGTest(max_connections=256)
        self.db_params.update(self.pg_cluster.dsn)

    def create_aiida_db(self):
        """Create the necessary database on the temporary postgres instance"""
        if is_dbenv_loaded():
            raise FixtureError('AiiDA dbenv can not be loaded while creating a test db environment')
        if not self.db_params:
            self.create_db_cluster()
        self.postgres = Postgres(interactive=False, quiet=True, dbinfo=self.db_params)
        self.postgres.determine_setup()
        self.db_params = self.postgres.get_dbinfo()
        if not self.postgres.pg_execute:
            raise FixtureError('Could not connect to the test postgres instance')
        self.postgres.create_dbuser(self.db_user, self.db_pass)
        self.postgres.create_db(self.db_user, self.db_name)
        self.__is_running_on_test_db = True

    def create_profile(self):
        """
        Set AiiDA to use the test config dir and create a default profile there

        Warning: the AiiDA dbenv must not be loaded when this is called!
        """
        if is_dbenv_loaded():
            raise FixtureError('AiiDA dbenv can not be loaded while creating a test profile')
        if not self.__is_running_on_test_db:
            self.create_aiida_db()
        from aiida.manage import configuration
        from aiida.manage.configuration import settings as configuration_settings
        from aiida.manage.configuration.setup import setup_profile
        if not self.root_dir:
            self.root_dir = tempfile.mkdtemp()
        configuration.CONFIG = None
        configuration_settings.AIIDA_CONFIG_FOLDER = self.config_dir
        backend_settings.AIIDADB_PROFILE = None
        create_instance_directories()
        config = load_config(create=True)
        profile_name = 'test_profile'
        setup_profile(profile_name=profile_name, only_config=False, non_interactive=True, **self.profile)
        config = load_config()
        config.set_default_profile(profile_name).store()
        self.__is_running_on_test_profile = True
        self._create_test_case()
        self.init_db()

    def reset_db(self):
        """Cleans all data from the database between tests"""

        self._test_case.clean_db()
        reset_manager()
        self.init_db()

    @staticmethod
    def init_db():
        """Initialise the database state"""
        # Create the default user
        from aiida import orm
        try:
            orm.User(email=get_manager().get_profile().default_user_email).store()
        except exceptions.IntegrityError:
            # The default user already exists, no problem
            pass

    @property
    def profile(self):
        """Profile parameters"""
        profile = {
            'backend': self.backend,
            'email': self.email,
            'repo': self.repo,
            'db_host': self.db_host,
            'db_port': self.db_port,
            'db_name': self.db_name,
            'db_user': self.db_user,
            'db_pass': self.db_pass,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'institution': self.institution
        }
        return profile

    @property
    def db_host(self):
        return self.db_params.get('host')

    @db_host.setter
    def db_host(self, hostname):
        self.db_params['host'] = hostname

    @property
    def first_name(self):
        return self.profile_info['first_name']

    @first_name.setter
    def first_name(self, name):
        self.profile_info['first_name'] = name

    @property
    def last_name(self):
        return self.profile_info['last_name']

    @last_name.setter
    def last_name(self, name):
        self.profile_info['last_name'] = name

    @property
    def institution(self):
        return self.profile_info['institution']

    @institution.setter
    def institution(self, institution):
        self.profile_info['institution'] = institution

    @property
    def db_port(self):
        return self.db_params.get('port', None)

    @db_port.setter
    def db_port(self, port):
        self.db_params['port'] = str(port)

    def repo_ok(self):
        return bool(self.repo and path.isdir(path.dirname(self.repo)))

    @property
    def repo(self):
        return self._return_dir('repo')

    @repo.setter
    def repo(self, repo_dir):
        self.fs_env['repo'] = repo_dir

    def _return_dir(self, key):
        """Return a path to a directory from the fs environment"""
        dir_path = self.fs_env[key]
        if not dir_path:
            raise FixtureError('no directory set for {}'.format(key))
        elif path.isabs(dir_path):
            return dir_path
        return path.join(self.root_dir, dir_path)

    @property
    def email(self):
        return self.profile_info['email']

    @email.setter
    def email(self, email):
        self.profile_info['email'] = email

    @property
    def backend(self):
        return self.profile_info['backend']

    @backend.setter
    def backend(self, backend):
        if self.__is_running_on_test_profile:
            raise FixtureError('backend cannot be changed after setting up the environment')

        valid_backends = [BACKEND_DJANGO, BACKEND_SQLA]
        if backend not in valid_backends:
            raise ValueError('invalid backend {}, must be one of {}'.format(backend, valid_backends))
        self.profile_info['backend'] = backend

    @property
    def config_dir_ok(self):
        return bool(self.config_dir and path.isdir(self.config_dir))

    @property
    def config_dir(self):
        return self._return_dir('config')

    @config_dir.setter
    def config_dir(self, config_dir):
        self.fs_env['config'] = config_dir

    @property
    def db_user(self):
        return self.profile_info['db_user']

    @db_user.setter
    def db_user(self, user):
        self.profile_info['db_user'] = user

    @property
    def db_pass(self):
        return self.profile_info['db_pass']

    @db_pass.setter
    def db_pass(self, passwd):
        self.profile_info['db_pass'] = passwd

    @property
    def db_name(self):
        return self.profile_info['db_name']

    @db_name.setter
    def db_name(self, name):
        self.profile_info['db_name'] = name

    @property
    def root_dir(self):
        return self.fs_env.get('root', '')

    @root_dir.setter
    def root_dir(self, root_dir):
        self.fs_env['root'] = root_dir

    @property
    def root_dir_ok(self):
        return bool(self.root_dir and path.isdir(self.root_dir))

    def destroy_all(self):
        """Remove all traces of the test run"""
        from aiida.manage import configuration
        from aiida.manage.configuration import settings as configuration_settings
        if self.root_dir:
            shutil.rmtree(self.root_dir)
            self.root_dir = None
        if self.pg_cluster:
            self.pg_cluster.close()
            self.pg_cluster = None
        self.__is_running_on_test_db = False
        self.__is_running_on_test_profile = False
        if 'config' in self._backup:
            configuration.CONFIG = self._backup['config']
        if 'config_dir' in self._backup:
            configuration_settings.AIIDA_CONFIG_FOLDER = self._backup['config_dir']
        if 'profile' in self._backup:
            backend_settings.AIIDADB_PROFILE = self._backup['profile']

    def _create_test_case(self):
        """
        Create the test case for the correct backend which will be used to clean up
        """
        if not self.__is_running_on_test_profile:
            raise FixtureError('No test profile has been set up yet, cannot create appropriate test case')
        if self.profile_info['backend'] == BACKEND_DJANGO:
            from aiida.backends.djsite.db.testbase import DjangoTests
            self._test_case = DjangoTests()
        elif self.profile_info['backend'] == BACKEND_SQLA:
            from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests
            from aiida.backends.sqlalchemy import get_scoped_session

            self._test_case = SqlAlchemyTests()
            self._test_case.test_session = get_scoped_session()

    def has_profile_open(self):
        return self.__is_running_on_test_profile


_GLOBAL_FIXTURE_MANAGER = FixtureManager()


@contextmanager
def fixture_manager(backend=BACKEND_DJANGO):
    """
    Context manager for FixtureManager objects

    Example test runner (unittest)::

        with fixture_manager(backend) as fixture_mgr:
            # ready for tests
        # everything cleaned up

    Example fixture (pytest)::

        def aiida_profile():
            with fixture_manager(backend) as fixture_mgr:
                yield fixture_mgr

    :param backend: database backend, either BACKEND_SQLA or BACKEND_DJANGO
    """
    try:
        if not _GLOBAL_FIXTURE_MANAGER.has_profile_open():
            _GLOBAL_FIXTURE_MANAGER.backend = backend
            _GLOBAL_FIXTURE_MANAGER.create_profile()
        yield _GLOBAL_FIXTURE_MANAGER
    finally:
        _GLOBAL_FIXTURE_MANAGER.destroy_all()


class PluginTestCase(unittest.TestCase):
    """
    Set up a complete temporary AiiDA environment for plugin tests.

    Note: This test class needs to be run through the :py:class:`TestRunner`
    and will **not** work simply with `python -m unittest discover`.

    Usage example::

        MyTestCase(aiida.manage.fixtures.PluginTestCase):

            def setUp(self):
                # load my test data

            # optionally extend setUpClass / tearDownClass / tearDown if needed

            def test_my_plugin(self):
                # execute tests
    """
    # Filled in during setUpClass
    backend = None  # type :class:`aiida.orm.Backend`

    @classmethod
    def setUpClass(cls):
        cls.fixture_manager = _GLOBAL_FIXTURE_MANAGER
        if not cls.fixture_manager.has_profile_open():
            raise ValueError(
                "Fixture mananger has no open profile. Please use aiida.manage.fixtures.TestRunner to run these tests.")

        cls.backend = get_manager().get_backend()

    def tearDown(self):
        self.fixture_manager.reset_db()


class TestRunner(unittest.runner.TextTestRunner):
    """
    Testrunner for unit tests using the fixture manager.

    Usage example::

        import unittest
        from aiida.manage.fixtures import TestRunner

        tests = unittest.defaultTestLoader.discover('.')
        TestRunner().run(tests)

    """

    # pylint: disable=arguments-differ
    def run(self, suite, backend=BACKEND_DJANGO):
        """
        Run tests using fixture manager for specified backend.

        :param tests: A suite of tests, as returned e.g. by :py:meth:`unittest.TestLoader.discover`
        :param backend: Database backend to be used.
        """
        from aiida.common.utils import Capturing
        with Capturing():
            with fixture_manager(backend=backend):
                return super(TestRunner, self).run(suite)
