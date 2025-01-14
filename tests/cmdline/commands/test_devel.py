###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``verdi devel``."""

import re

import pytest

from aiida.cmdline.commands import cmd_devel
from aiida.orm import Node, ProcessNode, QueryBuilder, WorkChainNode


@pytest.mark.requires_psql
def test_run_sql(run_cli_command):
    """Test ``verdi devel run-sql``."""
    options = ['SELECT COUNT(*) FROM db_dbnode;']
    result = run_cli_command(cmd_devel.devel_run_sql, options)
    assert str(Node.collection.count()) in result.output, result.output


@pytest.mark.usefixtures('aiida_profile_clean')
def test_launch_add(run_cli_command):
    """Test ``verdi devel launch-add``.

    Start with a clean profile such that the functionality that automatically sets up the localhost computer and code is
    tested properly.
    """
    result = run_cli_command(cmd_devel.devel_launch_arithmetic_add)
    assert re.search(r'Warning: No `localhost` computer exists yet: creating and configuring', result.stdout)
    assert re.search(r'Success: ArithmeticAddCalculation<.*> finished successfully', result.stdout)

    node = QueryBuilder().append(ProcessNode, tag='node').order_by({'node': {'ctime': 'desc'}}).first(flat=True)
    assert node.is_finished_ok


@pytest.mark.usefixtures('started_daemon_client')
def test_launch_add_daemon(run_cli_command, submit_and_await):
    """Test ``verdi devel launch-add`` with the ``--daemon`` flag."""
    result = run_cli_command(cmd_devel.devel_launch_arithmetic_add, ['--daemon'])
    assert re.search(r'Submitted calculation', result.stdout)

    node = QueryBuilder().append(ProcessNode, tag='node').order_by({'node': {'ctime': 'desc'}}).first(flat=True)
    submit_and_await(node)
    assert node.is_finished_ok


def test_launch_add_code(run_cli_command, aiida_code_installed):
    """Test ``verdi devel launch-add`` passing an explicit ``Code``."""
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    result = run_cli_command(cmd_devel.devel_launch_arithmetic_add, ['-X', str(code.pk)])
    assert not re.search(r'Warning: No `localhost` computer exists yet: creating and configuring', result.stdout)

    node = QueryBuilder().append(ProcessNode, tag='node').order_by({'node': {'ctime': 'desc'}}).first(flat=True)
    assert node.is_finished_ok


@pytest.mark.usefixtures('aiida_profile_clean')
def test_launch_multiply_add(run_cli_command):
    """Test ``verdi devel launch-multiply-add``.

    Start with a clean profile such that the functionality that automatically sets up the localhost computer and code is
    tested properly.
    """
    result = run_cli_command(cmd_devel.devel_launch_multiply_add)
    assert re.search(r'Warning: No `localhost` computer exists yet: creating and configuring', result.stdout)
    assert re.search(r'Success: MultiplyAddWorkChain<.*> finished successfully', result.stdout)

    node = QueryBuilder().append(WorkChainNode, tag='node').order_by({'node': {'ctime': 'desc'}}).first(flat=True)
    assert node.is_finished_ok


@pytest.mark.usefixtures('started_daemon_client')
def test_launch_multiply_add_daemon(run_cli_command, submit_and_await):
    """Test ``verdi devel launch-multiply-add`` with the ``--daemon`` flag."""
    result = run_cli_command(cmd_devel.devel_launch_multiply_add, ['--daemon'])
    assert re.search(r'Submitted workflow', result.stdout)

    node = QueryBuilder().append(ProcessNode, tag='node').order_by({'node': {'ctime': 'desc'}}).first(flat=True)
    submit_and_await(node)
    assert node.is_finished_ok


def test_launch_add_multiply_code(run_cli_command, aiida_code_installed):
    """Test ``verdi devel launch-multiply-add`` passing an explicit ``Code``."""
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    result = run_cli_command(cmd_devel.devel_launch_multiply_add, ['-X', str(code.pk)])
    assert not re.search(r'Warning: No `localhost` computer exists yet: creating and configuring', result.stdout)

    node = QueryBuilder().append(ProcessNode, tag='node').order_by({'node': {'ctime': 'desc'}}).first(flat=True)
    assert node.is_finished_ok
