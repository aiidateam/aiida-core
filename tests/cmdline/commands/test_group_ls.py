###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for GroupPath command line interface"""

from textwrap import dedent

import pytest
from click.testing import CliRunner

from aiida import orm
from aiida.cmdline.commands.cmd_group import group_path_ls


@pytest.fixture
def setup_groups(aiida_profile_clean):
    """Setup some groups for testing."""
    for label in ['a', 'a/b', 'a/c/d', 'a/c/e/g', 'a/f']:
        group, _ = orm.Group.collection.get_or_create(label)
        group.description = f'A description of {label}'
    orm.UpfFamily.collection.get_or_create('a/x')
    yield


def test_with_no_opts(setup_groups):
    """Test ``verdi group path ls``"""
    cli_runner = CliRunner()

    result = cli_runner.invoke(group_path_ls)
    assert result.exit_code == 0, result.exception
    assert result.output == 'a\n'

    result = cli_runner.invoke(group_path_ls, ['a'])
    assert result.exit_code == 0, result.exception
    assert result.output == 'a/b\na/c\na/f\n'

    result = cli_runner.invoke(group_path_ls, ['a/c'])
    assert result.exit_code == 0, result.exception
    assert result.output == 'a/c/d\na/c/e\n'


def test_recursive(setup_groups):
    """Test ``verdi group path ls --recursive``"""
    cli_runner = CliRunner()

    for tag in ['-R', '--recursive']:
        result = cli_runner.invoke(group_path_ls, [tag])
        assert result.exit_code == 0, result.exception
        assert result.output == 'a\na/b\na/c\na/c/d\na/c/e\na/c/e/g\na/f\n'

        result = cli_runner.invoke(group_path_ls, [tag, 'a/c'])
        assert result.exit_code == 0, result.exception
        assert result.output == 'a/c/d\na/c/e\na/c/e/g\n'


@pytest.mark.parametrize('tag', ['-l', '--long'])
def test_long(setup_groups, tag):
    """Test ``verdi group path ls --long``"""
    cli_runner = CliRunner()

    result = cli_runner.invoke(group_path_ls, [tag])
    assert result.exit_code == 0, result.exception
    assert result.output == dedent(
        """\
        Path      Sub-Groups
        ------  ------------
        a                  4
        """
    )

    result = cli_runner.invoke(group_path_ls, [tag, '-d', 'a'])
    assert result.exit_code == 0, result.exception
    assert result.output == dedent(
        """\
        Path      Sub-Groups  Description
        ------  ------------  --------------------
        a/b                0  A description of a/b
        a/c                2  -
        a/f                0  A description of a/f
        """
    )

    result = cli_runner.invoke(group_path_ls, [tag, '-R'])
    assert result.exit_code == 0, result.exception
    assert result.output == dedent(
        """\
        Path       Sub-Groups
        -------  ------------
        a                   4
        a/b                 0
        a/c                 2
        a/c/d               0
        a/c/e               1
        a/c/e/g             0
        a/f                 0
        """
    )


@pytest.mark.parametrize('tag', ['--no-virtual'])
def test_groups_only(setup_groups, tag):
    """Test ``verdi group path ls --no-virtual``"""
    cli_runner = CliRunner()

    result = cli_runner.invoke(group_path_ls, [tag, '-l', '-R', '--with-description'])
    assert result.exit_code == 0, result.exception
    assert result.output == dedent(
        """\
        Path       Sub-Groups  Description
        -------  ------------  ------------------------
        a                   4  A description of a
        a/b                 0  A description of a/b
        a/c/d               0  A description of a/c/d
        a/c/e/g             0  A description of a/c/e/g
        a/f                 0  A description of a/f
        """
    )
