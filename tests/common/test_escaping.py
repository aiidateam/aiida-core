# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.common.escaping`."""
from aiida.common.escaping import escape_for_bash


def test_escape_for_bash():
    """Tests various inputs for `aiida.common.escaping.escape_for_bash`."""
    tests = (
        [None, ''],
        ['string', "'string'"],
        ['string with space', "'string with space'"],
        ["string with a ' single quote", """'string with a '"'"' single quote'"""],
        [1, "'1'"],
        [2.0, "'2.0'"],
    )

    for string_input, string_escaped in tests:
        assert escape_for_bash(string_input) == string_escaped
