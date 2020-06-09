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
import pytest  # pylint: disable=unused-import

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
    import os
    from unittest.mock import patch
    from click._termui_impl import Editor

    os.environ['EDITOR'] = request.param
    os.environ['VISUAL'] = request.param

    def edit_file(self, filename):
        import os
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

    def _generate_calculation_node(process_state=ProcessState.FINISHED, exit_status=None):
        """Generate an instance of a `CalculationNode`..

        :param process_state: state to set
        :param exit_status: optional exit status, will be set to `0` if `process_state` is `ProcessState.FINISHED`
        :return: a `CalculationNode` instance.
        """
        from aiida.orm import CalculationNode

        if process_state is ProcessState.FINISHED and exit_status is None:
            exit_status = 0

        node = CalculationNode()
        node.set_process_state(process_state)

        if exit_status is not None:
            node.set_exit_status(exit_status)

        return node

    return _generate_calculation_node
