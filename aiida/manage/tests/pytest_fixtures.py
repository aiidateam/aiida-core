# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name,unused-argument
"""Collection of ``pytest`` fixtures that are intended for use in plugin packages.

To use these fixtures, simply create a ``conftest.py`` in the tests folder and add the following line:

    pytest_plugins = ['aiida.manage.tests.pytest_fixtures']

This will make all the fixtures in this file available and ready for use. Simply use them as you would any other
``pytest`` fixture.
"""
from __future__ import annotations

import asyncio
import contextlib
import copy
import inspect
import io
import os
import pathlib
import shutil
import tempfile
import time
import typing as t
import uuid
import warnings

import plumpy
import pytest
import wrapt

from aiida import plugins
from aiida.common.exceptions import NotExistent
from aiida.common.lang import type_check
from aiida.common.log import AIIDA_LOGGER
from aiida.common.warnings import warn_deprecation
from aiida.engine import Process, ProcessBuilder, submit
from aiida.engine.daemon.client import DaemonClient
from aiida.manage import Config, Profile, get_manager, get_profile
from aiida.manage.manager import Manager
from aiida.orm import Computer, ProcessNode, User


def recursive_merge(left: dict[t.Any, t.Any], right: dict[t.Any, t.Any]) -> None:
    """Recursively merge the ``right`` dictionary into the ``left`` dictionary.

    :param left: Base dictionary.
    :param right: Dictionary to recurisvely merge on top of ``left`` dictionary.
    """
    for key, value in right.items():
        if (key in left and isinstance(left[key], dict) and isinstance(value, dict)):
            recursive_merge(left[key], value)
        else:
            left[key] = value


@pytest.fixture(scope='function')
def aiida_caplog(caplog):
    """A copy of pytest's caplog fixture, which allows ``AIIDA_LOGGER`` to propagate."""
    propogate = AIIDA_LOGGER.propagate
    AIIDA_LOGGER.propagate = True
    yield caplog
    AIIDA_LOGGER.propagate = propogate


@pytest.fixture(scope='session')
def postgres_cluster(
    database_name: str | None = None,
    database_username: str | None = None,
    database_password: str | None = None
) -> t.Generator[dict[str, str], None, None]:
    """Create a temporary and isolated PostgreSQL cluster using ``pgtest`` and cleanup after the yield.

    :param database_name: Name of the database.
    :param database_username: Username to use for authentication.
    :param database_password: Password to use for authentication.
    :returns: Dictionary with parameters to connect to the PostgreSQL cluster.
    """
    from pgtest.pgtest import PGTest

    from aiida.manage.external.postgres import Postgres

    postgres_config = {
        'database_engine': 'postgresql_psycopg2',
        'database_name': database_name or str(uuid.uuid4()),
        'database_username': database_username or 'guest',
        'database_password': database_password or 'guest',
    }

    try:
        cluster = PGTest()

        postgres = Postgres(interactive=False, quiet=True, dbinfo=cluster.dsn)
        postgres.create_dbuser(postgres_config['database_username'], postgres_config['database_password'], 'CREATEDB')
        postgres.create_db(postgres_config['database_username'], postgres_config['database_name'])

        postgres_config['database_hostname'] = postgres.host_for_psycopg2
        postgres_config['database_port'] = postgres.port_for_psycopg2

        yield postgres_config
    finally:
        cluster.close()


@pytest.fixture(scope='session')
def aiida_test_profile() -> str | None:
    """Return the name of the AiiDA test profile if defined.

    The name is taken from the ``AIIDA_TEST_PROFILE`` environment variable.

    :returns: The name of the profile to you for the test session or ``None`` if not defined.
    """
    return os.environ.get('AIIDA_TEST_PROFILE', None)


@pytest.fixture(scope='session')
def aiida_manager() -> Manager:
    """Return the global instance of the :class:`~aiida.manage.manager.Manager`.

    :returns: The global manager instance.
    """
    return get_manager()


