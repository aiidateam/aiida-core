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
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
import tempfile
import shutil
from os import path
from contextlib import contextmanager

from pgtest.pgtest import PGTest

from aiida.backends import BACKEND_DJANGO, BACKEND_SQLA
from aiida.common import exceptions
from aiida.manage import configuration
from aiida.manage.configuration.settings import create_instance_directories
from aiida.manage.manager import get_manager, reset_manager
from aiida.manage.external.postgres import Postgres

__all__ = ('TestManager', 'TestManagerError', '_GLOBAL_TEST_MANAGER')


class TestManagerError(Exception):
    """Raised by TestManager in situations that may lead to inconsistent behaviour."""

    def __init__(self, msg):
        super(TestManagerError, self).__init__()
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class TestManager(object):  # pylint: disable=too-many-public-methods
    """
    Manage the life cycle of a completely separated and temporary AiiDA environment.

     * No profile / database setup required
     * Tests run via the TestManager never pollute the user's working environment

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

        tests = TestManager()
        tests.create_aiida_db()  # set up only the database
        tests.create_profile()  # set up a profile (creates the db too if necessary)

        # ready for tests

        # run tests 1

        tests.reset_db()
        # database ready for independent tests 2

        # run tests 2

        tests.destroy_all()
        # everything cleaned up

    For usage with pytest, see :py:class:`~aiida.manage.tests.pytest_fixtures`.
    For usage with unittest, see :py:class:`~aiida.manage.tests.unittest_classes`.
    """

    _test_case = None

    def __init__(self):
        from aiida.manage.configuration import settings
        self.db_params = {}
        self.fs_env = {'repo': 'test_repo', 'config': '.aiida'}
        self.profile_info = {
            'engine': 'postgresql_psycopg2',
            'backend': 'django',
            'email': 'tests@aiida.mail',
            'first_name': 'AiiDA',
            'last_name': 'Plugintest',
            'institution': 'aiidateam',
            'db_user': 'aiida',
            'db_pass': 'aiida_pw',
            'db_name': 'aiida_db'
        }
        self.pg_cluster = None
        self.postgres = None
        self._is_running_on_test_db = False
        self._is_running_on_test_profile = False
        self._backup = {}
        self._backup['config'] = configuration.CONFIG
        self._backup['config_dir'] = settings.AIIDA_CONFIG_FOLDER
        self._backup['profile'] = configuration.PROFILE
        self._backend = None

    @property
    def _backend(self):
        """
        Get the backend
        """
        if self._backend is None:
            # Lazy load the backend so we don't do it too early (i.e. before load_dbenv())
            self._backend = get_manager().get_backend()
        return self._backend

    def create_db_cluster(self, pgtest=None):
        """
        Create the database cluster using PGTest.

        :param pgtest: a dictionary containing input to PGTest()
        """
        if pgtest is None:
            pgtest = {}
        if not self.pg_cluster:
            self.pg_cluster = PGTest(**pgtest)
        self.db_params.update(self.pg_cluster.dsn)

    def create_aiida_db(self, pgtest=None):
        """
        Create the necessary database on the temporary postgres instance.

        By utilizing pgtest it is possible to forward initialization arguments to PGTest().

        :param pgtest: a dictionary containing input to PGTest()
        """
        if configuration.PROFILE is not None:
            raise TestManagerError('AiiDA dbenv can not be loaded while creating a tests db environment')
        if not self.db_params:
            self.create_db_cluster(pgtest)
        self.postgres = Postgres(interactive=False, quiet=True, dbinfo=self.db_params)
        self.db_params = self.postgres.dbinfo.copy()
        self.postgres.create_dbuser(self.db_user, self.db_pass)
        self.postgres.create_db(self.db_user, self.db_name)
        self._is_running_on_test_db = True

    def create_profile(self, pgtest=None):
        """
        Set AiiDA to use the tests config dir and create a default profile there

        Warning: the AiiDA dbenv must not be loaded when this is called!
        :param pgtest: a dictionary containing input to PGTest()
        """
        if configuration.PROFILE is not None:
            raise TestManagerError('AiiDA dbenv can not be loaded while creating a tests profile')
        if not self._is_running_on_test_db:
            self.create_aiida_db(pgtest)
        from aiida.manage.configuration import settings, load_profile, Profile
        if not self.root_dir:
            self.root_dir = tempfile.mkdtemp()
        configuration.CONFIG = None
        settings.AIIDA_CONFIG_FOLDER = self.config_dir
        configuration.PROFILE = None
        create_instance_directories()
        profile_name = 'test_profile'
        config = configuration.get_config(create=True)
        profile = Profile(profile_name, self.profile_dictionary)
        config.add_profile(profile)
        config.set_default_profile(profile_name).store()
        load_profile(profile_name)
        backend = get_manager()._load_backend(schema_check=False)
        backend.migrate()

        from aiida.orm import User
        from aiida.cmdline.commands.cmd_user import set_default_user

        user = User(**self.user_dictionary)
        user.store()
        set_default_user(profile, user)
        load_profile(profile_name)

        self._is_running_on_test_profile = True
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
        configuration.reset_profile()
        configuration.load_profile()

        # Create the default user
        from aiida import orm
        try:
            orm.User(email=get_manager().get_profile().default_user).store()
        except exceptions.IntegrityError:
            # The default user already exists, no problem
            pass

    @property
    def profile_dictionary(self):
        """Profile parameters"""
        dictionary = {
            'database_engine': self.engine,
            'database_backend': self.backend,
            'database_port': self.db_port,
            'database_name': self.db_name,
            'database_hostname': self.db_host,
            'database_username': self.db_user,
            'database_password': self.db_pass,
            'repository_uri': 'file://' + self.repo,
        }
        return dictionary

    @property
    def user_dictionary(self):
        """User parameters"""
        dictionary = {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'institution': self.institution
        }
        return dictionary

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
            raise TestManagerError('no directory set for {}'.format(key))
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
    def engine(self):
        return self.profile_info['engine']

    @property
    def backend(self):
        return self.profile_info['backend']

    @backend.setter
    def backend(self, backend):
        if self._is_running_on_test_profile:
            raise TestManagerError('backend cannot be changed after setting up the environment')

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
        """Remove all traces of the tests run"""
        from aiida.manage.configuration import settings
        if self.root_dir:
            shutil.rmtree(self.root_dir)
            self.root_dir = None
        if self.pg_cluster:
            self.pg_cluster.close()
            self.pg_cluster = None
        self._is_running_on_test_db = False
        self._is_running_on_test_profile = False
        if 'config' in self._backup:
            configuration.CONFIG = self._backup['config']
        if 'config_dir' in self._backup:
            settings.AIIDA_CONFIG_FOLDER = self._backup['config_dir']
        if 'profile' in self._backup:
            configuration.PROFILE = self._backup['profile']

    def _create_test_case(self):
        """
        Create the tests case for the correct backend which will be used to clean up
        """
        if not self._is_running_on_test_profile:
            raise TestManagerError('No tests profile has been set up yet, cannot create appropriate tests case')
        if self.profile_info['backend'] == BACKEND_DJANGO:
            from aiida.backends.djsite.db.testbase import DjangoTests
            self._test_case = DjangoTests()
        elif self.profile_info['backend'] == BACKEND_SQLA:
            from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests
            from aiida.backends.sqlalchemy import get_scoped_session

            self._test_case = SqlAlchemyTests()
            self._test_case.test_session = get_scoped_session()

    def has_profile_open(self):
        return self._is_running_on_test_profile


