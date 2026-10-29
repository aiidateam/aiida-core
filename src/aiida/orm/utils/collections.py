###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for collections of ORM objects."""

from __future__ import annotations

import typing as t

__all__ = ('shallow_copy_nested_dict',)


def shallow_copy_nested_dict(dictionary: dict[t.Any, t.Any]) -> dict[t.Any, t.Any]:
    """Return a recursive shallow copy of a nested dictionary.

    Use this to modify nested process-input dictionaries without cloning their ORM nodes, as ``copy.deepcopy`` would.
    Only dictionary containers are copied, into plain dictionaries. Other values, including lists, tuples and ORM nodes,
    are kept by reference. Dictionaries inside lists or tuples are therefore not copied either.

    :param dictionary: Dictionary to copy. Nested dictionaries must not contain reference cycles.
    :return: New dictionary with independent nested dictionaries and the original non-dictionary values.
    """
    return {
        key: shallow_copy_nested_dict(value) if isinstance(value, dict) else value for key, value in dictionary.items()
    }
