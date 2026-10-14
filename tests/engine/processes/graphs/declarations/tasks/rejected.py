###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file       #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Task declarations rejected at decoration shared by the behavior suites."""

import typing as t

__all__ = (
    'kwargs_function',
    'unannotated_function',
)


def unannotated_function(x: int):
    """Reject functions without a return annotation at decoration.

    Static lowering wires placements against declared outputs, so annotate the
    function or wrap it in an annotated one instead of leaving it dynamic.
    """
    return x


def kwargs_function(**kwargs: t.Any) -> int:
    """Reject undecorated functions with kwargs at decoration."""
    return 1