@pytest.fixture(scope='session')
def aiida_instance(
    tmp_path_factory: pytest.TempPathFactory,
    aiida_manager: Manager,
    aiida_test_profile: str | None,
) -> t.Generator[Config, None, None]:
    """Return the :class:`~aiida.manage.configuration.config.Config` instance that is used for the test session.

    If an existing test profile is defined through the ``aiida_test_profile`` fixture, the configuration of the actual
    AiiDA instance is loaded and returned. If no test profile is defined, a completely independent and temporary AiiDA
    instance is generated in a temporary directory with a clean `.aiida` folder and basic configuration file. The
    currently loaded configuration and profile are stored in memory and are automatically restored at the end of the
    test session. The temporary instance is automatically deleted.

    :return: The configuration the AiiDA instance loaded for this test session.
    """
    from aiida.manage import configuration
    from aiida.manage.configuration import settings

    if aiida_test_profile:
        yield configuration.get_config()

    else:
        reset = False

        if configuration.CONFIG is not None:
            reset = True
            current_config = configuration.CONFIG
            current_config_path = current_config.dirpath
            current_profile = configuration.get_profile()
            current_path_variable = os.environ.get(settings.DEFAULT_AIIDA_PATH_VARIABLE, None)

        dirpath_config = tmp_path_factory.mktemp('config')
        os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE] = str(dirpath_config)
        settings.AIIDA_CONFIG_FOLDER = dirpath_config
        settings.set_configuration_directory()
        configuration.CONFIG = configuration.load_config(create=True)

        try:
            yield configuration.CONFIG
        finally:
            if reset:
                if current_path_variable is None:
                    os.environ.pop(settings.DEFAULT_AIIDA_PATH_VARIABLE, None)
                else:
                    os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE] = current_path_variable

                settings.AIIDA_CONFIG_FOLDER = current_config_path
                configuration.CONFIG = current_config
                if current_profile:
                    aiida_manager.load_profile(current_profile.name, allow_switch=True)


@pytest.fixture(scope='session')
def config_psql_dos(
    tmp_path_factory: pytest.TempPathFactory,
    postgres_cluster: dict[str, str],
) -> t.Callable[[dict[str, t.Any] | None], dict[str, t.Any]]:
    """Return a profile configuration for the :class:`~aiida.storage.psql_dos.backend.PsqlDosBackend`."""

    def factory(custom_configuration: dict[str, t.Any] | None = None) -> dict[str, t.Any]:
        """Return a profile configuration for the :class:`~aiida.storage.psql_dos.backend.PsqlDosBackend`.

        :param custom_configuration: Custom configuration to override default profile configuration.
        :returns: The profile configuration.
        """
        configuration = {
            'storage': {
                'backend': 'core.psql_dos',
                'config': {
                    **postgres_cluster,
                    'repository_uri': f'file://{tmp_path_factory.mktemp("repository")}',
                }
            }
        }
        recursive_merge(configuration, custom_configuration or {})
        return configuration

    return factory


def clear_profile():
    """Clear the currently loaded profile.

    This ensures that the contents of the profile are reset as well as the ``Manager``, which may hold references to
    data that will be destroyed. The daemon will also be stopped if it was running.
    """
    from aiida.engine.daemon.client import get_daemon_client

    daemon_client = get_daemon_client()

    if daemon_client.is_daemon_running:
        daemon_client.stop_daemon(wait=True)

    manager = get_manager()
    manager.get_profile_storage()._clear()  # pylint: disable=protected-access
    manager.reset_communicator()
    manager.reset_runner()

    User(get_manager().get_profile().default_user_email).store()


