###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.cmdline.utils.repository` module."""

import io

import pytest

from aiida.cmdline.utils.repository import list_repository_contents
from aiida.orm import FolderData


@pytest.fixture
def runner():
    """Return a `click` test runner."""
    from click.testing import CliRunner

    return CliRunner()


@pytest.fixture
def folder_data():
    """Create a `FolderData` instance with basic file and directory structure."""
    node = FolderData()
    node.base.repository.put_object_from_filelike(io.StringIO(''), 'nested/file.txt')
    node.base.repository.put_object_from_filelike(io.StringIO(''), 'file.txt')

    return node


def test_list_repository_contents(capsys, folder_data):
    """Test the `list_repository_contents` method."""
    list_repository_contents(folder_data, path='', color=True)
    assert capsys.readouterr().out == 'file.txt\nnested\n'


def test_list_repository_contents_color(runner, folder_data):
    """Test the `list_repository_contents` method.

    The `click` library will automatically strip the ANSI sequences that are used to present color in the terminal when
    echo'ing to anything other then a terminal. Trying to call `list_repository_contents` normally and capturing the
    output will then not contain the sequences so we cannot test the `--color` flag. Instead we run within `click`'s
    `isolation` context manager of the test runner, setting `color=True` which will prevent the ANSI sequences from
    being stripped, allowing us to check for them in the output
    """
    with runner.isolation(color=True) as outstreams:
        list_repository_contents(folder_data, path='', color=True)

    values = outstreams[0].getvalue()
    # \x1b[22m  normal text
    # \x1b[0m   unset sequence
    # \x1b[34m  blue text
    # \x1b[1m   bold text
    assert values == b'\x1b[22mfile.txt\x1b[0m\n\x1b[34m\x1b[1mnested\x1b[0m\n'
