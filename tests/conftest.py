# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Configuration file for pytest tests."""
import os

import pytest

from aiida.manage.configuration import Config, Profile, get_config

pytest_plugins = ['aiida.manage.tests.pytest_fixtures']  # pylint: disable=invalid-name


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
                '{} {}'.format(editor, filename),  # This is the line that we change removing `shlex_quote`
                env=environ,
                shell=True,
            )
            exit_code = process.wait()
            if exit_code != 0:
                raise click.ClickException('{}: Editing failed!'.format(editor))
        except OSError as exception:
            raise click.ClickException('{}: Editing failed: {}'.format(editor, exception))

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

    def _generate_calc_job(folder, entry_point_name, inputs=None):
        """Fixture to generate a mock `CalcInfo` for testing calculation jobs."""
        from aiida.engine.utils import instantiate_process
        from aiida.manage.manager import get_manager
        from aiida.plugins import CalculationFactory

        manager = get_manager()
        runner = manager.get_runner()

        process_class = CalculationFactory(entry_point_name)
        process = instantiate_process(runner, process_class, **inputs)

        calc_info = process.prepare_for_submission(folder)

        return calc_info

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
def create_empty_config_instance(tmp_path) -> Config:
    """Create a temporary configuration instance.

    This creates a temporary directory with a clean `.aiida` folder and basic configuration file. The currently loaded
    configuration and profile are stored in memory and are automatically restored at the end of this context manager.

    :return: a new empty config instance.
    """
    from aiida.common.utils import Capturing
    from aiida.manage import configuration
    from aiida.manage.configuration import settings, load_profile, reset_profile

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
def create_profile() -> Profile:
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
            'repository_uri': 'file:///' + os.path.join(repository_dirpath, 'repository_' + name),
        }

        return Profile(name, profile_dictionary)

    return _create_profile
