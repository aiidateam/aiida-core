###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.common.escaping`."""

import pytest

from aiida.common.escaping import escape_for_bash


@pytest.mark.parametrize(
    ('to_escape, expected_single_quotes, expected_double_quotes'),
    (
        (None, '', ''),
        ('string', "'string'", '"string"'),
        ('string with space', "'string with space'", '"string with space"'),
        (
            """string with ' single and " double quote""",
            """'string with '"'"' single and " double quote'""",
            '''"string with ' single and "'"'" double quote"''',
        ),
        (1, "'1'", '"1"'),
        (2.0, "'2.0'", '"2.0"'),
        ('$PWD', "'$PWD'", '"$PWD"'),
    ),
)
def test_escape_for_bash(to_escape, expected_single_quotes, expected_double_quotes):
    """Tests various inputs for `aiida.common.escaping.escape_for_bash`."""
    assert escape_for_bash(to_escape, use_double_quotes=False) == expected_single_quotes
    assert escape_for_bash(to_escape, use_double_quotes=True) == expected_double_quotes