_GLOBAL_TEST_MANAGER = TestManager()


@contextmanager
def test_manager(backend=BACKEND_DJANGO, pgtest=None):
    """ Context manager for TestManager objects.

    Example unittest test runner::

        with test_manager(backend) as test_mgr:
            # ready for tests
        # everything cleaned up

    Example pytest fixture::

        def aiida_profile():
            with test_manager(backend) as test_mgr:
                yield fixture_mgr

    :param backend: database backend, either BACKEND_SQLA or BACKEND_DJANGO
    :param pgtest: a dictionary of arguments to be passed to PGTest() for starting the postgresql cluster,
       e.g. {'pg_ctl': '/somepath/pg_ctl'}. Should usually not be necessary.
    """
    try:
        if not _GLOBAL_TEST_MANAGER.has_profile_open():
            _GLOBAL_TEST_MANAGER.backend = backend
            _GLOBAL_TEST_MANAGER.create_profile(pgtest)
        yield _GLOBAL_TEST_MANAGER
    finally:
        _GLOBAL_TEST_MANAGER.destroy_all()


def get_test_backend():
    """ Read database backend from environment variable.

    Reads from 'TEST_AIIDA_BACKEND' environment variable.
    Defaults to django backend.
    """
    import os

    backend_env = os.environ.get('TEST_AIIDA_BACKEND', BACKEND_DJANGO)
    if backend_env in (BACKEND_DJANGO, BACKEND_SQLA):
        return backend_env
    raise ValueError("Unknown backend '{}' read from TEST_AIIDA_BACKEND environment variable".format(backend_env))
