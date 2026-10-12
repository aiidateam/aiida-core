###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.common.escaping`."""

import shlex

import pytest
from hypothesis import given
from hypothesis import strategies as st

from aiida.common.escaping import escape_for_bash, escape_for_sql_like, sql_string_match

PRINTABLE = st.characters(blacklist_categories=('Cs', 'Cc'), blacklist_characters='\x00')


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


@given(st.text(alphabet=PRINTABLE, min_size=1))
def test_escape_for_bash_single_quote_round_trip(value):
    """Single-quoted output parses back to the exact input under POSIX rules."""
    assert shlex.split(escape_for_bash(value)) == [value]


@given(st.text(alphabet=PRINTABLE))
def test_sql_like_escape_round_trip(literal):
    """An escaped literal always matches itself."""
    assert sql_string_match(literal, escape_for_sql_like(literal))


def naive_like_match(string, pattern):
    """Reference SQL LIKE matcher: `%` spans any run, `_` one char, `\\` escapes next."""

    def match(string_index, pattern_index):
        while pattern_index < len(pattern):
            token = pattern[pattern_index]
            if token == '\\' and pattern_index + 1 < len(pattern):
                if string_index >= len(string) or string[string_index] != pattern[pattern_index + 1]:
                    return False
                string_index += 1
                pattern_index += 2
            elif token == '%':
                return any(match(end, pattern_index + 1) for end in range(string_index, len(string) + 1))
            elif token == '_':
                if string_index >= len(string):
                    return False
                string_index += 1
                pattern_index += 1
            else:
                if string_index >= len(string) or string[string_index] != token:
                    return False
                string_index += 1
                pattern_index += 1
        return string_index == len(string)

    return match(0, 0)


# Well-formed patterns: every backslash escapes `\\`, `%`, or `_`, which is all `escape_for_sql_like`
# emits. A lone backslash before an ordinary character is interpreted literally by
# `get_regex_pattern_from_sql` but as an escape by standard SQL LIKE; that divergence is out of scope here.
WELLFORMED_PIECE = st.characters(blacklist_categories=('Cs', 'Cc'), blacklist_characters='\x00%_\\') | st.sampled_from(
    ['%', '_', '\\\\', '\\%', '\\_']
)
WELLFORMED_PATTERN = st.lists(WELLFORMED_PIECE, max_size=8).map(''.join)


@given(st.text(alphabet=PRINTABLE, max_size=10), WELLFORMED_PATTERN)
def test_sql_like_matches_reference(string, pattern):
    """`sql_string_match` agrees with the handwritten matcher (no newlines: `.` semantics)."""
    assert sql_string_match(string, pattern) == naive_like_match(string, pattern)
