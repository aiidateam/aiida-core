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
"""Configuration file for pytest tests."""
import os

import pytest

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
        import click

        editor = self.get_editor()
        if self.env:
            environ = os.environ.copy()
            environ.update(self.env)
        else:
            environ = None
        try:
            process = subprocess.Popen(
                f'{editor} {filename}',  # This is the line that we change removing `shlex_quote`
                env=environ,
                shell=True,
            )
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
        from aiida.manage.manager import get_manager
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
        from aiida.manage.manager import get_manager
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
def empty_config(tmp_path) -> Config:
    """Create a temporary configuration instance.

    This creates a temporary directory with a clean `.aiida` folder and basic configuration file. The currently loaded
    configuration and profile are stored in memory and are automatically restored at the end of this context manager.

    :return: a new empty config instance.
    """
    from aiida.common.utils import Capturing
    from aiida.manage import configuration
    from aiida.manage.configuration import settings, reset_profile

    # Store the current configuration instance and config directory path
    current_config = configuration.CONFIG
    current_config_path = current_config.dirpath
    current_profile_name = configuration.PROFILE.name

    reset_profile()
    configuration.CONFIG = None

    # Create a temporary folder, set it as the current config directory path and reset the loaded configuration
    settings.AIIDA_CONFIG_FOLDER = str(tmp_path)

    # Create the instance base directory structure, the config file and a dummy profile
    settings.create_instance_directories()

    # The constructor of `Config` called by `load_config` will print warning messages about migrating it
    with Capturing():
        configuration.CONFIG = configuration.load_config(create=True)

    yield get_config()

    # Reset the config folder path and the config instance. Note this will always be executed after the yield no
    # matter what happened in the test that used this fixture.
    reset_profile()
    settings.AIIDA_CONFIG_FOLDER = current_config_path
    configuration.CONFIG = current_config
    load_profile(current_profile_name)


@pytest.fixture
def profile_factory() -> Profile:
    """Create a new profile instance.

    :return: the profile instance.
    """

    def _create_profile(name, **kwargs):

        repository_dirpath = kwargs.pop('repository_dirpath', get_config().dirpath)

        profile_dictionary = {
            'default_user': kwargs.pop('default_user', 'dummy@localhost'),
            'database_engine': kwargs.pop('database_engine', 'postgresql_psycopg2'),
            'database_backend': kwargs.pop('database_backend', 'django'),
            'database_hostname': kwargs.pop('database_hostname', 'localhost'),
            'database_port': kwargs.pop('database_port', 5432),
            'database_name': kwargs.pop('database_name', name),
            'database_username': kwargs.pop('database_username', 'user'),
            'database_password': kwargs.pop('database_password', 'pass'),
            'repository_uri': f"file:///{os.path.join(repository_dirpath, f'repository_{name}')}",
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
            config = config_with_profile_factory(set_as_default=True, name='default', database_backend='django')
            assert config.current_profile.name == 'default'

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
def manager(aiida_profile):  # pylint: disable=unused-argument
    """Get the ``Manager`` instance of the currently loaded profile."""
    from aiida.manage.manager import get_manager
    return get_manager()


@pytest.fixture
def event_loop(manager):
    """Get the event loop instance of the currently loaded profile.

    This is automatically called as a fixture for any test marked with ``@pytest.mark.asyncio``.
    """
    yield manager.get_runner().loop


@pytest.fixture
def backend(manager):
    """Get the ``Backend`` instance of the currently loaded profile."""
    return manager.get_backend()


@pytest.fixture
def communicator(manager):
    """Get the ``Communicator`` instance of the currently loaded profile to communicate with RabbitMQ."""
    return manager.get_communicator()


@pytest.fixture
def skip_if_not_django(backend):
    """Fixture that will skip any test that uses it when a profile is loaded with any other backend then Django."""
    from aiida.orm.implementation.django.backend import DjangoBackend
    if not isinstance(backend, DjangoBackend):
        pytest.skip('this test should only be run for the Django backend.')


@pytest.fixture
def skip_if_not_sqlalchemy(backend):
    """Fixture that will skip any test that uses it when a profile is loaded with any other backend then SqlAlchemy."""
    from aiida.orm.implementation.sqlalchemy.backend import SqlaBackend
    if not isinstance(backend, SqlaBackend):
        pytest.skip('this test should only be run for the SqlAlchemy backend.')


@pytest.fixture(scope='function')
def override_logging():
    """Return a `SandboxFolder`."""
    from aiida.common.log import configure_logging

    config = get_config()

    try:
        config.set_option('logging.aiida_loglevel', 'DEBUG')
        config.set_option('logging.db_loglevel', 'DEBUG')
        configure_logging(with_orm=True)
        yield
    finally:
        config.unset_option('logging.aiida_loglevel')
        config.unset_option('logging.db_loglevel')
        configure_logging(with_orm=True)


@pytest.fixture
def with_daemon():
    """Starts the daemon process and then makes sure to kill it once the test is done."""
    import sys
    import signal
    import subprocess

    from aiida.engine.daemon.client import DaemonClient
    from aiida.cmdline.utils.common import get_env_with_venv_bin

    # Add the current python path to the environment that will be used for the daemon sub process.
    # This is necessary to guarantee the daemon can also import all the classes that are defined
    # in this `tests` module.
    env = get_env_with_venv_bin()
    env['PYTHONPATH'] = ':'.join(sys.path)

    profile = get_config().current_profile
    daemon = subprocess.Popen(
        DaemonClient(profile).cmd_string.split(),
        stderr=sys.stderr,
        stdout=sys.stdout,
        env=env,
    )

    yield

    # Note this will always be executed after the yield no matter what happened in the test that used this fixture.
    os.kill(daemon.pid, signal.SIGTERM)
