###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the ``--advanced`` flag on ``verdi config list`` (Phase 1d of logging redesign)."""

import pytest

from aiida.cmdline.commands import cmd_verdi


@pytest.mark.presto
def test_config_list_hides_advanced_options(run_cli_command, config_with_profile_factory):
    """By default, ``verdi config list`` should hide advanced per-logger options."""
    config_with_profile_factory()
    result = run_cli_command(cmd_verdi.verdi, ['config', 'list'], use_subprocess=False)

    # The new routing options SHOULD be visible
    assert 'logging.terminal_loglevel' in result.output
    assert 'logging.logfile_loglevel' in result.output

    # The advanced per-logger options should NOT be visible
    assert 'logging.aiida_loglevel' not in result.output
    assert 'logging.plumpy_loglevel' not in result.output
    assert 'logging.kiwipy_loglevel' not in result.output


@pytest.mark.presto
def test_config_list_advanced_shows_all(run_cli_command, config_with_profile_factory):
    """``verdi config list --advanced`` should show all options including advanced ones."""
    config_with_profile_factory()
    result = run_cli_command(cmd_verdi.verdi, ['config', 'list', '--advanced'], use_subprocess=False)

    # Both new and old logging options should be visible
    assert 'logging.terminal_loglevel' in result.output
    assert 'logging.logfile_loglevel' in result.output
    assert 'logging.aiida_loglevel' in result.output
    assert 'logging.plumpy_loglevel' in result.output
    assert 'logging.kiwipy_loglevel' in result.output


@pytest.mark.presto
def test_config_list_footer_hint(run_cli_command, config_with_profile_factory):
    """When advanced options are hidden, a footer hint should be shown."""
    config_with_profile_factory()
    result = run_cli_command(cmd_verdi.verdi, ['config', 'list'], use_subprocess=False)
    assert '--advanced' in result.output


@pytest.mark.presto
def test_config_list_no_footer_hint_with_advanced(run_cli_command, config_with_profile_factory):
    """When ``--advanced`` is specified, the footer hint should NOT be shown."""
    config_with_profile_factory()
    result = run_cli_command(cmd_verdi.verdi, ['config', 'list', '--advanced'], use_subprocess=False)
    # The hint text should not appear when already showing all options
    assert 'Use `verdi config list --advanced` to show all per-logger options.' not in result.output


@pytest.mark.presto
def test_config_list_non_logging_options_visible(run_cli_command, config_with_profile_factory):
    """Non-logging options should always be visible regardless of --advanced."""
    config_with_profile_factory()
    result = run_cli_command(cmd_verdi.verdi, ['config', 'list'], use_subprocess=False)
    assert 'daemon.timeout' in result.output


@pytest.mark.presto
def test_config_list_prefix_filter_with_advanced(run_cli_command, config_with_profile_factory):
    """``verdi config list logging --advanced`` should show all logging options."""
    config_with_profile_factory()
    result = run_cli_command(cmd_verdi.verdi, ['config', 'list', 'logging', '--advanced'], use_subprocess=False)

    assert 'logging.terminal_loglevel' in result.output
    assert 'logging.aiida_loglevel' in result.output
    # Non-logging options should NOT appear when filtering by "logging" prefix
    assert 'daemon.timeout' not in result.output