@pytest.fixture(scope='session')
def aiida_profile_factory(
    aiida_instance: Config,
    aiida_manager: Manager,
) -> t.Callable[[dict[str, t.Any]], Profile]:
    """Create a temporary profile, add it to the config of the loaded AiiDA instance and load the profile.

    The default configuration is complete except for the configuration of the storage, which should be provided through
    the ``custom_configuration`` argument. The storage will be fully reset and initalised, destroying all data that it
    contains and recreate the default user, making the profile ready for use.
    """

    def factory(custom_configuration: dict[str, t.Any]) -> Profile:
        """Create an isolated AiiDA instance with a temporary and fully loaded profile.

        :param custom_configuration: Custom configuration to override default profile configuration.
        :returns: The constructed profile.
        """
        config = aiida_instance
        configuration = {
            'default_user_email': 'test@aiida.local',
            'storage': {},
            'process_control': {
                'backend': 'rabbitmq',
                'config': {
                    'broker_protocol': 'amqp',
                    'broker_username': 'guest',
                    'broker_password': 'guest',
                    'broker_host': '127.0.0.1',
                    'broker_port': 5672,
                    'broker_virtual_host': '',
                }
            },
            'options': {
                'warnings.development_version': False,
                'warnings.rabbitmq_version': False,
            }
        }
        recursive_merge(configuration, custom_configuration or {})
        configuration['test_profile'] = True

        with contextlib.redirect_stdout(io.StringIO()):
            profile_name = str(uuid.uuid4())
            profile = Profile(profile_name, configuration)
            profile.storage_cls.initialise(profile, reset=True)

            config.add_profile(profile)
            config.set_default_profile(profile_name)
            config.store()

            aiida_manager.load_profile(profile_name, allow_switch=True)

            User(profile.default_user_email).store()

        # Add the ``clear_profile`` method, such that users can empty the storage through the ``Profile`` instance that
        # is returned by this fixture. This functionality is added for backwards-compatibility as before the fixture
        # used to return an instance of the :class:`~aiida.manage.tests.main.TestManager` which provided this method
        # that was often used.
        setattr(profile, 'clear_profile', clear_profile)

        return profile

    return factory


@pytest.fixture(scope='session', autouse=True)
def aiida_profile(
    aiida_manager: Manager,
    aiida_test_profile: str | None,
    aiida_profile_factory: t.Callable[[dict[str, t.Any] | None], Profile],
    config_psql_dos: t.Callable[[dict[str, t.Any] | None], dict[str, t.Any]],
) -> t.Generator[Profile, None, None]:
    """Return a loaded AiiDA test profile.

    If a test profile has been declared, as returned by the ``aiida_test_profile`` fixture, that is loaded and yielded.
    Otherwise, a temporary and fully isolated AiiDA instance is created, complete with a loaded test profile, that are
    all automatically cleaned up at the end of the test session. The storage backend used for the profile is
    :class:`~aiida.storage.psql_dos.backend.PsqlDosBackend`.
    """
    if aiida_test_profile is not None:
        aiida_manager.load_profile(aiida_test_profile)
        profile = get_profile()

        if profile is None:
            raise RuntimeError(f'could not load the `{aiida_test_profile}` test profile.')

        if not profile.is_test_profile:
            raise RuntimeError(f'specified test profile `{aiida_test_profile}` is not a test profile.')

        # Add the ``clear_profile`` method. See ``aiida_profile_factory`` for the reasoning. Note that since it is added
        # there, this only needs to be added here, for an existing test profile, because the temporarily created profile
        # will have it added by the ``aiida_profile_factory`` fixture itself.
        setattr(profile, 'clear_profile', clear_profile)
    else:
        profile = aiida_profile_factory(config_psql_dos({}))

    yield profile


@pytest.fixture(scope='function')
def aiida_profile_clean(aiida_profile):
    """Provide an AiiDA test profile, with the storage reset at test function setup."""
    aiida_profile.clear_profile()
    yield aiida_profile


@pytest.fixture(scope='class')
def aiida_profile_clean_class(aiida_profile):
    """Provide an AiiDA test profile, with the storage reset at test class setup."""
    aiida_profile.clear_profile()
    yield aiida_profile


@pytest.fixture(scope='function')
def clear_database(clear_database_after_test):
    """Alias for 'clear_database_after_test'.

    Clears the database after each test. Use of the explicit
    'clear_database_after_test' is preferred.
    """


@pytest.fixture(scope='function')
def clear_database_after_test(aiida_profile):
    """Clear the database after the test."""
    warn_deprecation('the clear_database_after_test fixture is deprecated, use aiida_profile_clean instead', version=3)
    yield aiida_profile
    aiida_profile.clear_profile()


