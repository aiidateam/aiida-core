"""Test fixtures for use in related projects"""
import unittest
import tempfile
import shutil
from os import path

from pgtest.pgtest import PGTest

from aiida.control.postgres import Postgres


class FixtureError(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class FixtureBuilder(object):

    def __init__(self):
        self.db_params = {}
        self.fs_env = {}
        self.profile = {
            'backend': 'django',
            'email': 'test@aiida.mail',
        }
        self.temp_dir = None
        self.pg_cluster = None
        self.postgres = None

    def create_db_cluster(self):
        self.pg_cluster = PGTest()
        self.db_params.update(self.pg_cluster.dsn)

    def create_aiida_db(self):
        if not db_params:
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

    def create_root_dir(self):
        self.root_dir = tempfile.mkdtemp()

    def create_config_dir(self):
        self.fs_env['config'] = path.join(self.root_dir, '.aiida')

    def create_profile(self):
        from aiida.common import setup as aiida_cfg
        from aiida.cmdline.verdilib import setup
        aiida_cfg.AIIDA_CONFIG_FOLDER = self.config_dir
        aiida_cfg.create_base_dirs()
        profile_name = 'test_profile'
        profile = {
            'repo': path.join(temp_dir, 'test_repo'),
            'db_host': db_fixture.pg_test.dsn['host'],
            'db_port': db_fixture.pg_test.port,
            'db_user': db_fixture.pg_test.dsn['user'],
            'db_pass': db_fixture.DB_PASS,
            'db_name': db_fixture.DB_NAME,
            'first_name': 'AiiDA',
            'last_name': 'Tester',
            'institution': 'aiidateam'
        }
        setup(
            profile=profile_name,
            only_config=False,
            non_interactive=True,
            **profile)
        aiida_cfg.set_default_profile('verdi', profile_name)
        aiida_cfg.set_default_profile('daemon', profile_name)

    @property
    def repo(self):
        if not self.repo:
            self.repo = path.join(self.root_dir, 'test_repo')
        return self.profile.get('repo', None)

    @repo.setter
    def repo(self, path):
        self.profile['repo'] = path

    @property
    def email(self):
        return self.profile.get('email', None)

    @email.setter
    def email(self, email):
        self.profile['email'] = email

    @property
    def backend(self):
        return self.profile.get('backend', None)

    @backend.setter
    def backend(self, backend):
        self.profile['backend'] = backend

    @property
    def config_dir_ok(self):
        return bool(self.config_dir and path.isdir(self.config_dir))

    @property
    def config_dir(self):
        if not self.config_dir_ok:
            self.create_config_dir(
            )  # TODO: Should never overwrite user set path but fail instead
        return self.fs_env.get('config', None)

    @config_dir.setter
    def config_dir(self, path):
        self.fs_env['config'] = path

    @property
    def db_user(self):
        return self.db_params['user']

    @db_user.setter
    def db_user(self, user):
        self.db_params['user'] = user

    @property
    def db_pass(self):
        return self.db_params['password']

    @db_pass.setter
    def db_pass(self, passwd):
        self.db_params['password'] = passwd

    @property
    def db_name(self):
        return self.db_params['database']

    @db_name.setter
    def db_name(self, name):
        self.db_params['database'] = name

    @property
    def root_dir(self):
        if not self.root_dir_ok:
            self.create_root_dir()
        return self.fs_env.get('root', None)

    @root_dir.setter
    def root_dir(self, path):
        self.fs_env['root'] = path

    @property
    def root_dir_ok(self):
        return bool(self.temp_dir and path.isdir(self.temp_dir))

    def __del__(self):
        if self.temp_dir:
            shutil.rmtree(self.temp_dir)
        if self.pg_cluster:
            self.pg_cluster.close()


class DbFixture(object):
    """Create temporary AiiDA db environment"""

    DB_USER = 'aiida'
    DB_NAME = 'aiida_db'
    DB_PASS = 'aiida_pw'

    def __init__(self):
        self.pg_test = PGTest()
        self.postgres = Postgres(
            port=self.pg_test.port, interactive=False, quiet=True)
        self.postgres.dbinfo = self.pg_test.dsn
        self.postgres.determine_setup()
        self.success = bool(self.postgres.pg_execute)
        if self.success:
            self.postgres.create_dbuser(self.DB_USER, self.DB_PASS)
            self.postgres.create_db(self.DB_USER, self.DB_NAME)

    def __del__(self):
        self.pg_test.close()

    def init_success(self):
        return self.success


def setup_fs_env():
    """Create temporary config / repo folders"""
    temp_dir = tempfile.mkdtemp()
    return temp_dir


def setup_aiida(temp_dir):
    from aiida.common import setup as aiida_cfg
    aiida_cfg.AIIDA_CONFIG_FOLDER = path.join(temp_dir, '.aiida')
    aiida_cfg.create_base_dirs()
    return aiida_cfg.get_or_create_config()


def create_test_profile(temp_dir, db_fixture, backend):
    from aiida.common import setup as aiida_cfg
    from aiida.cmdline.verdilib import setup
    profile_name = 'test_profile'
    profile = {
        'backend': backend,
        'email': 'test@aiida.mail',
        'repo': path.join(temp_dir, 'test_repo'),
        'db_host': db_fixture.pg_test.dsn['host'],
        'db_port': db_fixture.pg_test.port,
        'db_user': db_fixture.pg_test.dsn['user'],
        'db_pass': db_fixture.DB_PASS,
        'db_name': db_fixture.DB_NAME,
        'first_name': 'AiiDA',
        'last_name': 'Tester',
        'institution': 'aiidateam'
    }
    setup(
        profile=profile_name,
        only_config=False,
        non_interactive=True,
        **profile)
    aiida_cfg.set_default_profile('verdi', profile_name)
    aiida_cfg.set_default_profile('daemon', profile_name)


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
        cls.db_fixture = DbFixture()
        assert cls.db_fixture.init_success()
        cls.temp_dir = setup_fs_env()
        cls.aiida_cfg = setup_aiida(cls.temp_dir)
        create_test_profile(cls.temp_dir, cls.db_fixture, cls.BACKEND)

    @classmethod
    def tearDownClass(cls):
        del cls.db_fixture
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
