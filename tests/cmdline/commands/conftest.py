# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Pytest fixtures for command line interface tests."""
import pathlib

import click
import pytest


@pytest.fixture
def run_cli_command():
    """Run a `click` command with the given options.

    The call will raise if the command triggered an exception or the exit code returned is non-zero.
    """
    from click.testing import Result

    def _run_cli_command(command: click.Command, options: list = None, raises: bool = False) -> Result:
        """Run the command and check the result.

        .. note:: the `output_lines` attribute is added to return value containing list of stripped output lines.

        :param options: the list of command line options to pass to the command invocation
        :param raises: whether the command is expected to raise an exception
        :return: test result
        """
        import traceback

        from aiida.cmdline.commands.cmd_verdi import VerdiCommandGroup
        from aiida.common import AttributeDict
        from aiida.manage.configuration import get_config, get_profile

        config = get_config()
        profile = get_profile()
        obj = AttributeDict({'config': config, 'profile': profile})

        # Convert any ``pathlib.Path`` objects in the ``options`` to their absolute filepath string representation.
        # This is necessary because the ``invoke`` command does not support these path objects.
        options = [str(option) if isinstance(option, pathlib.Path) else option for option in options or []]

        # We need to apply the ``VERBOSITY`` option. When invoked through the command line, this is done by the logic
        # of the ``VerdiCommandGroup``, but when testing commands, the command is retrieved directly from the module
        # which circumvents this machinery.
        command = VerdiCommandGroup.add_verbosity_option(command)

        runner = click.testing.CliRunner()
        result = runner.invoke(command, options, obj=obj)

        if raises:
            assert result.exception is not None, result.output
            assert result.exit_code != 0
        else:
            assert result.exception is None, ''.join(traceback.format_exception(*result.exc_info))
            assert result.exit_code == 0, result.output

        result.output_lines = [line.strip() for line in result.output.split('\n') if line.strip()]

        return result

    return _run_cli_command