@pytest.fixture(scope='function')
def clear_database_before_test(aiida_profile):
    """Clear the database before the test."""
    warn_deprecation('the clear_database_before_test fixture deprecated, use aiida_profile_clean instead', version=3)
    aiida_profile.clear_profile()
    yield aiida_profile


@pytest.fixture(scope='class')
def clear_database_before_test_class(aiida_profile):
    """Clear the database before a test class."""
    warn_deprecation(
        'the clear_database_before_test_class is deprecated, use aiida_profile_clean_class instead', version=3
    )
    aiida_profile.clear_profile()
    yield


@pytest.fixture(scope='function')
def temporary_event_loop():
    """Create a temporary loop for independent test case"""
    current = asyncio.get_event_loop()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield
    finally:
        loop.close()
        asyncio.set_event_loop(current)


@pytest.fixture(scope='function')
def temp_dir():
    """Get a temporary directory.

    E.g. to use as the working directory of an AiiDA computer.

    :return: The path to the directory
    :rtype: str

    """
    warn_deprecation('This fixture is deprecated, use the `tmp_path` fixture of `pytest` instead.', version=3)
    try:
        dirpath = tempfile.mkdtemp()
        yield dirpath
    finally:
        # after the test function has completed, remove the directory again
        shutil.rmtree(dirpath)


@pytest.fixture
def aiida_local_code_factory(aiida_localhost):
    """Get an AiiDA code on localhost.

    Searches in the PATH for a given executable and creates an AiiDA code with provided entry point.

    Usage::

      def test_1(aiida_local_code_factory):
          code = aiida_local_code_factory('quantumespresso.pw', '/usr/bin/pw.x')
          # use code for testing ...

    :return: A function get_code(entry_point, executable) that returns the `Code` node.
    :rtype: object
    """

    def get_code(entry_point, executable, computer=aiida_localhost, label=None, prepend_text=None, append_text=None):
        """Get local code.

        Sets up code for given entry point on given computer.

        :param entry_point: Entry point of calculation plugin
        :param executable: name of executable; will be searched for in local system PATH.
        :param computer: (local) AiiDA computer
        :param prepend_text: a string of code that will be put in the scheduler script before the execution of the code.
        :param append_text: a string of code that will be put in the scheduler script after the execution of the code.
        :return: the `Code` either retrieved from the database or created if it did not yet exist.
        :rtype: :py:class:`~aiida.orm.Code`
        """
        from aiida.common import exceptions
        from aiida.orm import InstalledCode, QueryBuilder

        if label is None:
            label = executable

        builder = QueryBuilder().append(Computer, filters={'uuid': computer.uuid}, tag='computer')
        builder.append(
            InstalledCode, filters={
                'label': label,
                'attributes.input_plugin': entry_point
            }, with_computer='computer'
        )

        try:
            code = builder.one()[0]
        except (exceptions.MultipleObjectsError, exceptions.NotExistent):
            code = None
        else:
            return code

        executable_path = shutil.which(executable)
        if not executable_path:
            raise ValueError(f'The executable "{executable}" was not found in the $PATH.')

        code = InstalledCode(
            label=label,
            description=label,
            default_calc_job_plugin=entry_point,
            computer=computer,
            filepath_executable=executable_path
        )

        if prepend_text is not None:
            code.prepend_text = prepend_text

        if append_text is not None:
            code.append_text = append_text

        return code.store()

    return get_code


@pytest.fixture(scope='session')
def ssh_key(tmp_path_factory) -> t.Generator[pathlib.Path, None, None]:
    """Generate a temporary SSH key pair for the test session and return the filepath of the private key.

    The filepath of the public key is the same as the private key, but it adds the ``.pub`` file extension.
    """
    from cryptography.hazmat.backends import default_backend as crypto_default_backend
    from cryptography.hazmat.primitives import serialization as crypto_serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=2048,
    )

    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption(),
    )

    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH,
    )

    dirpath = tmp_path_factory.mktemp('keys')
    filename = uuid.uuid4().hex
    filepath_private_key = dirpath / filename
    filepath_public_key = dirpath / f'{filename}.pub'

    filepath_private_key.write_bytes(private_key)
    filepath_public_key.write_bytes(public_key)

    try:
        yield filepath_private_key
    finally:
        filepath_private_key.unlink(missing_ok=True)
        filepath_public_key.unlink(missing_ok=True)


