###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Collection of ``pytest`` fixtures that are intended for internal use to ``aiida-core`` only.

Fixtures that are intended for use in plugin packages are kept in :mod:`aiida.manage.tests.pytest_fixtures`. They are
loaded in this file as well, such that they can also be used for the tests of ``aiida-core`` itself.
"""

from __future__ import annotations

import copy
import dataclasses
import os
import pathlib
import subprocess
import types
import typing as t
import warnings
from enum import Enum
from pathlib import Path

import click
import pytest

from aiida import get_profile, orm
from aiida.common.folders import Folder
from aiida.common.links import LinkType
from aiida.manage import get_manager
from aiida.manage.configuration import Profile, get_config, load_profile

try:
    from typing import ParamSpec
except ImportError:
    # Fallback for Python 3.9 and older
    from typing_extensions import ParamSpec  # type: ignore[assignment]

if t.TYPE_CHECKING:
    from aiida.manage.configuration.config import Config

pytest_plugins = ['aiida.tools.pytest_fixtures', 'sphinx.testing.fixtures']

P = ParamSpec('P')


class TestDbBackend(Enum):
    """Options for the '--db-backend' CLI argument when running pytest."""

    SQLITE = 'sqlite'
    PSQL = 'psql'


def pytest_collection_modifyitems(items, config):
    """Automatically generate markers for certain tests.

    Most notably, we add the 'presto' marker for all tests that
    are not marked with either requires_rmq or requires_psql.
    """
    filepath_psqldos = Path(__file__).parent / 'storage' / 'psql_dos'
    filepath_django = Path(__file__).parent / 'storage' / 'psql_dos' / 'migrations' / 'django_branch'
    filepath_sqla = Path(__file__).parent / 'storage' / 'psql_dos' / 'migrations' / 'sqlalchemy_branch'

    # If the user requested the SQLite backend, automatically skip incompatible tests
    if config.option.db_backend is TestDbBackend.SQLITE:
        if config.option.markexpr != '':
            # Don't overwrite markers that the user already provided via '-m ' cmdline argument
            config.option.markexpr += ' and (not requires_psql)'
        else:
            config.option.markexpr = 'not requires_psql'

    for item in items:
        filepath_item = Path(item.fspath)

        # Add 'nightly' marker to all tests in 'storage/psql_dos/migrations/<django|sqlalchemy>_branch'
        if filepath_item.is_relative_to(filepath_django) or filepath_item.is_relative_to(filepath_sqla):
            item.add_marker('nightly')

        # Add 'requires_rmq' for all tests that depend 'daemon_client' and its dependant fixtures
        if 'daemon_client' in item.fixturenames:
            item.add_marker('requires_rmq')

        # All tests in 'storage/psql_dos' require PostgreSQL
        if filepath_item.is_relative_to(filepath_psqldos):
            item.add_marker('requires_psql')

        # Add 'presto' marker to all tests that require neither PostgreSQL nor RabbitMQ services.
        markers = [marker.name for marker in item.iter_markers()]
        if 'requires_rmq' not in markers and 'requires_psql' not in markers and 'nightly' not in markers:
            item.add_marker('presto')


def db_backend_type(string):
    """Conversion function for the custom '--db-backend' pytest CLI option

    :param string: String provided by the user via CLI
    :returns: DbBackend enum corresponding to user input string
    """
    try:
        return TestDbBackend(string)
    except ValueError:
        msg = f"Invalid --db-backend option '{string}'\nMust be one of: {tuple(db.value for db in TestDbBackend)}"
        raise pytest.UsageError(msg)


def pytest_addoption(parser):
    parser.addoption(
        '--db-backend',
        action='store',
        default=TestDbBackend.SQLITE,
        required=False,
        help=f'Database backend to be used for tests {tuple(db.value for db in TestDbBackend)}',
        type=db_backend_type,
    )


@pytest.fixture(scope='session')
def aiida_profile(pytestconfig, aiida_config, aiida_profile_factory, config_psql_dos, config_sqlite_dos):
    """Create and load a profile with ``core.psql_dos`` as a storage backend and RabbitMQ as the broker.

    This overrides the ``aiida_profile`` fixture provided by ``aiida-core`` which runs with ``core.sqlite_dos`` and
    without broker. However, tests in this package make use of the daemon which requires a broker and the tests should
    be run against the main storage backend, which is ``core.sqlite_dos``.
    """
    marker_opts = pytestconfig.getoption('-m')
    db_backend = pytestconfig.getoption('--db-backend')

    # We use RabbitMQ broker by default unless 'presto' marker is specified
    broker = 'core.rabbitmq'
    if 'not requires_rmq' in marker_opts or 'presto' in marker_opts:
        broker = None

    if db_backend is TestDbBackend.SQLITE:
        storage = 'core.sqlite_dos'
        config = config_sqlite_dos()
    elif db_backend is TestDbBackend.PSQL:
        storage = 'core.psql_dos'
        config = config_psql_dos()
    else:
        # This should be unreachable
        raise ValueError(f'Invalid DB backend {db_backend}')

    with aiida_profile_factory(
        aiida_config, storage_backend=storage, storage_config=config, broker_backend=broker
    ) as profile:
        yield profile


@pytest.fixture()
def non_interactive_editor(request):
    """Fixture to patch default editor.

    We (ab)use the `os.environ['EDITOR']` variable to define an automated
    vim command in order to make an interactive command non-interactive

    :param request: the command to set for the editor that is to be called
    """
    os.environ['EDITOR'] = request.param
    os.environ['VISUAL'] = request.param


@pytest.fixture(scope='function')
def fixture_sandbox():
    """Return a `SandboxFolder`."""
    from aiida.common.folders import SandboxFolder

    with SandboxFolder() as folder:
        yield folder


@pytest.fixture
def generate_calc_job():
    """Fixture to construct a new `CalcJob` instance and call `prepare_for_submission` for testing `CalcJob` classes.

    The fixture will return the `CalcInfo` returned by `prepare_for_submission` and the temporary folder that was passed
    to it, into which the raw input files will have been written.
    """

    def _generate_calc_job(folder, entry_point_name, inputs=None, return_process=False):
        """Fixture to generate a mock `CalcInfo` for testing calculation jobs."""
        from aiida.engine.utils import instantiate_process
        from aiida.manage import get_manager
        from aiida.plugins import CalculationFactory

        inputs = inputs or {}
        manager = get_manager()
        runner = manager.get_runner()

        process_class = CalculationFactory(entry_point_name)
        process = instantiate_process(runner, process_class, **inputs)

        if return_process:
            return process

        return process.prepare_for_submission(folder)

    return _generate_calc_job


@pytest.fixture
def generate_work_chain():
    """Generate an instance of a `WorkChain`."""

    def _generate_work_chain(entry_point, inputs=None):
        """Generate an instance of a `WorkChain` with the given entry point and inputs.

        :param entry_point: entry point name of the work chain subclass.
        :param inputs: inputs to be passed to process construction.
        :return: a `WorkChain` instance.
        """
        from aiida.engine.utils import instantiate_process
        from aiida.manage import get_manager
        from aiida.plugins import WorkflowFactory

        inputs = inputs or {}
        process_class = WorkflowFactory(entry_point) if isinstance(entry_point, str) else entry_point
        runner = get_manager().get_runner()
        process = instantiate_process(runner, process_class, **inputs)

        return process

    return _generate_work_chain


@pytest.fixture
def generate_calcjob_node():
    """Generate an instance of a `CalcJobNode`."""
    from aiida.engine import ProcessState

    def _generate_calcjob_node(
        process_state: ProcessState = ProcessState.FINISHED,
        exit_status: int | None = None,
        entry_point: str | None = None,
        workdir: pathlib.Path | None = None,
    ):
        """Generate an instance of a `CalcJobNode`..

        :param process_state: state to set
        :param exit_status: optional exit status, will be set to `0` if `process_state` is `ProcessState.FINISHED`
        :return: a `CalcJobNode` instance.
        """
        from aiida.orm import CalcJobNode

        if process_state is ProcessState.FINISHED and exit_status is None:
            exit_status = 0

        calcjob_node = CalcJobNode(process_type=entry_point)
        calcjob_node.set_remote_workdir(workdir)

        return calcjob_node

    return _generate_calcjob_node


@pytest.fixture
def generate_calculation_node():
    """Generate an instance of a `CalculationNode`."""
    from aiida.engine import ProcessState

    def _generate_calculation_node(
        process_state: ProcessState = ProcessState.FINISHED,
        exit_status: int | None = None,
        entry_point: str | None = None,
        inputs: dict | None = None,
        outputs: dict | None = None,
        repository: pathlib.Path | None = None,
    ):
        """Generate an instance of a `CalculationNode`..

        :param process_state: state to set
        :param exit_status: optional exit status, will be set to `0` if `process_state` is `ProcessState.FINISHED`
        :return: a `CalculationNode` instance.
        """
        from aiida.orm import CalculationNode

        if process_state is ProcessState.FINISHED and exit_status is None:
            exit_status = 0

        calculation_node = CalculationNode(process_type=entry_point)
        calculation_node.set_process_state(process_state)

        if exit_status is not None:
            calculation_node.set_exit_status(exit_status)

        if repository is not None:
            calculation_node.base.repository.put_object_from_tree(repository)

        # For storing, need to first store the input nodes, then the CalculationNode, then the output nodes
        if inputs is not None:
            for input_label, input_node in inputs.items():
                calculation_node.base.links.add_incoming(
                    input_node,
                    link_type=LinkType.INPUT_CALC,
                    link_label=input_label,
                )

                input_node.store()

        if outputs is not None:
            # Need to first store CalculationNode before I can attach `created` outputs
            calculation_node.store()
            for output_label, output_node in outputs.items():
                output_node.base.links.add_incoming(
                    calculation_node, link_type=LinkType.CREATE, link_label=output_label
                )

                output_node.store()

        # Return unstored by default
        return calculation_node

    return _generate_calculation_node


@pytest.fixture
def isolated_config(monkeypatch):
    """Return a copy of the currently loaded config and set that as the loaded config.

    This allows a test to change the config during the test, and after the test the original config will be restored
    making the changes of the test fully temporary. In addition, the ``Config._backup`` method is monkeypatched to be a
    no-op in order to prevent that backup files are written to disk when the config is stored. Storing the config after
    changing it in tests maybe necessary if a command is invoked that will be reading the config from disk in another
    Python process and so doesn't have access to the loaded config in memory in the process that is running the test.
    """
    from aiida.manage import configuration
    from aiida.manage.configuration.config import Config

    monkeypatch.setattr(Config, '_backup', lambda *args, **kwargs: None)

    current_config = configuration.CONFIG
    configuration.CONFIG = copy.deepcopy(current_config)
    configuration.CONFIG.set_default_profile(configuration.get_profile().name, overwrite=True)

    try:
        yield configuration.CONFIG
    finally:
        configuration.CONFIG = current_config
        configuration.CONFIG.store()


@pytest.fixture
def empty_config(tmp_path) -> Config:
    """Create a temporary configuration instance.

    This creates a temporary directory with a clean `.aiida` folder and basic configuration file. The currently loaded
    configuration and profile are stored in memory and are automatically restored at the end of this context manager.

    :return: a new empty config instance.
    """
    from aiida.common.utils import Capturing
    from aiida.manage import configuration
    from aiida.manage.configuration.settings import AiiDAConfigDir

    manager = get_manager()

    # Store the current configuration instance and config directory path
    current_config = configuration.CONFIG
    current_config_path = current_config.dirpath
    current_profile_name = configuration.get_profile().name

    manager.unload_profile()
    configuration.CONFIG = None

    # Set the configuration directory to a temporary directory. This will create the necessary folders for an empty
    # AiiDA configuration and set relevant global variables in :mod:`aiida.manage.configuration.settings`.
    AiiDAConfigDir.set(tmp_path)

    # The constructor of `Config` called by `load_config` will print warning messages about migrating it
    with Capturing():
        configuration.CONFIG = configuration.load_config(create=True)

    try:
        yield get_config()
    finally:
        # Reset the config folder path and the config instance. Note this will always be executed after the yield no
        # matter what happened in the test that used this fixture.
        manager.unload_profile()
        configuration.CONFIG = current_config

        # This sets important global constants that are based on the location of the config folder. Without it, things
        # like the :class:`aiida.engine.daemon.client.DaemonClient` will not function properly after a test that uses
        # this fixture because the paths of the daemon files would still point to the path of the temporary config
        # folder created by this fixture.
        AiiDAConfigDir.set(pathlib.Path(current_config_path))

        # Reload the original profile
        manager.load_profile(current_profile_name)


@pytest.fixture  # type: ignore[misc]
def profile_factory() -> t.Callable[t.Concatenate[str, P], Profile]:
    """Create a new profile instance.

    :return: the profile instance.
    """

    def _create_profile(name='test-profile', **kwargs) -> Profile:
        repository_dirpath = kwargs.pop('repository_dirpath', get_config().dirpath)

        profile_dictionary = {
            'default_user_email': kwargs.pop('default_user_email', 'dummy@localhost'),
            'storage': {
                'backend': kwargs.pop('storage_backend', 'core.psql_dos'),
                'config': {
                    'database_engine': kwargs.pop('database_engine', 'postgresql_psycopg'),
                    'database_hostname': kwargs.pop('database_hostname', 'localhost'),
                    'database_port': kwargs.pop('database_port', 5432),
                    'database_name': kwargs.pop('database_name', name),
                    'database_username': kwargs.pop('database_username', 'user'),
                    'database_password': kwargs.pop('database_password', 'pass'),
                    'repository_uri': f"file:///{os.path.join(repository_dirpath, f'repository_{name}')}",
                },
            },
            'process_control': {
                'backend': kwargs.pop('process_control_backend', 'rabbitmq'),
                'config': {
                    'broker_protocol': kwargs.pop('broker_protocol', 'amqp'),
                    'broker_username': kwargs.pop('broker_username', 'guest'),
                    'broker_password': kwargs.pop('broker_password', 'guest'),
                    'broker_host': kwargs.pop('broker_host', 'localhost'),
                    'broker_port': kwargs.pop('broker_port', 5672),
                    'broker_virtual_host': kwargs.pop('broker_virtual_host', ''),
                    'broker_parameters': kwargs.pop('broker_parameters', {}),
                },
            },
            'test_profile': kwargs.pop('test_profile', True),
        }

        return Profile(name, profile_dictionary)

    return _create_profile


@pytest.fixture
def config_with_profile_factory(empty_config, profile_factory) -> Config:
    """Create a temporary configuration instance with one profile.

    This fixture builds on the `empty_config` fixture, to add a single profile.

    The defaults of the profile can be overridden in the callable, as well as whether it should be set as default.

    Example::

        def test_config_with_profile(config_with_profile_factory):
            config = config_with_profile_factory(name='default', set_as_default=True, load=True)
            assert get_profile().name == 'default'

    As with `empty_config`, the currently loaded configuration and profile are stored in memory,
    and are automatically restored at the end of this context manager.

    This fixture should be used by tests that modify aspects of the AiiDA configuration or profile
    and require a preconfigured profile, but do not require an actual configured database.
    """

    def _config_with_profile_factory(set_as_default=True, load=True, name='default', **kwargs):
        """Create a temporary configuration instance with one profile.

        :param set_as_default: whether to set the one profile as the default.
        :param load: whether to load the profile.
        :param name: the profile name
        :param kwargs: parameters that are forwarded to the `Profile` constructor.

        :return: a config instance with a configured profile.
        """
        profile = profile_factory(name=name, **kwargs)
        config = empty_config
        config.add_profile(profile)

        if set_as_default:
            config.set_default_profile(profile.name, overwrite=True)

        config.store()

        if load:
            load_profile(profile.name)

        return config

    return _config_with_profile_factory


@pytest.fixture
def config_with_profile(config_with_profile_factory):
    """Create a temporary configuration instance with one default, loaded profile."""
    yield config_with_profile_factory()


@pytest.fixture
def manager():
    """Get the ``Manager`` instance of the currently loaded profile."""

    return get_manager()


@pytest.fixture
def runner(manager):
    """Get the ``Runner`` instance of the currently loaded profile."""
    return manager.get_runner()


@pytest.fixture
def event_loop(manager, aiida_profile_clean):
    """Get the event loop instance of a cleaned profile.
    This works, because ``aiida_profile_clean`` fixture, apart from loading a profile and cleaning it,
    and also triggers ``manager.reset_profile()`` which clears the event loop.

    This is automatically called as a fixture for any test marked with ``@pytest.mark.asyncio``.
    """
    yield manager.get_runner().loop


@pytest.fixture
def backend(manager):
    """Get the ``Backend`` storage instance of the currently loaded profile."""
    return manager.get_profile_storage()


@pytest.fixture
def communicator(manager):
    """Get the ``Communicator`` instance of the currently loaded profile to communicate with RabbitMQ."""
    return manager.get_communicator()


@pytest.fixture
def default_user():
    """Return the default user."""
    from aiida.orm import User

    return User.collection.get_default()


@pytest.fixture(scope='function')
def override_logging(isolated_config):
    """Temporarily override the log level for the AiiDA logger and the database log handler to ``DEBUG``.

    The changes are made by changing the configuration options ``logging.aiida_loglevel`` and ``logging.db_loglevel``.
    To ensure the changes are temporary, the are made on an isolated temporary configuration.
    """
    from aiida.common.log import configure_logging

    try:
        isolated_config.set_option('logging.aiida_loglevel', 'DEBUG')
        isolated_config.set_option('logging.db_loglevel', 'DEBUG')
        configure_logging(with_orm=True)
        yield
    finally:
        isolated_config.unset_option('logging.aiida_loglevel')
        isolated_config.unset_option('logging.db_loglevel')
        configure_logging(with_orm=True)


@pytest.fixture
def suppress_internal_deprecations():
    """Suppress all internal deprecations.

    Warnings emmitted of type :class:`aiida.common.warnings.AiidaDeprecationWarning` for the duration of the test.
    """
    from aiida.common.warnings import AiidaDeprecationWarning

    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=AiidaDeprecationWarning)
        yield


@pytest.fixture(scope='function')
def chdir_tmp_path(request, tmp_path):
    """Change to a temporary directory before running the test and reverting to original working directory."""
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(request.config.invocation_dir)


def cli_command_map() -> dict[click.Command, list[str]]:
    """Return a map of all ``verdi`` subcommands and their path in the command tree."""
    from aiida.cmdline.commands.cmd_verdi import verdi

    def recurse_commands(ctx, command: click.Command, breadcrumbs: list[str] | None = None):
        """Recursively return all subcommands that are part of ``command``.

        :param command: The click command to start with.
        :param parents: A list of strings that represent the parent commands leading up to the current command.
        :returns: A list of strings denoting the full path to the current command.
        """
        breadcrumbs = (breadcrumbs or []) + [command.name]

        yield command, breadcrumbs

        if isinstance(command, click.Group):
            for command_name in command.commands:
                yield from recurse_commands(ctx, command.get_command(ctx, command_name), breadcrumbs)

    ctx = click.Context(verdi)
    command_map = {}

    for command, breadcrumbs in recurse_commands(ctx, verdi):
        command_map[command] = breadcrumbs

    return command_map


@dataclasses.dataclass
class CliResult:
    """Dataclass representing the result of a command line interface invocation."""

    stderr_bytes: bytes
    stdout_bytes: bytes
    exc_info: tuple[t.Type[BaseException], BaseException, types.TracebackType] | tuple[None, None, None] = (
        None,
        None,
        None,
    )
    exception: BaseException | None = None
    exit_code: int | None = 0

    @property
    def stdout(self) -> str:
        """Return the output that was written to stdout."""
        return self.stdout_bytes.decode('utf-8', 'replace').replace('\r\n', '\n')

    @property
    def stderr(self) -> str:
        """Return the output that was written to stderr."""
        return self.stderr_bytes.decode('utf-8', 'replace').replace('\r\n', '\n')

    @property
    def output(self) -> str:
        """Return the output that was written to stdout."""
        return self.stdout + self.stderr

    @property
    def output_lines(self) -> list[str]:
        """Return the output that was written to stdout as a list of lines."""
        return [line for line in self.output.split('\n') if line.strip()]


@pytest.fixture
def run_cli_command(reset_log_level, aiida_config, aiida_profile):
    """Run a ``click`` command with the given options.

    The call will raise if the command triggered an exception or the exit code returned is non-zero.
    """

    def factory(
        command: click.Command,
        parameters: list[str] | None = None,
        user_input: str | bytes | t.IO | None = None,
        raises: bool = False,
        use_subprocess: bool = False,
        suppress_warnings: bool = False,
        initialize_ctx_obj: bool = True,
        **kwargs,
    ) -> CliResult:
        """Run the command and check the result.

        :param command: The base command to invoke.
        :param parameters: The command line parameters to pass to the invocation.
        :param user_input: string with data to be provided at the prompt. Can include newline characters to simulate
            responses to multiple prompts.
        :param raises: Boolean, if ``True``, the command should raise an exception.
        :param use_subprocess: Boolean, if ``True``, runs the command in a subprocess, otherwise it is run in the same
            interpreter using :class:`click.testing.CliRunner`. The advantage of running in a subprocess is that it
            simulates exactly what a user would invoke through the CLI. The test runner provided by ``click`` invokes
            commands in a way that is not always a 100% analogous to an actual CLI call and so tests may not cover the
            exact behavior. The direct reason for adding this argument was when a bug was introduced that was not caught
            because of this problem. The changes made by the command to the database were properly added to the session
            but were never flushed to the database, meaning the changes were not persisted. This was not caught by the
            test runner, since the test saw the correct changes but didn't know they wouldn't be persisted. Finally, if
            a test monkeypatches the behavior of code that is called by the command being tested, then a subprocess
            cannot be used, since the monkeypatch only applies to the current interpreter. In these cases it is
            necessary to set ``use_subprocesses = False``.
        :param suppress_warnings: Boolean, if ``True``, the ``PYTHONWARNINGS`` environment variable is set to
            ``ignore::Warning``. This is important when testing a command using ``use_subprocess = True`` and the check
            on the output is very strict. By running in a sub process, any warnings that are emitted by the code will be
            shown since they have not already been hit as would be the case when running the test through the test
            runner in this interpreter.
        :param initialize_ctx_obj: Boolean, if ``True``, the custom ``obj`` attribute of the ``ctx`` is initialized when
            ``use_subprocess == False``. When invoking the ``verdi`` command from the command line (and when running
            tests with ``use_subprocess == True``), this is done by the ``VerdiContext``, but when using the test runner
            in this interpreter, the object has to be initialized manually and passed to the test runner. In certain
            cases, however, this initialization should not be done, to simulate for example the absence of a loaded
            profile.
        :returns: Instance of ``CliResult``.
        :raises AssertionError: If ``raises == True`` and the command didn't except, or if ``raises == True`` and the
            the command did except.
        """
        # Cast all elements in ``parameters`` to strings as that is required by ``subprocess.run``.
        parameters = [str(param) for param in parameters or []]

        try:
            config_show_deprecations = aiida_config.get_option('warnings.showdeprecations')

            if config_show_deprecations and suppress_warnings:
                aiida_config.set_option('warnings.showdeprecations', False)
                if use_subprocess:
                    aiida_config.store()

            if use_subprocess:
                result = run_cli_command_subprocess(
                    command, parameters, user_input, aiida_profile.name, suppress_warnings
                )
            else:
                result = run_cli_command_runner(command, parameters, user_input, initialize_ctx_obj, kwargs)

            if raises:
                assert result.exception is not None, result.output
                assert result.exit_code != 0, result.exit_code
            else:
                import traceback

                assert result.exception is None, ''.join(traceback.format_exception(*result.exc_info))
                assert result.exit_code == 0, (result.exit_code, result.stderr)
        finally:
            if config_show_deprecations and suppress_warnings:
                aiida_config.set_option('warnings.showdeprecations', config_show_deprecations)
                if use_subprocess:
                    aiida_config.store()

        return result

    return factory


def run_cli_command_subprocess(command, parameters, user_input, profile_name, suppress_warnings):
    """Run CLI command through ``subprocess``."""
    import subprocess
    import sys

    env = os.environ.copy()
    command_path = cli_command_map()[command]
    args = command_path[:1] + ['-p', profile_name] + command_path[1:] + parameters

    if suppress_warnings:
        env['PYTHONWARNINGS'] = 'ignore::Warning'
        # Need to explicitly remove the ``AIIDA_WARN_v3`` variable as this will trigger ``AiidaDeprecationWarning`` to
        # be emitted by the ``aiida.common.warnings.warn_deprecation`` method and for an unknown reason these are not
        # affected by the ``ignore::Warning`` setting.
        env.pop('AIIDA_WARN_v3', None)

    try:
        completed_process = subprocess.run(
            args, capture_output=True, check=True, input=user_input.encode('utf-8') if user_input else None, env=env
        )
    except subprocess.CalledProcessError as exception:
        result = CliResult(
            exc_info=sys.exc_info(),
            exception=exception,
            exit_code=exception.returncode,
            stderr_bytes=exception.stderr,
            stdout_bytes=exception.stdout,
        )
    else:
        result = CliResult(
            stderr_bytes=completed_process.stderr,
            stdout_bytes=completed_process.stdout,
        )

    return result


def run_cli_command_runner(command, parameters, user_input, initialize_ctx_obj, kwargs):
    """Run CLI command through ``click.testing.CliRunner``."""
    from click.testing import CliRunner

    from aiida.cmdline.commands.cmd_verdi import VerdiCommandGroup
    from aiida.cmdline.groups.verdi import LazyVerdiObjAttributeDict

    if initialize_ctx_obj:
        config = get_config()
        profile = get_profile()
        obj = LazyVerdiObjAttributeDict(None, {'config': config})
        if profile is not None:
            obj.profile = profile
    else:
        obj = None

    # We need to apply the ``VERBOSITY`` option. When invoked through the command line, this is done by the logic of the
    # ``VerdiCommandGroup``, but when testing commands, the command is retrieved directly from the module which
    # circumvents this machinery.
    command = VerdiCommandGroup.add_verbosity_option(command)

    try:
        runner = CliRunner(mix_stderr=False)
    except TypeError:
        # click >=8.2.0
        runner = CliRunner()
    result = runner.invoke(command, parameters, input=user_input, obj=obj, **kwargs)
    return CliResult(
        exc_info=result.exc_info or (None, None, None),
        exception=result.exception,
        exit_code=result.exit_code,
        stderr_bytes=result.stderr_bytes or b'',
        stdout_bytes=result.stdout_bytes,
    )


@pytest.fixture
def reset_log_level():
    """Reset the ``CLI_LOG_ACTIVE`` and ``CLI_LOG_LEVEL`` globals in ``aiida.common.log`` and reconfigure the logging.

    This fixture should be used by tests that will change these globals, for example, through the
    :class:`~aiida.cmdline.params.options.main.VERBOSITY` option in a CLI command invocation.
    """
    from aiida.common import log

    try:
        yield
    finally:
        log.CLI_ACTIVE = None
        log.CLI_LOG_LEVEL = None
        log.configure_logging(with_orm=True)


@pytest.fixture
def generate_calculation_node_add(aiida_localhost):
    def _generate_calculation_node_add():
        from aiida.engine import run_get_node
        from aiida.orm import InstalledCode, Int
        from aiida.plugins import CalculationFactory

        arithmetic_add = CalculationFactory('core.arithmetic.add')

        add_inputs = {
            'x': Int(1),
            'y': Int(2),
            'code': InstalledCode(computer=aiida_localhost, filepath_executable='/bin/bash'),
        }

        _, add_node = run_get_node(arithmetic_add, **add_inputs)

        return add_node

    return _generate_calculation_node_add


@pytest.fixture(scope='class')
def construct_calculation_node_add(tmp_path_factory):
    def _construct_calculation_node_add(x: int = 1, y: int = 2):
        import json
        import textwrap

        from aiida.common import LinkType
        from aiida.orm import CalcJobNode, Computer, FolderData, InstalledCode, Int

        # Create a minimal computer
        # Not using any of the `aiida_localhost` or `aiida_computer_local` fixtures as they are function-scoped
        created, computer = Computer.collection.get_or_create(
            label='mock_computer', hostname='localhost', transport_type='core.local', scheduler_type='core.direct'
        )
        if created:
            computer.store()

        # Create the calculation node
        calc_node = CalcJobNode(computer=computer)

        # Create input nodes
        x_node = Int(x)
        y_node = Int(y)
        code_node = InstalledCode(computer=computer, filepath_executable='/bin/bash')

        # Store input nodes
        x_node.store()
        y_node.store()
        code_node.store()

        # Input files
        input_content = f'echo $(({x} + {y}))\n'
        calc_node.base.repository.put_object_from_bytes(input_content.encode(), 'aiida.in')

        # .aiida folder content
        calcinfo_dict = {
            'codes_info': [{'stdin_name': 'aiida.in', 'stdout_name': 'aiida.out', 'code_uuid': code_node.uuid}],
            'retrieve_list': ['aiida.out', '_scheduler-stdout.txt', '_scheduler-stderr.txt'],
            'uuid': calc_node.uuid,
            'file_copy_operation_order': [2, 0, 1],
        }

        job_tmpl_dict = {
            'submit_as_hold': False,
            'rerunnable': False,
            'job_name': 'aiida-42',
            'sched_output_path': '_scheduler-stdout.txt',
            'shebang': '#!/bin/bash',
            'sched_error_path': '_scheduler-stderr.txt',
            'sched_join_files': False,
            'prepend_text': '',
            'append_text': '',
            'job_resource': {
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1,
                'num_cores_per_machine': None,
                'num_cores_per_mpiproc': None,
                'tot_num_mpiprocs': 1,
            },
            'codes_info': [
                {
                    'prepend_cmdline_params': [],
                    'cmdline_params': ['/usr/bin/bash'],
                    'use_double_quotes': [False, False],
                    'wrap_cmdline_params': False,
                    'stdin_name': 'aiida.in',
                    'stdout_name': 'aiida.out',
                    'stderr_name': None,
                    'join_files': False,
                }
            ],
            'codes_run_mode': 0,
            'import_sys_environment': True,
            'job_environment': {},
            'environment_variables_double_quotes': False,
            'max_memory_kb': None,
            'max_wallclock_seconds': 3600,
        }

        calc_node.base.repository.put_object_from_bytes(
            json.dumps(calcinfo_dict, indent=4).encode(), '.aiida/calcinfo.json'
        )
        calc_node.base.repository.put_object_from_bytes(
            json.dumps(job_tmpl_dict, indent=4).encode(), '.aiida/job_tmpl.json'
        )

        # Submit script
        submit_script = textwrap.dedent("""\
            #!/bin/bash
            exec > _scheduler-stdout.txt
            exec 2> _scheduler-stderr.txt

            '/usr/bin/bash' < 'aiida.in' > 'aiida.out'
        """)

        calc_node.base.repository.put_object_from_bytes(submit_script.encode(), '_aiidasubmit.sh')

        # Store CalcInfo in node attributes
        calc_node.base.attributes.set('input_filename', 'aiida.in')
        calc_node.base.attributes.set('output_filename', 'aiida.out')

        # Add input links
        calc_node.base.links.add_incoming(x_node, link_type=LinkType.INPUT_CALC, link_label='x')
        calc_node.base.links.add_incoming(y_node, link_type=LinkType.INPUT_CALC, link_label='y')
        calc_node.base.links.add_incoming(code_node, link_type=LinkType.INPUT_CALC, link_label='code')

        # Must store CalcjobNode before I can add output files
        calc_node.store()

        # Create FolderData node for retrieved
        retrieved_folder = FolderData()
        output_content = f'{x+y}\n'.encode()
        retrieved_folder.put_object_from_bytes(output_content, 'aiida.out')

        scheduler_stdout = '\n'.encode()
        scheduler_stderr = '\n'.encode()
        retrieved_folder.base.repository.put_object_from_bytes(scheduler_stdout, '_scheduler-stdout.txt')
        retrieved_folder.base.repository.put_object_from_bytes(scheduler_stderr, '_scheduler-stderr.txt')
        retrieved_folder.store()

        retrieved_folder.base.links.add_incoming(calc_node, link_type=LinkType.CREATE, link_label='retrieved')

        # Create and link output node (sum)
        output_node = Int(x + y)
        output_node.store()
        output_node.base.links.add_incoming(calc_node, link_type=LinkType.CREATE, link_label='sum')

        # Set process properties
        calc_node.set_process_state('finished')
        calc_node.set_process_label('ArithmeticAddCalculation')
        calc_node.set_process_type('aiida.calculations:core.arithmetic.add')
        calc_node.set_exit_status(0)

        return calc_node

    return _construct_calculation_node_add


@pytest.fixture
def generate_workchain_multiply_add(aiida_localhost):
    def _generate_workchain_multiply_add():
        from aiida.engine import run_get_node
        from aiida.orm import InstalledCode, Int
        from aiida.plugins import WorkflowFactory

        multiplyaddworkchain = WorkflowFactory('core.arithmetic.multiply_add')

        multiply_add_inputs = {
            'x': Int(1),
            'y': Int(2),
            'z': Int(3),
            'code': InstalledCode(computer=aiida_localhost, filepath_executable='/bin/bash'),
        }

        _, multiply_add_node = run_get_node(multiplyaddworkchain, **multiply_add_inputs)

        return multiply_add_node

    return _generate_workchain_multiply_add


@pytest.fixture
def create_file_hierarchy():
    """Create a file hierarchy in the target location.

    .. note:: empty directories are ignored and are not created explicitly.

    :param hierarchy: mapping with directory structure, e.g. returned by ``serialize_file_hierarchy``.
    :param target: the target where the hierarchy should be created.
    """

    def _create_file_hierarchy(hierarchy: t.Dict, target: t.Union[pathlib.Path, Folder]) -> None:
        for filename, value in hierarchy.items():
            if isinstance(value, dict):
                if isinstance(target, pathlib.Path):
                    _create_file_hierarchy(value, target / filename)
                elif isinstance(target, Folder):
                    _create_file_hierarchy(value, target.get_subfolder(filename, create=True))
                else:
                    raise TypeError('target must be either a `Path` or a `Folder` instance.')

            elif isinstance(target, pathlib.Path):
                target.mkdir(parents=True, exist_ok=True)
                (target / filename).write_text(value)

            elif isinstance(target, Folder):
                with target.open(filename, 'w') as handle:
                    handle.write(value)
            else:
                raise TypeError('target must be either a `Path` or a `Folder` instance.')

    return _create_file_hierarchy


@pytest.fixture
def serialize_file_hierarchy():
    """Serialize the file hierarchy at ``dirpath``.

    .. note:: empty directories are ignored.

    :param dirpath: the base path.
    :return: a mapping representing the file hierarchy, where keys are filenames. The leafs correspond to files and the
        values are the text contents.
    """

    def factory(dirpath: pathlib.Path, read_bytes=True) -> dict:
        serialized = {}

        for root, _, files in os.walk(dirpath):
            for filepath in files:
                relpath = pathlib.Path(root).relative_to(dirpath)
                subdir = serialized
                if relpath.parts:
                    for part in relpath.parts:
                        subdir = subdir.setdefault(part, {})
                if read_bytes:
                    subdir[filepath] = (pathlib.Path(root) / filepath).read_bytes()
                else:
                    subdir[filepath] = (pathlib.Path(root) / filepath).read_text()

        return serialized

    return factory


@pytest.fixture(scope='session')
def bash_path() -> Path:
    run_process = subprocess.run(['which', 'bash'], capture_output=True, check=True)
    path = run_process.stdout.decode('utf-8').strip()
    return Path(path)


@pytest.fixture(scope='session')
def cat_path() -> Path:
    run_process = subprocess.run(['which', 'cat'], capture_output=True, check=True)
    path = run_process.stdout.decode('utf-8').strip()
    return Path(path)


@pytest.fixture
def generate_calculation_node_io(generate_calculation_node, tmp_path):
    def _generate_calculation_node_io(entry_point: str | None = None, attach_outputs: bool = True):
        import io

        import numpy as np

        from aiida.orm import ArrayData, FolderData, SinglefileData

        filename = 'file.txt'
        filecontent = 'a'
        singlefiledata_linklabel = 'singlefile'
        folderdata_linklabel = 'folderdata'
        folderdata_relpath = Path('relative_path')
        arraydata_linklabel = 'arraydata'

        singlefiledata_input = SinglefileData.from_string(content=filecontent, filename=filename)
        # ? Use instance for folderdata
        folderdata = FolderData()
        folderdata.put_object_from_filelike(handle=io.StringIO(filecontent), path=str(folderdata_relpath / filename))  # type: ignore[arg-type]
        arraydata_input = ArrayData(arrays=np.ones(3))

        # Create calculation inputs, outputs
        calculation_node_inputs = {
            singlefiledata_linklabel: singlefiledata_input,
            folderdata_linklabel: folderdata,
            arraydata_linklabel: arraydata_input,
        }

        singlefiledata_output = singlefiledata_input.clone()
        folderdata_output = folderdata.clone()

        if attach_outputs:
            calculation_outputs = {
                folderdata_linklabel: folderdata_output,
                singlefiledata_linklabel: singlefiledata_output,
            }
        else:
            calculation_outputs = None

        # Actually write repository file and then read it in when generating calculation_node
        (tmp_path / filename).write_text(filecontent)

        calculation_node = generate_calculation_node(
            repository=tmp_path,
            inputs=calculation_node_inputs,
            outputs=calculation_outputs,
            entry_point=entry_point,
        )
        return calculation_node

    return _generate_calculation_node_io


@pytest.fixture
def generate_workchain_node_io():
    def _generate_workchain_node_io(cj_nodes, store_all: bool = True, seal_all: bool = True):
        """Generate an instance of a `WorkChain` that contains a sub-`WorkChain` and a `Calculation` with file io."""
        from aiida.orm import WorkflowNode

        wc_node = WorkflowNode()
        wc_node_sub = WorkflowNode()

        # Add sub-workchain that calls a calculation
        wc_node_sub.base.links.add_incoming(wc_node, link_type=LinkType.CALL_WORK, link_label='sub_workflow')
        for cj_node in cj_nodes:
            cj_node.base.links.add_incoming(wc_node_sub, link_type=LinkType.CALL_CALC, link_label='calculation')

        # Set process_state so that tests don't throw exception for build_call_graph of README generation
        [cj_node.set_process_state('finished') for cj_node in cj_nodes]
        wc_node.set_process_state('finished')
        wc_node_sub.set_process_state('finished')

        # Need to store/seal (?) so that outputs are being dumped
        if seal_all:
            wc_node.seal()
            wc_node_sub.seal()
            [cj_node.seal() for cj_node in cj_nodes]
            [node.seal() for node in wc_node.called_descendants]

        if store_all:
            wc_node.store()
            wc_node_sub.store()
            [cj_node.store() for cj_node in cj_nodes]
            [node.store() for node in wc_node.called_descendants]

        return wc_node

    return _generate_workchain_node_io


@pytest.fixture()
def setup_no_process_group() -> orm.Group:
    no_process_group, _ = orm.Group.collection.get_or_create(label='no-process-group')
    if no_process_group.is_empty:
        int_node = orm.Int(1).store()
        no_process_group.add_nodes([int_node])
    return no_process_group


# TODO: Add possibility to parametrize with number of nodes created (make factory?)
@pytest.fixture()
def setup_add_group(generate_calculation_node_add) -> orm.Group:
    add_group, _ = orm.Group.collection.get_or_create(label='add-group')
    if add_group.is_empty:
        add_node = generate_calculation_node_add()
        add_group.add_nodes([add_node])
    return add_group


@pytest.fixture()
def setup_multiply_add_group(generate_workchain_multiply_add) -> orm.Group:
    multiply_add_group, _ = orm.Group.collection.get_or_create(label='multiply-add-group')
    if multiply_add_group.is_empty:
        multiply_add_node = generate_workchain_multiply_add()
        multiply_add_group.add_nodes([multiply_add_node])
    return multiply_add_group


@pytest.fixture()
def setup_duplicate_group():
    def _setup_duplicate_group(source_group: orm.Group, dest_group_label: str):
        dupl_group, created = orm.Group.collection.get_or_create(label=dest_group_label)
        dupl_group.add_nodes(list(source_group.nodes))
        return dupl_group

    return _setup_duplicate_group
