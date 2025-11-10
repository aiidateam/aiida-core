###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Miscellaneous functions for escaping strings."""

from __future__ import annotations

import re


def escape_for_bash(str_to_escape: str | None, use_double_quotes: bool | None = False) -> str:
    """This function takes any string and escapes it in a way that
    bash will interpret it as a single string.

    Explanation:

    At the end, in the return statement, the string is put within single
    quotes. Therefore, the only thing that I have to escape in bash is the
    single quote character. To do this, I substitute every single
    quote ' with '"'"' which means:

    First single quote: exit from the enclosing single quotes

    Second, third and fourth character: "'" is a single quote character,
    escaped by double quotes

    Last single quote: reopen the single quote to continue the string

    Finally, note that for python I have to enclose the string '"'"'
    within triple quotes to make it work, getting finally: the complicated
    string found below.

    :param str_to_escape: the string to escape.
    :param use_double_quotes: boolean, if ``True``, use double quotes instead of single quotes.
    :return: the escaped string.
    """
    if str_to_escape is None:
        return ''

    str_to_escape = str(str_to_escape)
    if use_double_quotes:
        escaped_quotes = str_to_escape.replace('"', '''"'"'"''')
        escaped = f'"{escaped_quotes}"'
    else:
        escaped_quotes = str_to_escape.replace("'", """'"'"'""")
        escaped = f"'{escaped_quotes}'"

    return escaped


# Mapping of "SQL" tokens into corresponding regex expressions
SQL_TO_REGEX_TOKENS = [  # Remember in the strings below we have to escape backslashes as well for python...
    # so '\\\\' is actually a string with two backslashes, '\\' a string with a single backslash, ...
    ('\\\\', re.escape('\\')),  # Double slash should be interpreted as a literal single backslash by regex
    ('\\%', re.escape('%')),  # literal '\%' should be interpreted as literal % by regex
    ('\\_', re.escape('_')),  # literal '\_' should be interpreted as literal _ by regex
    ('%', '.*'),
    ('_', '.'),
]


def escape_for_sql_like(string: str) -> str:
    """Function that escapes % or _ symbols provided by user

    SQL LIKE syntax summary:

    - ``%`` -> match any number of characters
    - ``_`` -> match exactly one character

    """
    return string.replace('%', '\\%').replace('_', '\\_')


def get_regex_pattern_from_sql(sql_pattern: str) -> str:
    r"""Convert a string providing a pattern to match in SQL
    syntax into a string performing the same match as a regex.

    SQL LIKE syntax summary:

    - ``%`` -> match any number of characters
    - ``_`` -> match exactly one character

    Moreover, ``\`` is the escape character (by default), so:

    - ``\\`` -> single backslash
    - ``\%`` -> literal % symbol
    - ``\_`` -> literal _ symbol

    and moreover the string should begin at the beginning of the line
    and end at the end of the line.

    :param sql_pattern: the string with the pattern in SQL syntax
    :return: a string with the pattern in regex syntax
    """

    def tokenizer(string: str, tokens_to_apply: list[str]) -> str:
        """Recursive function that tokenizes a string using the provided tokens

        :param string: the string to tokenize
        :param tokens_to_apply: the list of tokens still to process (in order: the first will be processed first)
        :return: a tokenized and escaped string for regex
        """
        if tokens_to_apply:
            # We still have tokens to process
            # find the first occurrence of the first token passed in the list
            # note that the order of the tokens list is important, e.g. we need
            # to match first \% and then %
            first, sep, rest = string.partition(tokens_to_apply[0])

            # There is indeed a separator:
            if sep:
                # at least one token was found; therefore I have to map tokens[sep]
                # to the corresponding regex expression (via the dictionary substitution)
                # Moreover, the 'rest' is not empty so I apply recursively `tokenizer`,
                # with ALL tokens passed (there could be more occurrences of tokens_to_apply[0])
                # Instead, for the first part, we know that we found the FIRST occurrence of tokens_to_apply[0]
                # so I pass the list without the first element
                return (
                    tokenizer(first, tokens_to_apply=tokens_to_apply[1:])
                    + dict(SQL_TO_REGEX_TOKENS)[sep]
                    + tokenizer(rest, tokens_to_apply=tokens_to_apply)
                )
            # Here sep is empty: it means also rest is empty, and we just
            # return (recursively) the tokenizer on the first part, avoiding
            # infinite loops
            return tokenizer(first, tokens_to_apply=tokens_to_apply[1:])
        # There is no more token to process: we now have
        # a string that we know we want to consider literally, so
        # we just make sure it's escaped for a regex to avoid
        # that the user passed in weird characters that are valid
        # regex symbols like $ ^ [ ] etc
        return re.escape(string)

    return f'^{tokenizer(sql_pattern, tokens_to_apply=[token_pair[0] for token_pair in SQL_TO_REGEX_TOKENS])}$'


def sql_string_match(string: str, pattern: str) -> bool:
    """Check if the string matches the provided pattern,
    specified using SQL syntax.

    See documentation of :py:func:`~aiida.common.escaping.get_regex_pattern_from_sql`
    for an explanation of the syntax.

    :param string: the string to check
    :param pattern: the SQL pattern
    :return: True if the string matches, False otherwise
    """
    return bool(re.match(get_regex_pattern_from_sql(pattern), string))
