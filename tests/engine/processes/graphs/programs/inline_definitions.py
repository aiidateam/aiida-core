###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Inline definitions shared by the graph behavior suites; rejected at lowering."""

from aiida.engine.processes.graphs.lowering import graph
from tests.engine.processes.graphs.programs.tasks import add


@graph
def inline_class(value: int) -> int:  # rejected at lowering
    """Reject process classes defined inside the body."""

    class InlineWorkChain:
        pass

    return add(x=value, y=1)