@pytest.fixture
def aiida_computer(tmp_path) -> t.Callable[[], Computer]:
    """Factory to return a :class:`aiida.orm.computers.Computer` instance."""

    def factory(
        label: str = None,
        minimum_job_poll_interval: int = 0,
        default_mpiprocs_per_machine: int = 1,
        configuration_kwargs: dict[t.Any, t.Any] = None,
        **kwargs
    ) -> Computer:
        """Return a :class:`aiida.orm.computers.Computer` instance.

        The database is queried for an existing computer with the given label. If it exists, it means it was probably
        created by this fixture in a previous call and it is simply returned. Otherwise a new instance is created.
        Note that the computer is not explicitly configured, unless ``configure_kwargs`` are specified.

        :param label: The computer label. If not specified, a random UUID4 is used.
        :param minimum_job_poll_interval: The default minimum job poll interval to set.
        :param configuration_kwargs: Optional keyword arguments that, if defined, are used to configure the computer
            by calling :meth:`aiida.orm.computers.Computer.configure`.
        :param kwargs: Optional keyword arguments that are passed to the :class:`aiida.orm.computers.Computer`
            constructor if a computer with the given label doesn't already exist.
        :return: A stored computer instance.
        """
        label = label or str(uuid.uuid4())

        try:
            computer = Computer.collection.get(label=label)
        except NotExistent:
            computer = Computer(
                label=label,
                description=kwargs.pop('description', 'computer created by `aiida_computer` fixture'),
                hostname=kwargs.pop('hostname', 'localhost'),
                workdir=kwargs.pop('workdir', str(tmp_path)),
                transport_type=kwargs.pop('transport_type', 'core.local'),
                scheduler_type=kwargs.pop('scheduler_type', 'core.direct'),
            )
            computer.store()
            computer.set_minimum_job_poll_interval(minimum_job_poll_interval)
            computer.set_default_mpiprocs_per_machine(default_mpiprocs_per_machine)

        if configuration_kwargs:
            computer.configure(**configuration_kwargs)

        return computer

    return factory


@pytest.fixture
def aiida_computer_local(aiida_computer) -> t.Callable[[], Computer]:
    """Factory to return a :class:`aiida.orm.computers.Computer` instance with ``core.local`` transport."""

    def factory(label: str = None, configure: bool = True) -> Computer:
        """Return a :class:`aiida.orm.computers.Computer` instance representing localhost with ``core.local`` transport.

        The database is queried for an existing computer with the given label. If it exists, it is returned, otherwise a
        new instance is created.

        :param label: The computer label. If not specified, a random UUID4 is used.
        :param configure: Boolean, if ``True``, ensures the computer is configured, otherwise the computer is returned
            as is. Note that if a computer with the given label already exists and it was configured before, the
            computer will not be "un-"configured. If an unconfigured computer is absolutely required, make sure to first
            delete the existing computer or specify another label.
        :return: A stored computer instance.
        """
        computer = aiida_computer(label=label, hostname='localhost', transport_type='core.local')

        if configure:
            computer.configure()

        return computer

    return factory


@pytest.fixture
def aiida_computer_ssh(aiida_computer, ssh_key) -> t.Callable[[], Computer]:
    """Factory to return a :class:`aiida.orm.computers.Computer` instance with ``core.ssh`` transport."""

    def factory(label: str = None, configure: bool = True) -> Computer:
        """Return a :class:`aiida.orm.computers.Computer` instance representing localhost with ``core.ssh`` transport.

        The database is queried for an existing computer with the given label. If it exists, it is returned, otherwise a
        new instance is created.

        If ``configure=True``, an SSH key pair is automatically added to the ``.ssh`` folder of the user, allowing an
        actual SSH connection to be made to the localhost.

        :param label: The computer label. If not specified, a random UUID4 is used.
        :param configure: Boolean, if ``True``, ensures the computer is configured, otherwise the computer is returned
            as is. Note that if a computer with the given label already exists and it was configured before, the
            computer will not be "un-"configured. If an unconfigured computer is absolutely required, make sure to first
            delete the existing computer or specify another label.
        :return: A stored computer instance.
        """
        computer = aiida_computer(label=label, hostname='localhost', transport_type='core.ssh')

        if configure:
            computer.configure(
                key_filename=str(ssh_key),
                key_policy='AutoAddPolicy',
            )

        return computer

    return factory


