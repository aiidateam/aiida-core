"""Test fixtures for use in related projects"""
import unittest
import tempfile
import shutil
from os import path
from contextlib import contextmanager

from pgtest.pgtest import PGTest

from aiida.control.postgres import Postgres
from aiida import is_dbenv_loaded


class FixtureError(Exception):
    """Raised by FixtureManager, when it encounters a situation in which consistent behaviour can not be guaranteed"""

    def __init__(self, msg):
        super(FixtureError, self).__init__()
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


# pylint: disable=too-many-public-methods
class FixtureManager(object):
    """
    Manage AiiDA fixtures

    Example::

        fixtures = FixtureManager()
        fixtures.create_aiida_db()
        fixtures.create_profile()

        # ready for testing

        # run test 1

        fixtures.reset_db()
        # database ready for independent test 2

        # run test 2

        fixtures.destroy_all()
        # everything cleaned up
    """

    def __init__(self):
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

    def create_db_cluster(self):
        self.pg_cluster = PGTest()
        self.db_params.update(self.pg_cluster.dsn)

    def create_aiida_db(self):
        """Create the necessary database on the temporary postgres instance"""
        if is_dbenv_loaded():
            raise FixtureError(
                'AiiDA dbenv can not be loaded while creating a test db environment'
            )
        if not self.db_params:
            self.create_db_cluster()
        self.postgres = Postgres(interactive=False, quiet=True)
        self.postgres.dbinfo = self.db_params
        self.postgres.determine_setup()
        self.db_params = self.postgres.dbinfo
        if not self.postgres.pg_execute:
            raise FixtureError(
                'Could not connect to the test postgres instance')
        self.postgres.create_dbuser(self.db_user, self.db_pass)
        self.postgres.create_db(self.db_user, self.db_name)
        self.__is_running_on_test_db = True

    def create_root_dir(self):
        self.root_dir = tempfile.mkdtemp()

    def create_profile(self):
        """
        Set AiiDA to use the test config dir and create a default profile there

        Warning: the AiiDA dbenv must not be loaded when this is called!
        """
        if is_dbenv_loaded():
            raise FixtureError(
                'AiiDA dbenv can not be loaded while creating a test profile')
        if not self.__is_running_on_test_db:
            self.create_aiida_db()
        from aiida.common import setup as aiida_cfg
        from aiida.cmdline.verdilib import setup
        if not self.root_dir:
            self.create_root_dir()
        print self.root_dir, self.config_dir
        aiida_cfg.AIIDA_CONFIG_FOLDER = self.config_dir
        aiida_cfg.create_base_dirs()
        profile_name = 'test_profile'
        setup(
            profile=profile_name,
            only_config=False,
            non_interactive=True,
            **self.profile)
        aiida_cfg.set_default_profile('verdi', profile_name)
        aiida_cfg.set_default_profile('daemon', profile_name)
        self.__is_running_on_test_profile = True

    def reset_db(self):
        """Cleans all data from the database between tests"""
        if not self.__is_running_on_test_profile:
            raise FixtureError(
                'No test profile has been set up yet, can not reset the db')
        if self.profile_info['backend'] == 'django':
            self.__clean_db_django()
        elif self.profile_info['backend'] == 'sqla':
            self.__clean_db_sqla()

    @property
    def profile(self):
        """Profile parameters"""
        profile = {
            'backend': self.backend,
            'email': self.email,
            'repo': self.repo,
            'db_host': self.db_host,
            'db_port': self.db_port,
            'db_user': self.db_user,
            'db_pass': self.db_pass,
            'db_name': self.db_name,
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
        if self.root_dir:
            shutil.rmtree(self.root_dir)
            self.root_dir = None
        if self.pg_cluster:
            self.pg_cluster.close()
            self.pg_cluster = None
        self.__is_running_on_test_db = False
        self.__is_running_on_test_profile = False

    @staticmethod
    def __clean_db_django():
        from aiida.backends.djsite.db.testbase import DjangoTests
        DjangoTests().clean_db()

    @staticmethod
    def __clean_db_sqla():
        from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests
        SqlAlchemyTests().clean_db()


@contextmanager
def plugin_fixture():
    """
    Context manager for FixtureManager objects

    Example::

        with plugin_fixture() as fixtures:
            fixtures.create_aiida_db()
            fixtures.create_profile()
            # ready for tests
        # everything cleaned up
    """
    manager = FixtureManager()
    try:
        yield manager
    finally:
        manager.destroy_all()


class PluginTestCase(unittest.TestCase):
    """
    Set up a complete temporary AiiDA environment for plugin tests

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
    BACKEND = 'django'

    @classmethod
    def setUpClass(cls):
        cls.fixture_builder = FixtureManager()
        cls.fixture_builder.create_aiida_db()
        cls.fixture_builder.create_profile()

    @classmethod
    def tearDownClass(cls):
        cls.fixture_builder.destroy_all()
