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

from typing import Any

__all__ = ('shallow_copy_nested_dict',)


def shallow_copy_nested_dict(dictionary: dict[Any, Any]) -> dict[Any, Any]:
    """Return a recursive shallow copy of a nested dictionary.

    Nested dictionaries are copied recursively, while all non-dictionary values are kept by reference. This is useful
    for dictionaries containing ORM nodes, where ``copy.deepcopy`` would invoke node-specific copy behavior.
    """
    return {
        key: shallow_copy_nested_dict(value) if isinstance(value, dict) else value
        for key, value in dictionary.items()
    }
