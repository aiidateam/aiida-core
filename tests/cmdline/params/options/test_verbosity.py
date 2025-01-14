###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :class:`~aiida.cmdline.params.options.main.VERBOSITY` option."""

import functools
import logging

import pytest

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import echo
from aiida.common import log


@pytest.fixture
def run_cli_command(run_cli_command):
    """Override the ``run_cli_command`` fixture to always run with ``use_subprocess=False`` for tests in this module."""
    return functools.partial(run_cli_command, use_subprocess=False)


@verdi.command('test')
def cmd():
    """Test command prints messages through the ``aiida`` and the ``verdi``.

    The messages to the ``verdi`` are performed indirect through the utilities of the ``echo`` module.
    """
    assert 'cli' in [handler.name for handler in log.AIIDA_LOGGER.handlers]

    for log_level in log.LOG_LEVELS.values():
        log.AIIDA_LOGGER.log(log_level, 'aiida')

    echo.echo_debug('verdi')
    echo.echo_info('verdi')
    echo.echo_report('verdi')
    echo.echo_warning('verdi')
    echo.echo_error('verdi')
    echo.echo_critical('verdi')


def verify_log_output(output: str, log_level_aiida: int, log_level_verdi: int):
    """Verify that the expected log messages are in the output for the given log levels

    :param output: The output written to stdout by the command.
    :param log_level_aiida: The expected log level of the ``aiida`` logger.
    :param log_level_verdi: The expected log level of the ``verdi`` logger.
    """
    for log_level_name, log_level in log.LOG_LEVELS.items():
        prefix = log_level_name.capitalize()

        if log_level >= log_level_aiida:
            assert f'{prefix}: aiida' in output
        else:
            assert f'{prefix}: aiida' not in output

        if log_level >= log_level_verdi:
            assert f'{prefix}: verdi' in output
        else:
            assert f'{prefix}: verdi' not in output


@pytest.mark.usefixtures('reset_log_level')
def test_default(run_cli_command):
    """Test the command without explicitly specifying the verbosity.

    The default log level is ``REPORT`` so its messages and everything above should show and the rest not.
    """
    result = run_cli_command(cmd, raises=True)
    verify_log_output(result.output, logging.REPORT, logging.REPORT)


@pytest.mark.parametrize('option_log_level', [level for level in log.LOG_LEVELS.values() if level != logging.NOTSET])
@pytest.mark.usefixtures('reset_log_level')
def test_explicit(run_cli_command, option_log_level):
    """Test explicitly settings a verbosity"""
    log_level_name = logging.getLevelName(option_log_level)
    result = run_cli_command(cmd, ['--verbosity', log_level_name], raises=True)
    verify_log_output(result.output, option_log_level, option_log_level)


@pytest.mark.usefixtures('reset_log_level')
def test_config_option_override(run_cli_command, isolated_config):
    """Test that config log levels are only overridden if the ``--verbosity`` is explicitly passed."""
    isolated_config.set_option('logging.aiida_loglevel', 'ERROR', scope=None)
    isolated_config.set_option('logging.verdi_loglevel', 'WARNING', scope=None)

    # If ``--verbosity`` is not explicitly defined, values from the config options should be used.
    result = run_cli_command(cmd, raises=True, use_subprocess=False)
    verify_log_output(result.output, logging.ERROR, logging.WARNING)

    # Manually reset the ``aiida.common.log.CLI_ACTIVE`` global otherwise the verbosity callback is a no-op
    log.CLI_ACTIVE = None

    # If ``--verbosity`` is explicitly defined, it override both both config options.
    result = run_cli_command(cmd, ['--verbosity', 'INFO'], raises=True, use_subprocess=False)
    verify_log_output(result.output, logging.INFO, logging.INFO)
