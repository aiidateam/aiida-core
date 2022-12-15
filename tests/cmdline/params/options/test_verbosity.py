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
"""Tests for the :class:`~aiida.cmdline.params.options.main.VERBOSITY` option."""
import functools
import logging

import click
import pytest

from aiida.cmdline.params import options
from aiida.cmdline.utils import echo
from aiida.common.log import AIIDA_LOGGER, LOG_LEVELS


@pytest.fixture
def run_cli_command(run_cli_command):
    """Override the ``run_cli_command`` fixture to always run with ``use_subprocess=False`` for tests in this module."""
    return functools.partial(run_cli_command, use_subprocess=False)


@click.command()
@options.VERBOSITY()
def cmd():
    """Test command prints messages through the ``AIIDA_LOGGER`` and the ``CMDLINE_LOGGER``.

    The messages to the ``CMDLINE_LOGGER`` are performed indirect through the utilities of the ``echo`` module.
    """
    for log_level in LOG_LEVELS.values():
        AIIDA_LOGGER.log(log_level, 'aiida')

    echo.echo_debug('verdi')
    echo.echo_info('verdi')
    echo.echo_report('verdi')
    echo.echo_warning('verdi')
    echo.echo_error('verdi')
    echo.echo_critical('verdi')


@pytest.mark.usefixtures('reset_log_level')
def test_default(run_cli_command):
    """Test the command without explicitly specifying the verbosity.

    The default log level is ``REPORT`` so its messages and everything above should show and the rest not.
    """
    result = run_cli_command(cmd, raises=True)

    for log_level_name, log_level in LOG_LEVELS.items():
        if log_level >= logging.REPORT:  # pylint: disable=no-member
            assert f'{log_level_name.capitalize()}: verdi' in result.output
            assert f'{log_level_name.capitalize()}: aiida' in result.output
        else:
            assert f'{log_level_name.capitalize()}: verdi' not in result.output
            assert f'{log_level_name.capitalize()}: aiida' not in result.output


@pytest.mark.parametrize('option_log_level', [level for level in LOG_LEVELS.values() if level != logging.NOTSET])
@pytest.mark.usefixtures('reset_log_level')
def test_explicit(run_cli_command, option_log_level):
    """Test explicitly settings a verbosity"""
    log_level_name = logging.getLevelName(option_log_level)
    result = run_cli_command(cmd, ['--verbosity', log_level_name], raises=True)

    for log_level_name, log_level in LOG_LEVELS.items():
        if log_level >= option_log_level:
            assert f'{log_level_name.capitalize()}: verdi' in result.output
            assert f'{log_level_name.capitalize()}: aiida' in result.output
        else:
            assert f'{log_level_name.capitalize()}: verdi' not in result.output
            assert f'{log_level_name.capitalize()}: aiida' not in result.output


@pytest.mark.usefixtures('reset_log_level', 'override_logging')
def test_config_aiida_loglevel(run_cli_command, caplog):
    """Test the behavior of the ``--verbosity`` option when the ``logging.aiida_loglevel`` config option is set.

    Even though the ``CMDLINE_LOGGER`` is technically a child of the ``AIIDA_LOGLEVEL`` and so normally the former
    should not override the latter, that is actually the desired behavior. The option should ensure that it overrides
    the value of the ``AIIDA_LOGGER`` that may be specified on the profile config.
    """
    # First log a ``DEBUG`` message to the ``AIIDA_LOGGER`` and capture it to see the logger is properly configured.
    message = 'debug test message'

    with caplog.at_level(logging.DEBUG):
        AIIDA_LOGGER.debug(message)

    assert message in caplog.text

    # Now we invoke the command while passing a verbosity level that is higher than is configured for the
    # ``AIIDA_LOGGER``. The explicit verbosity value should override the value configured on the profile.
    option_log_level = logging.WARNING
    option_log_level_name = logging.getLevelName(option_log_level)
    result = run_cli_command(cmd, ['--verbosity', option_log_level_name], raises=True)

    for log_level_name, log_level in LOG_LEVELS.items():
        if log_level >= option_log_level:
            assert f'{log_level_name.capitalize()}: verdi' in result.output
            assert f'{log_level_name.capitalize()}: aiida' in result.output
        else:
            assert f'{log_level_name.capitalize()}: verdi' not in result.output
            assert f'{log_level_name.capitalize()}: aiida' not in result.output
