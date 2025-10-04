###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to define commonly used data structures."""

from __future__ import annotations

import pathlib
from typing import Union

# TypeAlias was added in 3.10
# Self was added in 3.11
try:
    from typing import Self, TypeAlias
except ImportError:
    from typing_extensions import Self, TypeAlias

__all__ = ('FilePath', 'Self', 'TypeAlias')


FilePath = Union[str, pathlib.PurePath]
