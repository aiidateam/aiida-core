# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name
"""Collection of ``pytest`` fixtures that are intended for internal use to ``aiida-core`` only.

Fixtures that are intended for use in plugin packages are kept in :mod:`aiida.manage.tests.pytest_fixtures`. They are
loaded in this file as well, such that they can also be used for the tests of ``aiida-core`` itself.
"""
from __future__ import annotations

import copy
import dataclasses
import os
import pathlib
import types
import typing as t
import warnings

import click
import pytest

from aiida import get_profile
from aiida.manage.configuration import Config, Profile, get_config, load_profile

pytest_plugins = ['aiida.manage.tests.pytest_fixtures', 'sphinx.testing.fixtures']  # pylint: disable=invalid-name


@pytest.fixture()
def non_interactive_editor(request):
    """Fixture to patch click's `Editor.edit_file`.

    In `click==7.1` the `Editor.edit_file` command was changed to escape the `os.environ['EDITOR']` command. Our tests
    are currently abusing this variable to define an automated vim command in order to make an interactive command
    non-interactive, and escaping it makes bash interpret the command and its arguments as a single command instead.
    Here we patch the method to remove the escaping of the editor command.

    :param request: the command to set for the editor that is to be called
    """
    from unittest.mock import patch

    from click._termui_impl import Editor

    os.environ['EDITOR'] = request.param
    os.environ['VISUAL'] = request.param

    def edit_file(self, filename):
        import subprocess

        editor = self.get_editor()
        if self.env:
            environ = os.environ.copy()
            environ.update(self.env)
        else:
            environ = None
        try:
            with subprocess.Popen(
                f'{editor} {filename}',  # This is the line that we change removing `shlex_quote`
                env=environ,
                shell=True,
            ) as process:
                exit_code = process.wait()
                if exit_code != 0:
                    raise click.ClickException(f'{editor}: Editing failed!')
        except OSError as exception:
            raise click.ClickException(f'{editor}: Editing failed: {exception}')

    with patch.object(Editor, 'edit_file', edit_file):
        yield


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
def generate_calculation_node():
    """Generate an instance of a `CalculationNode`."""
    from aiida.engine import ProcessState

    def _generate_calculation_node(process_state=ProcessState.FINISHED, exit_status=None, entry_point=None):
        """Generate an instance of a `CalculationNode`..

        :param process_state: state to set
        :param exit_status: optional exit status, will be set to `0` if `process_state` is `ProcessState.FINISHED`
        :return: a `CalculationNode` instance.
        """
        from aiida.orm import CalculationNode

        if process_state is ProcessState.FINISHED and exit_status is None:
            exit_status = 0

        node = CalculationNode(process_type=entry_point)
        node.set_process_state(process_state)

        if exit_status is not None:
            node.set_exit_status(exit_status)

        return node

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

    monkeypatch.setattr(configuration.Config, '_backup', lambda *args, **kwargs: None)

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
    from aiida.manage import configuration, get_manager
    from aiida.manage.configuration import settings

    manager = get_manager()

    # Store the current configuration instance and config directory path
    current_config = configuration.CONFIG
    current_config_path = current_config.dirpath
    current_profile_name = configuration.get_profile().name

    manager.unload_profile()
    configuration.CONFIG = None

    # Set the configuration directory to a temporary directory. This will create the necessary folders for an empty
    # AiiDA configuration and set relevant global variables in :mod:`aiida.manage.configuration.settings`.
    settings.set_configuration_directory(tmp_path)

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
        settings.set_configuration_directory(pathlib.Path(current_config_path))

        # Reload the original profile
        manager.load_profile(current_profile_name)


@pytest.fixture
def profile_factory() -> Profile:
    """Create a new profile instance.

    :return: the profile instance.
    """

    def _create_profile(name='test-profile', **kwargs):

        repository_dirpath = kwargs.pop('repository_dirpath', get_config().dirpath)

        profile_dictionary = {
            'default_user_email': kwargs.pop('default_user_email', 'dummy@localhost'),
            'storage': {
                'backend': kwargs.pop('storage_backend', 'core.psql_dos'),
                'config': {
                    'database_engine': kwargs.pop('database_engine', 'postgresql_psycopg2'),
                    'database_hostname': kwargs.pop('database_hostname', 'localhost'),
                    'database_port': kwargs.pop('database_port', 5432),
                    'database_name': kwargs.pop('database_name', name),
                    'database_username': kwargs.pop('database_username', 'user'),
                    'database_password': kwargs.pop('database_password', 'pass'),
                    'repository_uri': f"file:///{os.path.join(repository_dirpath, f'repository_{name}')}",
                }
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
                }
            },
            'test_profile': kwargs.pop('test_profile', True)
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
    from aiida.manage import get_manager
    return get_manager()


@pytest.fixture
def event_loop(manager):
    """Get the event loop instance of the currently loaded profile.

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
    yield
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
    exc_info: tuple[t.Type[BaseException], BaseException, types.TracebackType] | tuple[None, None,
                                                                                       None] = (None, None, None)
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
def run_cli_command(reset_log_level, aiida_instance, aiida_profile):  # pylint: disable=unused-argument
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
        **kwargs
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

        if use_subprocess:
            result = run_cli_command_subprocess(command, parameters, user_input, aiida_profile.name, suppress_warnings)
        else:
            result = run_cli_command_runner(command, parameters, user_input, initialize_ctx_obj, kwargs)

        if raises:
            assert result.exception is not None, result.output
            assert result.exit_code != 0, result.exit_code
        else:
            import traceback
            assert result.exception is None, ''.join(traceback.format_exception(*result.exc_info))
            assert result.exit_code == 0, (result.exit_code, result.stderr)

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
    from aiida.common import AttributeDict

    if initialize_ctx_obj:
        config = get_config()
        profile = get_profile()
        obj = AttributeDict({'config': config, 'profile': profile})
    else:
        obj = None

    # We need to apply the ``VERBOSITY`` option. When invoked through the command line, this is done by the logic of the
    # ``VerdiCommandGroup``, but when testing commands, the command is retrieved directly from the module which
    # circumvents this machinery.
    command = VerdiCommandGroup.add_verbosity_option(command)

    runner = CliRunner(mix_stderr=False)
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