@pytest.fixture(scope='function')
def aiida_localhost(aiida_computer_local) -> Computer:
    """Return a :class:`aiida.orm.computers.Computer` instance representing localhost with ``core.local`` transport.

    Usage::

        def test(aiida_localhost):
            assert aiida_localhost.transport_type == 'core.local'

    :return: The computer.
    """
    return aiida_computer_local(label='localhost')


@pytest.fixture(scope='session')
def daemon_client(aiida_profile):
    """Return a daemon client for the configured test profile for the test session.

    The daemon will be automatically stopped at the end of the test session.
    """
    daemon_client = DaemonClient(aiida_profile)

    try:
        yield daemon_client
    finally:
        daemon_client.stop_daemon(wait=True)
        assert not daemon_client.is_daemon_running


@pytest.fixture()
def started_daemon_client(daemon_client):
    """Ensure that the daemon is running for the test profile and return the associated client."""
    if not daemon_client.is_daemon_running:
        daemon_client.start_daemon()
        assert daemon_client.is_daemon_running

    yield daemon_client


@pytest.fixture()
def stopped_daemon_client(daemon_client):
    """Ensure that the daemon is not running for the test profile and return the associated client."""
    if daemon_client.is_daemon_running:
        daemon_client.stop_daemon(wait=True)
        assert not daemon_client.is_daemon_running

    yield daemon_client


@pytest.fixture
def submit_and_await(started_daemon_client):
    """Submit a process and wait for it to achieve the given state."""

    def _factory(
        submittable: Process | ProcessBuilder | ProcessNode,
        state: plumpy.ProcessState = plumpy.ProcessState.FINISHED,
        timeout: int = 20,
        **kwargs
    ):
        """Submit a process and wait for it to achieve the given state.

        :param submittable: A process, a process builder or a process node. If it is a process or builder, it is
            submitted first before awaiting the desired state.
        :param state: The process state to wait for, by default it waits for the submittable to be ``FINISHED``.
        :param timeout: The time to wait for the process to achieve the state.
        :param kwargs: If the ``submittable`` is a process class, it is instantiated with the ``kwargs`` as inputs.
        :raises RuntimeError: If the process fails to achieve the specified state before the timeout expires.
        """
        if inspect.isclass(submittable) and issubclass(submittable, Process):
            node = submit(submittable, **kwargs)
        elif isinstance(submittable, ProcessBuilder):
            node = submit(submittable)
        elif isinstance(submittable, ProcessNode):
            node = submittable
        else:
            raise ValueError(f'type of submittable `{type(submittable)}` is not supported.')

        start_time = time.time()

        while node.process_state is not state:

            if node.is_excepted:
                raise RuntimeError(f'The process excepted: {node.exception}')

            if time.time() - start_time >= timeout:
                daemon_log_file = pathlib.Path(started_daemon_client.daemon_log_file).read_text(encoding='utf-8')
                daemon_status = 'running' if started_daemon_client.is_daemon_running else 'stopped'
                raise RuntimeError(
                    f'Timed out waiting for process with state `{node.process_state}` to enter state `{state}`.\n'
                    f'Daemon <{started_daemon_client.profile.name}|{daemon_status}> log file content: \n'
                    f'{daemon_log_file}'
                )

        return node

    return _factory


@wrapt.decorator
def suppress_deprecations(wrapped, _, args, kwargs):
    """Decorator that suppresses all ``DeprecationWarning``."""
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=DeprecationWarning)
        return wrapped(*args, **kwargs)


