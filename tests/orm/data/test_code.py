# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `Code` class."""
# pylint: disable=redefined-outer-name
import pytest

from aiida.orm import Code


@pytest.fixture
def create_codes(tmpdir, aiida_localhost):
    """Create a local and remote `Code` instance."""
    filename = 'add.sh'
    filepath = str(tmpdir / filename)  # Cast the filepath to str as Python 3.5 does not support Path objects for `open`

    with open(filepath, 'w'):
        pass

    code_local = Code(local_executable=filename, files=[filepath]).store()
    code_remote = Code(remote_computer_exec=(aiida_localhost, '/bin/true')).store()

    return code_local, code_remote


@pytest.mark.usefixtures('clear_database_before_test')
def test_get_full_text_info(create_codes):
    """Test the `Code.get_full_text_info` method."""
    for code in create_codes:
        full_text_info = code.get_full_text_info()

        assert isinstance(full_text_info, list)
        assert ['PK', code.pk] in full_text_info
        assert ['UUID', code.uuid] in full_text_info
        assert ['Label', code.label] in full_text_info
        assert ['Description', code.description] in full_text_info

        if code.is_local():
            assert ['Type', 'local'] in full_text_info
            assert ['Exec name', code.get_execname()] in full_text_info
            assert ['List of files/folders:', ''] in full_text_info
        else:
            assert ['Type', 'remote'] in full_text_info
            assert ['Remote machine', code.computer.name] in full_text_info
            assert ['Remote absolute path', code.get_remote_exec_path()] in full_text_info

    for code in create_codes:
        full_text_info = code.get_full_text_info(verbose=True)
        assert ['Calculations', 0] in full_text_info