class EntryPointManager:
    """Manager to temporarily add or remove entry points."""

    @staticmethod
    def eps():
        return plugins.entry_point.eps()

    @staticmethod
    def _validate_entry_point(entry_point_string: str | None, group: str | None, name: str | None) -> tuple[str, str]:
        """Validate the definition of the entry point.

        :param entry_point_string: Fully qualified entry point string.
        :param name: Entry point name.
        :param group: Entry point group.
        :returns: The entry point group and name.
        :raises TypeError: If `entry_point_string`, `group` or `name` are not a string, when defined.
        :raises ValueError: If `entry_point_string` is not defined, nor a `group` and `name`.
        :raises ValueError: If `entry_point_string` is not a complete entry point string with group and name.
        """
        if entry_point_string is not None:
            try:
                group, name = plugins.entry_point.parse_entry_point_string(entry_point_string)
            except TypeError as exception:
                raise TypeError('`entry_point_string` should be a string when defined.') from exception
            except ValueError as exception:
                raise ValueError('invalid `entry_point_string` format, should `group:name`.') from exception

        if name is None or group is None:
            raise ValueError('neither `entry_point_string` is defined, nor `name` and `group`.')

        type_check(group, str)
        type_check(name, str)

        return group, name

    @suppress_deprecations
    def add(
        self,
        value: type | str,
        entry_point_string: str | None = None,
        *,
        name: str | None = None,
        group: str | None = None
    ) -> None:
        """Add an entry point.

        :param value: The class or function to register as entry point. The resource needs to be importable, so it can't
            be inlined. Alternatively, the fully qualified name can be passed as a string.
        :param entry_point_string: Fully qualified entry point string.
        :param name: Entry point name.
        :param group: Entry point group.
        :returns: The entry point group and name.
        :raises TypeError: If `entry_point_string`, `group` or `name` are not a string, when defined.
        :raises ValueError: If `entry_point_string` is not defined, nor a `group` and `name`.
        :raises ValueError: If `entry_point_string` is not a complete entry point string with group and name.
        """
        if not isinstance(value, str):
            value = f'{value.__module__}:{value.__name__}'

        group, name = self._validate_entry_point(entry_point_string, group, name)
        entry_point = plugins.entry_point.EntryPoint(name, value, group)
        self.eps()[group].append(entry_point)

    @suppress_deprecations
    def remove(
        self, entry_point_string: str | None = None, *, name: str | None = None, group: str | None = None
    ) -> None:
        """Remove an entry point.

        :param value: Entry point value, fully qualified import path name.
        :param entry_point_string: Fully qualified entry point string.
        :param name: Entry point name.
        :param group: Entry point group.
        :returns: The entry point group and name.
        :raises TypeError: If `entry_point_string`, `group` or `name` are not a string, when defined.
        :raises ValueError: If `entry_point_string` is not defined, nor a `group` and `name`.
        :raises ValueError: If `entry_point_string` is not a complete entry point string with group and name.
        """
        group, name = self._validate_entry_point(entry_point_string, group, name)

        for entry_point in self.eps()[group]:
            if entry_point.name == name:
                self.eps()[group].remove(entry_point)
                break
        else:
            raise KeyError(f'entry point `{name}` does not exist in group `{group}`.')


@pytest.fixture
def entry_points(monkeypatch) -> EntryPointManager:
    """Return an instance of the ``EntryPointManager`` which allows to temporarily add or remove entry points.

    This fixture creates a deep copy of the entry point cache returned by the :func:`aiida.plugins.entry_point.eps`
    method and then monkey patches that function to return the deepcopy. This ensures that the changes on the entry
    point cache performed during the test through the manager are undone at the end of the function scope.

    .. note:: This fixture does not use the ``suppress_deprecations`` decorator on purpose, but instead adds it manually
        inside the fixture's body. The reason is that otherwise all deprecations would be suppressed for the entire
        scope of the fixture, including those raised by the code run in the test using the fixture, which is not
        desirable.

    """
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=DeprecationWarning)
        eps_copy = copy.deepcopy(plugins.entry_point.eps())
    monkeypatch.setattr(plugins.entry_point, 'eps', lambda: eps_copy)
    yield EntryPointManager()
